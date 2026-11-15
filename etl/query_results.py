# -*- coding: utf-8 -*-
"""阶段 6：C→D 查询结果交付（docs/contracts/c-to-d-query-contract.md）。

五种结果：ride_overview / trip_trend / weekday_hour / station_flow / type_comparison。
约定：
- run_id 省略时使用当前唯一 PUBLISHED 运行，整次请求固定该 run；
- 时间筛选左闭右开、源时间不换时区，默认 2024Q3；
- JSON 中计数/键/总微秒为十进制整数字符串；平均分钟 2 位小数；
  比例为 0..1 的 12 位小数字符串，由精确分子分母一次 HALF_UP 计算；
- 覆盖完整时 include_empty_buckets=true 才补零桶；覆盖不足不显示成真实 0。

用法示例：
  python -X utf8 etl/query_results.py --result ride_overview
  python -X utf8 etl/query_results.py --result trip_trend --granularity day
  python -X utf8 etl/query_results.py --result station_flow --granularity day \\
      --start 2024-08-01 --end 2024-09-01
也可被 D 作为模块导入：from etl.query_results import get_result
"""
import argparse
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import re
import sys

if __package__:
    from .common import EtlError, Sqlcmd, validate_database
else:
    from common import EtlError, Sqlcmd, validate_database

DEFAULT_START, DEFAULT_END = '2024-07-01', '2024-10-01'
GRANULARITIES = ('hour', 'day', 'month')
TIME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}([ T]\d{2}(:\d{2})?(:\d{2})?)?$')


def ratio_text(numer, denom):
    """比例：0..1 十二位小数；分母为 0 → None（不显示成真实 0）。"""
    if not denom:
        return None
    return str((Decimal(numer) / Decimal(denom)).quantize(
        Decimal('0.000000000001'), rounding=ROUND_HALF_UP))


def avg_minutes(duration_us, count):
    if not count:
        return None
    return str((Decimal(duration_us) / Decimal(60000000 * count)).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP))


class Warehouse:
    """一次请求内的取数上下文：固定 run、解析筛选、组装 metadata。"""

    def __init__(self, client, database, params):
        self.client, self.db = client, database
        self.params = params
        run_id = params.get('run_id')
        if run_id:
            rows = client.query("SELECT run_id,status,is_current,input_set_sha256,"
                                "model_version,metric_rule_version,processing_policy_version,"
                                "code_revision FROM meta.load_run WHERE run_id='" + run_id + "'",
                                database)
        else:
            rows = client.query("SELECT run_id,status,is_current,input_set_sha256,"
                                "model_version,metric_rule_version,processing_policy_version,"
                                "code_revision FROM meta.load_run "
                                "WHERE is_current=1 AND status='PUBLISHED'", database)
        if not rows or rows[0]['status'] != 'PUBLISHED':
            raise EtlError('run_unavailable', '没有可用的已发布运行')
        self.run = rows[0]
        self.run_id = str(self.run['run_id'])
        self.start = params.get('start') or DEFAULT_START
        self.end = params.get('end') or DEFAULT_END
        for label, value in (('start', self.start), ('end', self.end)):
            if not TIME_RE.match(value):
                raise EtlError('invalid_request', f'时间参数格式错误：{label}={value}')
        try:
            start, end = datetime.fromisoformat(self.start), datetime.fromisoformat(self.end)
        except ValueError as error:
            raise EtlError('invalid_request', '日期或时间不存在') from error
        if start >= end:
            raise EtlError('invalid_request', 'filter_start 必须早于 filter_end_exclusive')
        self.start, self.end = start.isoformat(sep=' '), end.isoformat(sep=' ')
        self.bike_filter = params.get('bike_filter')  # None 或键列表
        if self.bike_filter is not None:
            known = {r['bike_type_key'] for r in client.query(
                'SELECT bike_type_key FROM dim.bike_type', database)}
            if not self.bike_filter or not set(self.bike_filter) <= known:
                raise EtlError('invalid_request', 'bike_filter 须为当前字典中的非空键列表')
        intervals = client.query(
            "SELECT time_role,coverage_status,coverage_start,coverage_end_exclusive "
            "FROM meta.coverage WHERE run_id='" + self.run_id + "' ORDER BY coverage_start", database)
        self.coverage = {}
        for role in ('departure', 'arrival'):
            cursor = datetime.fromisoformat(self.start)
            end = datetime.fromisoformat(self.end)
            for interval in intervals:
                if interval['time_role'] != role or interval['coverage_status'] != 'complete':
                    continue
                left = datetime.fromisoformat(interval['coverage_start'])
                right = datetime.fromisoformat(interval['coverage_end_exclusive'])
                if left <= cursor < right:
                    cursor = right
            self.coverage[role] = 'complete' if cursor >= end else 'unknown'

    def w_start(self, alias='f'):
        return ("{a}.started_at>='{s}' AND {a}.started_at<'{e}'"
                .format(a=alias, s=self.start, e=self.end))

    def w_end(self, alias='f'):
        return ("{a}.ended_at>='{s}' AND {a}.ended_at<'{e}'"
                .format(a=alias, s=self.start, e=self.end))

    def w_bike(self, alias='f'):
        if self.bike_filter is None:
            return '1=1'
        keys = ','.join(str(k) for k in self.bike_filter)
        return alias + '.bike_type_key IN (' + keys + ')'

    def metadata(self, result_name, status, time_role=None, warnings=None):
        return {'result_name': result_name, 'result_status': status,
                'run_id': self.run_id,
                'source_hashes': {'input_set_sha256': self.run['input_set_sha256']},
                'filter': {'start': self.start, 'end_exclusive': self.end,
                           'bike_filter': self.bike_filter,
                           'station_filter': self.params.get('station_filter')},
                'time_role': time_role,
                'coverage': self.coverage,
                'versions': {'model': self.run['model_version'],
                             'metric_rule': self.run['metric_rule_version'],
                             'processing_policy': self.run['processing_policy_version'],
                             'code_revision': self.run['code_revision']},
                'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                'warnings': warnings or []}

    def status_for(self, role, row_count):
        cov = self.coverage.get(role, 'unknown')
        if cov != 'complete':
            return 'insufficient_coverage'
        return 'ok' if row_count else 'empty'


# ---------- ① 总览 ----------

def ride_overview(wh):
    where = "f.run_id='{}' AND {} AND {}".format(wh.run_id, wh.w_start(), wh.w_bike())
    r = wh.client.query(
        "SELECT COUNT_BIG(*) AS n,"
        "CONVERT(varchar(40),COALESCE(SUM(duration_us),0)) AS us,"
        "SUM(CASE WHEN member_type_key=1 THEN 1 ELSE 0 END) AS mem,"
        "SUM(CASE WHEN member_type_key IN (1,2) THEN 1 ELSE 0 END) AS known,"
        "SUM(CASE WHEN member_type_key=0 THEN 1 ELSE 0 END) AS unknown "
        "FROM dwd.fact_trip f WHERE " + where, wh.db)[0]
    n, us = r['n'], int(r['us'])
    status = wh.status_for('departure', n)
    data = [] if status == 'insufficient_coverage' else [{
        'ride_count': str(n), 'duration_us': str(us),
        'avg_duration_minutes': avg_minutes(us, n),
        'member_count': str(r['mem'] or 0),
        'known_member_type_count': str(r['known'] or 0),
        'member_share': ratio_text(r['mem'], r['known']),
        'member_type_coverage': ratio_text(r['known'], n) if n else None,
        'unknown_member_type_count': str(r['unknown'] or 0)}]
    return {'metadata': wh.metadata('ride_overview', status, time_role='departure'),
            'data': data}


# ---------- 时间桶工具 ----------

def bucket_expr(granularity, alias, col):
    if granularity == 'hour':
        return ("CONVERT(char(13),{a}.{c},120)".format(a=alias, c=col))
    if granularity == 'day':
        return "CONVERT(char(10),{a}.{c},120)".format(a=alias, c=col)
    return "LEFT(CONVERT(char(10),{a}.{c},120),7)".format(a=alias, c=col)


def bucket_end(bucket, granularity):
    if granularity == 'hour':
        dt = datetime.strptime(bucket, '%Y-%m-%d %H') + timedelta(hours=1)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    if granularity == 'day':
        dt = datetime.strptime(bucket, '%Y-%m-%d') + timedelta(days=1)
        return dt.strftime('%Y-%m-%d')
    dt = datetime.strptime(bucket, '%Y-%m')
    year, month = dt.year + (dt.month == 12), dt.month % 12 + 1
    return '{}-{:02d}-01'.format(year, month)


def aligned_to_bucket(wh, granularity):
    """筛选边界是否与桶边界对齐；不对齐的小时窗口须回事实精确筛选。"""
    fmt = {'hour': '%Y-%m-%d %H', 'day': '%Y-%m-%d', 'month': '%Y-%m'}
    for value in (wh.start, wh.end):
        text = value.replace('T', ' ')
        if granularity == 'hour' and not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:00(:00)?$', text):
            return False
        if granularity == 'day' and len(text) > 10:
            return False
        if granularity == 'month' and text != text[:7] + '-01' and len(text) > 7:
            return False
    return True


def fill_buckets(rows, wh, granularity, keys):
    """include_empty_buckets 且覆盖完整时补零桶；比率/均值保持 NULL。"""
    if not wh.params.get('include_empty_buckets'):
        return rows
    existing = {r['time_bucket'] for r in rows}
    out = list(rows)
    b = wh.start[:13] if granularity == 'hour' else (
        wh.start[:10] if granularity == 'day' else wh.start[:7])
    end = datetime.fromisoformat(wh.end)
    fmt = {'hour': '%Y-%m-%d %H', 'day': '%Y-%m-%d', 'month': '%Y-%m'}[granularity]
    while datetime.strptime(b, fmt) < end:
        if b not in existing:
            zero = {k: ('0' if k in ('ride_count', 'duration_us', 'member_count',
                                     'known_member_type_count') else None)
                    for k in keys}
            zero['time_bucket'] = b
            zero['bucket_end_exclusive'] = bucket_end(b, granularity)
            out.append(zero)
        b = bucket_end(b, granularity)
        if granularity == 'hour':
            b = b[:13]
        elif granularity == 'day':
            b = b[:10]
        else:
            b = b[:7]
    return sorted(out, key=lambda r: r['time_bucket'])


# ---------- ② 趋势 ----------

def trip_trend(wh, granularity):
    if granularity not in GRANULARITIES:
        raise EtlError('invalid_request', 'granularity 须为 hour/day/month')
    where = "f.run_id='{}' AND {} AND {}".format(wh.run_id, wh.w_start(), wh.w_bike())
    bucket = bucket_expr(granularity, 'f', 'started_at')
    rows = wh.client.query(
        "SELECT " + bucket + " AS b, COUNT_BIG(*) AS n,"
        "CONVERT(varchar(40),SUM(duration_us)) AS us,"
        "SUM(CASE WHEN member_type_key=1 THEN 1 ELSE 0 END) AS mem,"
        "SUM(CASE WHEN member_type_key IN (1,2) THEN 1 ELSE 0 END) AS known "
        "FROM dwd.fact_trip f WHERE " + where + " GROUP BY " + bucket + " ORDER BY b", wh.db)
    data = [{'time_bucket': r['b'], 'bucket_end_exclusive': bucket_end(r['b'], granularity),
             'ride_count': str(r['n']), 'duration_us': r['us'],
             'avg_duration_minutes': avg_minutes(int(r['us']), r['n']),
             'member_count': str(r['mem']), 'known_member_type_count': str(r['known']),
             'member_share': ratio_text(r['mem'], r['known']),
             'member_type_coverage': ratio_text(r['known'], r['n'])} for r in rows]
    data = fill_buckets(data, wh, granularity,
                        ['ride_count', 'duration_us', 'avg_duration_minutes',
                         'member_count', 'known_member_type_count',
                         'member_share', 'member_type_coverage'])
    status = wh.status_for('departure', len(data))
    return {'metadata': wh.metadata('trip_trend', status, time_role='departure'),
            'data': data if status != 'insufficient_coverage' else []}


# ---------- ③ 星期×小时热力图 ----------

def weekday_hour(wh):
    where = "f.run_id='{}' AND {} AND {}".format(wh.run_id, wh.w_start(), wh.w_bike())
    rows = wh.client.query(
        "SELECT d.iso_weekday AS wd, f.start_hour_key AS h, COUNT_BIG(*) AS n,"
        "CONVERT(varchar(40),SUM(duration_us)) AS us "
        "FROM dwd.fact_trip f JOIN dim.date d ON d.date_key=f.start_date_key "
        "WHERE " + where + " GROUP BY d.iso_weekday, f.start_hour_key "
        "ORDER BY wd, h", wh.db)
    data = [{'iso_weekday': str(r['wd']), 'hour_key': str(r['h']),
             'ride_count': str(r['n']), 'duration_us': r['us'],
             'avg_duration_minutes': avg_minutes(int(r['us']), r['n'])} for r in rows]
    status = wh.status_for('departure', len(data))
    return {'metadata': wh.metadata('weekday_hour', status, time_role='departure'),
            'data': data if status != 'insufficient_coverage' else []}


# ---------- ④ 站点借还 ----------

def station_flow(wh, granularity):
    if granularity not in GRANULARITIES:
        raise EtlError('invalid_request', 'granularity 须为 hour/day/month')
    station_filter = wh.params.get('station_filter')
    sf_dep = sf_arr = '1=1'
    if station_filter is not None:
        if not station_filter:
            raise EtlError('invalid_request', 'station_filter 不能为空列表')
        keys = ','.join(str(int(k)) for k in station_filter)
        sf_dep = 'f.start_station_key IN (' + keys + ')'
        sf_arr = 'f.end_station_key IN (' + keys + ')'
    dep = wh.client.query(
        "SELECT " + bucket_expr(granularity, 'f', 'started_at') + " AS b,"
        "f.start_station_key AS s, COUNT_BIG(*) AS n FROM dwd.fact_trip f WHERE f.run_id='"
        + wh.run_id + "' AND " + wh.w_start() + " AND " + wh.w_bike() + " AND " + sf_dep
        + " GROUP BY " + bucket_expr(granularity, 'f', 'started_at')
        + ", f.start_station_key", wh.db)
    arr = wh.client.query(
        "SELECT " + bucket_expr(granularity, 'f', 'ended_at') + " AS b,"
        "f.end_station_key AS s, COUNT_BIG(*) AS n FROM dwd.fact_trip f WHERE f.run_id='"
        + wh.run_id + "' AND " + wh.w_end() + " AND " + wh.w_bike() + " AND " + sf_arr
        + " GROUP BY " + bucket_expr(granularity, 'f', 'ended_at')
        + ", f.end_station_key", wh.db)
    merged = {}
    for r in dep:
        merged.setdefault((r['b'], r['s']), [0, 0])[0] = r['n']
    for r in arr:
        merged.setdefault((r['b'], r['s']), [0, 0])[1] = r['n']
    stations = {r['station_key']: r for r in wh.client.query(
        "SELECT station_key,station_id,station_name,is_unknown,reference_lat,reference_lng "
        "FROM dim.station WHERE run_id='" + wh.run_id + "'", wh.db)}
    data = []
    for (b, s), (d, a) in sorted(merged.items()):
        st = stations.get(s, {})
        data.append({'station_key': str(s),
                     'station_id': st.get('station_id'),
                     'station_name': st.get('station_name'),
                     'unknown_station_flag': bool(st.get('is_unknown')),
                     'time_bucket': b, 'bucket_end_exclusive': bucket_end(b, granularity),
                     'departures': str(d), 'arrivals': str(a),
                     'net_outflow': str(d - a),
                     'reference_lat': (str(st['reference_lat'])
                                       if st.get('reference_lat') is not None else None),
                     'reference_lng': (str(st['reference_lng'])
                                       if st.get('reference_lng') is not None else None)})
    total_d = sum(int(r['departures']) for r in data)
    total_a = sum(int(r['arrivals']) for r in data)
    unk_d = sum(int(r['departures']) for r in data if r['unknown_station_flag'])
    unk_a = sum(int(r['arrivals']) for r in data if r['unknown_station_flag'])
    cov_ok = (wh.coverage.get('departure') == 'complete'
              and wh.coverage.get('arrival') == 'complete')
    status = 'insufficient_coverage' if not cov_ok else ('ok' if data else 'empty')
    if not cov_ok:
        data = []
    return {'metadata': wh.metadata('station_flow', status, time_role='both'),
            'summary': {'departures_total': str(total_d) if cov_ok else None,
                        'arrivals_total': str(total_a) if cov_ok else None,
                        'unknown_departures': str(unk_d) if cov_ok else None,
                        'unknown_arrivals': str(unk_a) if cov_ok else None,
                        'start_station_id_coverage': ratio_text(total_d - unk_d, total_d) if cov_ok else None,
                        'end_station_id_coverage': ratio_text(total_a - unk_a, total_a) if cov_ok else None},
            'data': data}


# ---------- ⑤ 会员×车型对比 ----------

def type_comparison(wh):
    where = "f.run_id='{}' AND {} AND {}".format(wh.run_id, wh.w_start(), wh.w_bike())
    rows = wh.client.query(
        "SELECT f.member_type_key AS mk, f.bike_type_key AS bk, COUNT_BIG(*) AS n,"
        "CONVERT(varchar(40),SUM(duration_us)) AS us "
        "FROM dwd.fact_trip f WHERE " + where +
        " GROUP BY f.member_type_key, f.bike_type_key ORDER BY mk, bk", wh.db)
    mtypes = {r['member_type_key']: r for r in wh.client.query(
        'SELECT member_type_key,member_type_code,is_unknown,is_recognized '
        'FROM dim.member_type', wh.db)}
    btypes = {r['bike_type_key']: r for r in wh.client.query(
        'SELECT bike_type_key,bike_type_code,is_unknown,is_recognized '
        'FROM dim.bike_type', wh.db)}
    data = []
    for r in rows:
        m, b = mtypes[r['mk']], btypes[r['bk']]
        data.append({'member_type_key': str(r['mk']), 'bike_type_key': str(r['bk']),
                     'member_casual': m['member_type_code'],
                     'rideable_type': b['bike_type_code'],
                     'member_type_is_unknown': bool(m['is_unknown']),
                     'member_type_is_recognized': bool(m['is_recognized']),
                     'bike_type_is_unknown': bool(b['is_unknown']),
                     'bike_type_is_recognized': bool(b['is_recognized']),
                     'ride_count': str(r['n']), 'duration_us': r['us'],
                     'avg_duration_minutes': avg_minutes(int(r['us']), r['n'])})
    status = wh.status_for('departure', len(data))
    return {'metadata': wh.metadata('type_comparison', status, time_role='departure'),
            'data': data if status != 'insufficient_coverage' else []}


RESULTS = {'ride_overview': lambda wh, p: ride_overview(wh),
           'trip_trend': lambda wh, p: trip_trend(wh, p.get('granularity') or 'day'),
           'weekday_hour': lambda wh, p: weekday_hour(wh),
           'station_flow': lambda wh, p: station_flow(wh, p.get('granularity') or 'day'),
           'type_comparison': lambda wh, p: type_comparison(wh)}


def get_result(name, params=None, server='localhost', database='CitibikeDW_B_Test'):
    """供 D 导入调用：get_result('trip_trend', {'granularity': 'day', ...})"""
    if name not in RESULTS:
        raise EtlError('invalid_request', '未知结果类型：' + str(name))
    params = dict(params or {})
    client = Sqlcmd(server)
    wh = Warehouse(client, database, params)
    wh.params = params
    return RESULTS[name](wh, params)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='localhost')
    parser.add_argument('--database', default='CitibikeDW_B_Test')
    parser.add_argument('--allow-target', action='store_true')
    parser.add_argument('--result', required=True, choices=sorted(RESULTS))
    parser.add_argument('--run-id')
    parser.add_argument('--start', help='筛选起点（含），默认 2024-07-01')
    parser.add_argument('--end', help='筛选终点（不含），默认 2024-10-01')
    parser.add_argument('--granularity', choices=GRANULARITIES)
    parser.add_argument('--bike-filter', help='车型键列表，逗号分隔，如 1,2')
    parser.add_argument('--station-filter', help='站点键列表，逗号分隔，0 为未知')
    parser.add_argument('--include-empty-buckets', action='store_true')
    args = parser.parse_args()
    try:
        database = validate_database(args.database, args.allow_target)
        params = {'run_id': args.run_id, 'start': args.start, 'end': args.end,
                  'granularity': args.granularity,
                  'include_empty_buckets': args.include_empty_buckets}
        if args.bike_filter is not None:
            params['bike_filter'] = [int(x) for x in args.bike_filter.split(',')]
        if args.station_filter is not None:
            params['station_filter'] = [int(x) for x in args.station_filter.split(',')]
        result = get_result(args.result, params, args.server, database)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except EtlError as error:
        kind = error.kind if error.kind in ('run_unavailable', 'invalid_request') \
            else 'invalid_request'
        print(json.dumps({'metadata': {'result_status': kind, 'warnings': [str(error)]},
                          'data': []}, ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
