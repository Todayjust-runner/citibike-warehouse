# 逻辑字段字典 v1.0

本文件由 [logical-model.json](logical-model.json) 中的逻辑定义整理。当前不指定 SQL 列长、定点精度、索引或部署脚本；它们属于对话三。`N` 为业务上不允许 NULL，`Y` 为允许；空字符串与 NULL 不混用。

`binary_identity` 为原值 UTF-16LE 无 BOM 的完整字节。SQL Server 普通字符串等号可能忽略尾空格；物理阶段必须实现此精确身份，不能只靠列的默认排序规则。所有唯一性均按本模型语义而非数据库默认比较。

`source_timestamp` 为无偏移源时间，至少保留毫秒；整微秒不能精确表达的输入先停止发布并提交版本决定，不静默截断、不冒充业务排除。`utc_instant` 仅用于执行审计。`exact_decimal` 须以收到数据的精度核定物理类型，不从本字典推断已完成剖析。

全输入完整性、去向完备和守恒是 VALIDATED/PUBLISHED 的发布门槛；RUNNING/FAILED 可能只保留部分处理记录，不得据此宣称对账通过。身份比较依据及截断风险见 [Microsoft 字符串比较](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-comparison-assignment?view=sql-server-ver15) 与 [binary/varbinary 转换](https://learn.microsoft.com/en-us/sql/t-sql/data-types/binary-and-varbinary-transact-sql?view=sql-server-ver15)；B2 必须无损实现，不默认省略转换长度。

逻辑类型中的 list/set 可在物理阶段用受校验 JSON 或关系结构实现，不改变粒度；raw_values 保留有序单元格，warning_codes 仅是非互斥附属问题。

共 14 个逻辑关系，其中只有 dwd.fact_trip 是业务事实；DWS 是该事实的派生汇总，meta/ods 为治理与原始记录。

## meta.source_member

粒度：一个原始 ZIP 哈希与其一个 CSV 成员路径；空 CSV 也登记。

主键：`source_member_id`。唯一键：`zip_sha256, member_path_identity`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| source_member_id | integer_key | N | 成员代理键 |
| zip_sha256 | sha256_hex | N | 完整 ZIP 字节 SHA-256；不是 ETag |
| zip_url | text | N | 官方取得地址 |
| zip_bytes | nonnegative_integer | N | 完整压缩包字节数 |
| zip_month_label | year_month | N | 文件名月份标签，不是事件日期 |
| zip_csv_member_count | positive_integer | N | ZIP 内全部 CSV 成员数，不只首个 |
| archive_inventory_verified | boolean | N | 全部成员清点并核验完成标志 |
| member_path | exact_string | N | ZIP 中原始 CSV 成员路径 |
| member_path_identity | binary_identity | N | member_path 的 UTF-16LE 无 BOM 字节，用于精确等值 |
| csv_sha256 | sha256_hex | N | 解压后完整 CSV 字节 SHA-256 |
| csv_header | ordered_string_list | N | 原始 13 列表头与次序 |
| csv_data_record_count | nonnegative_integer | N | CSV 数据记录数，不含表头 |
| acquired_at_utc | utc_instant | N | 取得时间；审计时间与业务时间分开 |

外键：无。

## meta.load_run

粒度：一次固定输入集合与规则/代码版本的全量构建尝试。

主键：`run_id`。唯一键：无额外声明。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 运行标识；不得跨运行聚合事实 |
| data_scope | exact_string | N | 固定 JC_official_snapshot，表示来源分区而非完整纽约 |
| input_set_sha256 | sha256_hex | N | 排序后的全成员身份/哈希清单指纹 |
| model_version | version_string | N | 本逻辑交接为 1.0 |
| metric_rule_version | version_string | N | A-1.0；业务定义变更需新版本 |
| processing_policy_version | version_string | N | B1-1.0；字节比较/排除顺序等技术规则 |
| code_revision | text | N | C 实际执行代码提交号，不得用设计提交冒充 ETL 代码 |
| status | enum | N | CREATED/RUNNING/VALIDATED/PUBLISHED/FAILED |
| is_current | boolean | N | 同一 data_scope 至多一行 true，且 status=PUBLISHED |
| started_at_utc | utc_instant | N | 执行审计开始 |
| finished_at_utc | utc_instant | Y | 执行完成，运行中可空 |

外键：无。

## meta.run_source

粒度：一个运行选中的一个源成员，包括无数据行成员。

主键：`run_id, source_member_id`。唯一键：无额外声明。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 所属构建尝试 |
| source_member_id | integer_key | N | 选入的完整 CSV 成员 |
| read_record_count | nonnegative_integer | N | 本次实际读取的数据记录数 |
| read_status | enum | N | PENDING/COMPLETE/FAILED；非 COMPLETE 禁止发布 |

外键：`run_id` → `meta.load_run(run_id)`；`source_member_id` → `meta.source_member(source_member_id)`。

## ods.trip_raw

粒度：一个 source_member_id 内的一条 CSV 数据记录，不去重、不筛时间。

主键：`source_row_id`。唯一键：`source_member_id, csv_record_number`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| source_row_id | integer_key | N | 原始行代理键 |
| source_member_id | integer_key | N | 原文件及成员身份 |
| csv_record_number | positive_integer | N | 表头为记录 1，首条数据为 2；不是物理文本行号 |
| field_count | nonnegative_integer | N | 实际解析单元格数量，要求 13 才可正常处理 |
| raw_values | ordered_string_list | N | 完整已解析单元格数组，保持空字符串和原文 |
| ride_id_raw | source_text | Y | 原始 ride_id 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| rideable_type_raw | source_text | Y | 原始 rideable_type 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| started_at_raw | source_text | Y | 原始 started_at 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| ended_at_raw | source_text | Y | 原始 ended_at 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| start_station_name_raw | source_text | Y | 原始 start_station_name 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| start_station_id_raw | source_text | Y | 原始 start_station_id 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| end_station_name_raw | source_text | Y | 原始 end_station_name 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| end_station_id_raw | source_text | Y | 原始 end_station_id 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| start_lat_raw | source_text | Y | 原始 start_lat 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| start_lng_raw | source_text | Y | 原始 start_lng 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| end_lat_raw | source_text | Y | 原始 end_lat 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| end_lng_raw | source_text | Y | 原始 end_lng 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |
| member_casual_raw | source_text | Y | 原始 member_casual 单元格；空字段保留空字符串，NULL 仅表示无法安全解析该列 |

外键：`source_member_id` → `meta.source_member(source_member_id)`。

## meta.row_disposition

粒度：一个运行对一个源行的唯一主去向；同时充当源行到事实血缘。

主键：`run_id, source_row_id`。唯一键：无额外声明。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 处理此源行的运行 |
| source_row_id | integer_key | N | 原始行，运行输入内每行恰好一条 |
| outcome | enum | N | ACCEPTED/DUPLICATE_EXACT/REJECTED |
| primary_reason | enum | N | NONE/MISSING_RIDE_ID/CONFLICTING_RIDE_ID/TIME_PARSE_ERROR/NONPOSITIVE_DURATION/DURATION_LT_60S/DURATION_GT_24H |
| trip_key | integer_key | Y | ACCEPTED 或 DUPLICATE_EXACT 指向同运行事实，REJECTED 必为空 |
| representative_source_row_id | integer_key | Y | 保留代表源行；ACCEPTED 指自己、DUPLICATE_EXACT 指代表、REJECTED 为空 |
| warning_codes | string_set | N | 非互斥附属问题，如缺坐标/站点、未知标签；空集合允许 |

外键：`run_id` → `meta.load_run(run_id)`；`source_row_id` → `ods.trip_raw(source_row_id)`；`representative_source_row_id` → `ods.trip_raw(source_row_id)`；`run_id,trip_key` → `dwd.fact_trip(run_id,trip_key)`。

## meta.coverage

粒度：一个运行、一个时间角色的一段有证据的覆盖声明；同角色区间不重叠。

主键：`coverage_id`。唯一键：`run_id, time_role, coverage_start`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| coverage_id | integer_key | N | 覆盖记录代理键 |
| run_id | opaque_id | N | 适用的运行输入 |
| time_role | enum | N | departure 或 arrival |
| coverage_start | source_timestamp | N | 左闭起点，源无偏移时间 |
| coverage_end_exclusive | source_timestamp | N | 右开终点，大于起点 |
| coverage_status | enum | N | complete/partial/unknown；只相对约定 JC 发布快照 |
| proof_ref | text | Y | 检查代码/输入清单/证据路径；complete 必须非空 |

外键：`run_id` → `meta.load_run(run_id)`。

## dim.date

粒度：一个源日历日期，覆盖所有入选有效事实两端日期。

主键：`date_key`。唯一键：`calendar_date`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| date_key | integer_key | N | YYYYMMDD；有效事实无未知日期 |
| calendar_date | date | N | 真实公历日期 |
| calendar_year | integer | N | 公历年 |
| calendar_quarter | integer | N | 1-4 |
| calendar_month | integer | N | 1-12 |
| year_month | year_month | N | YYYY-MM |
| day_of_month | integer | N | 1-31 |
| iso_weekday | integer | N | 1=周一，7=周日，计算不得依赖默认 DATEFIRST |
| weekday_name | text | N | 固定中文星期名称，不代表当地工作日 |

外键：无。

## dim.hour

粒度：一个日内小时；日期与小时组合才标识事件小时桶。

主键：`hour_key`。唯一键：无额外声明。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| hour_key | integer_key | N | 0-23 |
| hour_label | text | N | 00:00 等展示文本 |

外键：无。

## dim.station

粒度：一个运行内的一个观察到的非空站点 ID，另有 key=0 未知成员。

主键：`run_id, station_key`。唯一键：`run_id, station_id_identity`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 运行内展示快照；不是业务历史版本 |
| station_key | integer_key | N | 0 表示专用未知，真实站点使用正数 |
| station_id | exact_string | Y | 原站点 ID，未知成员为空 |
| station_id_identity | binary_identity | Y | 非空 station_id 的 UTF-16LE 无 BOM 精确身份 |
| station_name | text | N | 确定性选出的非空源名；无名时回退 ID，未知显示未知站点 |
| is_unknown | boolean | N | 仅 station_key=0 为 true |
| name_is_fallback | boolean | N | 站名是否回退显示 |
| name_source_row_id | integer_key | Y | 选名所用源行；无源名时空 |
| reference_lat | exact_decimal | Y | 最近有效源坐标观察纬度，不是官方现状坐标 |
| reference_lng | exact_decimal | Y | 与纬度同一次观察；必须成对存在 |
| coordinate_source_row_id | integer_key | Y | 参考坐标来源行 |
| coordinate_role | enum | Y | start/end；无参考坐标时空 |

外键：`run_id` → `meta.load_run(run_id)`；`name_source_row_id` → `ods.trip_raw(source_row_id)`；`coordinate_source_row_id` → `ods.trip_raw(source_row_id)`。

## dim.bike_type

粒度：一个非空原始标签，另有 key=0 缺失成员。

主键：`bike_type_key`。唯一键：`bike_type_identity`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| bike_type_key | integer_key | N | 0 是缺失标签，其余代理键；不借键值推断已知类别 |
| bike_type_code | exact_string | Y | 原始标签；未知缺失成员为空 |
| bike_type_identity | binary_identity | Y | 非空原标签的 UTF-16LE 无 BOM 字节 |
| bike_type_label | text | N | 展示名；未识别标签仍独立保留 |
| is_unknown | boolean | N | 仅缺失成员为 true |
| is_recognized | boolean | N | 车型仅 classic_bike/electric_bike；会员类型仅 member/casual 为 true |

外键：无。

## dim.member_type

粒度：一个非空原始标签，另有 key=0 缺失成员。

主键：`member_type_key`。唯一键：`member_type_identity`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| member_type_key | integer_key | N | 0 是缺失标签，其余代理键；不借键值推断已知类别 |
| member_type_code | exact_string | Y | 原始标签；未知缺失成员为空 |
| member_type_identity | binary_identity | Y | 非空原标签的 UTF-16LE 无 BOM 字节 |
| member_type_label | text | N | 展示名；未识别标签仍独立保留 |
| is_unknown | boolean | N | 仅缺失成员为 true |
| is_recognized | boolean | N | 车型仅 classic_bike/electric_bike；会员类型仅 member/casual 为 true |

外键：无。

## dwd.fact_trip

粒度：一个运行内，一次通过规则的唯一 ride_id 的完整骑行，不裁为 Q3 出发。

主键：`run_id, trip_key`。唯一键：`run_id, ride_id_identity`。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 查询必须锁定一个已发布运行 |
| trip_key | integer_key | N | 运行内骑行代理键，不作为用户身份 |
| ride_id | exact_string | N | 非空源骑行 ID，保留大小写及非空值边缘字符 |
| ride_id_identity | binary_identity | N | ride_id 的 UTF-16LE 无 BOM 字节，精确唯一比较 |
| representative_source_row_id | integer_key | N | 确定性选出的接受源行 |
| started_at | source_timestamp | N | 源出发时间，保留实际精度至少毫秒 |
| ended_at | source_timestamp | N | 源归还时间，保留实际精度至少毫秒 |
| duration_us | positive_integer | N | 精确整数微秒，60000000 至 86400000000 含两端 |
| trip_count | positive_integer | N | 恒为 1，不能存聚合骑行数 |
| start_date_key | integer_key | N | started_at 对应日期 |
| start_hour_key | integer_key | N | started_at 小时 0-23 |
| end_date_key | integer_key | N | ended_at 对应日期 |
| end_hour_key | integer_key | N | ended_at 小时 0-23 |
| start_station_key | integer_key | N | 起点站角色，可为 0 |
| end_station_key | integer_key | N | 终点站角色，可为 0 |
| bike_type_key | integer_key | N | 车型标签，包括缺失或未识别值 |
| member_type_key | integer_key | N | 骑行类型标签，不是用户键 |
| start_lat | exact_decimal | Y | 仅保留有效坐标对的解析纬度 |
| start_lng | exact_decimal | Y | 仅保留有效坐标对的解析经度 |
| end_lat | exact_decimal | Y | 仅保留有效坐标对的解析纬度 |
| end_lng | exact_decimal | Y | 仅保留有效坐标对的解析经度 |
| start_coordinate_status | enum | N | valid/missing/nonnumeric/out_of_range |
| end_coordinate_status | enum | N | valid/missing/nonnumeric/out_of_range |

外键：`run_id` → `meta.load_run(run_id)`；`representative_source_row_id` → `ods.trip_raw(source_row_id)`；`start_date_key` → `dim.date(date_key)`；`start_hour_key` → `dim.hour(hour_key)`；`run_id,start_station_key` → `dim.station(run_id,station_key)`；`end_date_key` → `dim.date(date_key)`；`end_hour_key` → `dim.hour(hour_key)`；`run_id,end_station_key` → `dim.station(run_id,station_key)`；`bike_type_key` → `dim.bike_type(bike_type_key)`；`member_type_key` → `dim.member_type(member_type_key)`。

## dws.trip_hourly

粒度：运行 × 出发日期 × 小时 × 车型 × 会员骑行类型。

主键：`run_id, start_date_key, start_hour_key, bike_type_key, member_type_key`。唯一键：无额外声明。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 单次运行 |
| start_date_key | integer_key | N | 出发日期 |
| start_hour_key | integer_key | N | 出发小时 |
| bike_type_key | integer_key | N | 车型 |
| member_type_key | integer_key | N | 会员骑行类型 |
| ride_count | nonnegative_integer | N | 互斥骑行数求和 |
| duration_us | nonnegative_integer | N | 总微秒，不存预先舍入的平均值 |

外键：`run_id` → `meta.load_run(run_id)`；`start_date_key` → `dim.date(date_key)`；`start_hour_key` → `dim.hour(hour_key)`；`bike_type_key` → `dim.bike_type(bike_type_key)`；`member_type_key` → `dim.member_type(member_type_key)`。

## dws.station_hourly

粒度：运行 × 事件日期 × 小时 × 站点 × 车型；两事件角色聚合后合并。

主键：`run_id, event_date_key, event_hour_key, station_key, bike_type_key`。唯一键：无额外声明。

| 字段 | 逻辑类型 | 可空 | 含义 |
|---|---|---|---|
| run_id | opaque_id | N | 单次运行 |
| event_date_key | integer_key | N | 两侧各自事件日期 |
| event_hour_key | integer_key | N | 两侧各自事件小时 |
| station_key | integer_key | N | 事件站点，可为 0 |
| bike_type_key | integer_key | N | 两侧使用相同车型维度 |
| departures | nonnegative_integer | N | 按 started_at/start_station_key 的次数 |
| arrivals | nonnegative_integer | N | 按 ended_at/end_station_key 的次数 |

外键：`run_id` → `meta.load_run(run_id)`；`event_date_key` → `dim.date(date_key)`；`event_hour_key` → `dim.hour(hour_key)`；`bike_type_key` → `dim.bike_type(bike_type_key)`；`run_id,station_key` → `dim.station(run_id,station_key)`。

## 关系之外必须验证的规则

- 每次运行输入集合须等于 run_source 中所有成员；其读取量必须与完整清单对齐，原始行不能只按时间筛选。
- ACCEPTED/DUPLICATE_EXACT 的 trip_key 和代表行必须非空，REJECTED 两者为空；每事实恰好一个 ACCEPTED 代表。
- fact 的代表行、station 属性来源行必须来自同运行输入；station 属性仅由该运行 ACCEPTED 事实两端观察确定。
- 非空标签的 is_recognized 只按已确认枚举判断；is_unknown 只标缺失，不能把新标签偷偷并入 member/casual。
- 同一 data_scope 至多一个 is_current=true 的 PUBLISHED 运行；is_current 切换需事务化，失败运行不得切换。
- complete 覆盖要求非空 proof_ref；同角色覆盖区间不重叠，完整覆盖须含整个请求窗口；从有事件不能推断没有缺口。
- dim.station 的未知成员允许空身份；其他站点必须非空身份。物理唯一约束需显式实现此条件。
- 坐标有效对与状态一致，reference_lat/lng 同时有值或同时为空；不据坐标删有效事实。
