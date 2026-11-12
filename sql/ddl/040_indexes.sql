IF DB_NAME() NOT IN (N'CitibikeDW_B_Test',N'CitibikeDW') OR COALESCE(CONVERT(nvarchar(128),(SELECT value FROM sys.extended_properties WHERE class=0 AND name=N'CitibikeWarehouseProject')),N'')<>N'citibike-warehouse' THROW 51000,'Use the protected project deployment entry point.',1;

IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'meta.load_run') AND name=N'UX_meta_load_run_current')
CREATE UNIQUE NONCLUSTERED INDEX [UX_meta_load_run_current] ON [meta].[load_run] ([data_scope]) WHERE [is_current]=1;

IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dwd.fact_trip') AND name=N'IX_fact_departure')
CREATE NONCLUSTERED INDEX [IX_fact_departure] ON [dwd].[fact_trip] ([run_id],[started_at],[bike_type_key]) INCLUDE ([duration_us],[trip_count],[member_type_key],[start_station_key]);

IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dwd.fact_trip') AND name=N'IX_fact_arrival')
CREATE NONCLUSTERED INDEX [IX_fact_arrival] ON [dwd].[fact_trip] ([run_id],[ended_at],[bike_type_key]) INCLUDE ([trip_count],[end_station_key]);

IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'meta.row_disposition') AND name=N'IX_disposition_trip')
CREATE NONCLUSTERED INDEX [IX_disposition_trip] ON [meta].[row_disposition] ([run_id],[trip_key]) INCLUDE ([outcome],[representative_source_row_id]);
