# C → D：查询结果契约

C提供数据，D负责展示；业务口径见[需求说明](../requirements.md)。以下是逻辑结果约定，通道可用SQL结果集或接口，当前尚未实现。

## 请求参数

| 参数 | 含义 |
|---|---|
| run_id | 可选；省略时使用当前PUBLISHED运行，整次请求固定这个run |
| filter_start / filter_end_exclusive | 无偏移源时间，左闭右开；默认2024Q3 |
| bike_filter | NULL为全部，或非空车型键列表；从当前字典取选项 |
| station_filter | 仅站点结果使用；借出筛起点、归还筛终点，0可选未知 |
| granularity | 趋势/站点结果用hour、day、month；热力图用weekday_hour |
| include_empty_buckets | 默认false；只在覆盖完整时允许补零桶 |

总览、趋势、类型比较不接受隐含站点或member_only筛选。筛选无效时明确返回错误；切换run后重取字典。部分小时窗口按实际时间筛选，不扩大到整点。

## 五种结果

| 结果 | 一行含义 | 字段 |
|---|---|---|
| ride_overview | 当前出发范围及车型总览 | ride_count、duration_us、avg_duration_minutes、member_count、known_member_type_count、member_share、member_type_coverage、unknown_member_type_count |
| trip_trend | 一个出发自然桶 | time_bucket、bucket_end_exclusive、ride_count、duration_us、avg_duration_minutes、member_count、known_member_type_count、member_share、member_type_coverage |
| weekday_hour | ISO星期×日内小时 | iso_weekday、hour_key、ride_count、duration_us、avg_duration_minutes |
| station_flow | 站点×事件桶，两侧独立聚合 | station_key/id/name、time_bucket、bucket_end_exclusive、departures、arrivals、net_outflow、unknown_station_flag、reference_lat/lng |
| type_comparison | 会员类型×车型 | member_type_key、bike_type_key、member_casual、rideable_type、ride_count、duration_us、avg_duration_minutes，member_type_is_unknown、member_type_is_recognized、bike_type_is_unknown、bike_type_is_recognized |

每种结果返回metadata和data行列表。metadata包含result_name/status、run_id、source_hashes、实际时间/车型/站点条件、time_role、coverage、规则/处理/模型版本、generated_at_utc和warnings。

station_flow另有summary：departures_total、arrivals_total、unknown_departures、unknown_arrivals、start_station_id_coverage、end_station_id_coverage。总量保留未知；真实排名/地图单列未知，无坐标真实站仍保留表格。

## 数值和显示

- JSON计数、键、总微秒使用十进制整数字符串；净流出可负。SQL通道使用精确整数/定点。
- 平均分钟显示2位小数；比例返回0..1的12位小数字符串。两位百分比从精确分子分母一次HALF_UP计算，分组汇总也重新计算，不平均显示值。
- member_share的分母仅member+casual；member_type_coverage=known/总次数。未知会员不计入分母，但仍在总次数中。
- 时间桶和热力图按时间/星期/小时升序。排名先汇总，再排序取Top；并列按精确站点ID和键稳定排序。
- 地图坐标是源观察参考点，不表示轨迹或实时库存。

## 空值与状态

| result_status | 返回/展示 |
|---|---|
| ok | 正常结果 |
| empty | 覆盖完整但无记录：计数/总微秒为0，均值/零分母比例为NULL |
| insufficient_coverage | 覆盖不足：总览权威值NULL，集合为空；站点两侧有一侧不足就不输出差值 |
| run_unavailable / invalid_request | data为空，说明没有可用运行或参数有误 |

只有未知会员且次数>0时，member_share=NULL、识别率=0。完整范围内某站某侧无事件可记0；缺覆盖不能当真实0。D与C在相同run/筛选下逐项对账后再录屏。
