IF DB_NAME() NOT IN (N'CitibikeDW_B_Test',N'CitibikeDW') THROW 51000,'Wrong project database.',1;
GO
CREATE OR ALTER PROCEDURE meta.usp_assert_run_ready @run_id uniqueidentifier
AS
BEGIN
 SET NOCOUNT ON;
 -- These are consistency gates, not an ETL implementation or proof of real input.
 IF NOT EXISTS(SELECT 1 FROM meta.run_source WHERE run_id=@run_id)
  THROW 51040,'A validated run needs an explicit nonempty member inventory.',1;
 IF EXISTS(SELECT 1 FROM meta.run_source r JOIN meta.source_member m ON m.source_member_id=r.source_member_id
  WHERE r.run_id=@run_id AND (SELECT COUNT(*) FROM OPENJSON(m.csv_header))<>13)
  THROW 51040,'The source member header must have thirteen columns.',1;
 IF EXISTS(SELECT 1 FROM meta.run_source r JOIN meta.source_member m ON m.source_member_id=r.source_member_id
  CROSS APPLY OPENJSON(m.csv_header) j
  LEFT JOIN (VALUES(0,N'ride_id'),(1,N'rideable_type'),(2,N'started_at'),(3,N'ended_at'),
   (4,N'start_station_name'),(5,N'start_station_id'),(6,N'end_station_name'),(7,N'end_station_id'),
   (8,N'start_lat'),(9,N'start_lng'),(10,N'end_lat'),(11,N'end_lng'),(12,N'member_casual')) e(ordinal,field_name)
   ON e.ordinal=TRY_CONVERT(int,j.[key])
  WHERE r.run_id=@run_id AND (j.type<>1 OR e.field_name IS NULL OR CONVERT(varbinary(max),j.value)<>CONVERT(varbinary(max),e.field_name)))
  THROW 51040,'The member header fields or order do not match the source contract.',1;
 IF EXISTS(SELECT 1 FROM meta.run_source r JOIN meta.source_member m ON m.source_member_id=r.source_member_id
  WHERE r.run_id=@run_id AND (r.read_status<>'COMPLETE' OR m.archive_inventory_verified=0
   OR r.read_record_count<>m.csv_data_record_count
   OR r.read_record_count<>(SELECT COUNT_BIG(*) FROM ods.trip_raw x WHERE x.source_member_id=r.source_member_id)))
  THROW 51040,'Member reading or full raw-row counts differ.',1;
 IF EXISTS(SELECT m.zip_sha256 FROM meta.run_source r JOIN meta.source_member m ON m.source_member_id=r.source_member_id
  WHERE r.run_id=@run_id GROUP BY m.zip_sha256
  HAVING COUNT_BIG(*)<>MIN(m.zip_csv_member_count) OR MIN(m.zip_csv_member_count)<>MAX(m.zip_csv_member_count))
  THROW 51040,'The selected archive does not include every CSV member.',1;
 IF EXISTS(SELECT 1 FROM ods.trip_raw x JOIN meta.run_source r ON r.source_member_id=x.source_member_id
  WHERE r.run_id=@run_id AND (x.field_count<>13 OR (SELECT COUNT(*) FROM OPENJSON(x.raw_values))<>13
   OR EXISTS(SELECT 1 FROM OPENJSON(x.raw_values) j WHERE j.type<>1)))
  THROW 51040,'A publishable source row must contain thirteen string cells.',1;
 IF EXISTS(SELECT 1 FROM ods.trip_raw x JOIN meta.run_source r ON r.source_member_id=x.source_member_id
  WHERE r.run_id=@run_id AND (x.ride_id_raw IS NULL OR x.rideable_type_raw IS NULL OR x.started_at_raw IS NULL
   OR x.ended_at_raw IS NULL OR x.start_station_name_raw IS NULL OR x.start_station_id_raw IS NULL
   OR x.end_station_name_raw IS NULL OR x.end_station_id_raw IS NULL OR x.start_lat_raw IS NULL
   OR x.start_lng_raw IS NULL OR x.end_lat_raw IS NULL OR x.end_lng_raw IS NULL OR x.member_casual_raw IS NULL))
  THROW 51040,'CSV empty cells must be retained as empty strings; unsafe NULL parsing blocks publication.',1;
 IF EXISTS(SELECT 1 FROM meta.run_source r JOIN ods.trip_raw x ON x.source_member_id=r.source_member_id
  LEFT JOIN meta.row_disposition d ON d.run_id=r.run_id AND d.source_row_id=x.source_row_id
  WHERE r.run_id=@run_id AND d.source_row_id IS NULL)
  THROW 51040,'Some selected source rows have no primary disposition.',1;
 IF EXISTS(SELECT 1 FROM meta.row_disposition d JOIN ods.trip_raw x ON x.source_row_id=d.source_row_id
  LEFT JOIN meta.run_source r ON r.run_id=d.run_id AND r.source_member_id=x.source_member_id
  WHERE d.run_id=@run_id AND r.source_member_id IS NULL)
  THROW 51040,'A disposition refers to a source outside the run inventory.',1;
 IF EXISTS(SELECT f.trip_key FROM dwd.fact_trip f LEFT JOIN meta.row_disposition d
  ON d.run_id=f.run_id AND d.trip_key=f.trip_key AND d.outcome='ACCEPTED'
  WHERE f.run_id=@run_id GROUP BY f.trip_key,f.representative_source_row_id
  HAVING COUNT(d.source_row_id)<>1 OR MIN(d.source_row_id)<>f.representative_source_row_id)
  THROW 51040,'Each fact needs exactly one matching accepted source representative.',1;
 IF EXISTS(SELECT 1 FROM meta.row_disposition d JOIN dwd.fact_trip f ON f.run_id=d.run_id AND f.trip_key=d.trip_key
  WHERE d.run_id=@run_id AND d.outcome<>'REJECTED'
    AND (d.representative_source_row_id IS NULL OR d.representative_source_row_id<>f.representative_source_row_id))
  THROW 51040,'Duplicate/accepted lineage points to the wrong representative.',1;
 IF NOT EXISTS(SELECT 1 FROM dim.station WHERE run_id=@run_id AND station_key=0)
  THROW 51040,'The run has no dedicated unknown station.',1;
 IF EXISTS(SELECT 1 FROM dim.station s CROSS APPLY(VALUES(s.name_source_row_id),(s.coordinate_source_row_id)) v(source_row_id)
  LEFT JOIN meta.row_disposition d ON d.run_id=s.run_id AND d.source_row_id=v.source_row_id AND d.outcome='ACCEPTED'
  WHERE s.run_id=@run_id AND v.source_row_id IS NOT NULL AND d.source_row_id IS NULL)
  THROW 51040,'Station observations must come from accepted representatives in the same run.',1;
 IF NOT EXISTS(SELECT 1 FROM meta.coverage WHERE run_id=@run_id AND time_role='departure')
 OR NOT EXISTS(SELECT 1 FROM meta.coverage WHERE run_id=@run_id AND time_role='arrival')
  THROW 51040,'Both time roles require an explicit coverage declaration.',1;
 IF EXISTS(
  SELECT start_date_key,start_hour_key,bike_type_key,member_type_key,COUNT_BIG(*) AS n,SUM(CONVERT(decimal(38,0),duration_us)) AS duration_us
   FROM dwd.fact_trip WHERE run_id=@run_id GROUP BY start_date_key,start_hour_key,bike_type_key,member_type_key
  EXCEPT SELECT start_date_key,start_hour_key,bike_type_key,member_type_key,ride_count,duration_us FROM dws.trip_hourly WHERE run_id=@run_id)
 OR EXISTS(
  SELECT start_date_key,start_hour_key,bike_type_key,member_type_key,ride_count,duration_us FROM dws.trip_hourly WHERE run_id=@run_id
  EXCEPT SELECT start_date_key,start_hour_key,bike_type_key,member_type_key,COUNT_BIG(*),SUM(CONVERT(decimal(38,0),duration_us))
   FROM dwd.fact_trip WHERE run_id=@run_id GROUP BY start_date_key,start_hour_key,bike_type_key,member_type_key)
  THROW 51040,'Trip-hour aggregates differ from the atomic facts.',1;
 ;WITH events AS(
  SELECT start_date_key AS date_key,start_hour_key AS hour_key,start_station_key AS station_key,bike_type_key,CONVERT(bigint,1) AS dep,CONVERT(bigint,0) AS arr
   FROM dwd.fact_trip WHERE run_id=@run_id
  UNION ALL
  SELECT end_date_key,end_hour_key,end_station_key,bike_type_key,CONVERT(bigint,0),CONVERT(bigint,1)
   FROM dwd.fact_trip WHERE run_id=@run_id
 ), expected AS(
  SELECT date_key,hour_key,station_key,bike_type_key,SUM(dep) AS dep,SUM(arr) AS arr FROM events GROUP BY date_key,hour_key,station_key,bike_type_key
 ), differences AS(
  SELECT * FROM expected EXCEPT SELECT event_date_key,event_hour_key,station_key,bike_type_key,departures,arrivals FROM dws.station_hourly WHERE run_id=@run_id
 )
 SELECT * INTO #station_difference FROM differences;
 IF EXISTS(SELECT 1 FROM #station_difference) THROW 51040,'Station-hour aggregates are missing or changed.',1;
 ;WITH events AS(
  SELECT start_date_key AS date_key,start_hour_key AS hour_key,start_station_key AS station_key,bike_type_key,CONVERT(bigint,1) AS dep,CONVERT(bigint,0) AS arr
   FROM dwd.fact_trip WHERE run_id=@run_id
  UNION ALL SELECT end_date_key,end_hour_key,end_station_key,bike_type_key,CONVERT(bigint,0),CONVERT(bigint,1) FROM dwd.fact_trip WHERE run_id=@run_id
 ), expected AS(
  SELECT date_key,hour_key,station_key,bike_type_key,SUM(dep) AS dep,SUM(arr) AS arr FROM events GROUP BY date_key,hour_key,station_key,bike_type_key
 ), differences AS(
  SELECT event_date_key,event_hour_key,station_key,bike_type_key,departures,arrivals FROM dws.station_hourly WHERE run_id=@run_id EXCEPT SELECT * FROM expected
 ) SELECT * INTO #station_extra FROM differences;
 IF EXISTS(SELECT 1 FROM #station_extra) THROW 51040,'Station-hour aggregates contain extra groups.',1;
END;
GO
CREATE OR ALTER TRIGGER meta.TR_coverage_no_overlap ON meta.coverage AFTER INSERT,UPDATE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM inserted i JOIN meta.coverage c WITH(UPDLOCK,HOLDLOCK)
  ON c.run_id=i.run_id AND c.time_role=i.time_role AND c.coverage_id<>i.coverage_id
  AND c.coverage_start<i.coverage_end_exclusive AND i.coverage_start<c.coverage_end_exclusive)
  THROW 51030,'Coverage intervals for the same run and role must not overlap.',1;
END;
GO
CREATE OR ALTER TRIGGER meta.TR_load_run_publication ON meta.load_run AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM deleted d LEFT JOIN inserted i ON i.run_id=d.run_id
  WHERE d.status IN('VALIDATED','PUBLISHED') AND i.run_id IS NULL)
  THROW 51043,'Validated or published run metadata cannot be deleted.',1;
 IF EXISTS(SELECT 1 FROM inserted i JOIN deleted d ON d.run_id=i.run_id
  WHERE d.status<>i.status AND NOT((d.status='CREATED' AND i.status IN('RUNNING','FAILED'))
    OR (d.status='RUNNING' AND i.status IN('VALIDATED','FAILED')) OR(d.status='VALIDATED' AND i.status IN('PUBLISHED','FAILED'))))
  THROW 51043,'Invalid run-state transition; create a new run for a rebuild.',1;
 IF EXISTS(
  SELECT run_id,CONVERT(varbinary(128),data_scope) AS scope_id,CONVERT(varbinary(64),input_set_sha256) AS input_id,
   CONVERT(varbinary(32),model_version) AS model,CONVERT(varbinary(32),metric_rule_version) AS metric,
   CONVERT(varbinary(32),processing_policy_version) AS policy,CONVERT(varbinary(256),code_revision) AS code,
   started_at_utc,finished_at_utc FROM deleted WHERE status IN('VALIDATED','PUBLISHED')
  EXCEPT SELECT run_id,CONVERT(varbinary(128),data_scope),CONVERT(varbinary(64),input_set_sha256),
   CONVERT(varbinary(32),model_version),CONVERT(varbinary(32),metric_rule_version),
   CONVERT(varbinary(32),processing_policy_version),CONVERT(varbinary(256),code_revision),started_at_utc,finished_at_utc FROM inserted)
  THROW 51043,'Validated run input, code, versions and audit times are immutable.',1;
 DECLARE @id uniqueidentifier;
 DECLARE publish_cursor CURSOR LOCAL FAST_FORWARD FOR SELECT i.run_id FROM inserted i LEFT JOIN deleted d ON d.run_id=i.run_id
  WHERE i.status IN('VALIDATED','PUBLISHED') AND (d.run_id IS NULL OR d.status<>i.status);
 OPEN publish_cursor; FETCH NEXT FROM publish_cursor INTO @id;
 WHILE @@FETCH_STATUS=0
 BEGIN
  EXEC meta.usp_assert_run_ready @id;
  FETCH NEXT FROM publish_cursor INTO @id;
 END;
 CLOSE publish_cursor; DEALLOCATE publish_cursor;
END;
GO
CREATE OR ALTER PROCEDURE meta.usp_publish_run @run_id uniqueidentifier
AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 DECLARE @initial_trancount int=@@TRANCOUNT,@lock_result int,@state varchar(20),@current bit;
 BEGIN TRY
  IF @initial_trancount=0 BEGIN TRANSACTION;
  ELSE SAVE TRANSACTION citibike_publish_save;
  EXEC @lock_result=sys.sp_getapplock @Resource=N'citibike-warehouse-current',@LockMode='Exclusive',
   @LockOwner='Transaction',@LockTimeout=10000;
  IF @lock_result<0 THROW 51044,'Could not acquire the publication lock.',1;
  SELECT @state=status,@current=is_current FROM meta.load_run WITH(UPDLOCK,HOLDLOCK) WHERE run_id=@run_id;
  IF @state IS NULL OR (@state<>'VALIDATED' AND NOT(@state='PUBLISHED' AND @current=1))
   THROW 51044,'Only a validated run or the already-current published run can be published.',1;
  IF @state='VALIDATED'
  BEGIN
   EXEC meta.usp_assert_run_ready @run_id;
   UPDATE meta.load_run SET is_current=0 WHERE data_scope=N'JC_official_snapshot' AND is_current=1;
   UPDATE meta.load_run SET status='PUBLISHED',is_current=1 WHERE run_id=@run_id;
  END;
  IF @initial_trancount=0 COMMIT TRANSACTION;
 END TRY
 BEGIN CATCH
  IF @initial_trancount=0 AND XACT_STATE()<>0 ROLLBACK TRANSACTION;
  ELSE IF @initial_trancount>0 AND XACT_STATE()=1 ROLLBACK TRANSACTION citibike_publish_save;
  -- If an ambient transaction is uncommittable, the caller must roll it back.
  THROW;
 END CATCH;
END;

GO
CREATE OR ALTER TRIGGER meta.TR_run_source_run_frozen ON meta.run_source AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER dim.TR_station_run_frozen ON dim.station AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER dwd.TR_fact_trip_run_frozen ON dwd.fact_trip AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER meta.TR_row_disposition_run_frozen ON meta.row_disposition AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER meta.TR_coverage_run_frozen ON meta.coverage AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER dws.TR_trip_hourly_run_frozen ON dws.trip_hourly AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER dws.TR_station_hourly_run_frozen ON dws.station_hourly AFTER INSERT,UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM (SELECT run_id FROM inserted UNION SELECT run_id FROM deleted) x
  JOIN meta.load_run r WITH(UPDLOCK,HOLDLOCK) ON r.run_id=x.run_id WHERE r.status IN('VALIDATED','PUBLISHED'))
  THROW 51041,'Validated/published run data is immutable; construct a new run.',1;
END;

GO
CREATE OR ALTER TRIGGER ods.TR_trip_raw_immutable ON ods.trip_raw AFTER UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM deleted) THROW 51042,'Source rows and global dimension identities are immutable.',1;
END;

GO
CREATE OR ALTER TRIGGER dim.TR_bike_type_immutable ON dim.bike_type AFTER UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM deleted) THROW 51042,'Source rows and global dimension identities are immutable.',1;
END;

GO
CREATE OR ALTER TRIGGER dim.TR_member_type_immutable ON dim.member_type AFTER UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM deleted) THROW 51042,'Source rows and global dimension identities are immutable.',1;
END;

GO
CREATE OR ALTER TRIGGER dim.TR_date_immutable ON dim.date AFTER UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM deleted) THROW 51042,'Source rows and global dimension identities are immutable.',1;
END;

GO
CREATE OR ALTER TRIGGER dim.TR_hour_immutable ON dim.hour AFTER UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT 1 FROM deleted) THROW 51042,'Source rows and global dimension identities are immutable.',1;
END;

GO
CREATE OR ALTER TRIGGER meta.TR_source_member_immutable ON meta.source_member AFTER UPDATE,DELETE
AS
BEGIN
 SET NOCOUNT ON;
 IF EXISTS(SELECT source_member_id,CONVERT(varbinary(max),zip_sha256) AS z,CONVERT(varbinary(max),zip_url) AS u,zip_bytes,zip_month_label,zip_csv_member_count,member_path_identity,csv_sha256,CONVERT(varbinary(max),csv_header) AS h,csv_data_record_count,acquired_at_utc FROM deleted
 EXCEPT SELECT source_member_id,CONVERT(varbinary(max),zip_sha256),CONVERT(varbinary(max),zip_url),zip_bytes,zip_month_label,zip_csv_member_count,member_path_identity,csv_sha256,CONVERT(varbinary(max),csv_header),csv_data_record_count,acquired_at_utc FROM inserted)
 OR EXISTS(SELECT 1 FROM inserted i JOIN deleted d ON d.source_member_id=i.source_member_id WHERE i.archive_inventory_verified<d.archive_inventory_verified)
  THROW 51042,'Source identity is immutable; inventory verification may only advance 0 to 1.',1;
END;
