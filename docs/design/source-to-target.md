# 源到目标、处理去向与覆盖映射 v1.0

依据 A v1.0 p2-3、5-7。当前只完成映射设计，真实附件和脚本未收到；所有处理策略是 B 的可实现约定，不能据此声称复现 A。

## 13 列逐字段映射

每个字段先无损进入 `ods.trip_raw.<字段名>_raw` 和有序 `raw_values`。CSV 空字段保留空字符串；只有无法安全解析该列时才可 NULL，该运行禁止发布。下表描述接受组代表行如何进入模型。

| 源字段 | 目标 / 转换 | 无效、缺失与血缘 |
|---|---|---|
| ride_id | fact_trip.ride_id；UTF-16LE 无 BOM → ride_id_identity | 空/仅 ASCII 空白主原因 MISSING_RIDE_ID；非空不 trim/casefold |
| rideable_type | dim.bike_type 的原 code/identity → fact.bike_type_key | 缺失 key=0；非空未识别标签单独保留，非排除 |
| started_at | fact.started_at → start_date_key/start_hour_key；参与 duration_us | 解析失败 REJECTED；无偏移，不转 UTC/北京时间；实际精度待核验 |
| ended_at | fact.ended_at → end_date_key/end_hour_key；参与 duration_us | 独立归还事件；不因超出主窗口删除事实 |
| start_station_name | dim.station 候选站名及 name_source_row_id | 仅描述，不做关联键；名字变化不生成业务 SCD2 |
| start_station_id | 原字符串/精确身份 → 当运行 dim.station → start_station_key | 缺失 key=0；不删除事实；有名无 ID 也仍为未知站点 |
| end_station_name | dim.station 的终点观察候选站名 | 与起点观察按共同确定性规则选择 |
| end_station_id | 原字符串/精确身份 → dim.station → end_station_key | 缺失 key=0；未知参与归还对账 |
| start_lat | 合法坐标对 → fact.start_lat，候选 station.reference_lat | 缺失/非数值/越界仅标质量状态，事实保留 |
| start_lng | 合法坐标对 → fact.start_lng，候选 station.reference_lng | 必须与纬度同次观察成对；不能分别拼接 |
| end_lat | 合法坐标对 → fact.end_lat，候选 station.reference_lat | 同起点规则；参考点选择记录角色 end |
| end_lng | 合法坐标对 → fact.end_lng，候选 station.reference_lng | 不由坐标计算实际路线距离 |
| member_casual | dim.member_type 原 code/identity → fact.member_type_key | 缺失 key=0；其他非空标签独立保留，不入 member/casual 分母 |

衍生字段 `duration_us = (ended_at-started_at)` 的精确整数微秒，`trip_count=1`。如果源时间不能被整数微秒无损表达，停止运行发布并记录属性问题，不静默舍入，也不新增一个业务排除原因。物理类型在 B2 结合源精度确认。

每侧坐标状态按对检查，优先级为任一值缺失→missing，否则任一不能解析→nonnumeric，否则越界→out_of_range，否则 valid。无效时该侧两个解析坐标都为 NULL；原文不变，附属 warning 可记录更多问题。

## 元数据与行定位

| 来源 / 计算 | 目标 | 要求 |
|---|---|---|
| 官方 URL、取得时间、ZIP 字节数与完整 SHA-256 | meta.source_member 的 zip_* / acquired_at_utc | ETag 不替代完整哈希 |
| ZIP 全 CSV 清单、成员路径与完整 CSV 哈希 | source_member、archive_inventory_verified | 所有成员均登记；禁止仅首成员 |
| CSV 表头与记录数 | csv_header / csv_data_record_count | 顺序与 13 列吻合；数据量排除表头 |
| 成员与 CSV 记录号 | ods 的唯一源行定位 | 表头记录 1、首数据记录 2；多行字段仍为一条 CSV 记录 |
| 排序后的全部成员清单 | load_run.input_set_sha256、run_source | 清单按 ZIP 哈希、成员路径 UTF-8 字节序排序；摘要输入为定长规则的 JSON 数组，含 ZIP 哈希、成员路径、CSV 哈希，不含取得时间 |
| 代码与模型/业务/处理版本 | load_run 版本字段 | 业务 A-1.0 与技术 B1-1.0 分开；设计版本不等于加工代码版本 |
| 每个输入源行的处理结果 | row_disposition | 同一 run 每行恰有一条，含 ACCEPTED、重复、排除及附属问题 |
| 全成员及时间覆盖核查证据 | coverage / proof_ref | 不以事实 min/max 证明完整性 |

清单指纹序列化固定 UTF-8、无 BOM、JSON 紧凑分隔、ensure_ascii=false、不做 Unicode 规范化；列表元素为三项字符串数组 `[zip_sha256, member_path, csv_sha256]`，哈希十六进制小写。两个不同 ZIP 包内相同 CSV 仍分别保留源行，由骑行规则处理重复，不因 CSV 哈希相同跳过原始记录。

## 唯一主去向与优先级

字段数不符、CSV 无法完整解析、压缩包不完整或精度不可表达属于运行错误：保存诊断、status=FAILED，不能把未能读到的行当“已业务排除”，也不能发布 complete 结果。以下仅适用于完整、13 列可解析的源行。

1. ride_id 缺失：每行 REJECTED / MISSING_RIDE_ID，不将全部缺 ID 行组成一个业务组。
2. 对非空精确 ride_id 分组；13 个原字段存在不同内容时，**整组** REJECTED / CONFLICTING_RIDE_ID。即使其中某些行内容相同或时间无效，也不选一条保留。
3. 同内容组解析时间；失败全组 REJECTED / TIME_PARSE_ERROR。
4. 精确时长 `<=0` 全组 NONPOSITIVE_DURATION；`0<duration_us<60000000` 全组 DURATION_LT_60S；`>86400000000` 全组 DURATION_GT_24H。
5. 有效组按 `(zip_sha256 小写 ASCII, member_path UTF-8 字节序, csv_record_number 数值)` 升序选一条 ACCEPTED / NONE，产生唯一事实；其余 DUPLICATE_EXACT / NONE，指向该事实和代表行。

60 秒和 24 小时均包含。重复无效组所有行计 REJECTED，不把其中一个伪标 ACCEPTED。warning_codes 可同时记录缺站点、坐标不合法或未知标签等，不能用于替代主原因或重复累计排除数。

`N_raw(run)=N_accepted+N_duplicate_exact+N_rejected`；`N_fact(run)=N_accepted`。守恒在全部输入上计算，不在 Q3 出发子集上计算。每个接受事实有一个 ACCEPTED 代表；接受/重复的 trip_key 必须存在且同 run，排除的 trip_key 必须 NULL。

## 跨月结束文件与覆盖证明

A 声称五包按 ended_at 月覆盖，本次尚未全量复核。C 必须扫描**所有成员、所有行**确认月份语义、边界记录和输入完整性；若不成立，不得套用下面的充分条件，应重新设计覆盖证明并记录差异。

在“完整月包按结束月分区”被证实、且分析骑行最长 24 小时的前提下：

- 要证明归还窗口 `[L,U)`，至少需要结束时间覆盖 `[L,U)` 的全部约定发布记录；窗口前出发的骑行已包含在这些归还记录中，不额外筛 started_at。
- 要证明出发窗口 `[L,U)`，一个保守充分条件是结束记录完整覆盖 `[L,U+24小时)`；因为所有准入骑行的归还均落在该范围。默认 Q3 的出发完整性因此需要 10 月边界包。
- 6 月包按 A 要求保留作前边界核验；不能声称“读了 6 月”就证明跨月已正确处理。完整的结束月文件本身可以包含上月出发，真正判定依赖事件时间。
- 不能把观察到最早/最晚时间、文件名或某侧零行当完整覆盖。缺月包、未读成员、归档规则不明时 coverage=partial/unknown，不能补成真实零。

覆盖只相对于约定的官方 JC 快照及分析过滤，不保证现实世界所有骑行，更不包含官方已预处理移除的业务。C 记录两个角色的证据，D 显示对应范围与不足；M06 同时要求两个角色覆盖。
