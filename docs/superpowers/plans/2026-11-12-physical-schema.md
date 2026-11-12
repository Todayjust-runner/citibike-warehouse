# B2 SQL Server 物理设计与建表验证 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.
>
> 用户授权在本会话继续对话三；当前会话顺序执行，不调用未提供的子技能或派发代理。

**Goal:** 将 B1 的 14 关系/132 字段模型实现为 SQL2019 DDL，在独立测试库验证结构、约束与安全重跑，并交接 B3。

**Architecture:** 标准库 Python 调用已有 sqlcmd，Windows 集成认证；默认只指向 CitibikeDW_B_Test。版本化物理清单对应 132 个逻辑字段，部署事务化，已存在但不匹配的结构拒绝自动覆盖。

**Tech Stack:** SQL Server 2019 / T-SQL / compatibility 150、Python 标准库 unittest、sqlcmd。

**Spec:** docs/design/logical-model.json、docs/contracts/、docs/planning/b-four-conversations.md；本次用户“继续进行下一步”。

## Global Constraints

- 不修改课程实验库，不默认部署 CitibikeDW；测试目标 CitibikeDW_B_Test。
- 默认入口无 DROP、清空或破坏性重置；同版本重跑保留已有数据，漂移时停止。
- 时长精确整数微秒，未知/角色/run 隔离与源行血缘不变。
- 不实现完整 ETL/页面，不把合成夹具或空库结构证明当 A 基准复现。

## Task 1：先建立失败的验收

**Files:** tests/test_b2.py、tests/sql/boundary_cases.sql。
**Interfaces:** 期望 scripts/warehouse.py 提供 inspect/deploy/verify/boundaries；默认数据库 test，业务库需 --allow-target；无外部 Python 依赖。

- [x] 只读确认本地/远程同步，15.0.2000.5、sysadmin=1；两个项目库当前均不存在。
- [x] 写安全目标校验、完整结构和安全重跑的行为测试；先运行，记录缺实现失败。
- [x] 预写真实 SQL CHECK/FK/唯一/角色/精度/覆盖与发布门槛的正反例；夹具逐例事务回滚。

## Task 2：实现受保护的部署和物理定义

**Files:** scripts/warehouse.py、docs/design/physical-model.json、sql/ddl/010_schemas.sql、020_tables.sql、030_foreign_keys.sql、040_indexes.sql、050_integrity.sql、060_seeds.sql、sql/validation/010_catalog.sql、.env.example。
**Interfaces:** inspect 返回引擎与目标标记；deploy 新建受管理库或验证后无操作；verify 比对所有列、键、检查、索引及模块；boundaries 只允许测试库。

- [x] 先实现数据库白名单、显式业务库开关、sqlcmd 错误传播和 JSON 输出；使安全测试通过。
- [x] 定义物理类型、持久化精确身份、全部约束及最小必要索引；保留 raw 为 nvarchar(max)。
- [x] 实现源行/角色/覆盖/发布完整性检查，区分数据库能约束与仍由 C 证明的事项。
- [x] 在新测试库执行部署，运行结构测试；更改后只重跑受影响检查。

## Task 3：真实验证、证据与阶段交接

**Files:** docs/design/physical-design.md、docs/evidence/b2-validation.md、docs/planning/STATUS.md、docs/handoff/next-stage.md 及受影响契约/决定/README。

- [x] 运行合成正反例，覆盖时间端点/亚微秒、未知、大小写/尾空格、组合 FK、去向/覆盖与当前运行唯一性。
- [x] 验证重跑保留指定合成标记数据；确认夹具清理后没有业务事实或运行残留。
- [x] 保存真实结构清单、检查退出码和范围；写 B2 物理假设、C 的输入精度/长度预检责任。
- [x] 更新对话三完成与对话四待开展状态；提交并同步既有 private main，核对完整文件树。
