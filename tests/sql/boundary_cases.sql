-- SYNTHETIC B2 fixtures only. Each case rolls back its entire transaction.
SET NOCOUNT ON;
SET XACT_ABORT OFF;
IF DB_NAME() <> N'CitibikeDW_B_Test' THROW 51200, 'Boundary fixtures are test-database only.', 1;
GO
CREATE PROCEDURE #b2_fixture @a uniqueidentifier OUTPUT, @b uniqueidentifier OUTPUT,
                           @raw bigint OUTPUT, @trip bigint OUTPUT
AS
BEGIN
 SET NOCOUNT ON;
 SET @a=NEWID(); SET @b=NEWID();
 INSERT meta.source_member(zip_sha256,zip_url,zip_bytes,zip_month_label,zip_csv_member_count,
 archive_inventory_verified,member_path,csv_sha256,csv_header,csv_data_record_count,acquired_at_utc)
 VALUES(REPLICATE('a',64),N'https://example.invalid/SYNTHETIC-B2.zip',1,'202409',1,1,
 N'SYNTHETIC-B2.csv',REPLICATE('b',64),
 N'["ride_id","rideable_type","started_at","ended_at","start_station_name","start_station_id","end_station_name","end_station_id","start_lat","start_lng","end_lat","end_lng","member_casual"]',1,SYSUTCDATETIME());
 DECLARE @member bigint=SCOPE_IDENTITY();
 INSERT meta.load_run(run_id,data_scope,input_set_sha256,model_version,metric_rule_version,
 processing_policy_version,code_revision,status,is_current,started_at_utc)
 VALUES(@a,N'JC_official_snapshot',REPLICATE('c',64),'1.0','A-1.0','B1-1.0',N'SYNTHETIC-B2','RUNNING',0,SYSUTCDATETIME()),
       (@b,N'JC_official_snapshot',REPLICATE('c',64),'1.0','A-1.0','B1-1.0',N'SYNTHETIC-B2','RUNNING',0,SYSUTCDATETIME());
 INSERT meta.run_source VALUES(@a,@member,1,'COMPLETE'),(@b,@member,1,'COMPLETE');
 INSERT ods.trip_raw(source_member_id,csv_record_number,field_count,raw_values,
 ride_id_raw,rideable_type_raw,started_at_raw,ended_at_raw,start_station_name_raw,start_station_id_raw,
 end_station_name_raw,end_station_id_raw,start_lat_raw,start_lng_raw,end_lat_raw,end_lng_raw,member_casual_raw)
 VALUES(@member,2,13,N'["SYNTHETIC-B2","classic_bike","2024-09-30 23:59:00.123456","2024-10-01 00:00:00.123456","","","","","","","","","member"]',
 N'SYNTHETIC-B2',N'classic_bike',N'2024-09-30 23:59:00.123456',N'2024-10-01 00:00:00.123456',
 N'',N'',N'',N'',N'',N'',N'',N'',N'member');
 SET @raw=SCOPE_IDENTITY();
 IF NOT EXISTS(SELECT 1 FROM dim.date WHERE date_key=20240930)
 INSERT dim.date VALUES(20240930,'20240930',2024,3,9,'2024-09',30,1,N'星期一');
 IF NOT EXISTS(SELECT 1 FROM dim.date WHERE date_key=20241001)
 INSERT dim.date VALUES(20241001,'20241001',2024,4,10,'2024-10',1,2,N'星期二');
 INSERT dim.station(run_id,station_key,station_id,station_name,is_unknown,name_is_fallback)
 VALUES(@a,0,NULL,N'未知站点',1,1),(@b,0,NULL,N'未知站点',1,1),(@a,1,N'B2-A',N'SYNTHETIC station A',0,1);
 INSERT dwd.fact_trip(run_id,ride_id,representative_source_row_id,started_at,ended_at,duration_us,
 trip_count,start_date_key,start_hour_key,end_date_key,end_hour_key,start_station_key,end_station_key,
 bike_type_key,member_type_key,start_coordinate_status,end_coordinate_status)
 VALUES(@a,N'SYNTHETIC-B2',@raw,'2024-09-30T23:59:00.123456','2024-10-01T00:00:00.123456',60000000,
 1,20240930,23,20241001,0,0,0,1,1,'missing','missing');
 SET @trip=SCOPE_IDENTITY();
 INSERT meta.row_disposition VALUES(@a,@raw,'ACCEPTED','NONE',@trip,@raw,N'[]');
 INSERT dwd.fact_trip(run_id,ride_id,representative_source_row_id,started_at,ended_at,duration_us,
 trip_count,start_date_key,start_hour_key,end_date_key,end_hour_key,start_station_key,end_station_key,
 bike_type_key,member_type_key,start_coordinate_status,end_coordinate_status)
 VALUES(@b,N'SYNTHETIC-B2',@raw,'2024-09-30T23:59:00.123456','2024-10-01T00:00:00.123456',60000000,
 1,20240930,23,20241001,0,0,0,1,1,'missing','missing');
 INSERT meta.row_disposition VALUES(@b,@raw,'ACCEPTED','NONE',CONVERT(bigint,SCOPE_IDENTITY()),@raw,N'[]');
 INSERT meta.coverage(run_id,time_role,coverage_start,coverage_end_exclusive,coverage_status,proof_ref)
 VALUES(@a,'departure','20240701','20241001','complete',N'SYNTHETIC-B2-proof'),
 (@a,'arrival','20240701','20241001','complete',N'SYNTHETIC-B2-proof'),
 (@b,'departure','20240701','20241001','complete',N'SYNTHETIC-B2-proof'),
 (@b,'arrival','20240701','20241001','complete',N'SYNTHETIC-B2-proof');
 INSERT dws.trip_hourly VALUES(@a,20240930,23,1,1,1,60000000),(@b,20240930,23,1,1,1,60000000);
 INSERT dws.station_hourly VALUES(@a,20240930,23,0,1,1,0),(@a,20241001,0,0,1,0,1),
 (@b,20240930,23,0,1,1,0),(@b,20241001,0,0,1,0,1);
END;
GO
CREATE TABLE #cases(name varchar(100) PRIMARY KEY, expected_errors varchar(100), action nvarchar(max));
INSERT #cases VALUES
('millisecond_and_microsecond_preserved','0',N'IF NOT EXISTS(SELECT 1 FROM dwd.fact_trip WHERE run_id=@a AND DATEPART(NANOSECOND,started_at)=123456000) THROW 51300,''precision lost'',1;'),
('sixty_seconds_is_valid','0',N'IF (SELECT duration_us FROM dwd.fact_trip WHERE run_id=@a)<>60000000 THROW 51300,''wrong duration'',1;'),
('exact_24h_is_valid','0',N'UPDATE dwd.fact_trip SET started_at=''2024-09-30T00:00:00.123456'',start_hour_key=0,duration_us=86400000000 WHERE run_id=@a;'),
('below_60s_one_microsecond','547',N'UPDATE dwd.fact_trip SET ended_at=''2024-10-01T00:00:00.123455'',duration_us=59999999 WHERE run_id=@a;'),
('over_24h_one_microsecond','547',N'UPDATE dwd.fact_trip SET started_at=''2024-09-30T00:00:00.123455'',start_hour_key=0,duration_us=86400000001 WHERE run_id=@a;'),
('sub_microsecond_is_rejected','547',N'UPDATE dwd.fact_trip SET started_at=''2024-09-30T23:59:00.1234567'' WHERE run_id=@a;'),
('duration_must_equal_timestamps','547',N'UPDATE dwd.fact_trip SET duration_us=60000001 WHERE run_id=@a;'),
('date_role_must_match_timestamp','547',N'UPDATE dwd.fact_trip SET start_date_key=20241001 WHERE run_id=@a;'),
('hour_role_must_match_timestamp','547',N'UPDATE dwd.fact_trip SET end_hour_key=1 WHERE run_id=@a;'),
('missing_station_still_counts','0',N'IF (SELECT COUNT_BIG(*) FROM dwd.fact_trip WHERE run_id=@a AND end_station_key=0)<>1 THROW 51300,''unknown lost'',1;'),
('station_fk_cannot_cross_run','547',N'UPDATE dwd.fact_trip SET start_station_key=1 WHERE run_id=@b;'),
('missing_source_fk_rejected','547',N'UPDATE dwd.fact_trip SET representative_source_row_id=-999 WHERE run_id=@a;'),
('ride_count_is_one','547',N'UPDATE dwd.fact_trip SET trip_count=2 WHERE run_id=@a;'),
('invalid_coordinate_pair','547',N'UPDATE dwd.fact_trip SET start_coordinate_status=''valid'',start_lat=40 WHERE run_id=@a;'),
('invalid_latitude','547',N'UPDATE dwd.fact_trip SET start_coordinate_status=''valid'',start_lat=91,start_lng=-74 WHERE run_id=@a;'),
('missing_coordinate_not_zero','547',N'UPDATE dwd.fact_trip SET end_lat=0,end_lng=0 WHERE run_id=@a;'),
('negative_aggregate_rejected','547',N'UPDATE dws.station_hourly SET arrivals=-1 WHERE run_id=@a;'),
('rejected_disposition_has_no_fact','547',N'UPDATE meta.row_disposition SET outcome=''REJECTED'',primary_reason=''TIME_PARSE_ERROR'' WHERE run_id=@a;'),
('duplicate_disposition_locator','2601,2627',N'INSERT meta.row_disposition SELECT * FROM meta.row_disposition WHERE run_id=@a;'),
('unknown_station_identity_is_null','547',N'UPDATE dim.station SET station_id=N''fake'' WHERE run_id=@a AND station_key=0;'),
('unknown_label_cannot_be_recognized','547',N'UPDATE dim.member_type SET is_recognized=1 WHERE member_type_key=0;'),
('recognized_flag_is_exact','547',N'INSERT dim.member_type(member_type_code,member_type_label,is_unknown,is_recognized) VALUES(N''Member'',N''SYNTHETIC'',0,1);'),
('case_and_trailing_space_are_distinct','0',N'INSERT dim.member_type(member_type_code,member_type_label,is_unknown,is_recognized) VALUES(N''Member'',N''SYNTHETIC'',0,0),(N''member '',N''SYNTHETIC'',0,0); IF (SELECT COUNT(*) FROM dim.member_type WHERE member_type_identity IN(CONVERT(varbinary(400),N''member''),CONVERT(varbinary(400),N''Member''),CONVERT(varbinary(400),N''member '')))<>3 THROW 51300,''identity collapsed'',1;'),
('exact_label_duplicate_rejected','2601,2627',N'INSERT dim.member_type(member_type_code,member_type_label,is_unknown,is_recognized) VALUES(N''member'',N''SYNTHETIC'',0,1);'),
('long_label_fails_without_truncation','2628,8152',N'INSERT dim.member_type(member_type_code,member_type_label,is_unknown,is_recognized) VALUES(REPLICATE(N''x'',201),N''SYNTHETIC'',0,0);'),
('coverage_proof_required','547',N'UPDATE meta.coverage SET proof_ref=NULL WHERE run_id=@a;'),
('coverage_overlap_rejected','51030',N'INSERT meta.coverage(run_id,time_role,coverage_start,coverage_end_exclusive,coverage_status,proof_ref) VALUES(@a,''departure'',''20240801'',''20241101'',''complete'',N''SYNTHETIC'');'),
('adjacent_coverage_allowed','0',N'INSERT meta.coverage(run_id,time_role,coverage_start,coverage_end_exclusive,coverage_status,proof_ref) VALUES(@a,''departure'',''20241001'',''20241101'',''partial'',NULL);'),
('current_requires_published','547',N'UPDATE meta.load_run SET is_current=1 WHERE run_id=@a;'),
('validated_requires_all_source_rows','51040',N'DELETE meta.row_disposition WHERE run_id=@a; UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a;'),
('validated_requires_exact_rollups','51040',N'UPDATE dws.station_hourly SET departures=2 WHERE run_id=@a AND event_date_key=20240930; UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a;'),
('complete_fixture_can_publish','0',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; UPDATE meta.load_run SET status=''PUBLISHED'',is_current=1 WHERE run_id=@a;'),
('only_one_current_run','2601,2627',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id IN(@a,@b); UPDATE meta.load_run SET status=''PUBLISHED'',is_current=1 WHERE run_id=@a; UPDATE meta.load_run SET status=''PUBLISHED'',is_current=1 WHERE run_id=@b;'),
('validated_fact_is_frozen','51041',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; UPDATE dwd.fact_trip SET ride_id=N''changed'' WHERE run_id=@a;'),
('raw_rows_are_immutable','51042',N'UPDATE ods.trip_raw SET ride_id_raw=N''changed'' WHERE source_row_id=@raw;'),
('cross_month_events_remain_in_fact','0',N'IF (SELECT COUNT(*) FROM dwd.fact_trip WHERE run_id=@a AND started_at<''20241001'' AND ended_at>=''20241001'')<>1 THROW 51300,''boundary lost'',1;'),
('iso_weekday_is_not_session_dependent','0',N'SET DATEFIRST 7; IF (SELECT iso_weekday FROM dim.date WHERE date_key=20240930)<>1 THROW 51300,''weekday wrong'',1; SET DATEFIRST 1;');
INSERT #cases VALUES
('accepted_requires_nonnull_representative','547',N'UPDATE meta.row_disposition SET representative_source_row_id=NULL WHERE run_id=@a;'),
('zero_zero_is_valid_coordinate','0',N'UPDATE dwd.fact_trip SET start_lat=0,start_lng=0,start_coordinate_status=''valid'' WHERE run_id=@a;'),
('duplicate_ride_identity_rejected','2601,2627',N'INSERT dwd.fact_trip(run_id,ride_id,representative_source_row_id,started_at,ended_at,duration_us,trip_count,start_date_key,start_hour_key,end_date_key,end_hour_key,start_station_key,end_station_key,bike_type_key,member_type_key,start_coordinate_status,end_coordinate_status) SELECT run_id,ride_id,representative_source_row_id,started_at,ended_at,duration_us,trip_count,start_date_key,start_hour_key,end_date_key,end_hour_key,start_station_key,end_station_key,bike_type_key,member_type_key,start_coordinate_status,end_coordinate_status FROM dwd.fact_trip WHERE run_id=@a;'),
('ride_trailing_space_identity_is_distinct','0',N'INSERT dwd.fact_trip(run_id,ride_id,representative_source_row_id,started_at,ended_at,duration_us,trip_count,start_date_key,start_hour_key,end_date_key,end_hour_key,start_station_key,end_station_key,bike_type_key,member_type_key,start_coordinate_status,end_coordinate_status) SELECT run_id,ride_id+N'' '',representative_source_row_id,started_at,ended_at,duration_us,trip_count,start_date_key,start_hour_key,end_date_key,end_hour_key,start_station_key,end_station_key,bike_type_key,member_type_key,start_coordinate_status,end_coordinate_status FROM dwd.fact_trip WHERE run_id=@a; IF (SELECT COUNT(*) FROM dwd.fact_trip WHERE run_id=@a)<>2 THROW 51300,''ride identity collapsed'',1;');
INSERT #cases VALUES
('validated_metadata_is_frozen','51043',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; UPDATE meta.load_run SET code_revision=N''SYNTHETIC-unreviewed-change'' WHERE run_id=@a;'),
('publish_procedure_switches_current','0',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id IN(@a,@b); EXEC meta.usp_publish_run @a; EXEC meta.usp_publish_run @b; IF (SELECT COUNT(*) FROM meta.load_run WHERE is_current=1)<>1 OR NOT EXISTS(SELECT 1 FROM meta.load_run WHERE run_id=@b AND is_current=1) THROW 51300,''publish switch failed'',1;'),
('failed_publish_preserves_current','51044',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; UPDATE meta.load_run SET status=''PUBLISHED'',is_current=1 WHERE run_id=@a; BEGIN TRY EXEC meta.usp_publish_run @b; END TRY BEGIN CATCH IF NOT EXISTS(SELECT 1 FROM meta.load_run WHERE run_id=@a AND is_current=1) THROW 51300,''current lost on failed publish'',1; THROW; END CATCH;');
INSERT #cases VALUES
('coverage_precision_is_microsecond_aligned','547',N'UPDATE meta.coverage SET coverage_start=''2024-07-01T00:00:00.0000001'' WHERE run_id=@a AND time_role=''departure'';'),
('header_shape_is_a_publication_gate','51040',N'INSERT meta.source_member(zip_sha256,zip_url,zip_bytes,zip_month_label,zip_csv_member_count,archive_inventory_verified,member_path,csv_sha256,csv_header,csv_data_record_count,acquired_at_utc) VALUES(REPLICATE(''d'',64),N''https://example.invalid/SYNTHETIC-bad-header.zip'',1,''202409'',1,1,N''SYNTHETIC-bad-header.csv'',REPLICATE(''e'',64),N''["wrong"]'',0,SYSUTCDATETIME()); DECLARE @extra bigint=SCOPE_IDENTITY(); INSERT meta.run_source VALUES(@a,@extra,0,''COMPLETE''); UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a;');
INSERT #cases VALUES
('null_raw_cell_prevents_validation','51040',N'INSERT meta.source_member(zip_sha256,zip_url,zip_bytes,zip_month_label,zip_csv_member_count,archive_inventory_verified,member_path,csv_sha256,csv_header,csv_data_record_count,acquired_at_utc) SELECT REPLICATE(''d'',64),N''https://example.invalid/SYNTHETIC-null-cell.zip'',1,''202409'',1,1,N''SYNTHETIC-null-cell.csv'',REPLICATE(''e'',64),csv_header,1,SYSUTCDATETIME() FROM meta.source_member WHERE source_member_id=(SELECT source_member_id FROM ods.trip_raw WHERE source_row_id=@raw); DECLARE @extra bigint=SCOPE_IDENTITY(); INSERT meta.run_source VALUES(@a,@extra,1,''COMPLETE''); INSERT ods.trip_raw(source_member_id,csv_record_number,field_count,raw_values,ride_id_raw,rideable_type_raw,started_at_raw,ended_at_raw,start_station_name_raw,start_station_id_raw,end_station_name_raw,end_station_id_raw,start_lat_raw,start_lng_raw,end_lat_raw,end_lng_raw,member_casual_raw) SELECT @extra,2,field_count,raw_values,NULL,rideable_type_raw,started_at_raw,ended_at_raw,start_station_name_raw,start_station_id_raw,end_station_name_raw,end_station_id_raw,start_lat_raw,start_lng_raw,end_lat_raw,end_lng_raw,member_casual_raw FROM ods.trip_raw WHERE source_row_id=@raw; DECLARE @badrow bigint=SCOPE_IDENTITY(); INSERT meta.row_disposition VALUES(@a,@badrow,''REJECTED'',''MISSING_RIDE_ID'',NULL,NULL,N''[]''); UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a;');
INSERT #cases VALUES
('validated_source_rejects_raw_append','51042',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; INSERT ods.trip_raw(source_member_id,csv_record_number,field_count,raw_values) SELECT source_member_id,3,13,raw_values FROM ods.trip_raw WHERE source_row_id=@raw;'),
('published_source_rejects_raw_append','51042',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; EXEC meta.usp_publish_run @a; INSERT ods.trip_raw(source_member_id,csv_record_number,field_count,raw_values) SELECT source_member_id,3,13,raw_values FROM ods.trip_raw WHERE source_row_id=@raw;'),
('new_source_remains_appendable_after_publish','0',N'UPDATE meta.load_run SET status=''VALIDATED'',finished_at_utc=SYSUTCDATETIME() WHERE run_id=@a; EXEC meta.usp_publish_run @a; INSERT meta.source_member(zip_sha256,zip_url,zip_bytes,zip_month_label,zip_csv_member_count,archive_inventory_verified,member_path,csv_sha256,csv_header,csv_data_record_count,acquired_at_utc) SELECT REPLICATE(''d'',64),N''https://example.invalid/SYNTHETIC-new-source.zip'',1,''202410'',1,1,N''SYNTHETIC-new-source.csv'',REPLICATE(''e'',64),csv_header,1,SYSUTCDATETIME() FROM meta.source_member WHERE source_member_id=(SELECT source_member_id FROM ods.trip_raw WHERE source_row_id=@raw); DECLARE @extra bigint=SCOPE_IDENTITY(); INSERT ods.trip_raw(source_member_id,csv_record_number,field_count,raw_values) VALUES(@extra,2,13,N''["","","","","","","","","","","","",""]''); IF NOT EXISTS(SELECT 1 FROM ods.trip_raw WHERE source_member_id=@extra) THROW 51300,''new source blocked'',1;');
CREATE TABLE #results(name varchar(100), passed bit, actual_error int, detail nvarchar(2048));
DECLARE @name varchar(100),@errors varchar(100),@action nvarchar(max),@a uniqueidentifier,@b uniqueidentifier,@raw bigint,@trip bigint;
DECLARE cases_cursor CURSOR LOCAL FAST_FORWARD FOR SELECT name,expected_errors,action FROM #cases ORDER BY name;
OPEN cases_cursor; FETCH NEXT FROM cases_cursor INTO @name,@errors,@action;
WHILE @@FETCH_STATUS=0
BEGIN
 BEGIN TRY
  BEGIN TRANSACTION;
  EXEC #b2_fixture @a OUTPUT,@b OUTPUT,@raw OUTPUT,@trip OUTPUT;
  EXEC sys.sp_executesql @action,N'@a uniqueidentifier,@b uniqueidentifier,@raw bigint,@trip bigint',@a,@b,@raw,@trip;
  IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
  INSERT #results VALUES(@name,CASE WHEN @errors='0' THEN 1 ELSE 0 END,0,N'Action completed');
 END TRY
 BEGIN CATCH
  DECLARE @error int=ERROR_NUMBER(),@detail nvarchar(2048)=ERROR_MESSAGE();
  IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
  INSERT #results VALUES(@name,CASE WHEN CHARINDEX(','+CONVERT(varchar(12),@error)+',',','+@errors+',')>0 THEN 1 ELSE 0 END,@error,@detail);
 END CATCH;
 FETCH NEXT FROM cases_cursor INTO @name,@errors,@action;
END;
CLOSE cases_cursor; DEALLOCATE cases_cursor;
DECLARE @json nvarchar(max)=(SELECT name,passed,actual_error,detail FROM #results ORDER BY name FOR JSON PATH);
SELECT N'__B2_CASES_BEGIN__'+@json+N'__B2_CASES_END__';
IF EXISTS(SELECT 1 FROM #results WHERE passed=0) THROW 51201, 'B2 boundary behavior failed.', 1;
