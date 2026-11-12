# 物理设计 B2-1.0

本阶段将 B1 的 14 关系、132 字段、31 外键落实为 SQL Server 2019 / 兼容级别 150 的关系型数仓。物理清单为 [physical-model.json](physical-model.json)，逐字段可读版见 [physical-data-dictionary.md](physical-data-dictionary.md)。逻辑模型 1.0、业务 A-1.0、处理 B1-1.0 不变。

已在独立 `CitibikeDW_B_Test` 实际建表并验证；业务库 `CitibikeDW` 本阶段未创建。A 原始快照和真实指标仍未复现；有限列长与坐标精度是明确的装载契约，不是已完成真实字段剖析。

## 分层、键与类型

| 层 | 实体 / 实现选择 |
|---|---|
| meta | source_member、load_run、run_source、row_disposition、coverage，均为表 |
| ods | trip_raw 表，全部 13 原字段和 raw_values 为 nvarchar(max)，保留原文 |
| dim | date、hour、station、bike_type、member_type；站点按 run 观察快照 |
| dwd | 唯一业务事实 fact_trip，PK(run_id,trip_key)，UQ(run_id,ride_id_identity) |
| dws | trip_hourly、station_hourly 落物理表；C 加工，发布门槛复核与 fact 的双向差集 |
| ads | 本阶段仅创建 schema；C/D 的命名结果和查询还未实现 |

- run_id 用 uniqueidentifier，由 C 为每次构建生成 UUID；对 D 仍是不透明字符串。
- 源成员、源行、覆盖和骑行代理键为 bigint IDENTITY；车型/会员类型为 int IDENTITY；站点键由 C 在 run 内分配非负 bigint；0 专用于未知。IDENTITY 回滚后允许空洞，不能当业务计数或来源行号。
- 日期键 int=YYYYMMDD，小时键 tinyint=0..23，日期维度的属性和固定 ISO 星期有 CHECK，不依赖 DATEFIRST。
- ID 与标签 nvarchar(200)，成员路径 nvarchar(512)。边界按 **UTF-16 代码单元/字节数**，不是简单 Unicode 字符数；超限必须停止装载并提模型变更，禁止裁短。
- 五个身份字段由对应原字符串计算为持久化 varbinary(400) / 成员路径 varbinary(1024)，非空身份显式 PERSISTED NOT NULL。调用方不写计算列；精确身份不用哈希替代，区分大小写和尾空格。
- 起止时间和覆盖边界为 datetime2(7)，CHECK 纳秒分量模 1000 为 0，使数据库收到的 100ns 值被拒绝，而非先舍入为 datetime2(3)/(6)。执行审计用 datetime2(7) UTC 约定，允许自身 100ns 精度。
- 单次时长 bigint 整微秒，含边界 `[60000000,86400000000]` 且等于 DATEDIFF_BIG(MICROSECOND,start,end)；trip_count 恒 1。DWS 总时长 decimal(38,0)，计数 bigint，比例/均值不预存。
- 坐标 decimal(20,15)，有效值还需范围和成对 CHECK。C 必须在绑定前以精确数确认无舍入；不足时停止并调整物理版本。原坐标文本始终在 ODS。
- 有限字符串统一 Latin1_General_100_BIN2；枚举另校验长度避免尾空格等值。哈希为小写十六进制 char(64)，ZIP 月标签 char(6)=YYYYMM、日期 year_month char(7)=YYYY-MM。

## 键、检查、索引与模块

实际结构为 14 PK、8 UQ、31 FK、52 CHECK、26 索引（含 PK/UQ）及 17 模块（2 过程、15 触发器）。所有 FK/CHECK 启用且受信任；无级联删除。

最长非聚集唯一键是 ZIP SHA 字符 64 字节 + 成员路径身份 1024 字节，共 1088 字节，低于 SQL2019 非聚集键上限 1700；各聚集主键低于 900 字节。仅增加 current 过滤唯一索引、出发/归还查询索引和去向按事实查询索引；没有声称已进行真实数据性能优化。

| 约束/模块 | 执行保证 |
|---|---|
| 组合 PK/FK | 两端日期/小时关联唯一，站点强制同 run；有效事实不被窗口提前截断 |
| 精确身份 UQ | 同 run 的 ride_id、同 ZIP 的成员路径、站点/类型代码不被大小写或尾空格合并 |
| 日期/时间/坐标/去向 CHECK | 正确日期属性、毫秒/微秒保留、时长端点、坐标状态与 NULL、接受/重复/排除的形状 |
| current 过滤唯一索引 | 同 data_scope 至多一个 current，且 current 必为 PUBLISHED |
| coverage_no_overlap | 同 run/role 区间不重叠，邻接允许；complete 需非空 proof_ref |
| usp_assert_run_ready | 全成员/13 列表头/读取量/13 字符串单元格、源行去向覆盖、代表唯一、角色声明、站点来源与两个 DWS 一致 |
| load_run_publication | 状态迁移与完成时间、已验证输入/版本/代码/审计时间不可改写；转入 VALIDATED/PUBLISHED 时执行门槛 |
| usp_publish_run | 事务及事务级应用锁切换 current；失败不清掉原 current；同一 current 重复调用无操作 |
| run_frozen / immutable | VALIDATED/PUBLISHED 后不再改写该 run 的事实/站点/血缘/覆盖/汇总；原始行及全局维度身份不可 UPDATE/DELETE |

源成员身份元数据不可改写，inventory_verified 仅允许 0→1。全局维度不是业务历史，允许追加新标签，不能复用旧代理键改变含义。站点未知成员需 C 为每个 run 创建；部署只种 24 小时和两类标签各 3 个固定成员。

## 部署、重跑与漂移

唯一默认入口是 [warehouse.py](../../scripts/warehouse.py)。它先白名单校验数据库名，再连接；默认 test，业务库必须显式 `--database CitibikeDW --allow-target`。即使业务库已存在，默认也不自动采用未经项目标记的库。

新库创建后写项目标记；六个编号 DDL 文件在同一连接事务中执行，失败回滚表/约束/种子。CREATE DATABASE 本身在事务外，失败可能留下受管理空壳，入口不删除它。已有完整同版本结构通过核对后直接返回 `already_matches_no_changes`，不重播种子、不重建、不清空；有漂移或未标记则停止，不自动修复。

`physical-model.json` 记录类型/键/检查/索引/计算列及模块编译基线和 DDL 哈希。计算列/CHECK 的 SQL Server 规范化形式在初次编译后与声明元数据、模块源及独立行为夹具复核，再固化；不把数据库自报结构当业务数据正确性。验证只对模块的 CREATE/ALTER 头和末尾空白作无语义变化处理，模块正文与 CHECK 等仍严格比较。不同引擎补丁若改变规范化文本需人工复核，不能直接忽略漂移。

编号 SQL 是新建结构的组成部分，不能当有数据库的自动迁移包；050 的 CREATE OR ALTER 与 060 的种子必须由受保护入口协调。未来更改需要明确迁移方案、新物理版本和真实数据影响检查，不在默认入口加入 DROP 或重置。

## C 仍必须做的事情

- 先完整解析原始文本，预检 UTF-16 字节长、时间/坐标精度和无损转换，再绑定精炼列。数据库无法识别客户端已经提前截断/舍入的值；不能仅依赖 INSERT 报错。
- 仅将文件 BOM 当编码标记处理，不规范化 ID/标签单元格；保留 ZIP/CSV 全哈希及全部成员、真实排除原因、确定性去重与源行守恒。
- 填全 date、当 run 的 station(0) 及所有角色映射；装入 fact 和去向、两个 DWS、各角色 coverage；在事务内完成必要工作后转 VALIDATED，再调用 usp_publish_run。
- 证明 source_hashes、input_set_sha256、code_revision、proof_ref 指向真实内容，证明月份覆盖充分和最新站名/坐标的选择。数据库只能检查声明的形状/关系/一致性，不能证明 URL、哈希、覆盖证据本身真实。
- 实现六查询的精确窗口、部分小时回事实、会员分母和 NULL/无覆盖语义；完整 ETL/查询/页面及 A 的数值复现不属于本次结构通过结论。

对应证据：[B2 验证记录](../evidence/b2-validation.md)；下一阶段为对话四 B3 复核、报告正文和最终交接。
