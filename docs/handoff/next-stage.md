# 下一阶段交接：对话三 / B2 物理设计与建表验证

对话二已经完成概念、逻辑与数据契约。接续根目录 `D:\数据仓库\期末大作业\citibike-warehouse`，不重新初始化。先读 [阶段 STATUS](../planning/STATUS.md)、[四阶段计划](../planning/b-four-conversations.md)、[AGENTS](../../AGENTS.md)、[设计入口](../design/README.md)、[契约入口](../contracts/b-c-d-contract.md)与决定记录。

## B2 具体工作与产物

| 顺序 | 动作 | 交付与门槛 |
|---|---|---|
| 1 | 检查 Git、实例、库存在性与权限；核对 A 附件状态 | 只读结果需有时点，不把旧方案“不存在 CitibikeDW”当当前事实 |
| 2 | 将 logical-model.json 落为 SQL2019/150 物理设计 | docs/design/physical-design.md，逐字段类型/长度/精度、NULL、键/检查/索引、分层策略 |
| 3 | 实现编号 DDL、配置示例与默认执行入口 | sql/ddl/、scripts/、.env.example；不含密码、不默认 DROP，不碰课程实验库 |
| 4 | 实现结构一致性与约束/边界检查 | sql/validation/ 和 tests/；单 run、精确身份、角色 FK、时间/时长、未知、去向和唯一 current |
| 5 | 在 CitibikeDW_B_Test 独立验证 | 实际对象/字段/约束/索引、重复执行和负例证据；夹具明确为合成，不入真实指标 |
| 6 | 更新物理契约差异、STATUS 和对话四交接 | 保留输入未核验与外部签收缺口；提交可审阅版本并同步 private main |

目标业务库为 `CitibikeDW`；结构验证库为 `CitibikeDW_B_Test`。如库已存在，先检查用途和内容，不覆盖既有业务数据；默认重跑不静默重建数据，破坏性重置另行隔离。未明确授权部署业务库时优先完成独立测试库结构证据。

## 必须落实的逻辑约束

- 一个 dwd.fact_trip，业务唯一为同 run 的精确 ride_id_identity；事实包含全部有效输入，不只 Q3 出发。
- 日期/小时分别 role-play；站点 FK 为 (run_id, station_key)，未知站点 key=0；每角色恰一匹配，不能跨运行。
- UTF-16LE 完整身份区分大小写与尾空格。评估 SQL 索引键长度上限，选择不截断且可检查的物理方案；不能用哈希碰撞假设代替唯一性。
- 源时间至少毫秒并保留实际精度；时长精确 bigint 微秒；边界 60 秒/24 小时含端点，超边界且可表示的 1 微秒应排除。不要直接套旧候选 datetime2(3)。
- 去向表每 run 每源行唯一；ACCEPTED/重复关联同 run fact，REJECTED 不关联；事实一个接受代表，全输入守恒。
- 同 scope 至多一个 current PUBLISHED；失败运行不切换。非 FK 可表达的跨表条件须配检查，并清楚划分 B 结构约束与 C 加工责任。
- 出发/归还独立覆盖及 proof_ref；partial/unknown 不伪装 0；完整小时才可直接用 DWS，部分小时回 fact。
- 站点观察快照不是业务历史；未知标签/坐标不能导致有效骑行被丢弃。两类 DWS 是派生关系，B2/C 可选表或视图，但粒度不能改。

## 验收和范围边界

本阶段没有执行数据库命令。B2 应保存实际实例版本/兼容级别、命令/退出码、对象清单、字段与 PK/FK/UNIQUE/CHECK/索引检查、合成负例及安全重跑证据；不得仅静态读 DDL 标通过。

附件缺失影响见 [open-attributes](../design/open-attributes.md)：可先做有假设的物理方案与结构验证；真实值域/源行/六指标需 C 后续核验。B2 不实现完整 ETL、页面或最终报告。对话四 B3 才整理报告第 3/4/5 章与最终交接。

## 下一次可直接使用的任务说明

> 接续现有工程，完成四阶段方案的对话三 B2。先读阶段 STATUS、决定、logical-model.json、字段字典与 B→C/C→D 契约。目标 SQL Server 2019/150，业务库 CitibikeDW、验证库 CitibikeDW_B_Test；执行前检查存在性、用途和权限。交付物理设计、编号 DDL、配置/执行入口及独立结构验收脚本，在测试库保存真实建表/重复执行/约束边界证据。默认不删除现有数据、不触碰课程实验库，不实现完整 ETL/页面。A 基准继续待真实数据复现，更新阶段计划和对话四交接。
