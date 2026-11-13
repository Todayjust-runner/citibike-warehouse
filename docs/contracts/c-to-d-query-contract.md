# C → D 查询结果契约 v1.0

状态：B1 逻辑接口基线，待 C/D 接入确认；本页业务查询尚未实现为 HTTP、存储过程、视图或页面。`ads.*` 是命名结果，不要求本阶段建实体表。业务 A-1.0 / 处理 B1-1.0 / 模型 1.0。

B2 补充：物理库已有结构及元数据验证/发布过程，仍没有实现本页的业务查询结果。run_id 在 SQL 中为 UUID，传输仍按字符串；数据必须来自同一 PUBLISHED 运行，不能把 B2 合成测试输出接到页面。物理字典与发布约束见 B→C 契约。

> 源侧补充：新官方五包独立源核算的38项A数值已匹配，见[公开源证据](../sources/public-snapshot-validation.md)；本契约的五种业务查询/API仍未实现，不把源JSON直接冒充已发布run结果。

## 请求与运行隔离

| 参数 | 类型与生效规则 |
|---|---|
| run_id | 可选不透明字符串；省略则一次解析当前 PUBLISHED，整次请求锁定该 run，不反复解析 current |
| filter_start / filter_end_exclusive | 无偏移 ISO `YYYY-MM-DDTHH:mm:ss[.ffffff]`；左闭右开、start<end，不带 Z/偏移，精度须无损 |
| bike_filter | NULL 或非空键字符串列表；NULL=全部含缺失/未识别；按同运行字典 bike_type_key 选择；`"0"` 可选缺失；重复去重，空列表/不存在键为 invalid_request |
| station_filter | 仅 station_flow 接受，NULL 或非空当 run 站点键字符串列表；各侧筛自己的事件站，不要求骑行两端都匹配；`"0"` 为未知 |
| granularity | trend/station_flow 为 hour/day/month；桶用源日历；热力图另用 weekday_hour |
| include_empty_buckets | boolean，默认 false；仅 complete 窗口允许日期骨架补真实零 |

总览、趋势、类型比较只接受时间/车型，不接受隐含站点或 member_only 筛选；会员类型用于分组。未支持筛选返回 invalid_request，不能静默忽略。D 选项来自该 run 的维度字典（key/code/label/is_unknown/is_recognized），不猜代理键；换 run 后重取选项。

默认 Q3，也可查询其他已证明覆盖区间。部分小时边界必须从 fact 精确筛选，完整小时才可直接用小时 DWS。自然桶结果只统计请求交集，不能把窗口擅自整点化。

## 公共返回与元信息

每个命名结果有 metadata 和 data，可映射成 SQL 多结果集或接口信封，但语义一致。data 统一为行列表：overview 在完整覆盖时（含有效空集合）恰一行，覆盖不足时一行但权威标量均 NULL；其他集合在覆盖不足时 []。invalid_request/run_unavailable 均 data=[]，无运行时 source_hashes=[]。

| metadata 字段 | 类型 / 可空与含义 |
|---|---|
| result_name | string，非空；ride_overview/trip_trend/station_flow/type_comparison/weekday_hour |
| result_status | enum；ok/empty/insufficient_coverage/run_unavailable/invalid_request |
| run_id | 已解析运行字符串；无可用运行时 NULL |
| rule_version | string，A-1.0 |
| processing_policy_version / model_version | string，实际运行版本；本基线 B1-1.0 / 1.0，接入须检查兼容 |
| source_hashes | 对象列表：ZIP 哈希、成员名、CSV 哈希；匹配 run，不传凭据/私有机器路径 |
| filter_start / filter_end_exclusive | 实际生效的无偏移边界，不偷偷扩大 |
| bike_filter / station_filter | 实际键选择或 NULL；非站点结果 station_filter=NULL |
| time_role | departure/arrival/dual；station_flow 必须 dual |
| coverage | 按角色列表：complete/partial/unknown、证据区间、proof_ref；无证据不称 complete |
| generated_at_utc | UTC 结果生成时间，与源业务时间分开 |
| warnings / missing_coverage | 问题/缺覆盖区间列表，允许 [] |

未知运行/未发布运行返回 run_unavailable；不把 FAILED 构建当空样本。缓存键必须含解析后的 run_id、过滤、粒度和版本。

invalid_request/run_unavailable 的最低元信息是 result_name、result_status、warnings 和可解析的 run_id；尚未成立的生效过滤/版本/时间信息可为 NULL，清单为 []，不捏造正常查询元信息。所有整数字符串的排序使用数值意义，不按字符串字典序把 10 排在 2 前。

## 数值、空集合与无覆盖

JSON 中所有计数、代理键和总微秒用**十进制整数字符串**，无千分位；SQL 通道用足够宽的精确整数/定点。净流出可负。D 不把微秒转 JavaScript Number 再相加。

平均分钟用精确总微秒/次数计算后一次 HALF_UP 两位，返回十进制字符串。占比/覆盖率返回 0..1 的十二位小数比例字符串；显示两位百分比必须从精确分子分母独立计算后一次 HALF_UP，不能从已舍入比例二次舍入。C 可另返两位百分比文本；D 合并组时仍用分子分母重算，不能平均显示值。

| 情况 | 返回行为 |
|---|---|
| complete 且有效空集合 | status=empty；总览次数/总微秒/member/known 为 `"0"`；平均/会员占比/识别覆盖率 NULL；集合可 []，显式补桶时计数 0、均值 NULL |
| complete 且只有未知会员类型 | status=ok；总次数>0、known=0、member_share=NULL、识别覆盖率=0；不展示为有已知样本的 0% |
| partial/unknown 覆盖 | status=insufficient_coverage；总览权威指标 NULL、集合 data=[]，明确提示缺覆盖，不能解释成正常 empty 或 0 |
| 无可用 run 或参数无效 | 对应 result_status，不生成伪零结果 |

station_flow 要双角色 complete，任一侧不足按 insufficient_coverage 返回，不输出半边权威差值；仍附两侧覆盖诊断。单独 M04/M05 查询可分别只要求自己的角色完整。若额外提供“观察到的计数”，须列非权威诊断，不能填进指标字段。

## ads.ride_overview

一行：当前出发范围及车型集合，time_role=departure。覆盖不足时下列权威标量全部允许 NULL；覆盖完整时除比率/均值零分母外非空。

| 字段 | 类型 / 含义 |
|---|---|
| ride_count | 非负整数字符串，M01 |
| duration_us | 非负整数字符串，同集合总微秒 |
| avg_duration_minutes | 两位十进制字符串或 NULL，M02 |
| member_count | 非负整数字符串，精确 member 次数 |
| known_member_type_count | 非负整数字符串，member+casual |
| member_share | 十二位比例字符串或 NULL，M03 |
| member_type_coverage | known/ride_count 的十二位比例字符串或 NULL |
| unknown_member_type_count | ride_count-known，含缺失与非空未识别标签 |

## ads.trip_trend 与 ads.weekday_hour

trend 一行是一出发自然桶，字段：`time_bucket`（桶源时间起点）、`bucket_end_exclusive`、`ride_count`、`duration_us`、`avg_duration_minutes`、`member_count`、`known_member_type_count`、`member_share`、`member_type_coverage`。数值与可空性同 overview，桶只聚合请求交集；按 time_bucket 升序。

weekday_hour 一行是请求内 ISO 星期×小时，字段：`iso_weekday`（整数 1..7）、`hour_key`（键字符串 0..23）、`ride_count`、`duration_us`、`avg_duration_minutes`；按星期、小时升序。它将多个日期折叠，不是一个具体日小时。补零仅限 complete 覆盖，不能由日历骨架伪造缺失覆盖。

## ads.station_flow

一行是一站点×事件自然桶，车型按请求共同筛选，time_role=dual。两侧独立过滤/聚合后按键并集合并。

| 字段 | 类型 / 可空及语义 |
|---|---|
| station_key | 非空整数键字符串，按选定 run 解释 |
| station_id | 精确字符串，未知成员 NULL |
| station_name | 非空展示名，允许明确标注回退 |
| time_bucket / bucket_end_exclusive | 无偏移事件自然桶起止 |
| departures / arrivals | 非负整数字符串，M04/M05 |
| net_outflow | 有符号整数字符串，M06，等于借出减归还 |
| unknown_station_flag | boolean，仅 station_key=0 为 true |
| reference_lat / reference_lng | 十进制字符串或同时 NULL；同次源观察参考点 |

全量核算保留未知行。station_flow 顶层 summary 另返当前筛选范围的 `unknown_departures`、`unknown_arrivals`、`departures_total`、`arrivals_total`（均整数字符串），以及 `start_station_id_coverage`、`end_station_id_coverage`（各自 1-unknown/total 的十二位比例，分母 0 为 NULL）；覆盖不足时这些权威字段全部 NULL。D 的真实排名/地图排除未知，同时显示未知数量，并明确这些覆盖率属于当前筛选而非整个网络。无坐标的真实站点仍保留于表格和总量。地图过滤不能反馈成事实过滤。

表格默认 time_bucket、station_key 升序。排名在请求窗口先按站点汇总，再按目标指标降序；净流入按 net_outflow 升序；并列按 station_id 精确字节序、再 station_key 排序。不得在事实 join 前 top N。双侧无事件站仅在请求补桶、属于当前字典且覆盖完整时可列零。

## ads.type_comparison

一行是 member_type_key×bike_type_key，字段：两键、`member_casual`（源 code，缺失 NULL）、`rideable_type`（源 code，缺失 NULL）、`ride_count`、`duration_us`、`avg_duration_minutes`，以及 `member_type_is_unknown`、`member_type_is_recognized`、`bike_type_is_unknown`、`bike_type_is_recognized` 四个 boolean。非空新标签保持独立行，不伪装成 member/casual。

默认只返有事件组合；补组合须另作明确约定且 complete。排序按会员类型精确 code（缺失后置）、车型精确 code、代理键。全组合次数/总微秒与同筛选 overview 相等；会员卡从全组 member/known 重算，不能先筛 member。

## 接入验收

逐项核验[六指标映射](../design/metric-model-mapping.md)中的角色、车型、未知、分母、空/无覆盖、部分小时和重跑。D 标注来源分区、范围、时间角色、规则/处理版本、run_id 与时长门槛。当前无真实 ETL 结果；A PDF 数字不能作为页面的真实数据。
