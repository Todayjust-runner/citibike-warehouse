# -*- coding: utf-8 -*-
"""阶段 4：DWS 汇总（dwd.fact_trip → dws.trip_hourly / dws.station_hourly）。

- dws.trip_hourly：run × 出发日 × 小时 × 车型 × 会员类型 → 次数、总微秒。
- dws.station_hourly：run × 事件日 × 小时 × 站点 × 车型 → 借出、归还。
  借出按出发时间/起点站、归还按归还时间/终点站**两侧独立聚合后再合并**
  （FULL OUTER JOIN），缺侧补 0——归还含窗口前出发的骑行，不能先筛出发集合。
- 只存分子（次数）和分母（总微秒），均值/占比一律查询时重算。

用法：python -X utf8 etl/build_dws.py --run-id <run_id>
"""
import argparse
import json

from common import EtlError, Sqlcmd, validate_database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default='localhost')
    parser.add_argument('--database', default='CitibikeDW_B_Test')
    parser.add_argument('--allow-target', action='store_true')
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    try:
        database = validate_database(args.database, args.allow_target)
        client = Sqlcmd(args.server)
        run = args.run_id

        for table in ('dws.trip_hourly', 'dws.station_hourly'):
            n = client.query("SELECT COUNT_BIG(*) AS n FROM " + table
                             + " WHERE run_id='" + run + "'", database)[0]['n']
            if n:
                raise EtlError('rerun', f'{table} 已有本 run 数据，拒绝重复累加')

        # ① 行程小时汇总（出发角色）
        client.execute(
            "INSERT INTO dws.trip_hourly (run_id,start_date_key,start_hour_key,"
            "bike_type_key,member_type_key,ride_count,duration_us) "
            "SELECT run_id,start_date_key,start_hour_key,bike_type_key,member_type_key,"
            "COUNT_BIG(*),CONVERT(decimal(38,0),SUM(duration_us)) "
            "FROM dwd.fact_trip WHERE run_id='" + run + "' "
            "GROUP BY run_id,start_date_key,start_hour_key,bike_type_key,member_type_key;",
            database)

        # ② 站点小时汇总（借还双侧独立聚合后合并）
        client.execute(
            "WITH dep AS ("
            "  SELECT start_date_key AS d, start_hour_key AS h, start_station_key AS s,"
            "         bike_type_key AS b, COUNT_BIG(*) AS dep_n"
            "  FROM dwd.fact_trip WHERE run_id='" + run + "'"
            "  GROUP BY start_date_key,start_hour_key,start_station_key,bike_type_key),"
            "arr AS ("
            "  SELECT end_date_key AS d, end_hour_key AS h, end_station_key AS s,"
            "         bike_type_key AS b, COUNT_BIG(*) AS arr_n"
            "  FROM dwd.fact_trip WHERE run_id='" + run + "'"
            "  GROUP BY end_date_key,end_hour_key,end_station_key,bike_type_key) "
            "INSERT INTO dws.station_hourly (run_id,event_date_key,event_hour_key,"
            "station_key,bike_type_key,departures,arrivals) "
            "SELECT '" + run + "',"
            "COALESCE(dep.d,arr.d),COALESCE(dep.h,arr.h),COALESCE(dep.s,arr.s),"
            "COALESCE(dep.b,arr.b),COALESCE(dep.dep_n,0),COALESCE(arr.arr_n,0) "
            "FROM dep FULL OUTER JOIN arr "
            "ON dep.d=arr.d AND dep.h=arr.h AND dep.s=arr.s AND dep.b=arr.b;",
            database)

        report = {
            'trip_hourly_rows': client.query(
                "SELECT COUNT_BIG(*) AS n FROM dws.trip_hourly WHERE run_id='" + run + "'",
                database)[0]['n'],
            'station_hourly_rows': client.query(
                "SELECT COUNT_BIG(*) AS n FROM dws.station_hourly WHERE run_id='" + run + "'",
                database)[0]['n'],
        }
        # 与事实层核对：两侧合计必须等于事实数（含未知站点）
        fact_n = client.query(
            "SELECT COUNT_BIG(*) AS n FROM dwd.fact_trip WHERE run_id='" + run + "'",
            database)[0]['n']
        report['fact_rows'] = fact_n
        report['trip_hourly_total_rides'] = client.query(
            "SELECT CONVERT(varchar(40),SUM(ride_count)) AS s FROM dws.trip_hourly "
            "WHERE run_id='" + run + "'", database)[0]['s']
        both = client.query(
            "SELECT CONVERT(varchar(40),SUM(departures)) AS d,"
            "CONVERT(varchar(40),SUM(arrivals)) AS a FROM dws.station_hourly "
            "WHERE run_id='" + run + "'", database)[0]
        report['station_hourly_total_departures'] = both['d']
        report['station_hourly_total_arrivals'] = both['a']
        report['consistent'] = (int(report['trip_hourly_total_rides']) == fact_n
                                and int(both['d']) == fact_n and int(both['a']) == fact_n)
        print(json.dumps({'ok': True, 'run_id': run, **report}, ensure_ascii=False, indent=2))
        return 0 if report['consistent'] else 1
    except EtlError as error:
        print(json.dumps({'ok': False, 'kind': error.kind, 'message': str(error)},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
