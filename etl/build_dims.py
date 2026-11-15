# -*- coding: utf-8 -*-
"""阶段 2（上）：构建 dim.date，并核对 hour / bike_type / member_type 三张种子维度。

- dim.date：按 ODS 实际可解析时间的最小/最大日期补齐两端，逐日生成；
  各属性必须与 CK_dim_date_calendar / CK_dim_date_weekday_name 公式一致；
  date_key = YYYYMMDD 整数（Kimball 日期维度的智能键特例）。
- dim.hour / dim.bike_type / dim.member_type：deploy 种子已含 0=未知成员；
  本脚本核对 ODS 实际标签是否全部被种子覆盖；出现未覆盖的非空标签时
  按"未识别标签单列"规则插入（is_unknown=0, is_recognized=0）。
- dim.station 依赖本 run 的 ACCEPTED 代表行，在阶段 3 事实加工时构建。

用法：python -X utf8 etl/build_dims.py
"""
import argparse
from datetime import date, timedelta
import json

from common import EtlError, Sqlcmd, batch_insert, sql_int, sql_nstr, validate_database

WEEKDAY_NAMES = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']

# 已识别标签必须与 CK_*_recognized 的判定一致
RECOGNIZED_BIKE = {'classic_bike', 'electric_bike'}
RECOGNIZED_MEMBER = {'member', 'casual'}
BIKE_LABELS = {'classic_bike': '普通自行车', 'electric_bike': '电助力车'}
MEMBER_LABELS = {'member': 'member', 'casual': 'casual'}


def daterange_rows(client, database):
    """从 ODS 探明可解析时间的范围，生成 [min日, max日] 全部日期行。"""
    r = client.query(
        "SELECT CONVERT(date, MIN(TRY_CONVERT(datetime2, started_at_raw))) AS d1,"
        "CONVERT(date, MIN(TRY_CONVERT(datetime2, ended_at_raw))) AS d2,"
        "CONVERT(date, MAX(TRY_CONVERT(datetime2, started_at_raw))) AS d3,"
        "CONVERT(date, MAX(TRY_CONVERT(datetime2, ended_at_raw))) AS d4 "
        "FROM ods.trip_raw", database)[0]
    first = date.fromisoformat(min(r['d1'], r['d2']))
    last = date.fromisoformat(max(r['d3'], r['d4']))
    rows, day = [], first
    while day <= last:
        iso_wd = day.isoweekday()  # 与 DDL 公式 ((DATEDIFF%7+7)%7)+1 一致（1900-01-01 为周一）
        rows.append([
            sql_int(day.year * 10000 + day.month * 100 + day.day),  # date_key
            "'" + day.isoformat() + "'",                            # calendar_date
            sql_int(day.year), sql_int((day.month - 1) // 3 + 1),
            sql_int(day.month), "'" + day.strftime('%Y-%m') + "'",
            sql_int(day.day), sql_int(iso_wd),
            sql_nstr(WEEKDAY_NAMES[iso_wd - 1]),
        ])
        day += timedelta(days=1)
    return first, last, rows


def build_date_dim(client, database):
    first, last, rows = daterange_rows(client, database)
    existing = client.query('SELECT COUNT(*) AS n FROM dim.date', database)[0]['n']
    if existing == len(rows):
        return {'status': 'already_complete', 'first': str(first), 'last': str(last),
                'rows': existing}
    if existing:
        raise EtlError('partial_dim_date',
                       f'dim.date 已有 {existing} 行，既不是 0 也不是预期 {len(rows)} 行，需人工核查')
    columns = ['date_key', 'calendar_date', 'calendar_year', 'calendar_quarter',
               'calendar_month', 'year_month', 'day_of_month', 'iso_weekday', 'weekday_name']
    batch_insert(client, database, 'dim.date', columns, rows)
    return {'status': 'inserted', 'first': str(first), 'last': str(last), 'rows': len(rows)}


def check_type_dim(client, database, table, key_col, code_col, raw_col,
                   recognized, labels):
    """核对种子维度是否覆盖 ODS 全部非空标签；未识别标签单列插入。"""
    seeds = {r[code_col]: r[key_col] for r in client.query(
        'SELECT ' + key_col + ',' + code_col + ' FROM ' + table, database)}
    actual = {r[raw_col] for r in client.query(
        'SELECT DISTINCT ' + raw_col + ' FROM ods.trip_raw', database) if r[raw_col] != ''}
    inserted = []
    for code in sorted(actual):
        if code in seeds:
            continue
        # 未识别标签单列：保留原标签，is_unknown=0（确实观察到）、is_recognized=0
        client.execute(
            'INSERT INTO ' + table + ' (' + code_col + ','
            + ('bike_type_label' if 'bike' in table else 'member_type_label')
            + ',is_unknown,is_recognized) VALUES ('
            + sql_nstr(code) + ',' + sql_nstr(labels.get(code, code)) + ',0,0);', database)
        inserted.append(code)
    missing_known = [c for c in recognized if c not in actual]
    return {'observed_labels': sorted(actual), 'newly_inserted_unrecognized': inserted,
            'recognized_not_observed': missing_known,
            'note': '空标签在事实装载时映射 key=0'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='localhost')
    parser.add_argument('--database', default='CitibikeDW_B_Test')
    parser.add_argument('--allow-target', action='store_true')
    args = parser.parse_args()
    try:
        database = validate_database(args.database, args.allow_target)
        client = Sqlcmd(args.server)
        report = {'dim_date': build_date_dim(client, database),
                  'dim_hour': client.query('SELECT COUNT(*) AS n FROM dim.hour', database)[0],
                  'dim_bike_type': check_type_dim(client, database, 'dim.bike_type',
                                                  'bike_type_key', 'bike_type_code',
                                                  'rideable_type_raw',
                                                  RECOGNIZED_BIKE, BIKE_LABELS),
                  'dim_member_type': check_type_dim(client, database, 'dim.member_type',
                                                    'member_type_key', 'member_type_code',
                                                    'member_casual_raw',
                                                    RECOGNIZED_MEMBER, MEMBER_LABELS)}
        print(json.dumps({'ok': True, **report}, ensure_ascii=False, indent=2))
        return 0
    except EtlError as error:
        print(json.dumps({'ok': False, 'kind': error.kind, 'message': str(error)},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
