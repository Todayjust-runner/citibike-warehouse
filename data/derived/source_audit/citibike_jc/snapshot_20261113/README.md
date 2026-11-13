# Q3独立源核算：JC公开快照2026-11-13

共同窗口：源时间 `[2024-07-01T00:00:00,2024-10-01T00:00:00)`，全部车型。准入60秒—24小时、原文本去重规则B1-1.0；源输入覆盖202406—202410。快照日期指取得时间，结果业务窗口为2024Q3。

| 文件 | 一行粒度 | 字段与含义 |
|---|---|---|
| [monthly.csv](monthly.csv) | 一个出发月份 | month、ride_count、duration_us、member_count、known_member_type_count、avg_duration_minutes_display、member_share_display；微秒/分子分母精确，显示值不可直接平均 |
| [station-flow.csv](station-flow.csv) | 一个事件站点，Q3两侧分别汇总 | station_id、is_unknown（CSV为True/False）、departures、arrivals、net_outflow；未知ID为空，仍保留核算总量 |
| [boundary-records.csv](boundary-records.csv) | 一条跨窗口有效源代表记录 | direction、zip_sha256、member_path、csv_record_number、started_at、ended_at；10条entering/11条leaving，记录号表头1/首数据2 |

全部UTF-8/LF。数字列需按整数/精确Decimal读取；平均分钟和百分比从精确分子分母重算。站点借还不直接连接明细，归还独立按ended_at筛选。

源身份见[输入清单](../../../../../inputs/public-source-snapshot.json)，执行与完整剖析见[源审计JSON](../../../../../docs/evidence/public-source-audit.json)，文件SHA见[data清单](../../../../catalog.json)。从工程根运行源审计可在本目录重建相同CSV；临时SQLite只在运行期间存在且保持忽略。这些源侧对照不代表C的仓库ETL/API已通过。
