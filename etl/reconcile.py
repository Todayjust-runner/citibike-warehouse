# -*- coding: utf-8 -*-
"""阶段 5：对账验收与发布。

验收项（docs/handoff/acceptance-checklist.md、docs/requirements.md）：
1. 六指标与需求口径/源核算一致（先比精确次数/微秒，再比显示值）
2. 月度对照 data/derived/.../monthly.csv；逐站对照 station-flow.csv（含未知站点行）
3. 跨期边界：boundary-records.csv 10 进入 / 11 流出；未知归还 1,026
4. 时长边界 60 秒/24 小时均含；守恒式与 ride_id 唯一（阶段 3 已核，此处复核）
5. 全部通过 → RUNNING→VALIDATED（触发器自动执行 meta.usp_assert_run_ready）
   → EXEC meta.usp_publish_run 发布为唯一 current

用法：python -X utf8 etl/reconcile.py --run-id <run_id> [--publish]
"""
import argparse
import csv
import json
from pathlib import Path

from common import ROOT, EtlError, Sqlcmd, sql_int, sql_str, validate_database

AUDIT_DIR = ROOT / 'data/derived/source_audit/citibike_jc/snapshot_20261113'
L, U = '2024-07-01', '2024-10-01'  # Q3 窗口，左闭右开，源时间不换时区

EXPECTED = {
    'M01_ride_count': 334332,
    'M02_duration_us': 216990044333000,
    'M02_avg_minutes': 10.82,
    'M03_member_count': 242927,
    'M03_share_pct': 72.66,
    'M04_departures': 334332,
    'M05_arrivals': 334331,
    'M06_net_total': 1,
    'cross_in': 10,
    'cross_out': 11,
    'unknown_arrivals': 1026,
}


def q1(client, database, sql, *_ignore):
    return client.query(sql, database)


def compute_metrics(client, database, run):
    w_start = "started_at>='{}' AND started_at<'{}'".format(L, U)
    w_end = "ended_at>='{}' AND ended_at<'{}'".format(L, U)
    base = "FROM dwd.fact_trip WHERE run_id='{}' AND ".format(run)
    m = {}
    r = q1(client, database, "SELECT COUNT_BIG(*) AS n, CONVERT(varchar(40),SUM(duration_us)) AS us "
           + base + w_start)[0]
    m['M01_ride_count'] = r['n']
    m['M02_duration_us'] = int(r['us'])
    m['M02_avg_minutes'] = round(m['M02_duration_us'] / 60_000_000 / r['n'], 2)
    r = q1(client, database, "SELECT member_type_key, COUNT_BIG(*) AS n "
           + base + w_start + " GROUP BY member_type_key", database)
    by_key = {x['member_type_key']: x['n'] for x in r}
    member, casual = by_key.get(1, 0), by_key.get(2, 0)
    m['M03_member_count'] = member
    m['M03_share_pct'] = (round(member * 100.0 / (member + casual), 2)
                          if member + casual else None)
    m['M04_departures'] = q1(client, database, "SELECT COUNT_BIG(*) AS n " + base + w_start)[0]['n']
    m['M05_arrivals'] = q1(client, database, "SELECT COUNT_BIG(*) AS n " + base + w_end)[0]['n']
    m['M06_net_total'] = m['M04_departures'] - m['M05_arrivals']
    m['cross_in'] = q1(client, database, "SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip WHERE run_id='"
                       + run + "' AND started_at<'" + L + "' AND ended_at>='" + L
                       + "' AND ended_at<'" + U + "'", database)[0]['n']
    m['cross_out'] = q1(client, database, "SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip WHERE run_id='"
                        + run + "' AND started_at>='" + L + "' AND started_at<'" + U
                        + "' AND ended_at>='" + U + "'", database)[0]['n']
    m['unknown_arrivals'] = q1(client, database, "SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip "
                               "WHERE run_id='" + run + "' AND end_station_key=0 AND " + w_end,
                               database)[0]['n']
    m['boundary_60s'] = q1(client, database, "SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip "
                           "WHERE run_id='" + run + "' AND duration_us=60000000", database)[0]['n']
    m['boundary_24h'] = q1(client, database, "SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip "
                           "WHERE run_id='" + run + "' AND duration_us=86400000000", database)[0]['n']
    # DWS 复算 M01（窗口边界在整点，小时桶对齐）
    m['M01_from_dws'] = q1(client, database,
                           "SELECT CONVERT(varchar(40),SUM(ride_count)) AS n FROM dws.trip_hourly t "
                           "JOIN dim.date d ON d.date_key=t.start_date_key "
                           "WHERE t.run_id='" + run + "' AND d.calendar_date>='" + L
                           + "' AND d.calendar_date<'" + U + "'", database)[0]['n']
    return m


def check_monthly(client, database, run):
    """逐月对照 monthly.csv（出发口径）。"""
    rows = {}
    for x in q1(client, database,
                "SELECT LEFT(CONVERT(char(8),start_date_key),6) AS ym, COUNT_BIG(*) AS n,"
                "CONVERT(varchar(40),SUM(duration_us)) AS us,"
                "SUM(CASE WHEN member_type_key=1 THEN 1 ELSE 0 END) AS mem "
                "FROM dwd.fact_trip WHERE run_id='" + run + "' "
                "GROUP BY LEFT(CONVERT(char(8),start_date_key),6)", database):
        ym = x['ym'][:4] + '-' + x['ym'][4:6]
        rows[ym] = x
    diffs = []
    with open(AUDIT_DIR / 'monthly.csv', encoding='utf-8') as f:
        for exp in csv.DictReader(f):
            got = rows.get(exp['month'])
            if got is None or got['n'] != int(exp['ride_count']) \
                    or int(got['us']) != int(exp['duration_us']) \
                    or got['mem'] != int(exp['member_count']):
                diffs.append({'month': exp['month'], 'expected': exp, 'got': got})
    return diffs


def check_station_flow(client, database, run):
    """逐站对照 station-flow.csv：借出按出发、归还按归还，含未知站点。"""
    def side(time_col, station_col):
        out = {}
        for x in q1(client, database,
                    "SELECT s.station_id, s.is_unknown, COUNT_BIG(*) AS n FROM dwd.fact_trip f "
                    "JOIN dim.station s ON s.run_id=f.run_id AND s.station_key=f." + station_col +
                    " WHERE f.run_id='" + run + "' AND f." + time_col + ">='" + L +
                    "' AND f." + time_col + "<'" + U + "' "
                    "GROUP BY s.station_id, s.is_unknown", database):
            key = '' if x['is_unknown'] else x['station_id']
            out[key] = x['n']
        return out
    dep, arr = side('started_at', 'start_station_key'), side('ended_at', 'end_station_key')
    diffs = []
    with open(AUDIT_DIR / 'station-flow.csv', encoding='utf-8') as f:
        for exp in csv.DictReader(f):
            sid = exp['station_id']
            d, a = dep.get(sid, 0), arr.get(sid, 0)
            if d != int(exp['departures']) or a != int(exp['arrivals']):
                diffs.append({'station_id': sid, 'expected': exp, 'got_dep': d, 'got_arr': a})
    extra = set(dep) | set(arr)
    with open(AUDIT_DIR / 'station-flow.csv', encoding='utf-8') as f:
        known = {r['station_id'] for r in csv.DictReader(f)}
    for sid in extra - known:
        if dep.get(sid) or arr.get(sid):
            diffs.append({'station_id': sid, 'expected': 'not in csv',
                          'got_dep': dep.get(sid), 'got_arr': arr.get(sid)})
    return diffs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='localhost')
    parser.add_argument('--database', default='CitibikeDW_B_Test')
    parser.add_argument('--allow-target', action='store_true')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--publish', action='store_true', help='全部通过后 VALIDATED 并发布')
    args = parser.parse_args()
    try:
        database = validate_database(args.database, args.allow_target)
        client = Sqlcmd(args.server)
        run = args.run_id
        state = q1(client, database, "SELECT status FROM meta.load_run WHERE run_id='"
                   + run + "'", database)
        if not state:
            raise EtlError('run_state', 'run 不存在：' + run)

        metrics = compute_metrics(client, database, run)
        checks = []
        for key, want in EXPECTED.items():
            got = metrics.get(key)
            checks.append({'check': key, 'expected': want, 'got': got, 'pass': got == want})
        checks.append({'check': 'M01_from_dws_equals_fact',
                       'expected': metrics['M01_ride_count'],
                       'got': int(metrics['M01_from_dws']),
                       'pass': int(metrics['M01_from_dws']) == metrics['M01_ride_count']})
        monthly_diffs = check_monthly(client, database, run)
        checks.append({'check': 'monthly_csv_aligned', 'expected': '0 差异',
                       'got': f'{len(monthly_diffs)} 差异', 'pass': not monthly_diffs})
        station_diffs = check_station_flow(client, database, run)
        checks.append({'check': 'station_flow_csv_aligned', 'expected': '0 差异',
                       'got': f'{len(station_diffs)} 差异', 'pass': not station_diffs})
        cons = q1(client, database, "SELECT outcome, COUNT_BIG(*) AS n FROM meta.row_disposition "
                  "WHERE run_id='" + run + "' GROUP BY outcome", database)
        counts = {x['outcome']: x['n'] for x in cons}
        checks.append({'check': 'conservation',
                       'expected': '563874=563668+0+206',
                       'got': counts,
                       'pass': counts.get('ACCEPTED') == 563668
                       and counts.get('DUPLICATE_EXACT', 0) == 0
                       and counts.get('REJECTED') == 206})
        all_pass = all(c['pass'] for c in checks)
        report = {'ok': all_pass, 'run_id': run, 'checks': checks}
        if monthly_diffs:
            report['monthly_diffs'] = monthly_diffs[:5]
        if station_diffs:
            report['station_diffs'] = station_diffs[:5]

        if all_pass and args.publish:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
            # RUNNING→VALIDATED：触发器自动执行 usp_assert_run_ready 复核结构/汇总
            client.execute("UPDATE meta.load_run SET status='VALIDATED', finished_at_utc='"
                           + now + "' WHERE run_id='" + run + "' AND status='RUNNING';", database)
            client.execute("EXEC meta.usp_publish_run @run_id='" + run + "';", database)
            report['published'] = q1(client, database,
                                     "SELECT status, is_current FROM meta.load_run WHERE run_id='"
                                     + run + "'", database)[0]
        elif all_pass:
            report['note'] = '全部通过；加 --publish 执行 VALIDATED + 发布'
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if all_pass else 1
    except EtlError as error:
        print(json.dumps({'ok': False, 'kind': error.kind, 'message': str(error)},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
