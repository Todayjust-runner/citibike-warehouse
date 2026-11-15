"""ETL判定的手工边界用例，不连接数据库。"""
import unittest
from etl.build_facts import judge, coord_pair


def row(number, ride_id, start='2024-07-01 00:00:00.123456', end='2024-07-01 00:01:00.123456'):
    return dict(source_row_id=number,csv_record_number=number+1,zip_sha256='a'*64,member_path='test.csv',
                ride_id_raw=ride_id,rideable_type_raw='classic_bike',started_at_raw=start,ended_at_raw=end,
                start_station_name_raw='',start_station_id_raw='',end_station_name_raw='',end_station_id_raw='',
                start_lat_raw='',start_lng_raw='',end_lat_raw='',end_lng_raw='',member_casual_raw='member')


class ProcessingTests(unittest.TestCase):
    def test_duration_boundaries_keep_exact_microseconds(self):
        records=[row(1,'min'),row(2,'max',end='2024-07-02 00:00:00.123456'),
                 row(3,'short',end='2024-07-01 00:01:00.123455'),
                 row(4,'long',end='2024-07-02 00:00:00.123457')]
        outcomes,accepted=judge(records)
        self.assertEqual([r['_t'][2] for r in accepted],[60000000,86400000000])
        self.assertEqual(outcomes[3][1],'DURATION_LT_60S')
        self.assertEqual(outcomes[4][1],'DURATION_GT_24H')
    def test_exact_duplicates_keep_one_conflicts_reject_whole_group(self):
        records=[row(1,'same'),row(2,'same'),row(3,'conflict'),row(4,'conflict',end='2024-07-01 00:02:00.123456')]
        outcomes,accepted=judge(records)
        self.assertEqual([r['source_row_id'] for r in accepted],[1])
        self.assertEqual(outcomes[2],('DUPLICATE_EXACT','NONE',1))
        self.assertEqual(outcomes[3][1],'CONFLICTING_RIDE_ID')
        self.assertEqual(outcomes[4][1],'CONFLICTING_RIDE_ID')
    def test_unknown_station_and_coordinates_keep_valid_trip(self):
        outcomes,accepted=judge([row(1,'unknown')])
        self.assertEqual(len(accepted),1)
        self.assertEqual(outcomes[1][0],'ACCEPTED')
        self.assertEqual(coord_pair('',''),('missing',None,None))

if __name__=='__main__': unittest.main()
