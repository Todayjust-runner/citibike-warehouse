"""C查询回归：SQL仅在边界替身处替换，断言真实结果与SQL筛选。"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'etl'))
import query_results as q
import build_facts as facts
sys.path.pop(0)

class Client:
    def __init__(self):
        self.sql = []
    def query(self, sql, database):
        self.sql.append(sql)
        if 'FROM meta.load_run' in sql:
            return [dict(run_id='00000000-0000-0000-0000-000000000001',status='PUBLISHED',is_current=True,
                         input_set_sha256='a'*64,model_version='1.0',metric_rule_version='A-1.0',
                         processing_policy_version='B1-1.0',code_revision='fixture')]
        if 'FROM meta.coverage' in sql:
            return [dict(time_role=r,coverage_status='complete',coverage_start='2024-07-01T00:00:00',
                         coverage_end_exclusive='2024-10-01T00:00:00') for r in ('departure','arrival')]
        if 'FROM dim.bike_type' in sql:
            return [dict(bike_type_key=1,bike_type_code='classic_bike',is_unknown=False,is_recognized=True),
                    dict(bike_type_key=2,bike_type_code='electric_bike',is_unknown=False,is_recognized=True)]
        if 'FROM dim.member_type' in sql:
            return [dict(member_type_key=1,member_type_code='member',is_unknown=False,is_recognized=True)]
        if 'AS mk' in sql:
            return [dict(mk=1,bk=2,n=2,us='120000000')] if 'bike_type_key IN (2)' in sql else [dict(mk=1,bk=1,n=4,us='240000000'),dict(mk=1,bk=2,n=2,us='120000000')]
        if 'COALESCE(SUM(duration_us),0)' in sql:
            return [dict(n=0,us='0',mem=None,known=None,unknown=None)]
        return []

class QueryTests(unittest.TestCase):
    def wh(self, **params):
        w=q.Warehouse(Client(),'test',params); w.params=params; return w
    def test_d_can_import_from_project_root(self):
        r=subprocess.run([sys.executable,'-X','utf8','-c','from etl.query_results import get_result'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
    def test_none_granularity_uses_day(self):
        r=q.RESULTS['trip_trend'](self.wh(),{'granularity':None})
        self.assertEqual(r['metadata']['result_status'],'empty')
    def test_type_comparison_respects_bike_filter(self):
        r=q.type_comparison(self.wh(bike_filter=[2]))
        self.assertEqual([x['bike_type_key'] for x in r['data']],['2'])
    def test_window_outside_coverage_is_not_zero(self):
        w=self.wh(start='2025-01-01',end='2025-02-01')
        r=q.ride_overview(w)
        self.assertEqual(r['metadata']['result_status'],'insufficient_coverage')
        self.assertEqual(r['data'],[])
        flow=q.station_flow(w,'day')
        self.assertIsNone(flow['summary']['departures_total'])
    def test_zero_rows_have_zero_counts_and_null_ratios(self):
        r=q.ride_overview(self.wh())['data'][0]
        self.assertEqual(r['member_count'],'0')
        self.assertEqual(r['known_member_type_count'],'0')
        self.assertIsNone(r['member_share'])
    def test_fill_buckets_excludes_window_end(self):
        w=self.wh(start='2024-07-01',end='2024-08-01',include_empty_buckets=True)
        r=q.fill_buckets([],w,'month',['ride_count','member_count','member_share'])
        self.assertEqual([x['time_bucket'] for x in r],['2024-07'])
        self.assertEqual(r[0]['member_count'],'0')
    def test_invalid_calendar_time_is_rejected_not_crashed(self):
        self.assertIsNone(facts.parse_time_us('2024-02-30 10:00:00'))
    def test_mixed_iso_formats_use_chronological_order(self):
        w=self.wh(start='2024-07-01T00:00:00',end='2024-07-01 12:00:00')
        self.assertEqual(w.coverage['departure'],'complete')
    def test_invalid_calendar_request_is_structured_error(self):
        with self.assertRaises(q.EtlError): self.wh(start='2024-02-30',end='2024-03-01')
    def test_unpublished_run_cannot_be_queried(self):
        client=Client(); original=client.query
        def query(sql,database):
            rows=original(sql,database)
            if 'FROM meta.load_run' in sql: rows[0]['status']='RUNNING'
            return rows
        client.query=query
        with self.assertRaises(q.EtlError): q.Warehouse(client,'test',{})
    def test_station_filter_is_reported_in_metadata(self):
        w=self.wh(station_filter=[0])
        result=q.station_flow(w,'day')
        self.assertEqual(result['metadata']['filter']['station_filter'],[0])
    def test_full_snapshot_produces_both_coverage_roles(self):
        rows=[dict(zip_month_label=m,ended_at_raw=m[:4]+'-'+m[4:]+'-15 00:00:00') for m in ['202406','202407','202408','202409','202410']]
        result=facts.coverage_declarations(rows)
        self.assertEqual([x['time_role'] for x in result],['departure','arrival'])
        self.assertTrue(all(x['coverage_status']=='complete' for x in result))
        self.assertEqual(facts.coverage_declarations(rows[:-1])[0]['coverage_status'],'unknown')

if __name__ == '__main__': unittest.main()
