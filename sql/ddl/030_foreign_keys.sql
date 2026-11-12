IF DB_NAME() NOT IN (N'CitibikeDW_B_Test',N'CitibikeDW') OR COALESCE(CONVERT(nvarchar(128),(SELECT value FROM sys.extended_properties WHERE class=0 AND name=N'CitibikeWarehouseProject')),N'')<>N'citibike-warehouse' THROW 51000,'Use the protected project deployment entry point.',1;

IF OBJECT_ID(N'meta.FK_meta_run_source_01',N'F') IS NULL
ALTER TABLE [meta].[run_source] WITH CHECK ADD CONSTRAINT [FK_meta_run_source_01] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'meta.FK_meta_run_source_02',N'F') IS NULL
ALTER TABLE [meta].[run_source] WITH CHECK ADD CONSTRAINT [FK_meta_run_source_02] FOREIGN KEY ([source_member_id]) REFERENCES [meta].[source_member] ([source_member_id]);

IF OBJECT_ID(N'ods.FK_ods_trip_raw_03',N'F') IS NULL
ALTER TABLE [ods].[trip_raw] WITH CHECK ADD CONSTRAINT [FK_ods_trip_raw_03] FOREIGN KEY ([source_member_id]) REFERENCES [meta].[source_member] ([source_member_id]);

IF OBJECT_ID(N'meta.FK_meta_row_disposition_04',N'F') IS NULL
ALTER TABLE [meta].[row_disposition] WITH CHECK ADD CONSTRAINT [FK_meta_row_disposition_04] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'meta.FK_meta_coverage_05',N'F') IS NULL
ALTER TABLE [meta].[coverage] WITH CHECK ADD CONSTRAINT [FK_meta_coverage_05] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'dim.FK_dim_station_06',N'F') IS NULL
ALTER TABLE [dim].[station] WITH CHECK ADD CONSTRAINT [FK_dim_station_06] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_07',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_07] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'dws.FK_dws_trip_hourly_08',N'F') IS NULL
ALTER TABLE [dws].[trip_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_trip_hourly_08] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'dws.FK_dws_station_hourly_09',N'F') IS NULL
ALTER TABLE [dws].[station_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_station_hourly_09] FOREIGN KEY ([run_id]) REFERENCES [meta].[load_run] ([run_id]);

IF OBJECT_ID(N'meta.FK_meta_row_disposition_10',N'F') IS NULL
ALTER TABLE [meta].[row_disposition] WITH CHECK ADD CONSTRAINT [FK_meta_row_disposition_10] FOREIGN KEY ([source_row_id]) REFERENCES [ods].[trip_raw] ([source_row_id]);

IF OBJECT_ID(N'meta.FK_meta_row_disposition_11',N'F') IS NULL
ALTER TABLE [meta].[row_disposition] WITH CHECK ADD CONSTRAINT [FK_meta_row_disposition_11] FOREIGN KEY ([representative_source_row_id]) REFERENCES [ods].[trip_raw] ([source_row_id]);

IF OBJECT_ID(N'meta.FK_meta_row_disposition_12',N'F') IS NULL
ALTER TABLE [meta].[row_disposition] WITH CHECK ADD CONSTRAINT [FK_meta_row_disposition_12] FOREIGN KEY ([run_id],[trip_key]) REFERENCES [dwd].[fact_trip] ([run_id],[trip_key]);

IF OBJECT_ID(N'dim.FK_dim_station_13',N'F') IS NULL
ALTER TABLE [dim].[station] WITH CHECK ADD CONSTRAINT [FK_dim_station_13] FOREIGN KEY ([name_source_row_id]) REFERENCES [ods].[trip_raw] ([source_row_id]);

IF OBJECT_ID(N'dim.FK_dim_station_14',N'F') IS NULL
ALTER TABLE [dim].[station] WITH CHECK ADD CONSTRAINT [FK_dim_station_14] FOREIGN KEY ([coordinate_source_row_id]) REFERENCES [ods].[trip_raw] ([source_row_id]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_15',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_15] FOREIGN KEY ([representative_source_row_id]) REFERENCES [ods].[trip_raw] ([source_row_id]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_16',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_16] FOREIGN KEY ([start_date_key]) REFERENCES [dim].[date] ([date_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_17',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_17] FOREIGN KEY ([start_hour_key]) REFERENCES [dim].[hour] ([hour_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_18',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_18] FOREIGN KEY ([run_id],[start_station_key]) REFERENCES [dim].[station] ([run_id],[station_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_19',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_19] FOREIGN KEY ([end_date_key]) REFERENCES [dim].[date] ([date_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_20',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_20] FOREIGN KEY ([end_hour_key]) REFERENCES [dim].[hour] ([hour_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_21',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_21] FOREIGN KEY ([run_id],[end_station_key]) REFERENCES [dim].[station] ([run_id],[station_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_22',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_22] FOREIGN KEY ([bike_type_key]) REFERENCES [dim].[bike_type] ([bike_type_key]);

IF OBJECT_ID(N'dwd.FK_dwd_fact_trip_23',N'F') IS NULL
ALTER TABLE [dwd].[fact_trip] WITH CHECK ADD CONSTRAINT [FK_dwd_fact_trip_23] FOREIGN KEY ([member_type_key]) REFERENCES [dim].[member_type] ([member_type_key]);

IF OBJECT_ID(N'dws.FK_dws_trip_hourly_24',N'F') IS NULL
ALTER TABLE [dws].[trip_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_trip_hourly_24] FOREIGN KEY ([start_date_key]) REFERENCES [dim].[date] ([date_key]);

IF OBJECT_ID(N'dws.FK_dws_trip_hourly_25',N'F') IS NULL
ALTER TABLE [dws].[trip_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_trip_hourly_25] FOREIGN KEY ([start_hour_key]) REFERENCES [dim].[hour] ([hour_key]);

IF OBJECT_ID(N'dws.FK_dws_trip_hourly_26',N'F') IS NULL
ALTER TABLE [dws].[trip_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_trip_hourly_26] FOREIGN KEY ([bike_type_key]) REFERENCES [dim].[bike_type] ([bike_type_key]);

IF OBJECT_ID(N'dws.FK_dws_station_hourly_27',N'F') IS NULL
ALTER TABLE [dws].[station_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_station_hourly_27] FOREIGN KEY ([event_date_key]) REFERENCES [dim].[date] ([date_key]);

IF OBJECT_ID(N'dws.FK_dws_station_hourly_28',N'F') IS NULL
ALTER TABLE [dws].[station_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_station_hourly_28] FOREIGN KEY ([event_hour_key]) REFERENCES [dim].[hour] ([hour_key]);

IF OBJECT_ID(N'dws.FK_dws_station_hourly_29',N'F') IS NULL
ALTER TABLE [dws].[station_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_station_hourly_29] FOREIGN KEY ([bike_type_key]) REFERENCES [dim].[bike_type] ([bike_type_key]);

IF OBJECT_ID(N'dws.FK_dws_trip_hourly_30',N'F') IS NULL
ALTER TABLE [dws].[trip_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_trip_hourly_30] FOREIGN KEY ([member_type_key]) REFERENCES [dim].[member_type] ([member_type_key]);

IF OBJECT_ID(N'dws.FK_dws_station_hourly_31',N'F') IS NULL
ALTER TABLE [dws].[station_hourly] WITH CHECK ADD CONSTRAINT [FK_dws_station_hourly_31] FOREIGN KEY ([run_id],[station_key]) REFERENCES [dim].[station] ([run_id],[station_key]);
