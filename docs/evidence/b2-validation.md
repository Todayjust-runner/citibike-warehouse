# B2 实际建表与验证记录

日期：2026-11-12（Asia/Shanghai）。**结论：SQL Server 2019 独立测试库结构和合成边界行为通过；真实数据及 A 基准未验收。**

机器可读结果见 [执行摘要](b2-execution-summary.json) 和 [实际目录快照](b2-catalog.json)；预期物理定义见 [physical-model.json](../design/physical-model.json)。完整临时测试输出在工程外 `D:\数据仓库\tmp\citibike-b2-review\`，远程只提交精选工程证据。

## 实际环境与执行范围

开始时只读检查：`localhost`，版本 `15.0.2000.5`，Developer Edition，当前 Windows 账户 sysadmin=1；CitibikeDW 与 CitibikeDW_B_Test 均不存在。没有把旧方案的存在性结论沿用到本次。

本次只新建并写入受管理的 **CitibikeDW_B_Test**，兼容级别 150，数据库及字符串列采用 Latin1_General_100_BIN2。CitibikeDW 结束时仍不存在。课程库没有被本阶段执行 DML/DDL；初末数据库清单仅新增测试库，没有对课程库逐表做内容审计。

实际结构：

```text
schemas                   6
tables                   14
columns                 132
persisted computed        5
primary keys             14
unique constraints        8
foreign keys             31  (enabled / trusted)
check constraints        52  (enabled / trusted)
indexes including keys   26
modules                  17  (2 procedures / 15 triggers)
catalog drift             0
```

## 测试与结果

| 命令/行为 | 实际结果 |
|---|---|
| `python -X utf8 scripts/warehouse.py inspect` | 正确识别引擎、数据库存在性及管理标记 |
| `python -X utf8 scripts/warehouse.py verify` | 退出 0，14/132/31，drift=[]；包括类型/精度/NULL/计算、PK/UQ/FK/CHECK、索引和模块 |
| `python -X utf8 scripts/warehouse.py boundaries` | 退出 0，47 个 SQL 正反例全部通过 |
| `python -X utf8 -m unittest discover -s tests -p test_b2.py -v` | 10 tests，OK；真实客户端及测试库，无模拟 SQL Server |
| 带一个已提交 SYNTHETIC-B2 CREATED 标记执行 deploy | 返回 already_matches_no_changes；该 UUID 行仍在，测试只清除了自己的标记 |
| 暂停一条 station 组合 FK | verify 检出 foreign_keys 漂移；deploy 退出非 0 拒绝自动修复；测试恢复 WITH CHECK CHECK 后再次通过 |
| 最终六文件 SET PARSEONLY | 退出 0，只解析，不执行新写入 |

SQL 正反例具体名称、预期拒绝的实际错误号和通过状态见 JSON 摘要。覆盖：60 秒/24 小时含端点、端点外一微秒、100ns 拒绝、时间/时长/日期小时一致性、未知保留、同 run FK、唯一源定位/骑行身份、大小写/尾空格、有限列长、坐标状态与范围、去向 NULL、覆盖重叠/证明/精度、表头、current 唯一、聚合一致、状态/数据冻结和事务发布失败保留旧 current。

本阶段只检查结构边界及已装载关系的相容性；没有运行完整 C ETL、真实排除/重复算法、实际六指标 SQL 或 D 页面。合成源均明确 SYNTHETIC-B2，并非课程真实业务数据。

## 先失败再修正的证据

- 实现前 6 项行为测试因缺受保护入口/结构而失败，随后安全目标测试先通过。
- 在真实 SQLServer 上发现空标量 JSON 可返回 NULL，先添加回归测试并观察失败，再用 COALESCE 返回 []；不是把缺库误当传输错误。
- 41 例初轮中“ACCEPTED 代表源行不能 NULL”失败：CHECK 的 UNKNOWN 被放行。先保留失败用例，再补 IS NOT NULL；其他 40 例原已通过。
- 另先证明 DDL 修改未被检查、同正文 CREATE OR ALTER 头造成误报、已验证元数据可被改写、缺发布过程、覆盖亚微秒及错误表头可越过门槛；末次复核还证明原始字符串列被置 NULL 时仍可发布。分别补实现和显式原文非空门槛后达到最终 10+47 通过，合法空单元格仍保留空字符串。

测试库开发中对受影响 CHECK/模块做了明确的局部修正，没有重建/清空已有表。第一次安装已创建结构，但后置比对因 SQLServer 编译定义规范化而拒绝；随后将类型/键/状态逐项对照声明、核对模块正文并运行独立行为测试后固化编译基线。没有把这次后置拒绝写成一次无误的新建成功。

最终版未在第二个空库重复新建；已验证的是本次新建测试库经局部修正后的最终结构、最后 SQL 的解析、默认无操作重跑和真实正反例。业务库和其他新实例的实际部署仍须按入口重新核验。

## 清理后状态

每个 SQL 用例完整事务回滚，独立 UUID 重跑标记及 FK 漂移均由各自测试恢复。最终 COUNT_BIG：dim.hour=24，dim.bike_type=3，dim.member_type=3；其余 11 表（含原始、运行、事实、DWS）均为 0。IDENTITY 计数器允许因回滚产生空洞，不能据此声称有业务行。

## 尚未证明

A 附件仍缺；真实 ZIP/CSV 哈希、最大 ID/标签长度、时间与坐标精度、月份归档、跨月数量、逐站基准和六项指标均未复现。非空 proof_ref 只是结构要求，不证明覆盖证据真实；C 必须用实际输入、代码和日志确认。没有进行真实数据规模的性能或并发压力测试，也没有确认团队最终演示/应用权限配置。
