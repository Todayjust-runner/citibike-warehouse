"""Independently audit hash-pinned public ZIPs; no SQL Server ETL or publication."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
import struct
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HEADER = ['ride_id','rideable_type','started_at','ended_at','start_station_name',
          'start_station_id','end_station_name','end_station_id','start_lat',
          'start_lng','end_lat','end_lng','member_casual']
TIME_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.(\d+))?$')
EPOCH = datetime(1,1,1)
LOWER, UPPER = datetime(2024,7,1), datetime(2024,10,1)
TEXT_LIMITS = {'ride_id':200,'rideable_type':200,'member_casual':200,
               'start_station_id':200,'end_station_id':200,
               'start_station_name':512,'end_station_name':512}


class AuditError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def compact(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True)


def present(value):
    return value if value.strip(' \t\r\n') else None


def identity(value):
    return value.encode('utf-16le') if present(value) is not None else None


def timestamp(value):
    m=TIME_RE.fullmatch(value)
    if not m:return None,0
    fraction=m[3] or ''
    if any(c!='0' for c in fraction[6:]):
        raise AuditError('unrepresentable_time_precision','Nonzero submicrosecond text blocks the audit; no truncation.')
    try:
        dt=datetime.fromisoformat(m[1]+'T'+m[2]+'.'+(fraction[:6].ljust(6,'0')))
    except ValueError:return None,len(fraction)
    return dt,len(fraction)


def micros(dt):
    d=dt-EPOCH
    return (d.days*86400+d.seconds)*1000000+d.microseconds


def fractional_digits(number):
    t=number.as_tuple();exponent=t.exponent;digits=list(t.digits)
    while digits and digits[-1]==0:
        digits.pop();exponent+=1
    return max(0,-exponent) if digits else 0


def coordinate_pair(lat,lng,stats,lat_name,lng_name):
    if present(lat) is None or present(lng) is None:return 'missing',None,False
    try:
        a,b=Decimal(lat),Decimal(lng)
        if not a.is_finite() or not b.is_finite():return 'nonnumeric',None,False
    except InvalidOperation:return 'nonnumeric',None,False
    da,db=fractional_digits(a),fractional_digits(b)
    for name,d in [(lat_name,da),(lng_name,db)]:
        stats[name]['max_fractional_digits']=max(stats[name].get('max_fractional_digits',0),d)
    if not(-90<=a<=90 and -180<=b<=180):return 'out_of_range',None,False
    with localcontext() as ctx:
        ctx.prec=max(80,len(a.as_tuple().digits)+10,len(b.as_tuple().digits)+10)
        canonical=compact([str(a.normalize()),str(b.normalize())])
    return 'valid',canonical,da>15 or db>15


def appledouble(data,name,names):
    # RFC1740 Appendix B: header magic/version and bounded entry descriptors.
    path=PurePosixPath(name)
    if not(name.startswith('__MACOSX/') and path.name.startswith('._')):return False
    if len(data)<26:return False
    magic,version,_,n=struct.unpack('>II16sH',data[:26])
    counterpart=str(PurePosixPath(*path.parts[1:-1])/path.name[2:])
    if magic!=0x00051607 or version!=0x00020000 or counterpart not in names:return False
    if len(data)<26+12*n:return False
    ids=[]
    for i in range(n):
        entry_id,offset,length=struct.unpack('>III',data[26+12*i:38+12*i])
        if offset<26+12*n or offset+length>len(data) or entry_id==1:return False
        ids.append(entry_id)
    return len(set(ids))==n


def decimal_display(numerator,denominator,places=2,multiplier=1):
    if not denominator:return None
    with localcontext() as ctx:
        ctx.prec=80
        return format((Decimal(numerator)*multiplier/Decimal(denominator)).quantize(
            Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP),'f')


def csv_output(folder,name,header,rows):
    path=folder/name
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(header);writer.writerows(rows)
    return {'name':name,'bytes':path.stat().st_size,'sha256':digest_file(path)}


def audit_manifest(manifest_path,output_dir):
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    folder=Path(output_dir);folder.mkdir(parents=True,exist_ok=True)
    fields={c:{'max_utf16_units':0,'empty_or_ascii_blank':0,'nonblank_outer_ascii_whitespace':0} for c in HEADER}
    for c in ['started_at','ended_at','start_lat','start_lng','end_lat','end_lng']:
        fields[c]['max_fractional_digits']=0
    members=[];sidecars=[];coordinate_quality={'start':Counter(),'end':Counter()}
    labels={'rideable_type':Counter(),'member_casual':Counter()};precision_failures=0
    fd,dbpath=tempfile.mkstemp(prefix='source-audit-',suffix='.sqlite3',dir=folder)
    import os
    os.close(fd)
    con=sqlite3.connect(dbpath)
    try:
        con.execute('PRAGMA journal_mode=OFF');con.execute('PRAGMA temp_store=FILE')
        con.execute('''CREATE TABLE raw(rid BLOB,payload TEXT,zip_sha TEXT,member_path BLOB,
          csv_record INTEGER,started TEXT,ended TEXT,started_us INTEGER,ended_us INTEGER,
          duration_us INTEGER,reason TEXT,bike TEXT,member TEXT,start_station BLOB,end_station BLOB,
          start_name TEXT,end_name TEXT,start_coord TEXT,end_coord TEXT)''')
        inventory=[]
        for archive in manifest['archives']:
            path=Path(archive['path_from_repo'])
            if not path.is_absolute():path=ROOT/path
            if not path.is_file() or path.stat().st_size!=archive['bytes'] or digest_file(path)!=archive['sha256']:
                raise AuditError('source_hash_mismatch','Missing or changed ZIP: '+path.name)
            with zipfile.ZipFile(path) as z:
                infos=[i for i in z.infolist() if not i.is_dir()]
                names=[i.filename for i in infos]
                if len(names)!=len(set(names)):
                    raise AuditError('duplicate_zip_member','Duplicate member paths are ambiguous.')
                expected={m['member_path']:m for m in archive['all_members']}
                if set(names)!=set(expected):raise AuditError('member_inventory_mismatch','Member inventory changed.')
                data_members=[]
                for info in infos:
                    h=hashlib.sha256()
                    with z.open(info) as f:
                        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
                    item=expected[info.filename]
                    if info.file_size!=item['bytes'] or h.hexdigest()!=item['sha256']:
                        raise AuditError('member_hash_mismatch','CSV/member bytes do not match manifest.')
                    if info.filename.startswith('__MACOSX/') and PurePosixPath(info.filename).name.startswith('._'):
                        if info.file_size>1024*1024 or not appledouble(z.read(info),info.filename,names):
                            raise AuditError('unrecognized_sidecar','Cannot skip a file by name alone.')
                        sidecars.append({'zip_sha256':archive['sha256'],'member_path':info.filename,
                                         'kind':'appledouble_metadata','sha256':item['sha256'],'bytes':item['bytes']})
                    elif info.filename.lower().endswith('.csv'):
                        data_members.append(info)
                    else:raise AuditError('unrecognized_archive_member','Unclassified archive member: '+info.filename)
                if not data_members:raise AuditError('no_csv_members','No data CSV member in archive.')
                for info in sorted(data_members,key=lambda i:i.filename.encode('utf-8')):
                    item=expected[info.filename];inventory.append([archive['sha256'],info.filename,item['sha256']])
                    count=0;bad_end_month=0;time_parse_errors=0;time_ranges={};batch=[]
                    with io.TextIOWrapper(z.open(info),encoding='utf-8-sig',newline='') as f:
                        reader=csv.reader(f,strict=True)
                        if next(reader,None)!=HEADER:raise AuditError('invalid_header','Header/order differs from all thirteen fields.')
                        for record_no,cells in enumerate(reader,2):
                            if len(cells)!=13:raise AuditError('invalid_field_count','Malformed CSV record blocks audit.')
                            count+=1
                            for c,v in zip(HEADER,cells):
                                s=fields[c];s['max_utf16_units']=max(s['max_utf16_units'],len(v.encode('utf-16le'))//2)
                                s['empty_or_ascii_blank']+=present(v) is None
                                s['nonblank_outer_ascii_whitespace']+=present(v) is not None and v!=v.strip(' \t\r\n')
                            started,sp=timestamp(cells[2]);ended,ep=timestamp(cells[3])
                            for key,dt,digits in [('started_at',started,sp),('ended_at',ended,ep)]:
                                fields[key]['max_fractional_digits']=max(fields[key]['max_fractional_digits'],digits)
                                if dt:
                                    iso=dt.isoformat(timespec='microseconds');bounds=time_ranges.setdefault(key,[iso,iso])
                                    bounds[0]=min(bounds[0],iso);bounds[1]=max(bounds[1],iso)
                            if not started or not ended:time_parse_errors+=1
                            if not ended or ended.strftime('%Y%m')!=archive['month']:bad_end_month+=1
                            su,eu=micros(started) if started else None,micros(ended) if ended else None
                            duration=eu-su if su is not None and eu is not None else None
                            reason=('TIME_PARSE_ERROR' if duration is None else 'NONPOSITIVE_DURATION' if duration<=0
                                    else 'DURATION_LT_60S' if duration<60000000 else 'DURATION_GT_24H' if duration>86400000000 else 'NONE')
                            sq,sc,sfail=coordinate_pair(cells[8],cells[9],fields,'start_lat','start_lng')
                            eq,ec,efail=coordinate_pair(cells[10],cells[11],fields,'end_lat','end_lng')
                            coordinate_quality['start'][sq]+=1;coordinate_quality['end'][eq]+=1
                            precision_failures+=sfail+efail
                            labels['rideable_type'][cells[1]]+=1;labels['member_casual'][cells[12]]+=1
                            batch.append((identity(cells[0]),compact(cells),archive['sha256'],info.filename.encode('utf-8'),record_no,
                                started.isoformat(timespec='microseconds') if started else None,
                                ended.isoformat(timespec='microseconds') if ended else None,su,eu,duration,reason,
                                cells[1],cells[12],identity(cells[5]),identity(cells[7]),present(cells[4]),present(cells[6]),sc,ec))
                            if len(batch)>=5000:
                                con.executemany('INSERT INTO raw VALUES('+','.join('?'*19)+')',batch);batch.clear()
                        if batch:con.executemany('INSERT INTO raw VALUES('+','.join('?'*19)+')',batch)
                    members.append({'zip_month':archive['month'],'zip_sha256':archive['sha256'],
                        'member_path':info.filename,'csv_sha256':item['sha256'],'header':HEADER,'data_records':count,
                        'csv_record_number_first':2 if count else None,'csv_record_number_last':count+1 if count else None,
                        'ended_month_mismatches':bad_end_month,'time_parse_errors':time_parse_errors,'time_ranges':time_ranges,
                        'member_path_utf16_units':len(info.filename.encode('utf-16le'))//2})
            con.commit()
            print('Audited '+archive['month']+' data CSVs',file=sys.stderr,flush=True)
        con.execute('CREATE INDEX raw_identity ON raw(rid)')
        con.execute('CREATE TABLE groups AS SELECT rid,COUNT(*) n,COUNT(DISTINCT payload) variants FROM raw WHERE rid IS NOT NULL GROUP BY rid')
        con.execute('CREATE UNIQUE INDEX group_identity ON groups(rid)')
        con.execute('''CREATE TABLE accepted AS SELECT * FROM(
          SELECT r.*,r.rowid audit_row,ROW_NUMBER() OVER(PARTITION BY r.rid ORDER BY zip_sha,member_path,csv_record) rn
          FROM raw r JOIN groups g ON g.rid=r.rid WHERE g.variants=1 AND r.reason='NONE') WHERE rn=1''')
        source_rows=con.execute('SELECT COUNT(*) FROM raw').fetchone()[0]
        accepted=con.execute('SELECT COUNT(*) FROM accepted').fetchone()[0]
        valid_rows=con.execute("SELECT COUNT(*) FROM raw r JOIN groups g ON g.rid=r.rid WHERE variants=1 AND reason='NONE'").fetchone()[0]
        duplicates=valid_rows-accepted
        rejected=dict(con.execute('''SELECT final_reason,COUNT(*) FROM(
          SELECT CASE WHEN r.rid IS NULL THEN 'MISSING_RIDE_ID' WHEN g.variants>1 THEN 'CONFLICTING_RIDE_ID' ELSE r.reason END final_reason
          FROM raw r LEFT JOIN groups g ON g.rid=r.rid) WHERE final_reason<>'NONE' GROUP BY final_reason'''))
        lower,upper=micros(LOWER),micros(UPPER)
        def totals(where,params):
            return con.execute('''SELECT COUNT(*),COALESCE(SUM(duration_us),0),
              COALESCE(SUM(member='member'),0),COALESCE(SUM(member IN('member','casual')),0)
              FROM accepted WHERE '''+where,params).fetchone()
        n,duration,member,known=totals('started_us>=? AND started_us<?',(lower,upper))
        arrivals=con.execute('SELECT COUNT(*) FROM accepted WHERE ended_us>=? AND ended_us<?',(lower,upper)).fetchone()[0]
        unknown_dep=con.execute('SELECT COUNT(*) FROM accepted WHERE started_us>=? AND started_us<? AND start_station IS NULL',(lower,upper)).fetchone()[0]
        unknown_arr=con.execute('SELECT COUNT(*) FROM accepted WHERE ended_us>=? AND ended_us<? AND end_station IS NULL',(lower,upper)).fetchone()[0]
        metrics={'ride_count':n,'duration_us':str(duration),'avg_duration_minutes_display':decimal_display(duration,n*60000000),
            'member_count':member,'known_member_type_count':known,'unknown_member_type_count':n-known,
            'member_share_display':(decimal_display(member,known,multiplier=100)+'%') if known else None,
            'member_type_coverage':decimal_display(known,n,12),'departures':n,'arrivals':arrivals,
            'net_outflow':n-arrivals,'unknown_departures':unknown_dep,'unknown_arrivals':unknown_arr}
        month_rows=[]
        for month,mn,md,mm,mk in con.execute('''SELECT SUBSTR(started,1,7),COUNT(*),SUM(duration_us),SUM(member='member'),SUM(member IN('member','casual'))
          FROM accepted WHERE started_us>=? AND started_us<? GROUP BY SUBSTR(started,1,7) ORDER BY 1''',(lower,upper)):
            month_rows.append({'month':month,'ride_count':mn,'duration_us':str(md),'member_count':mm,'known_member_type_count':mk,
                'avg_duration_minutes_display':decimal_display(md,mn*60000000),'member_share_display':decimal_display(mm,mk,multiplier=100)+'%' if mk else None})
        station_rows=[]
        for sid,dep,arr in con.execute('''SELECT station,SUM(dep),SUM(arr) FROM(
          SELECT start_station station,1 dep,0 arr FROM accepted WHERE started_us>=? AND started_us<?
          UNION ALL SELECT end_station,0,1 FROM accepted WHERE ended_us>=? AND ended_us<?)
          GROUP BY station ORDER BY station''',(lower,upper,lower,upper)):
            station_rows.append({'station_id':sid.decode('utf-16le') if sid is not None else None,
                'is_unknown':sid is None,'departures':dep,'arrivals':arr,'net_outflow':dep-arr})
        boundary_rows=list(con.execute('''SELECT CASE WHEN started_us<? THEN 'entering' ELSE 'leaving' END,
          zip_sha,member_path,csv_record,started,ended FROM accepted
          WHERE (started_us<? AND ended_us>=? AND ended_us<?) OR (started_us>=? AND started_us<? AND ended_us>=?)
          ORDER BY zip_sha,member_path,csv_record''',(lower,lower,lower,upper,lower,upper,upper)))
        boundary_counts=Counter(r[0] for r in boundary_rows)
        observed=con.execute('''WITH observations AS(
          SELECT start_station station,start_name name,start_coord coord FROM accepted
          UNION ALL SELECT end_station,end_name,end_coord FROM accepted)
          SELECT COUNT(*),COALESCE(SUM(names>1),0),COALESCE(SUM(coords>1),0) FROM(
          SELECT station,COUNT(DISTINCT name) names,COUNT(DISTINCT coord) coords
          FROM observations WHERE station IS NOT NULL GROUP BY station)''').fetchone()
        outputs=[csv_output(folder,'monthly.csv',list(month_rows[0]) if month_rows else ['month','ride_count'],
            [list(r.values()) for r in month_rows]),
            csv_output(folder,'station-flow.csv',['station_id','is_unknown','departures','arrivals','net_outflow'],
                       [list(r.values()) for r in station_rows]),
            csv_output(folder,'boundary-records.csv',['direction','zip_sha256','member_path','csv_record_number','started_at','ended_at'],
                       [[a,b,c.decode('utf-8'),d,e,f] for a,b,c,d,e,f in boundary_rows])]
        overlong=[c for c,limit in TEXT_LIMITS.items() if fields[c]['max_utf16_units']>limit]
        long_paths=[m['member_path'] for m in members if m['member_path_utf16_units']>512]
        physical={'version':'B2-1.1','ok':not(overlong or long_paths or precision_failures),
                  'overlong_fields':overlong,'overlong_member_paths':long_paths,
                  'valid_coordinate_pairs_exceeding_scale_15':precision_failures,
                  'time_semantics':'source text without offset; no timezone conversion'}
        input_list=sorted(inventory,key=lambda t:(t[0],t[1].encode('utf-8')))
        # This fingerprint intentionally uses arrays and no key sorting/normalization.
        input_hash=hashlib.sha256(json.dumps(input_list,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
        result={'audit_version':'source-audit-1.0','snapshot_id':manifest['snapshot_id'],
            'input_set_sha256':input_hash,'scope':'Full public source audit only; no SQL Server ETL, query API or publication.',
            'source_rows':source_rows,'members':members,'archive_sidecars':sidecars,'fields':fields,
            'labels':{k:dict(sorted(v.items())) for k,v in labels.items()},
            'quality':{'outcomes':{'ACCEPTED':accepted,'DUPLICATE_EXACT':duplicates,'REJECTED':source_rows-valid_rows},
                'rejected_reasons':rejected,'duplicate_id_groups':con.execute('SELECT COUNT(*) FROM groups WHERE n>1').fetchone()[0],
                'conflicting_id_groups':con.execute('SELECT COUNT(*) FROM groups WHERE variants>1').fetchone()[0],
                'coordinates':{k:dict(sorted(v.items())) for k,v in coordinate_quality.items()},
                'conservation_ok':accepted+duplicates+sum(rejected.values())==source_rows},
            'physical_fit':physical,'window':{'start_inclusive':LOWER.isoformat(),'end_exclusive':UPPER.isoformat(),'bike_filter':None},
            'metrics':metrics,'departure_months':month_rows,'boundary':{'entering':boundary_counts['entering'],'leaving':boundary_counts['leaving']},
            'station_observations':{'real_station_ids':observed[0],'multiple_nonempty_names':observed[1],'multiple_valid_coordinate_pairs':observed[2]},
            'station_example_HB102':next((r for r in station_rows if r['station_id']=='HB102'),None),
            'ended_month_rule_observed_all_rows':all(m['ended_month_mismatches']==0 for m in members),
            'local_outputs':outputs}
        result['semantic_sha256']=hashlib.sha256(compact(result).encode('utf-8')).hexdigest()
        result['execution']={'generated_at_utc':datetime.now(timezone.utc).isoformat(),
            'code_sha256':digest_file(Path(__file__)),'source_database_written':False,
            'A_original_hash_identity':'unverified_without_A_manifest'}
        return result
    except (csv.Error,UnicodeError,zipfile.BadZipFile) as error:
        raise AuditError('invalid_csv_or_archive',str(error)) from error
    finally:
        con.close()
        Path(dbpath).unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=ROOT/'inputs/public-source-snapshot.json')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'data/audit/public-jc-20261113')
    parser.add_argument('--summary',type=Path,default=ROOT/'docs/evidence/public-source-audit.json')
    args=parser.parse_args()
    try:
        result=audit_manifest(args.manifest,args.output_dir)
        args.summary.parent.mkdir(parents=True,exist_ok=True)
        args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({k:result[k] for k in ['snapshot_id','source_rows','metrics','physical_fit','semantic_sha256']},ensure_ascii=False,indent=2))
        return 0 if result['physical_fit']['ok'] else 1
    except (AuditError,OSError,ValueError,sqlite3.Error) as error:
        print(json.dumps({'ok':False,'kind':getattr(error,'kind','source_audit_error'),'message':str(error)},ensure_ascii=False))
        return 2


if __name__=='__main__':raise SystemExit(main())
