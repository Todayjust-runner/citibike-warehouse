# SQL Server 2019 物理字段字典 B2-1.1

来源：[physical-model.json](physical-model.json)。与逻辑 14 关系/132 字段一一对应；以下是实际 SQL 定义，列长与精度为受控装载上限，尚未由真实五包剖析证明。完整键/检查/索引和编译定义在清单与编号 SQL 中。

`计算/持久化` 列由 SQL Server 生成，C 不在 INSERT 中传入；IDENTITY 也通常由服务器分配。源码原文进入 ODS 的 nvarchar(max)，精炼字段不得截断。

## meta.source_member

PK：`source_member_id`；UQ：`zip_sha256,member_path_identity`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| source_member_id | bigint | N | IDENTITY(1,1) |
| zip_sha256 | char(64) | N | 调用方提供 |
| zip_url | nvarchar(2048) | N | 调用方提供 |
| zip_bytes | bigint | N | 调用方提供 |
| zip_month_label | char(6) | N | 调用方提供 |
| zip_csv_member_count | int | N | 调用方提供 |
| archive_inventory_verified | bit | N | 调用方提供 |
| member_path | nvarchar(512) | N | 调用方提供 |
| member_path_identity | varbinary(1024) | N | 计算/持久化：`CONVERT(varbinary(1024),[member_path])` |
| csv_sha256 | char(64) | N | 调用方提供 |
| csv_header | nvarchar(max) | N | 调用方提供 |
| csv_data_record_count | bigint | N | 调用方提供 |
| acquired_at_utc | datetime2(7) | N | 调用方提供 |

## meta.load_run

PK：`run_id`；UQ：无。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| data_scope | nvarchar(64) | N | 调用方提供 |
| input_set_sha256 | char(64) | N | 调用方提供 |
| model_version | varchar(32) | N | 调用方提供 |
| metric_rule_version | varchar(32) | N | 调用方提供 |
| processing_policy_version | varchar(32) | N | 调用方提供 |
| code_revision | nvarchar(128) | N | 调用方提供 |
| status | varchar(20) | N | 调用方提供 |
| is_current | bit | N | 调用方提供 |
| started_at_utc | datetime2(7) | N | 调用方提供 |
| finished_at_utc | datetime2(7) | Y | 调用方提供 |

## meta.run_source

PK：`run_id,source_member_id`；UQ：无。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| source_member_id | bigint | N | 调用方提供 |
| read_record_count | bigint | N | 调用方提供 |
| read_status | varchar(20) | N | 调用方提供 |

## ods.trip_raw

PK：`source_row_id`；UQ：`source_member_id,csv_record_number`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| source_row_id | bigint | N | IDENTITY(1,1) |
| source_member_id | bigint | N | 调用方提供 |
| csv_record_number | bigint | N | 调用方提供 |
| field_count | int | N | 调用方提供 |
| raw_values | nvarchar(max) | N | 调用方提供 |
| ride_id_raw | nvarchar(max) | Y | 调用方提供 |
| rideable_type_raw | nvarchar(max) | Y | 调用方提供 |
| started_at_raw | nvarchar(max) | Y | 调用方提供 |
| ended_at_raw | nvarchar(max) | Y | 调用方提供 |
| start_station_name_raw | nvarchar(max) | Y | 调用方提供 |
| start_station_id_raw | nvarchar(max) | Y | 调用方提供 |
| end_station_name_raw | nvarchar(max) | Y | 调用方提供 |
| end_station_id_raw | nvarchar(max) | Y | 调用方提供 |
| start_lat_raw | nvarchar(max) | Y | 调用方提供 |
| start_lng_raw | nvarchar(max) | Y | 调用方提供 |
| end_lat_raw | nvarchar(max) | Y | 调用方提供 |
| end_lng_raw | nvarchar(max) | Y | 调用方提供 |
| member_casual_raw | nvarchar(max) | Y | 调用方提供 |

## meta.row_disposition

PK：`run_id,source_row_id`；UQ：无。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| source_row_id | bigint | N | 调用方提供 |
| outcome | varchar(20) | N | 调用方提供 |
| primary_reason | varchar(32) | N | 调用方提供 |
| trip_key | bigint | Y | 调用方提供 |
| representative_source_row_id | bigint | Y | 调用方提供 |
| warning_codes | nvarchar(max) | N | 调用方提供 |

## meta.coverage

PK：`coverage_id`；UQ：`run_id,time_role,coverage_start`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| coverage_id | bigint | N | IDENTITY(1,1) |
| run_id | uniqueidentifier | N | 调用方提供 |
| time_role | varchar(20) | N | 调用方提供 |
| coverage_start | datetime2(7) | N | 调用方提供 |
| coverage_end_exclusive | datetime2(7) | N | 调用方提供 |
| coverage_status | varchar(20) | N | 调用方提供 |
| proof_ref | nvarchar(2048) | Y | 调用方提供 |

## dim.date

PK：`date_key`；UQ：`calendar_date`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| date_key | int | N | 调用方提供 |
| calendar_date | date | N | 调用方提供 |
| calendar_year | smallint | N | 调用方提供 |
| calendar_quarter | tinyint | N | 调用方提供 |
| calendar_month | tinyint | N | 调用方提供 |
| year_month | char(7) | N | 调用方提供 |
| day_of_month | tinyint | N | 调用方提供 |
| iso_weekday | tinyint | N | 调用方提供 |
| weekday_name | nvarchar(8) | N | 调用方提供 |

## dim.hour

PK：`hour_key`；UQ：无。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| hour_key | tinyint | N | 调用方提供 |
| hour_label | varchar(5) | N | 调用方提供 |

## dim.station

PK：`run_id,station_key`；UQ：`run_id,station_id_identity`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| station_key | bigint | N | 调用方提供 |
| station_id | nvarchar(200) | Y | 调用方提供 |
| station_id_identity | varbinary(400) | Y | 计算/持久化：`CONVERT(varbinary(400),[station_id])` |
| station_name | nvarchar(512) | N | 调用方提供 |
| is_unknown | bit | N | 调用方提供 |
| name_is_fallback | bit | N | 调用方提供 |
| name_source_row_id | bigint | Y | 调用方提供 |
| reference_lat | decimal(20,15) | Y | 调用方提供 |
| reference_lng | decimal(20,15) | Y | 调用方提供 |
| coordinate_source_row_id | bigint | Y | 调用方提供 |
| coordinate_role | varchar(20) | Y | 调用方提供 |

## dim.bike_type

PK：`bike_type_key`；UQ：`bike_type_identity`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| bike_type_key | int | N | IDENTITY(1,1) |
| bike_type_code | nvarchar(200) | Y | 调用方提供 |
| bike_type_identity | varbinary(400) | Y | 计算/持久化：`CONVERT(varbinary(400),[bike_type_code])` |
| bike_type_label | nvarchar(256) | N | 调用方提供 |
| is_unknown | bit | N | 调用方提供 |
| is_recognized | bit | N | 调用方提供 |

## dim.member_type

PK：`member_type_key`；UQ：`member_type_identity`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| member_type_key | int | N | IDENTITY(1,1) |
| member_type_code | nvarchar(200) | Y | 调用方提供 |
| member_type_identity | varbinary(400) | Y | 计算/持久化：`CONVERT(varbinary(400),[member_type_code])` |
| member_type_label | nvarchar(256) | N | 调用方提供 |
| is_unknown | bit | N | 调用方提供 |
| is_recognized | bit | N | 调用方提供 |

## dwd.fact_trip

PK：`run_id,trip_key`；UQ：`run_id,ride_id_identity`。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| trip_key | bigint | N | IDENTITY(1,1) |
| ride_id | nvarchar(200) | N | 调用方提供 |
| ride_id_identity | varbinary(400) | N | 计算/持久化：`CONVERT(varbinary(400),[ride_id])` |
| representative_source_row_id | bigint | N | 调用方提供 |
| started_at | datetime2(7) | N | 调用方提供 |
| ended_at | datetime2(7) | N | 调用方提供 |
| duration_us | bigint | N | 调用方提供 |
| trip_count | tinyint | N | 调用方提供 |
| start_date_key | int | N | 调用方提供 |
| start_hour_key | tinyint | N | 调用方提供 |
| end_date_key | int | N | 调用方提供 |
| end_hour_key | tinyint | N | 调用方提供 |
| start_station_key | bigint | N | 调用方提供 |
| end_station_key | bigint | N | 调用方提供 |
| bike_type_key | int | N | 调用方提供 |
| member_type_key | int | N | 调用方提供 |
| start_lat | decimal(20,15) | Y | 调用方提供 |
| start_lng | decimal(20,15) | Y | 调用方提供 |
| end_lat | decimal(20,15) | Y | 调用方提供 |
| end_lng | decimal(20,15) | Y | 调用方提供 |
| start_coordinate_status | varchar(20) | N | 调用方提供 |
| end_coordinate_status | varchar(20) | N | 调用方提供 |

## dws.trip_hourly

PK：`run_id,start_date_key,start_hour_key,bike_type_key,member_type_key`；UQ：无。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| start_date_key | int | N | 调用方提供 |
| start_hour_key | tinyint | N | 调用方提供 |
| bike_type_key | int | N | 调用方提供 |
| member_type_key | int | N | 调用方提供 |
| ride_count | bigint | N | 调用方提供 |
| duration_us | decimal(38,0) | N | 调用方提供 |

## dws.station_hourly

PK：`run_id,event_date_key,event_hour_key,station_key,bike_type_key`；UQ：无。

| 字段 | SQL 类型 | 可空 | 生成方式 |
|---|---|---|---|
| run_id | uniqueidentifier | N | 调用方提供 |
| event_date_key | int | N | 调用方提供 |
| event_hour_key | tinyint | N | 调用方提供 |
| station_key | bigint | N | 调用方提供 |
| bike_type_key | int | N | 调用方提供 |
| departures | bigint | N | 调用方提供 |
| arrivals | bigint | N | 调用方提供 |

## 物理索引

| 表 | 索引 | 键 | 包含列 | 唯一 / 过滤 |
|---|---|---|---|---|
| meta.source_member | PK_meta_source_member | source_member_id | 无 | 是 / 无 |
| meta.source_member | UQ_meta_source_member_1 | zip_sha256,member_path_identity | 无 | 是 / 无 |
| meta.load_run | PK_meta_load_run | run_id | 无 | 是 / 无 |
| meta.load_run | UX_meta_load_run_current | data_scope | 无 | 是 / ([is_current]=(1)) |
| meta.run_source | PK_meta_run_source | run_id,source_member_id | 无 | 是 / 无 |
| ods.trip_raw | PK_ods_trip_raw | source_row_id | 无 | 是 / 无 |
| ods.trip_raw | UQ_ods_trip_raw_1 | source_member_id,csv_record_number | 无 | 是 / 无 |
| meta.row_disposition | PK_meta_row_disposition | run_id,source_row_id | 无 | 是 / 无 |
| meta.row_disposition | IX_disposition_trip | run_id,trip_key | outcome,representative_source_row_id | 否 / 无 |
| meta.coverage | PK_meta_coverage | coverage_id | 无 | 是 / 无 |
| meta.coverage | UQ_meta_coverage_1 | run_id,time_role,coverage_start | 无 | 是 / 无 |
| dim.date | PK_dim_date | date_key | 无 | 是 / 无 |
| dim.date | UQ_dim_date_1 | calendar_date | 无 | 是 / 无 |
| dim.hour | PK_dim_hour | hour_key | 无 | 是 / 无 |
| dim.station | PK_dim_station | run_id,station_key | 无 | 是 / 无 |
| dim.station | UQ_dim_station_1 | run_id,station_id_identity | 无 | 是 / 无 |
| dim.bike_type | PK_dim_bike_type | bike_type_key | 无 | 是 / 无 |
| dim.bike_type | UQ_dim_bike_type_1 | bike_type_identity | 无 | 是 / 无 |
| dim.member_type | PK_dim_member_type | member_type_key | 无 | 是 / 无 |
| dim.member_type | UQ_dim_member_type_1 | member_type_identity | 无 | 是 / 无 |
| dwd.fact_trip | PK_dwd_fact_trip | run_id,trip_key | 无 | 是 / 无 |
| dwd.fact_trip | UQ_dwd_fact_trip_1 | run_id,ride_id_identity | 无 | 是 / 无 |
| dwd.fact_trip | IX_fact_departure | run_id,started_at,bike_type_key | duration_us,trip_count,member_type_key,start_station_key | 否 / 无 |
| dwd.fact_trip | IX_fact_arrival | run_id,ended_at,bike_type_key | trip_count,end_station_key | 否 / 无 |
| dws.trip_hourly | PK_dws_trip_hourly | run_id,start_date_key,start_hour_key,bike_type_key,member_type_key | 无 | 是 / 无 |
| dws.station_hourly | PK_dws_station_hourly | run_id,event_date_key,event_hour_key,station_key,bike_type_key | 无 | 是 / 无 |
