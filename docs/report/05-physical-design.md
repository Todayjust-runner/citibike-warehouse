# 5 物理设计

## 5.1 平台与实现范围

本项目采用 SQL Server 2019、T-SQL 和数据库兼容级别 150。实际结构验证运行于本机 localhost，版本 15.0.2000.5、Developer Edition，Windows 集成认证。独立测试数据库为 `CitibikeDW_B_Test`；截至 2026-11-13，业务数据库 `CitibikeDW` 未创建，课程实验库未被本阶段写入。本机验证使用的 sysadmin 身份不等于已确定团队应用账号与最小权限方案。

物理版为 B2-1.1，对应逻辑 1.0、业务 A-1.0 和处理策略 B1-1.0。数据库包含 ods、dim、dwd、dws、ads、meta 六个 schema、14 张表、132 个列，其中 5 个为持久化计算身份列。ADS 尚无业务查询对象，完整 ETL 和展示由 C/D 接续。

完整结构以[物理清单](../design/physical-model.json)为机器可读定义，[物理字典](../design/physical-data-dictionary.md)列出每个列、键与索引。当前实现不额外引入实时链路、SSAS 或分布式组件。

## 5.2 类型、长度与精度

表 5-1 列出影响正确性的主要物理选择。

| 对象 / 字段 | SQL2019 类型 | 设计目的与边界 |
|---|---|---|
| run_id | uniqueidentifier | C 生成构建 UUID，查询固定一个已发布运行 |
| 源成员/源行/骑行/覆盖代理键 | bigint IDENTITY | 技术身份，允许回滚后空洞，不表示计数或 CSV 行号 |
| 站点代理键 | bigint | C 在运行内分配，0 为未知；PK/FK 含 run_id |
| 车型/会员键 | int IDENTITY | 非空精确标签和缺失成员，固定种子不代表完整真实值域 |
| 日期键 / 小时键 | int / tinyint | YYYYMMDD / 0—23，属性 CHECK 保持一致 |
| 13 列原文 / raw_values | nvarchar(max) | 无损保留原文本；CSV 空字段保留空字符串 |
| 精炼 ID、车型/会员 code | nvarchar(200) | 上限按 UTF-16 单元计；超限停止，不裁短 |
| member_path | nvarchar(512) | 成员路径精确保留，本快照已剖析适配，未来继续预检 |
| 五个精确身份 | varbinary(400) / 路径 varbinary(1024)，PERSISTED | 完整 UTF-16LE 字节；区分大小写和尾空格，服务器生成 |
| 事件 / 覆盖时间 | datetime2(7) | 接收精度 100ns，CHECK 限为整微秒以拒绝非对齐输入 |
| 执行审计时间 | datetime2(7) | 明确 UTC 约定，与源业务时间分开，允许 100ns |
| duration_us / DWS 总微秒 | bigint / decimal(38,0) | 原子精确微秒，汇总扩大容量，避免 int/浮点和中间溢出 |
| 解析坐标 | decimal(20,15) | 两侧质量状态和合法范围约束；本快照已验证精度适配，客户端绑定仍待C核验 |
| 文件 SHA-256 | char(64)，小写十六进制 | 完整内容身份，不用 ETag 代替 |

文本列采用 Latin1_General_100_BIN2，业务唯一性仍通过完整二进制身份实现，以处理 SQL 字符串尾空格比较的差异。最长非聚集身份键为 ZIP 哈希 64 字节加路径 1024 字节，共 1088 字节；聚集键较短，分别处于本实现适用的索引键长限制内。

事实时长用 `DATEDIFF_BIG(MICROSECOND, started_at, ended_at)` 精确对应起止时间，并限定 `[60000000,86400000000]`，trip_count 固定为 1。事件时间与覆盖边界的 `DATEPART(NANOSECOND,值)%1000=0` 检查会拒绝实际送达数据库的非整微秒值。C 仍须在客户端绑定之前检查源文本精度、UTF-16 字节长及坐标可表示性；如果客户端预先截断或舍入，数据库不能恢复原值。

## 5.3 完整性、索引与发布保护

实库有 14 个主键、8 个唯一约束、31 个外键、52 个 CHECK、26 个索引和 17 个过程/触发器（2 过程、15 触发器）。外键和 CHECK 均启用且受信任，触发器启用。索引数量包含 PK/UQ 创建的索引，不是另加 26 个普通索引。

表 5-2 汇总关键机制。

| 机制 | 实现 / 行为 |
|---|---|
| 运行内唯一事实 | PK(run_id,trip_key)，UQ(run_id,ride_id_identity) |
| 角色关联 | 独立起终日期/小时/站点 FK；站点 FK 包含 run_id，防串运行 |
| 精度和未知 | 精确时长/微秒对齐、角色键对应时间、未知成员形状及坐标对一致 CHECK |
| 来源与血缘 | 源定位唯一、去向主键/形状、同运行 fact FK、接受代表一致门槛 |
| 覆盖 | 同运行同角色区间禁止重叠，可相邻；complete 必须有 proof_ref |
| 汇总 | VALIDATED/PUBLISHED 前将两 DWS 与事实计算结果作双向差集 |
| 冻结 | 原始行/全局维度禁止改删；验证/发布后的运行数据禁止改写，关联源成员禁止追加 ODS |
| 当前发布 | scope 上过滤唯一索引；usp_publish_run 事务与应用锁原子切换，失败保留旧 current |
| 查询访问 | IX_fact_departure、IX_fact_arrival 分别支持 run+角色时间+车型；IX_disposition_trip 支持血缘检索 |

运行状态包括 CREATED、RUNNING、VALIDATED、PUBLISHED 和 FAILED。正常构建进入 RUNNING，C 完成真实质量检查、覆盖与汇总后设置 VALIDATED，再调用 `meta.usp_publish_run`。就绪门槛检查全成员/读取量、13 列形状、全源去向、接受代表、站点观察来源、双角色声明及 DWS 相容性。该检查不替代真实哈希、归档规则、排除算法或覆盖证明的外部核验。

B3 复核发现 B2-1.0 允许向已验证/发布运行引用的源成员追加原始行，会破坏已确认读取守恒。先增加负例观察到插入未被拒绝，再调整既有 ODS 触发器加入 INSERT 保护；新成员仍可写。修订为 B2-1.1，表/列/键与业务语义不变，证据见 [B3 复核](../review/b3-final-review.md)。

## 5.4 部署顺序与安全重跑

DDL 顺序为 `010_schemas`→`020_tables`→`030_foreign_keys`→`040_indexes`→`050_integrity`→`060_seeds`。种子仅有小时 24 行、车型 3 行、会员类型 3 行；每运行站点未知成员、日期和真实业务行由 C 装载。

部署入口为 Python 3.10+ 标准库脚本，调用现有 Microsoft sqlcmd，使用 Windows 集成认证及错误即失败参数。目标白名单只有两个项目数据库；默认测试库，业务库需要显式 `--allow-target`。现有未标记数据库拒绝接管，现有版本或结构漂移拒绝自动修复；同版匹配返回 `already_matches_no_changes`。默认入口不提供 reset、DROP 或清表操作。

新库先创建并标记所有权，六份 DDL 和种子在一个事务内执行；建库本身不包含在该 DDL 事务中，失败可能留下项目标记的空壳库，入口不会擅自删除它。旧版升级须审阅迁移，不能靠改指纹冒充升级。本次只对确认无真实数据、旧目录完全匹配的测试库，事务内调整一个触发器及两项版本属性，没有重建表。未在第二空库重新新建验证。

在既有工程根目录可运行：

```powershell
python -X utf8 scripts/warehouse.py inspect
python -X utf8 scripts/warehouse.py deploy
python -X utf8 scripts/warehouse.py verify
python -X utf8 scripts/warehouse.py boundaries
python -X utf8 -m unittest discover -s tests -p test_b2.py -v
```

测试夹具仅允许独立测试库且每例事务回滚；接续前先 inspect/verify 并检查是否已有 C 数据，不能把本次空测试库的假设当永久事实。配置/退出码和业务库显式开关见[运行说明](../../scripts/README.md)，`.env.example` 仅供参考，不自动加载。

## 5.5 实际验证与局限

2026-11-13 完成 B3 回归，表 5-3 为可追溯的实际结果。原 B2 证据作为历史保留，当前目录另存，不用新快照覆盖旧证据。

| 检查 | 实际结果 | 证据范围 |
|---|---|---|
| 引擎/兼容级别/完整目录 | SQL2019/150；14 表、132 列、31 FK，drift=[] | 当前测试库与修订物理清单一致 |
| Python 行为检查 | 10 项通过 | 白名单、业务开关、DDL 指纹、目录/漂移拒绝、重跑保留标记等 |
| SQL 边界与负例 | 50 项通过 | 60 秒/24 小时、微秒、未知/角色、大小写/尾空格、覆盖/血缘/发布及新增追加保护 |
| 无操作重跑 | 保留已提交的专用合成运行标记 | 测试后只清理本例标记，无默认重建 |
| 测试后数据 | 仅 24+3+3 固定种子，其余 11 表 0 行 | 前后行数一致，合成记录未留作业务结果 |
| 业务与真实数据 | 业务库不存在；真实 ETL/六指标未验 | 此为B3时点结果；新源核算见5.6，仓库验收仍未完成 |

精选证据为[执行摘要](../evidence/b3-execution-summary.json)及[实际目录](../evidence/b3-catalog.json)。本轮没有真实数据性能、并发压力或第二空库安装测试，索引适用性仍需 C 在真实工作负载下评估。A 数值不在结构验收中判定通过；真实来源、字段上限充分性、精确微秒合计、逐站与页面一致性按[联合验收清单](../handoff/acceptance-checklist.md)继续完成。

## 5.6 真实公开输入适配验证（补充）

B3后按用户授权直接取得官方202406—202410五个JC包，共20311165字节；全部ZIP和10成员SHA/CRC已核验，其中5个骑行CSV共563874行，另5个AppleDouble元数据不计入zip_csv_member_count/ODS。来源身份及源核验程序见[公开快照说明](../sources/public-snapshot-validation.md)。

全量剖析最大UTF-16单元：ride_id16、两端站点ID7、车型13、会员6、站名44；时间最大小数秒3位，纬度/经度最多15/14位小数，当前nvarchar上限、datetime2(7)与decimal(20,15)均能无损容纳该快照，无需DDL变更。接受源观察中427个真实站点ID，1站多名、160站多坐标，保留确定性源观察快照策略。

独立源核算新增10个真实小ZIP行为测试通过，同固定输入全量重跑两次语义摘要相同。38项A数值均匹配（精确总微秒216990044333000、Q3骑行334332等），属于源侧独立复算；A原哈希身份/原脚本仍未知，SQLServer本轮只读verify无漂移、除种子仍为空，完整ETL/查询及仓库对源对账未实施。不得把此补充改写成数仓业务验收通过。
