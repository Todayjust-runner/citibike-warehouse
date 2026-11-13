# B → D 展示依赖交接 v1.0

2026-11-13。D 可依赖逻辑结果契约准备接入；C 的业务查询/API 尚未实现，本页不表示真实图表已有数据。字段类型、空值和排序的完整基线为 [C→D 查询契约 v1.0](../contracts/c-to-d-query-contract.md)，不要按 B2 测试表行或 A PDF 数字做正式页面。

## 结果依赖与字段

| 命名结果 | 一行粒度 / D 可依赖字段 |
|---|---|
| ride_overview | 当前出发窗口及车型；ride_count、duration_us、avg_duration_minutes、member_count、known_member_type_count、member_share、member_type_coverage、unknown_member_type_count |
| trip_trend | 一个出发自然桶；time_bucket、bucket_end_exclusive 与总览基础分子分母/均值/比例 |
| weekday_hour | ISO星期×日内小时；iso_weekday、hour_key、ride_count、duration_us、avg_duration_minutes |
| station_flow | 站点×事件桶；station_key/id/name、桶起止、departures、arrivals、net_outflow、unknown_station_flag、参考经纬度；summary 另返未知两侧/全量/站点ID覆盖率 |
| type_comparison | 会员类型×车型；两键及源code、次数/总微秒/均值、四个unknown/recognized标志 |

这些 `ads.*` 是命名结果，尚未承诺 HTTP 路由、视图或页面技术栈。C/D 选择通道后按原契约实现并记录接入确认，不能把数据库结构已建等同接口已可调用。

## 筛选与显示规则

- 源时间无偏移，不附加 Z、不转北京时间。所有时间窗口左闭右开；默认 Q3。run_id 省略时 C 一次解析 current PUBLISHED 并锁定，切换 run 后 D 重取字典和选项。
- 时间和车型作用于所有结果；NULL车型=全部含缺失/未识别，非空列表用当前可用键，空列表/非法键拒绝。总览/趋势/类型比较不接受隐含站点或 member_only 过滤。
- station_filter 只用于 station_flow：借出筛起点事件，归还筛终点事件，不要求一骑行两端匹配。两侧车型条件相同；M05可包含窗口前出发，净流出由两侧聚合结果相减。
- 会员占比是骑行占比，分母只含精确 member/casual；另显识别覆盖率。D 合并组时用精确分子分母重算，不能平均显示百分比/均值。
- JSON计数、键和总微秒均十进制整数字符串，净流出允许负数；不得先转 JS Number 后加微秒。平均分钟为两位小数字符串；比例为十二位小数字符串。两位百分比从精确分数一次 HALF_UP，不能对十二位比例再次舍入代替精确分数。
- 真实站点排名/地图单列未知成员0，并显示未知两侧数量/覆盖率；无坐标真实站仍在表格和核算总量。参考坐标不称实时位置，不能画真实骑行轨迹或宣称骑行距离。
- 趋势按桶时间排序、星期热力图按ISO星期/小时排序；键按数值排序。站点排名在窗口内先汇总，再排序/取Top，不能在事实关联前截断。

## 空值、覆盖与运行状态

| 状态 | D 行为 |
|---|---|
| ok | 展示当前运行的有效结果、单位与范围 |
| empty（覆盖完整但无有效记录） | 总次数/总微秒0；均值、会员占比和零分母覆盖率显示“无可计算样本”；完整范围才可补桶0 |
| insufficient_coverage | 标明缺区间/角色；总览权威指标NULL，其他集合[]，不显示为真实0；station_flow任一角色不足就不出权威差值 |
| run_unavailable / invalid_request | data=[]，提示无已发布运行或参数错误，不伪造业务值 |

只有未知会员类型且次数>0时，known=0、share=NULL、识别覆盖率=0；不能显示为“已知样本中会员0%”。覆盖不足与完整空集合不是同一状态。

各结果带 metadata：result_name/status、run_id、业务/处理/模型版本、source_hashes、实际filter_start/end、bike_filter/station_filter、time_role、双角色coverage/proof_ref、generated_at_utc、warnings/missing_coverage。界面至少能查看来源分区、当前范围/车型、事件角色、60秒—24小时门槛、版本及run；不暴露本机私有路径或凭据。

## 接入验收与课程汇总

按[联合验收清单](acceptance-checklist.md)逐项对齐查询/图表的同一 run、过滤和精确分子分母；测试跨月、未知、完整空/无覆盖、部分小时、换run和无效筛选。页面真实指标须来自 C 已验结果。B 已提供[报告3/4/5章与图件](../report/README.md)，D/团队汇总第7章、PPT、录屏及分工；课程最终材料包不因 B 完成而视为完成。当前没有外部签收记录。
