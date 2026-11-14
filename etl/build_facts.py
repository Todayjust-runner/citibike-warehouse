# -*- coding: utf-8 -*-
"""阶段 3：事实加工（ODS → 判定去向 → dim.station / dwd.fact_trip / meta.row_disposition / coverage）。

判定流水线（source-to-target.md 唯一主去向与优先级）：
  1. ride_id 缺失（空或仅 ASCII 空白）→ 逐行 REJECTED / MISSING_RIDE_ID
  2. 同 ride_id 分组，13 字段原文有差异 → 整组 REJECTED / CONFLICTING_RIDE_ID
  3. 时间解析失败 → 整组 REJECTED / TIME_PARSE_ERROR
  4. 时长 <=0 → NONPOSITIVE_DURATION；<60s → DURATION_LT_60S；>24h → DURATION_GT_24H（整组）
  5. 有效组按 (zip_sha256, member_path, csv_record_number) 选代表 ACCEPTED，其余 DUPLICATE_EXACT
时长为精确整数微秒；亚微秒不可表达属运行错误（FAILED），不静默舍入。
坐标按对检查：任一缺失 missing → 解析失败 nonnumeric → 越界 out_of_range → valid；
无效侧两坐标均置 NULL，事实保留。

用法：python -X utf8 etl/build_facts.py --run-id <阶段1的run_id>
"""
import argparse
import csv
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from common import (ROOT, EtlError, Sqlcmd, batch_insert, sql_int, sql_nstr,
                    sql_str, validate_database)

RAW_DIR = ROOT / 'data/raw/citibike_jc/snapshot_20261113'
EVIDENCE_DIR = ROOT / 'docs/evidence'
ASCII_BLANK = ' \t\r\n'
TIME_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,7}))?$')
US_PER_SECOND = 1_000_000
MIN_US = 60 * US_PER_SECOND            # 60 秒，含边界
MAX_US = 24 * 3600 * US_PER_SECOND     # 24 小时，含边界

FIELDS = ['ride_id', 'rideable_type', 'started_at', 'ended_at', 'start_station_name',
          'start_station_id', 'end_station_name', 'end_station_id', 'start_lat',
          'start_lng', 'end_lat', 'end_lng', 'member_casual']


def parse_time_us(text):
    """'YYYY-MM-DD HH:MM:SS[.f..]' → (基准datetime, 微秒部分)。亚微秒返回 'submicro'。"""
    m = TIME_RE.match(text)
    if not m:
        return None
    frac = m.group(7) or ''
    if len(frac) > 6 and int(frac[6:]) != 0:
        return 'submicro'  # 亚微秒不可无损表达：运行错误，不静默舍入
    base = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                    int(m.group(4)), int(m.group(5)), int(m.group(6)))
    micros = int((frac + '000000')[:6]) if frac else 0
    return base, micros


def to_us(base, micros):
    epoch = datetime(1970, 1, 1)
    return int((base - epoch).total_seconds()) * US_PER_SECOND + micros


def sql_dt(base, micros):
    return "'{}.{:06d}'".format(base.strftime('%Y-%m-%d %H:%M:%S'), micros)


def is_blank(text):
    return text is None or text.strip(ASCII_BLANK) == ''


def coord_pair(lat_raw, lng_raw):
    """按对检查坐标 → (status, lat_text, lng_text)；无效时两个值均为 None。"""
    if is_blank(lat_raw) or is_blank(lng_raw):
        return 'missing', None, None
    try:
        lat, lng = float(lat_raw), float(lng_raw)
    except ValueError:
        return 'nonnumeric', None, None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return 'out_of_range', None, None
    return 'valid', lat_raw.strip(), lng_raw.strip()


def date_key(base):
    return base.year * 10000 + base.month * 100 + base.day


def load_ods_rows(client, database):
    """从 ODS 取回全部源行（按成员分块），附 zip 哈希用于代表行排序。"""
    members = client.query(
        'SELECT source_member_id, zip_sha256, member_path FROM meta.source_member', database)
    rows = []
    for member in members:
        part = client.query(
            'SELECT source_row_id, csv_record_number, ride_id_raw, rideable_type_raw,'
            'started_at_raw, ended_at_raw, start_station_name_raw, start_station_id_raw,'
            'end_station_name_raw, end_station_id_raw, start_lat_raw, start_lng_raw,'
            'end_lat_raw, end_lng_raw, member_casual_raw FROM ods.trip_raw '
            'WHERE source_member_id=' + sql_int(member['source_member_id']), database)
        for r in part:
            r['zip_sha256'] = member['zip_sha256']
            r['member_path'] = member['member_path']
        rows.extend(part)
    return members, rows


def judge(rows):
    """判定流水线：返回 (dispositions, accepted代表列表)。
    dispositions: source_row_id -> (outcome, primary_reason, representative_source_row_id)
    accepted: 代表行记录列表，附解析结果。"""
    dispositions = {}
    groups = {}
    for r in rows:
        ride_id = r['ride_id_raw']
        if is_blank(ride_id):
            dispositions[r['source_row_id']] = ('REJECTED', 'MISSING_RIDE_ID', None)
        else:
            groups.setdefault(ride_id, []).append(r)

    accepted = []
    for ride_id, group in groups.items():
        first = group[0]
        keys = ['ride_id_raw', 'rideable_type_raw', 'started_at_raw', 'ended_at_raw',
                'start_station_name_raw', 'start_station_id_raw', 'end_station_name_raw',
                'end_station_id_raw', 'start_lat_raw', 'start_lng_raw', 'end_lat_raw',
                'end_lng_raw', 'member_casual_raw']
        conflict = any(any(g[k] != first[k] for k in keys) for g in group[1:])
        if conflict:
            for g in group:
                dispositions[g['source_row_id']] = ('REJECTED', 'CONFLICTING_RIDE_ID', None)
            continue
        t1, t2 = parse_time_us(first['started_at_raw']), parse_time_us(first['ended_at_raw'])
        if t1 == 'submicro' or t2 == 'submicro':
            raise EtlError('precision', '存在亚微秒源时间，无法整数微秒无损表达，停止发布')
        if t1 is None or t2 is None:
            for g in group:
                dispositions[g['source_row_id']] = ('REJECTED', 'TIME_PARSE_ERROR', None)
            continue
        duration = to_us(*t2) - to_us(*t1)
        reason = None
        if duration <= 0:
            reason = 'NONPOSITIVE_DURATION'
        elif duration < MIN_US:
            reason = 'DURATION_LT_60S'
        elif duration > MAX_US:
            reason = 'DURATION_GT_24H'
        if reason:
            for g in group:
                dispositions[g['source_row_id']] = ('REJECTED', reason, None)
            continue
        # 有效组：按 (zip哈希, 成员路径, 记录号) 升序选代表
        group.sort(key=lambda g: (g['zip_sha256'], g['member_path'].encode('utf-8'),
                                  g['csv_record_number']))
        rep = group[0]
        rep['_t'] = (t1, t2, duration)
        accepted.append(rep)
        for g in group:
            if g is rep:
                dispositions[g['source_row_id']] = ('ACCEPTED', 'NONE', g['source_row_id'])
            else:
                dispositions[g['source_row_id']] = ('DUPLICATE_EXACT', 'NONE',
                                                    rep['source_row_id'])
    accepted.sort(key=lambda g: (g['zip_sha256'], g['member_path'].encode('utf-8'),
                                 g['csv_record_number']))
    return dispositions, accepted


def build_stations(accepted):
    """站点快照：站名/坐标分别从接受代表行的两端观察中取事件时间最新值；
    并列按源行序升序、start 角色在 end 前。"""
    observations = {}  # station_id -> {'name': (key, name, row_id), 'coord': (key, lat, lng, row_id, role)}

    def better(cand, cur):
        """cand/cur 的排序键：(事件微秒, 源行序, 角色序)。时间晚者胜；并列时源行序小者胜；再并列 start 胜。"""
        if cur is None:
            return True
        if cand[0] != cur[0]:
            return cand[0] > cur[0]
        if cand[1] != cur[1]:
            return cand[1] < cur[1]
        return cand[2] < cur[2]

    for r in accepted:
        (t1, t2, _dur) = r['_t']
        seq = (r['zip_sha256'], r['member_path'].encode('utf-8'), r['csv_record_number'])
        for role, sid, sname, lat_raw, lng_raw, event in (
                ('start', r['start_station_id_raw'], r['start_station_name_raw'],
                 r['start_lat_raw'], r['start_lng_raw'], t1),
                ('end', r['end_station_id_raw'], r['end_station_name_raw'],
                 r['end_lat_raw'], r['end_lng_raw'], t2)):
            if is_blank(sid):
                continue
            slot = observations.setdefault(sid, {'name': None, 'coord': None})
            key = (to_us(*event), seq, 0 if role == 'start' else 1)
            if not is_blank(sname) and better(key, slot['name'] and slot['name'][0]):
                slot['name'] = (key, sname, r['source_row_id'])
            status, lat, lng = coord_pair(lat_raw, lng_raw)
            if status == 'valid' and better(key, slot['coord'] and slot['coord'][0]):
                slot['coord'] = (key, lat, lng, r['source_row_id'], role)
    return observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='localhost')
    parser.add_argument('--database', default='CitibikeDW_B_Test')
    parser.add_argument('--allow-target', action='store_true')
    parser.add_argument('--run-id', required=True, help='阶段 1 ODS 导入的 run_id')
    parser.add_argument('--check-only', action='store_true',
                        help='只运行判定流水线并打印统计，不写数据库（彩排）')
    args = parser.parse_args()
    try:
        database = validate_database(args.database, args.allow_target)
        client = Sqlcmd(args.server)
        run_id = args.run_id
        run = client.query("SELECT status FROM meta.load_run WHERE run_id='" + run_id + "'",
                           database)
        if not run or run[0]['status'] not in ('RUNNING',):
            raise EtlError('run_state', 'run 不存在或状态不是 RUNNING：' + run_id)

        members, rows = load_ods_rows(client, database)
        dispositions, accepted = judge(rows)
        n_acc = sum(1 for d in dispositions.values() if d[0] == 'ACCEPTED')
        n_dup = sum(1 for d in dispositions.values() if d[0] == 'DUPLICATE_EXACT')
        n_rej = sum(1 for d in dispositions.values() if d[0] == 'REJECTED')
        if len(rows) != n_acc + n_dup + n_rej:
            raise EtlError('conservation', '行数守恒不成立')

        if args.check_only:
            reasons = {}
            for d in dispositions.values():
                if d[0] == 'REJECTED':
                    reasons[d[1]] = reasons.get(d[1], 0) + 1
            print(json.dumps({'ok': True, 'mode': 'check_only', 'raw': len(rows),
                              'accepted': n_acc, 'duplicate_exact': n_dup,
                              'rejected': n_rej, 'rejected_by_reason': reasons,
                              'station_count': len(build_stations(accepted))},
                             ensure_ascii=False, indent=2))
            return 0

        # 幂等：本 run 已加工过则拒绝重复（同输入重跑不累加）
        existing = client.query("SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip WHERE run_id='"
                                + run_id + "'", database)[0]['n']
        if existing:
            raise EtlError('rerun', '该 run 已有事实数据；如需重跑请开新 run')

        try:
            # ---- 站点维度（未知成员 key=0 + 观察快照）----
            observations = build_stations(accepted)
            station_ids = sorted(observations)
            station_key_of = {sid: i + 1 for i, sid in enumerate(station_ids)}
            srows = [["'" + run_id + "'", '0', 'NULL', sql_nstr('未知站点'),
                      '1', '1', 'NULL', 'NULL', 'NULL', 'NULL', 'NULL']]
            for sid in station_ids:
                obs = observations[sid]
                if obs['name'] is not None:
                    name, name_fb, name_row = obs['name'][1], 0, obs['name'][2]
                else:
                    name, name_fb, name_row = sid, 1, None  # 缺名回退站点 ID
                if obs['coord'] is not None:
                    _, lat, lng, crow, crole = obs['coord']
                    coord = [lat, lng, sql_int(crow), sql_str(crole)]
                else:
                    coord = ['NULL', 'NULL', 'NULL', 'NULL']
                srows.append(["'" + run_id + "'", sql_int(station_key_of[sid]),
                              sql_nstr(sid), sql_nstr(name), '0', sql_int(name_fb),
                              sql_int(name_row)] + coord)
            batch_insert(client, database, 'dim.station',
                         ['run_id', 'station_key', 'station_id', 'station_name',
                          'is_unknown', 'name_is_fallback', 'name_source_row_id',
                          'reference_lat', 'reference_lng', 'coordinate_source_row_id',
                          'coordinate_role'], srows)

            # ---- 类型维度键查询 ----
            bike_keys = {r['bike_type_code']: r['bike_type_key'] for r in client.query(
                'SELECT bike_type_key, bike_type_code FROM dim.bike_type', database)}
            member_keys = {r['member_type_code']: r['member_type_key'] for r in client.query(
                'SELECT member_type_key, member_type_code FROM dim.member_type', database)}

            # ---- 事实表 ----
            frows, warnings_of = [], {}
            for r in accepted:
                (t1, t2, dur) = r['_t']
                s_status, s_lat, s_lng = coord_pair(r['start_lat_raw'], r['start_lng_raw'])
                e_status, e_lat, e_lng = coord_pair(r['end_lat_raw'], r['end_lng_raw'])
                s_station = (0 if is_blank(r['start_station_id_raw'])
                             else station_key_of[r['start_station_id_raw']])
                e_station = (0 if is_blank(r['end_station_id_raw'])
                             else station_key_of[r['end_station_id_raw']])
                bike = (0 if is_blank(r['rideable_type_raw'])
                        else bike_keys[r['rideable_type_raw']])
                mem = (0 if is_blank(r['member_casual_raw'])
                       else member_keys[r['member_casual_raw']])
                frows.append(["'" + run_id + "'", sql_nstr(r['ride_id_raw']),
                              sql_int(r['source_row_id']), sql_dt(*t1), sql_dt(*t2),
                              sql_int(dur), '1',
                              sql_int(date_key(t1[0])), sql_int(t1[0].hour),
                              sql_int(date_key(t2[0])), sql_int(t2[0].hour),
                              sql_int(s_station), sql_int(e_station),
                              sql_int(bike), sql_int(mem),
                              s_lat or 'NULL', s_lng or 'NULL',
                              e_lat or 'NULL', e_lng or 'NULL',
                              sql_str(s_status), sql_str(e_status)])
                warn = []
                if s_station == 0:
                    warn.append('START_STATION_MISSING')
                if e_station == 0:
                    warn.append('END_STATION_MISSING')
                if s_status != 'valid':
                    warn.append('START_COORD_' + s_status.upper())
                if e_status != 'valid':
                    warn.append('END_COORD_' + e_status.upper())
                warnings_of[r['source_row_id']] = warn
            batch_insert(client, database, 'dwd.fact_trip',
                         ['run_id', 'ride_id', 'representative_source_row_id',
                          'started_at', 'ended_at', 'duration_us', 'trip_count',
                          'start_date_key', 'start_hour_key', 'end_date_key',
                          'end_hour_key', 'start_station_key', 'end_station_key',
                          'bike_type_key', 'member_type_key', 'start_lat', 'start_lng',
                          'end_lat', 'end_lng', 'start_coordinate_status',
                          'end_coordinate_status'], frows)

            # ---- 回取 trip_key（IDENTITY 由服务器生成）----
            key_map = {r['representative_source_row_id']: r['trip_key'] for r in client.query(
                "SELECT trip_key, representative_source_row_id FROM dwd.fact_trip "
                "WHERE run_id='" + run_id + "'", database)}

            # ---- 行去向（全部源行，每行恰一条）----
            drows = []
            for r in rows:
                outcome, reason, rep_id = dispositions[r['source_row_id']]
                trip_key = key_map.get(rep_id) if rep_id else None
                warn = warnings_of.get(rep_id if outcome != 'REJECTED' else
                                       r['source_row_id'], [])
                warn_text = json.dumps(warn, ensure_ascii=False, separators=(',', ':'))
                drows.append(["'" + run_id + "'", sql_int(r['source_row_id']),
                              sql_str(outcome), sql_str(reason),
                              sql_int(trip_key), sql_int(rep_id), sql_nstr(warn_text)])
            batch_insert(client, database, 'meta.row_disposition',
                         ['run_id', 'source_row_id', 'outcome', 'primary_reason',
                          'trip_key', 'representative_source_row_id', 'warning_codes'],
                         drows, chunk=400)
        except EtlError:
            client.execute("UPDATE meta.load_run SET status='FAILED', finished_at_utc='"
                           + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
                           + "' WHERE run_id='" + run_id + "';", database)
            raise

        stats = {'run_id': run_id, 'raw': len(rows), 'accepted': n_acc,
                 'duplicate_exact': n_dup, 'rejected': n_rej,
                 'stations': len(station_ids) + 1,
                 'facts': len(frows),
                 'conservation_ok': len(rows) == n_acc + n_dup + n_rej}
        print(json.dumps({'ok': True, **stats}, ensure_ascii=False, indent=2))
        return 0
    except EtlError as error:
        print(json.dumps({'ok': False, 'kind': error.kind, 'message': str(error)},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
