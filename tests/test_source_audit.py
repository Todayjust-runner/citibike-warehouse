"""Independent tiny ZIP fixtures; never assert the real A numbers here."""
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HEADER = ['ride_id','rideable_type','started_at','ended_at','start_station_name',
          'start_station_id','end_station_name','end_station_id','start_lat',
          'start_lng','end_lat','end_lng','member_casual']


def row(ride='r1', start='2024-07-01 12:00:00.123',
        end='2024-07-01 12:01:00.123', member='member', station='A', name='Station A'):
    return [ride,'classic_bike',start,end,name,'A',name,station,
            '40.7','-74.0','40.7' if station else '', '-74.0' if station else '',member]


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='citibike-source-test-')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location('source_audit', ROOT/'scripts/audit_public_source.py')
        self.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.audit)

    def manifest(self, parts, sidecar=None):
        archive = self.folder/'fixture.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for name, rows in parts.items():
                stream=io.StringIO(newline='');writer=csv.writer(stream)
                writer.writerow(HEADER);writer.writerows(rows)
                z.writestr(name,stream.getvalue().encode('utf-8'))
            if sidecar is not None:
                z.writestr('__MACOSX/._part-a.csv',sidecar)
        with zipfile.ZipFile(archive) as z:
            members=[{'member_path':n,'bytes':len(z.read(n)),
                      'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist()]
        manifest={'snapshot_id':'SYNTHETIC-SOURCE-TEST','archives':[{
            'month':'202407','url':'https://example.invalid/SYNTHETIC.zip',
            'path_from_repo':str(archive),'bytes':archive.stat().st_size,
            'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'all_members':members}]}
        path=self.folder/'manifest.json';path.write_text(json.dumps(manifest),encoding='utf-8')
        return path

    def run_audit(self, manifest, suffix='first'):
        return self.audit.audit_manifest(manifest,self.folder/suffix)

    def test_conflicting_group_wins_and_invalid_duplicates_are_all_rejected(self):
        good=row();conflict=row('conflict');bad=row('conflict',start='bad')
        invalid=row('invalid',start='bad')
        manifest=self.manifest({'part-a.csv':[good,conflict,conflict,invalid],
                                'part-b.csv':[good,bad,invalid,row(' \t')]})
        r=self.run_audit(manifest)
        self.assertEqual(r['quality']['outcomes'],{'ACCEPTED':1,'DUPLICATE_EXACT':1,'REJECTED':6})
        self.assertEqual(r['quality']['rejected_reasons'],
                         {'CONFLICTING_RIDE_ID':3,'MISSING_RIDE_ID':1,'TIME_PARSE_ERROR':2})
        self.assertEqual(r['metrics']['ride_count'],1)
        self.assertEqual(len(r['members']),2)

    def test_arrivals_use_their_own_window_and_member_denominator_excludes_unknown(self):
        rows=[row('enter','2024-06-30 23:59:00','2024-07-01 00:00:00'),
              row('leave','2024-09-30 23:59:00','2024-10-01 00:00:00'),
              row('inside',end='2024-07-01 12:02:00.123',member='casual'),
              row('unknown',member='other',station='')]
        r=self.run_audit(self.manifest({'part-a.csv':rows}))
        m=r['metrics']
        self.assertEqual((m['ride_count'],m['arrivals'],m['net_outflow']),(3,3,0))
        self.assertEqual((m['member_count'],m['known_member_type_count']),(1,2))
        self.assertEqual(m['member_share_display'],'50.00%')
        self.assertEqual(m['duration_us'],'240000000')
        self.assertEqual(m['avg_duration_minutes_display'],'1.33')
        self.assertEqual(m['unknown_arrivals'],1)
        self.assertEqual(r['boundary']['entering'],1)
        self.assertEqual(r['boundary']['leaving'],1)

    def test_case_and_nonblank_outer_space_identities_remain_distinct(self):
        r=self.run_audit(self.manifest({'part-a.csv':[row('abc'),row('ABC'),row('abc ')]}))
        self.assertEqual(r['metrics']['ride_count'],3)
        self.assertEqual(r['quality']['duplicate_id_groups'],0)

    def test_microseconds_are_exact_and_zero_denominator_is_null(self):
        r=self.run_audit(self.manifest({'part-a.csv':[row(end='2024-07-01 12:01:00.123001',member='new')]}))
        self.assertEqual(r['metrics']['duration_us'],'60000001')
        self.assertIsNone(r['metrics']['member_share_display'])
        self.assertEqual(r['fields']['ended_at']['max_fractional_digits'],6)

    def test_nonzero_submicrosecond_is_a_blocker_not_silently_truncated(self):
        manifest=self.manifest({'part-a.csv':[row(end='2024-07-01 12:01:00.1230001')]})
        with self.assertRaises(self.audit.AuditError) as error:self.run_audit(manifest)
        self.assertEqual(error.exception.kind,'unrepresentable_time_precision')

    def test_macos_sidecar_is_not_counted_as_trip_csv(self):
        sidecar=b'Mac metadata, not a ride CSV'
        r=self.run_audit(self.manifest({'part-a.csv':[row()]},sidecar))
        self.assertEqual(r['source_rows'],1)
        self.assertEqual(len(r['members']),1)
        self.assertEqual(len(r['archive_sidecars']),1)
        self.assertEqual(r['archive_sidecars'][0]['kind'],'appledouble_metadata')

    def test_manifest_hash_mismatch_refuses_changed_input(self):
        manifest=self.manifest({'part-a.csv':[row()]})
        (self.folder/'fixture.zip').write_bytes(b'changed')
        with self.assertRaises(self.audit.AuditError) as error:self.run_audit(manifest)
        self.assertEqual(error.exception.kind,'source_hash_mismatch')

    def test_multiline_cell_uses_csv_record_number_and_rerun_is_stable(self):
        record=row('enter','2024-06-30 23:59:00','2024-07-01 00:00:00',name='A\n第二行')
        manifest=self.manifest({'part-a.csv':[record]})
        a=self.run_audit(manifest);b=self.run_audit(manifest,'second')
        self.assertEqual(a['source_rows'],1)
        self.assertEqual(a['semantic_sha256'],b['semantic_sha256'])
        with (self.folder/'first/boundary-records.csv').open(encoding='utf-8',newline='') as f:
            self.assertEqual(next(csv.DictReader(f))['csv_record_number'],'2')

    def test_utf16_units_and_coordinate_precision_are_checked_before_binding(self):
        r=row('😀'*101);r[8]='40.12345678901234567'
        result=self.run_audit(self.manifest({'part-a.csv':[r]}))
        self.assertEqual(result['fields']['ride_id']['max_utf16_units'],202)
        self.assertFalse(result['physical_fit']['ok'])
        self.assertIn('ride_id',result['physical_fit']['overlong_fields'])
        self.assertEqual(result['fields']['start_lat']['max_fractional_digits'],17)


if __name__=='__main__':unittest.main()
