"""只读验收当前已发布运行。先完成ETL，再运行本文件。"""
import csv
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from etl.query_results import get_result
from scripts.warehouse import Sqlcmd

DB = 'CitibikeDW_B_Test'
AUDIT = ROOT / 'data/derived/source_audit/citibike_jc/snapshot_20261113'

class CAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Sqlcmd('localhost')
        cls.overview = get_result('ride_overview')
        cls.run_id = cls.overview['metadata']['run_id']
    def result(self, name, **params):
        return get_result(name, dict(run_id=self.run_id, **params))
    def test_six_metrics_match_source(self):
        row = self.overview['data'][0]
        self.assertEqual(row['ride_count'], '334332')
        self.assertEqual(row['duration_us'], '216990044333000')
        self.assertEqual(row['avg_duration_minutes'], '10.82')
        self.assertEqual(row['member_count'], '242927')
        self.assertEqual(row['known_member_type_count'], '334332')
        pct = (Decimal(row['member_count'])*100/Decimal(row['known_member_type_count'])).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        self.assertEqual(pct, Decimal('72.66'))
        summary = self.result('station_flow', granularity='month')['summary']
        self.assertEqual((summary['departures_total'], summary['arrivals_total']), ('334332','334331'))
        self.assertEqual(int(summary['departures_total'])-int(summary['arrivals_total']), 1)
    def test_monthly_trend_matches_independent_csv(self):
        actual = {r['time_bucket']:r for r in self.result('trip_trend', granularity='month')['data']}
        with (AUDIT/'monthly.csv').open(encoding='utf-8') as f:
            for expected in csv.DictReader(f):
                got = actual[expected['month']]
                for name in ('ride_count','duration_us','member_count'):
                    self.assertEqual(got[name], expected[name])
    def test_every_station_matches_independent_csv(self):
        actual = {}
        for r in self.result('station_flow',granularity='month')['data']:
            key = r['station_id'] or ''
            d,a = actual.get(key,(0,0))
            actual[key] = d+int(r['departures']), a+int(r['arrivals'])
        with (AUDIT/'station-flow.csv').open(encoding='utf-8') as f:
            expected = {r['station_id']:(int(r['departures']),int(r['arrivals'])) for r in csv.DictReader(f)}
        self.assertEqual(actual, expected)
    def test_five_views_agree_and_filter_bikes(self):
        for filters in ({}, {'bike_filter':[2]}):
            total = self.result('ride_overview',**filters)['data'][0]
            for name in ('trip_trend','weekday_hour','type_comparison'):
                rows = self.result(name,**filters)['data']
                self.assertEqual(sum(int(r['ride_count']) for r in rows), int(total['ride_count']))
                self.assertEqual(sum(int(r['duration_us']) for r in rows), int(total['duration_us']))
            summary=self.result('station_flow',granularity='month',**filters)['summary']
            self.assertEqual(summary['departures_total'],total['ride_count'])
        types=self.result('type_comparison',bike_filter=[2])['data']
        self.assertTrue(all(r['bike_type_key']=='2' for r in types))
    def test_partial_hour_window_uses_exact_events(self):
        p=dict(start='2024-07-01 00:15:00',end='2024-07-01 01:45:00')
        expected=self.client.query("SELECT COUNT_BIG(*) AS n, CONVERT(varchar(40),SUM(duration_us)) AS us FROM dwd.fact_trip WHERE run_id='"+self.run_id+"' AND started_at>='2024-07-01 00:15:00' AND started_at<'2024-07-01 01:45:00'",DB)[0]
        rows=self.result('trip_trend',granularity='hour',**p)['data']
        self.assertEqual(sum(int(r['ride_count']) for r in rows),expected['n'])
        self.assertEqual(sum(int(r['duration_us']) for r in rows),int(expected['us'] or 0))
    def test_outside_coverage_is_not_real_zero(self):
        p=dict(start='2025-01-01',end='2025-02-01')
        for name in ('ride_overview','trip_trend','weekday_hour','station_flow','type_comparison'):
            r=self.result(name,**p)
            self.assertEqual(r['metadata']['result_status'],'insufficient_coverage')
            self.assertEqual(r['data'],[])
            if name=='station_flow': self.assertIsNone(r['summary']['departures_total'])
    def test_empty_buckets_respect_exclusive_end(self):
        rows=self.result('trip_trend',granularity='month',include_empty_buckets=True)['data']
        self.assertEqual([r['time_bucket'] for r in rows],['2024-07','2024-08','2024-09'])
    def test_unknown_station_is_preserved_and_filter_reported(self):
        r=self.result('station_flow',station_filter=[0],granularity='month')
        self.assertEqual(r['metadata']['filter']['station_filter'],[0])
        self.assertTrue(all(x['unknown_station_flag'] for x in r['data']))
        self.assertEqual(r['summary']['arrivals_total'],'1026')
    def test_empty_second_inside_coverage_has_zero_counts(self):
        r=self.result('ride_overview',start='2024-07-01 00:00:00',end='2024-07-01 00:00:01')
        self.assertEqual(r['metadata']['result_status'],'empty')
        row=r['data'][0]
        self.assertEqual((row['ride_count'],row['member_count'],row['duration_us']),('0','0','0'))
        self.assertIsNone(row['avg_duration_minutes'])
        self.assertIsNone(row['member_share'])
    def test_cli_default_granularity_is_day(self):
        p=subprocess.run([sys.executable,'-X','utf8','etl/query_results.py','--result','trip_trend'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(p.returncode,0,p.stderr)
        rows=json.loads(p.stdout)['data']
        self.assertEqual(len(rows),92)
        self.assertEqual(rows[0]['time_bucket'],'2024-07-01')
    def test_run_conservation_and_unique_rides(self):
        r=self.client.query("SELECT COUNT_BIG(*) AS n, COUNT_BIG(DISTINCT ride_id_identity) AS unique_n FROM dwd.fact_trip WHERE run_id='"+self.run_id+"'",DB)[0]
        self.assertEqual((r['n'],r['unique_n']),(563668,563668))
        rows=self.client.query("SELECT outcome,COUNT_BIG(*) AS n FROM meta.row_disposition WHERE run_id='"+self.run_id+"' GROUP BY outcome",DB)
        self.assertEqual({r['outcome']:r['n'] for r in rows},{'ACCEPTED':563668,'REJECTED':206})

if __name__=='__main__': unittest.main(verbosity=2)
