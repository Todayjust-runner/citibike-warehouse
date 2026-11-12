IF DB_NAME() NOT IN (N'CitibikeDW_B_Test',N'CitibikeDW') OR COALESCE(CONVERT(nvarchar(128),(SELECT value FROM sys.extended_properties WHERE class=0 AND name=N'CitibikeWarehouseProject')),N'')<>N'citibike-warehouse' THROW 51000,'Use the protected project deployment entry point.',1;


IF OBJECT_ID(N'meta.source_member',N'U') IS NULL
CREATE TABLE [meta].[source_member] (
  [source_member_id] bigint IDENTITY(1,1) NOT NULL,
  [zip_sha256] char(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [zip_url] nvarchar(2048) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [zip_bytes] bigint NOT NULL,
  [zip_month_label] char(6) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [zip_csv_member_count] int NOT NULL,
  [archive_inventory_verified] bit NOT NULL,
  [member_path] nvarchar(512) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [member_path_identity] AS CONVERT(varbinary(1024),[member_path]) PERSISTED NOT NULL,
  [csv_sha256] char(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [csv_header] nvarchar(max) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [csv_data_record_count] bigint NOT NULL,
  [acquired_at_utc] datetime2(7) NOT NULL,
  CONSTRAINT [PK_meta_source_member] PRIMARY KEY CLUSTERED ([source_member_id]),
  CONSTRAINT [UQ_meta_source_member_1] UNIQUE NONCLUSTERED ([zip_sha256],[member_path_identity]),
  CONSTRAINT [CK_meta_source_member_zip_sha256] CHECK (DATALENGTH([zip_sha256])=64 AND [zip_sha256] NOT LIKE '%[^0-9a-f]%'),
  CONSTRAINT [CK_meta_source_member_zip_bytes] CHECK ([zip_bytes]>=0),
  CONSTRAINT [CK_meta_source_member_zip_csv_member_count] CHECK ([zip_csv_member_count]>0),
  CONSTRAINT [CK_meta_source_member_csv_sha256] CHECK (DATALENGTH([csv_sha256])=64 AND [csv_sha256] NOT LIKE '%[^0-9a-f]%'),
  CONSTRAINT [CK_meta_source_member_csv_header] CHECK (ISJSON([csv_header])=1 AND LEFT(LTRIM([csv_header]),1)=N'['),
  CONSTRAINT [CK_meta_source_member_csv_data_record_count] CHECK ([csv_data_record_count]>=0),
  CONSTRAINT [CK_meta_source_member_member_path] CHECK (LEN(REPLACE(REPLACE(REPLACE(REPLACE([member_path],NCHAR(9),N''),NCHAR(10),N''),NCHAR(13),N''),N' ',N''))>0),
  CONSTRAINT [CK_meta_source_member_month] CHECK (TRY_CONVERT(date,[zip_month_label]+'01',112) IS NOT NULL AND DATALENGTH([zip_month_label])=6)
);

IF OBJECT_ID(N'meta.load_run',N'U') IS NULL
CREATE TABLE [meta].[load_run] (
  [run_id] uniqueidentifier NOT NULL,
  [data_scope] nvarchar(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [input_set_sha256] char(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [model_version] varchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [metric_rule_version] varchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [processing_policy_version] varchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [code_revision] nvarchar(128) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [status] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [is_current] bit NOT NULL,
  [started_at_utc] datetime2(7) NOT NULL,
  [finished_at_utc] datetime2(7) NULL,
  CONSTRAINT [PK_meta_load_run] PRIMARY KEY CLUSTERED ([run_id]),
  CONSTRAINT [CK_meta_load_run_input_set_sha256] CHECK (DATALENGTH([input_set_sha256])=64 AND [input_set_sha256] NOT LIKE '%[^0-9a-f]%'),
  CONSTRAINT [CK_meta_load_run_scope] CHECK (CONVERT(varbinary(128),[data_scope])=CONVERT(varbinary(400),N'JC_official_snapshot')),
  CONSTRAINT [CK_meta_load_run_status] CHECK ([status] IN ('CREATED','RUNNING','VALIDATED','PUBLISHED','FAILED') AND DATALENGTH([status])=LEN([status])),
  CONSTRAINT [CK_meta_load_run_current] CHECK ([is_current]=0 OR [status]='PUBLISHED'),
  CONSTRAINT [CK_meta_load_run_finished] CHECK (([status] NOT IN ('VALIDATED','PUBLISHED','FAILED') OR [finished_at_utc] IS NOT NULL) AND ([finished_at_utc] IS NULL OR [finished_at_utc]>=[started_at_utc])),
  CONSTRAINT [CK_meta_load_run_versions] CHECK ([model_version]='1.0' AND DATALENGTH([model_version])=3 AND [metric_rule_version]='A-1.0' AND DATALENGTH([metric_rule_version])=5 AND [processing_policy_version]='B1-1.0' AND DATALENGTH([processing_policy_version])=6)
);

IF OBJECT_ID(N'meta.run_source',N'U') IS NULL
CREATE TABLE [meta].[run_source] (
  [run_id] uniqueidentifier NOT NULL,
  [source_member_id] bigint NOT NULL,
  [read_record_count] bigint NOT NULL,
  [read_status] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  CONSTRAINT [PK_meta_run_source] PRIMARY KEY CLUSTERED ([run_id],[source_member_id]),
  CONSTRAINT [CK_meta_run_source_read_record_count] CHECK ([read_record_count]>=0),
  CONSTRAINT [CK_meta_run_source_read_status] CHECK ([read_status] IN ('PENDING','COMPLETE','FAILED') AND DATALENGTH([read_status])=LEN([read_status]))
);

IF OBJECT_ID(N'ods.trip_raw',N'U') IS NULL
CREATE TABLE [ods].[trip_raw] (
  [source_row_id] bigint IDENTITY(1,1) NOT NULL,
  [source_member_id] bigint NOT NULL,
  [csv_record_number] bigint NOT NULL,
  [field_count] int NOT NULL,
  [raw_values] nvarchar(max) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [ride_id_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [rideable_type_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [started_at_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [ended_at_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [start_station_name_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [start_station_id_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [end_station_name_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [end_station_id_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [start_lat_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [start_lng_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [end_lat_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [end_lng_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  [member_casual_raw] nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
  CONSTRAINT [PK_ods_trip_raw] PRIMARY KEY CLUSTERED ([source_row_id]),
  CONSTRAINT [UQ_ods_trip_raw_1] UNIQUE NONCLUSTERED ([source_member_id],[csv_record_number]),
  CONSTRAINT [CK_ods_trip_raw_csv_record_number] CHECK ([csv_record_number]>0),
  CONSTRAINT [CK_ods_trip_raw_field_count] CHECK ([field_count]>=0),
  CONSTRAINT [CK_ods_trip_raw_raw_values] CHECK (ISJSON([raw_values])=1 AND LEFT(LTRIM([raw_values]),1)=N'['),
  CONSTRAINT [CK_ods_trip_raw_record_number] CHECK ([csv_record_number]>=2)
);

IF OBJECT_ID(N'meta.row_disposition',N'U') IS NULL
CREATE TABLE [meta].[row_disposition] (
  [run_id] uniqueidentifier NOT NULL,
  [source_row_id] bigint NOT NULL,
  [outcome] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [primary_reason] varchar(32) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [trip_key] bigint NULL,
  [representative_source_row_id] bigint NULL,
  [warning_codes] nvarchar(max) COLLATE Latin1_General_100_BIN2 NOT NULL,
  CONSTRAINT [PK_meta_row_disposition] PRIMARY KEY CLUSTERED ([run_id],[source_row_id]),
  CONSTRAINT [CK_meta_row_disposition_warning_codes] CHECK (ISJSON([warning_codes])=1 AND LEFT(LTRIM([warning_codes]),1)=N'['),
  CONSTRAINT [CK_meta_row_disposition_outcome] CHECK ([outcome] IN ('ACCEPTED','DUPLICATE_EXACT','REJECTED') AND DATALENGTH([outcome])=LEN([outcome])),
  CONSTRAINT [CK_meta_row_disposition_reason] CHECK ([primary_reason] IN ('NONE','MISSING_RIDE_ID','CONFLICTING_RIDE_ID','TIME_PARSE_ERROR','NONPOSITIVE_DURATION','DURATION_LT_60S','DURATION_GT_24H') AND DATALENGTH([primary_reason])=LEN([primary_reason])),
  CONSTRAINT [CK_meta_row_disposition_shape] CHECK (([outcome]='REJECTED' AND [primary_reason]<>'NONE' AND [trip_key] IS NULL AND [representative_source_row_id] IS NULL) OR ([outcome]='ACCEPTED' AND [primary_reason]='NONE' AND [trip_key] IS NOT NULL AND [representative_source_row_id] IS NOT NULL AND [representative_source_row_id]=[source_row_id]) OR ([outcome]='DUPLICATE_EXACT' AND [primary_reason]='NONE' AND [trip_key] IS NOT NULL AND [representative_source_row_id] IS NOT NULL AND [representative_source_row_id]<>[source_row_id]))
);

IF OBJECT_ID(N'meta.coverage',N'U') IS NULL
CREATE TABLE [meta].[coverage] (
  [coverage_id] bigint IDENTITY(1,1) NOT NULL,
  [run_id] uniqueidentifier NOT NULL,
  [time_role] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [coverage_start] datetime2(7) NOT NULL,
  [coverage_end_exclusive] datetime2(7) NOT NULL,
  [coverage_status] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [proof_ref] nvarchar(2048) COLLATE Latin1_General_100_BIN2 NULL,
  CONSTRAINT [PK_meta_coverage] PRIMARY KEY CLUSTERED ([coverage_id]),
  CONSTRAINT [UQ_meta_coverage_1] UNIQUE NONCLUSTERED ([run_id],[time_role],[coverage_start]),
  CONSTRAINT [CK_meta_coverage_role] CHECK ([time_role] IN ('departure','arrival') AND DATALENGTH([time_role])=LEN([time_role])),
  CONSTRAINT [CK_meta_coverage_state] CHECK ([coverage_status] IN ('complete','partial','unknown') AND DATALENGTH([coverage_status])=LEN([coverage_status])),
  CONSTRAINT [CK_meta_coverage_range] CHECK ([coverage_start]<[coverage_end_exclusive]),
  CONSTRAINT [CK_meta_coverage_precision] CHECK (DATEPART(NANOSECOND,[coverage_start])%1000=0 AND DATEPART(NANOSECOND,[coverage_end_exclusive])%1000=0),
  CONSTRAINT [CK_meta_coverage_proof] CHECK ([coverage_status]<>'complete' OR ([proof_ref] IS NOT NULL AND LEN(LTRIM(RTRIM([proof_ref])))>0))
);

IF OBJECT_ID(N'dim.date',N'U') IS NULL
CREATE TABLE [dim].[date] (
  [date_key] int NOT NULL,
  [calendar_date] date NOT NULL,
  [calendar_year] smallint NOT NULL,
  [calendar_quarter] tinyint NOT NULL,
  [calendar_month] tinyint NOT NULL,
  [year_month] char(7) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [day_of_month] tinyint NOT NULL,
  [iso_weekday] tinyint NOT NULL,
  [weekday_name] nvarchar(8) COLLATE Latin1_General_100_BIN2 NOT NULL,
  CONSTRAINT [PK_dim_date] PRIMARY KEY CLUSTERED ([date_key]),
  CONSTRAINT [UQ_dim_date_1] UNIQUE NONCLUSTERED ([calendar_date]),
  CONSTRAINT [CK_dim_date_calendar] CHECK ([date_key]=YEAR([calendar_date])*10000+MONTH([calendar_date])*100+DAY([calendar_date]) AND [calendar_year]=YEAR([calendar_date]) AND [calendar_quarter]=DATEPART(QUARTER,[calendar_date]) AND [calendar_month]=MONTH([calendar_date]) AND [year_month]=CONVERT(char(7),[calendar_date],126) AND [day_of_month]=DAY([calendar_date]) AND [iso_weekday]=((DATEDIFF(DAY,CONVERT(date,'19000101',112),[calendar_date])%7+7)%7)+1),
  CONSTRAINT [CK_dim_date_weekday_name] CHECK ([weekday_name]=CASE [iso_weekday] WHEN 1 THEN N'星期一' WHEN 2 THEN N'星期二' WHEN 3 THEN N'星期三' WHEN 4 THEN N'星期四' WHEN 5 THEN N'星期五' WHEN 6 THEN N'星期六' WHEN 7 THEN N'星期日' END)
);

IF OBJECT_ID(N'dim.hour',N'U') IS NULL
CREATE TABLE [dim].[hour] (
  [hour_key] tinyint NOT NULL,
  [hour_label] varchar(5) COLLATE Latin1_General_100_BIN2 NOT NULL,
  CONSTRAINT [PK_dim_hour] PRIMARY KEY CLUSTERED ([hour_key]),
  CONSTRAINT [CK_dim_hour_hour] CHECK ([hour_key]<=23 AND [hour_label]=RIGHT('0'+CONVERT(varchar(2),[hour_key]),2)+':00' AND DATALENGTH([hour_label])=5)
);

IF OBJECT_ID(N'dim.station',N'U') IS NULL
CREATE TABLE [dim].[station] (
  [run_id] uniqueidentifier NOT NULL,
  [station_key] bigint NOT NULL,
  [station_id] nvarchar(200) COLLATE Latin1_General_100_BIN2 NULL,
  [station_id_identity] AS CONVERT(varbinary(400),[station_id]) PERSISTED,
  [station_name] nvarchar(512) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [is_unknown] bit NOT NULL,
  [name_is_fallback] bit NOT NULL,
  [name_source_row_id] bigint NULL,
  [reference_lat] decimal(20,15) NULL,
  [reference_lng] decimal(20,15) NULL,
  [coordinate_source_row_id] bigint NULL,
  [coordinate_role] varchar(20) COLLATE Latin1_General_100_BIN2 NULL,
  CONSTRAINT [PK_dim_station] PRIMARY KEY CLUSTERED ([run_id],[station_key]),
  CONSTRAINT [UQ_dim_station_1] UNIQUE NONCLUSTERED ([run_id],[station_id_identity]),
  CONSTRAINT [CK_dim_station_unknown] CHECK (([station_key]=0 AND [is_unknown]=1 AND [station_id] IS NULL AND [station_name]=N'未知站点' AND [name_is_fallback]=1 AND [name_source_row_id] IS NULL AND [reference_lat] IS NULL AND [reference_lng] IS NULL AND [coordinate_source_row_id] IS NULL AND [coordinate_role] IS NULL) OR ([station_key]>0 AND [is_unknown]=0 AND [station_id] IS NOT NULL AND LEN(REPLACE(REPLACE(REPLACE(REPLACE([station_id],NCHAR(9),N''),NCHAR(10),N''),NCHAR(13),N''),N' ',N''))>0)),
  CONSTRAINT [CK_dim_station_name_source] CHECK (([name_is_fallback]=1 AND [name_source_row_id] IS NULL) OR ([name_is_fallback]=0 AND [name_source_row_id] IS NOT NULL)),
  CONSTRAINT [CK_dim_station_coordinates] CHECK (([reference_lat] IS NULL AND [reference_lng] IS NULL AND [coordinate_source_row_id] IS NULL AND [coordinate_role] IS NULL) OR ([reference_lat] IS NOT NULL AND [reference_lng] IS NOT NULL AND [reference_lat]>=-90 AND [reference_lat]<=90 AND [reference_lng]>=-180 AND [reference_lng]<=180 AND [coordinate_source_row_id] IS NOT NULL AND [coordinate_role] IS NOT NULL AND [coordinate_role] IN ('start','end') AND DATALENGTH([coordinate_role])=LEN([coordinate_role])))
);

IF OBJECT_ID(N'dim.bike_type',N'U') IS NULL
CREATE TABLE [dim].[bike_type] (
  [bike_type_key] int IDENTITY(1,1) NOT NULL,
  [bike_type_code] nvarchar(200) COLLATE Latin1_General_100_BIN2 NULL,
  [bike_type_identity] AS CONVERT(varbinary(400),[bike_type_code]) PERSISTED,
  [bike_type_label] nvarchar(256) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [is_unknown] bit NOT NULL,
  [is_recognized] bit NOT NULL,
  CONSTRAINT [PK_dim_bike_type] PRIMARY KEY CLUSTERED ([bike_type_key]),
  CONSTRAINT [UQ_dim_bike_type_1] UNIQUE NONCLUSTERED ([bike_type_identity]),
  CONSTRAINT [CK_dim_bike_type_unknown] CHECK (([bike_type_key]=0 AND [is_unknown]=1 AND [bike_type_code] IS NULL) OR ([bike_type_key]>0 AND [is_unknown]=0 AND [bike_type_code] IS NOT NULL AND LEN(REPLACE(REPLACE(REPLACE(REPLACE([bike_type_code],NCHAR(9),N''),NCHAR(10),N''),NCHAR(13),N''),N' ',N''))>0)),
  CONSTRAINT [CK_dim_bike_type_recognized] CHECK ([is_recognized]=CASE WHEN [bike_type_identity] IN (CONVERT(varbinary(400),N'classic_bike'),CONVERT(varbinary(400),N'electric_bike')) THEN 1 ELSE 0 END)
);

IF OBJECT_ID(N'dim.member_type',N'U') IS NULL
CREATE TABLE [dim].[member_type] (
  [member_type_key] int IDENTITY(1,1) NOT NULL,
  [member_type_code] nvarchar(200) COLLATE Latin1_General_100_BIN2 NULL,
  [member_type_identity] AS CONVERT(varbinary(400),[member_type_code]) PERSISTED,
  [member_type_label] nvarchar(256) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [is_unknown] bit NOT NULL,
  [is_recognized] bit NOT NULL,
  CONSTRAINT [PK_dim_member_type] PRIMARY KEY CLUSTERED ([member_type_key]),
  CONSTRAINT [UQ_dim_member_type_1] UNIQUE NONCLUSTERED ([member_type_identity]),
  CONSTRAINT [CK_dim_member_type_unknown] CHECK (([member_type_key]=0 AND [is_unknown]=1 AND [member_type_code] IS NULL) OR ([member_type_key]>0 AND [is_unknown]=0 AND [member_type_code] IS NOT NULL AND LEN(REPLACE(REPLACE(REPLACE(REPLACE([member_type_code],NCHAR(9),N''),NCHAR(10),N''),NCHAR(13),N''),N' ',N''))>0)),
  CONSTRAINT [CK_dim_member_type_recognized] CHECK ([is_recognized]=CASE WHEN [member_type_identity] IN (CONVERT(varbinary(400),N'member'),CONVERT(varbinary(400),N'casual')) THEN 1 ELSE 0 END)
);

IF OBJECT_ID(N'dwd.fact_trip',N'U') IS NULL
CREATE TABLE [dwd].[fact_trip] (
  [run_id] uniqueidentifier NOT NULL,
  [trip_key] bigint IDENTITY(1,1) NOT NULL,
  [ride_id] nvarchar(200) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [ride_id_identity] AS CONVERT(varbinary(400),[ride_id]) PERSISTED NOT NULL,
  [representative_source_row_id] bigint NOT NULL,
  [started_at] datetime2(7) NOT NULL,
  [ended_at] datetime2(7) NOT NULL,
  [duration_us] bigint NOT NULL,
  [trip_count] tinyint NOT NULL,
  [start_date_key] int NOT NULL,
  [start_hour_key] tinyint NOT NULL,
  [end_date_key] int NOT NULL,
  [end_hour_key] tinyint NOT NULL,
  [start_station_key] bigint NOT NULL,
  [end_station_key] bigint NOT NULL,
  [bike_type_key] int NOT NULL,
  [member_type_key] int NOT NULL,
  [start_lat] decimal(20,15) NULL,
  [start_lng] decimal(20,15) NULL,
  [end_lat] decimal(20,15) NULL,
  [end_lng] decimal(20,15) NULL,
  [start_coordinate_status] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  [end_coordinate_status] varchar(20) COLLATE Latin1_General_100_BIN2 NOT NULL,
  CONSTRAINT [PK_dwd_fact_trip] PRIMARY KEY CLUSTERED ([run_id],[trip_key]),
  CONSTRAINT [UQ_dwd_fact_trip_1] UNIQUE NONCLUSTERED ([run_id],[ride_id_identity]),
  CONSTRAINT [CK_dwd_fact_trip_duration_us] CHECK ([duration_us]>0),
  CONSTRAINT [CK_dwd_fact_trip_trip_count] CHECK ([trip_count]>0),
  CONSTRAINT [CK_dwd_fact_trip_ride_id] CHECK (LEN(REPLACE(REPLACE(REPLACE(REPLACE([ride_id],NCHAR(9),N''),NCHAR(10),N''),NCHAR(13),N''),N' ',N''))>0),
  CONSTRAINT [CK_dwd_fact_trip_duration] CHECK ([trip_count]=1 AND [duration_us]>=60000000 AND [duration_us]<=86400000000 AND [duration_us]=DATEDIFF_BIG(MICROSECOND,[started_at],[ended_at])),
  CONSTRAINT [CK_dwd_fact_trip_precision] CHECK (DATEPART(NANOSECOND,[started_at])%1000=0 AND DATEPART(NANOSECOND,[ended_at])%1000=0),
  CONSTRAINT [CK_dwd_fact_trip_time_roles] CHECK ([start_date_key]=YEAR([started_at])*10000+MONTH([started_at])*100+DAY([started_at]) AND [end_date_key]=YEAR([ended_at])*10000+MONTH([ended_at])*100+DAY([ended_at]) AND [start_hour_key]=DATEPART(HOUR,[started_at]) AND [end_hour_key]=DATEPART(HOUR,[ended_at])),
  CONSTRAINT [CK_dwd_fact_trip_start_coordinates] CHECK (([start_coordinate_status] IN ('valid','missing','nonnumeric','out_of_range') AND DATALENGTH([start_coordinate_status])=LEN([start_coordinate_status])) AND (([start_coordinate_status]='valid' AND [start_lat] IS NOT NULL AND [start_lng] IS NOT NULL AND [start_lat]>=-90 AND [start_lat]<=90 AND [start_lng]>=-180 AND [start_lng]<=180) OR ([start_coordinate_status]<>'valid' AND [start_lat] IS NULL AND [start_lng] IS NULL))),
  CONSTRAINT [CK_dwd_fact_trip_end_coordinates] CHECK (([end_coordinate_status] IN ('valid','missing','nonnumeric','out_of_range') AND DATALENGTH([end_coordinate_status])=LEN([end_coordinate_status])) AND (([end_coordinate_status]='valid' AND [end_lat] IS NOT NULL AND [end_lng] IS NOT NULL AND [end_lat]>=-90 AND [end_lat]<=90 AND [end_lng]>=-180 AND [end_lng]<=180) OR ([end_coordinate_status]<>'valid' AND [end_lat] IS NULL AND [end_lng] IS NULL)))
);

IF OBJECT_ID(N'dws.trip_hourly',N'U') IS NULL
CREATE TABLE [dws].[trip_hourly] (
  [run_id] uniqueidentifier NOT NULL,
  [start_date_key] int NOT NULL,
  [start_hour_key] tinyint NOT NULL,
  [bike_type_key] int NOT NULL,
  [member_type_key] int NOT NULL,
  [ride_count] bigint NOT NULL,
  [duration_us] decimal(38,0) NOT NULL,
  CONSTRAINT [PK_dws_trip_hourly] PRIMARY KEY CLUSTERED ([run_id],[start_date_key],[start_hour_key],[bike_type_key],[member_type_key]),
  CONSTRAINT [CK_dws_trip_hourly_ride_count] CHECK ([ride_count]>=0),
  CONSTRAINT [CK_dws_trip_hourly_duration_us] CHECK ([duration_us]>=0),
  CONSTRAINT [CK_dws_trip_hourly_duration_bounds] CHECK ([duration_us]>=CONVERT(decimal(20,0),[ride_count])*60000000 AND [duration_us]<=CONVERT(decimal(20,0),[ride_count])*86400000000)
);

IF OBJECT_ID(N'dws.station_hourly',N'U') IS NULL
CREATE TABLE [dws].[station_hourly] (
  [run_id] uniqueidentifier NOT NULL,
  [event_date_key] int NOT NULL,
  [event_hour_key] tinyint NOT NULL,
  [station_key] bigint NOT NULL,
  [bike_type_key] int NOT NULL,
  [departures] bigint NOT NULL,
  [arrivals] bigint NOT NULL,
  CONSTRAINT [PK_dws_station_hourly] PRIMARY KEY CLUSTERED ([run_id],[event_date_key],[event_hour_key],[station_key],[bike_type_key]),
  CONSTRAINT [CK_dws_station_hourly_departures] CHECK ([departures]>=0),
  CONSTRAINT [CK_dws_station_hourly_arrivals] CHECK ([arrivals]>=0)
);
