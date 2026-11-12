# Citi Bike 工程基础 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> 本次为工程文档初始化，按用户已授权范围在当前会话执行；上述技能模板提及的子技能未在本会话提供，不以其为阻塞，不派发子代理。下阶段实施另按届时可用技能和用户范围执行。

**Goal:** 完成 A 交付审查和可提交的 B 工程基础，并发布到当前账户的同名 GitHub 私有仓库。

**Architecture:** 原课程材料原位保留，仓库只收工程说明、证据清单和后续开发契约。证据按已核验、A 声明未复现、设计决定、待实施区分。

**Tech Stack:** Markdown、JSON、CSV、Git；后续 SQL Server 2019 / T-SQL / compatibility level 150。

**Spec:** 用户本阶段指令；原位 A PDF 第 1-9 页、课程要求第 1-2 页及报告/PPT 模板（见 inputs/local-materials.json）。

## Global Constraints

- 工程根目录为 D:\数据仓库\期末大作业\citibike-warehouse；存在则接续。
- 本阶段仅 A 交付审查、工程结构、README、AGENTS.md、忽略规则、输入清单、决定记录和 STATUS。
- B 负责三级设计、DDL、建表验证及交接契约；完整 ETL 和展示由 C/D 负责。
- 只有 A PDF，无其附件；文中基准不能标为已复现。
- 保留课程材料原位；待提交文件检查通过后创建/核实私有仓库再提交。

## Task 1: 材料与证据预审

**Files:** inputs/local-materials.json、inputs/required-inputs.csv、inputs/a-claimed-baselines.json、docs/review/a-delivery-review.md、docs/review/course-requirements.md、docs/sources/official-sources.md、docs/evidence/official-object-check.json。

**Interfaces:** 消费原位 PDF/模板及官方页面；输出有来源定位、核验层级及缺口影响的输入契约。

- [x] 读取 A 全文与课程要求，检查模板、参考指南及现有目录。
- [x] 检查官方字段页和五个月对象元数据，只取 7 月包前 64 KiB 核对表头。
- [x] 写本地材料 SHA-256、A 声明基准及附件缺失清单。
- [x] 对照来源检查每条核验结论和缺口影响；不写复现通过结论。

## Task 2: 工程结构与协作约束

**Files:** README.md、AGENTS.md、.gitignore、.gitattributes、docs/decisions/README.md、docs/handoff/next-stage.md、docs/contracts/b-c-d-contract.md、docs/design/README.md、sql/ddl/README.md、sql/validation/README.md、etl/README.md、dashboard/README.md、scripts/README.md、data/README.md、tests/README.md、docs/evidence/environment-check.md、STATUS.md。

**Interfaces:** 消费 Task 1 的证据等级；输出后续 B/C/D 的职责、命名边界、验收与接续顺序。本阶段无数据导入、DDL 执行或页面开发。

- [x] 写范围、阅读顺序、目录职责和 SQL Server 2019 约束。
- [x] 写时间角色、未知站点、精度、去重、源行血缘和指标接口最低要求。
- [x] 写决定记录及下阶段设计/建表验收清单。
- [x] 只读核验数据库版本，记录环境可用与建表未实施的区别。

## Task 3: 检查并提交

**Files:** docs/evidence/submission-check.md、docs/evidence/github-delivery.md、STATUS.md。

**Interfaces:** 消费完整候选提交；输出可审查的 Git 提交与私有仓库远程一致性。

- [x] 检查文件编码、Markdown 本地链接、JSON/CSV 格式与忽略命中。
- [x] 检查待提交文件无原始数据、课程 PDF/书籍、凭据、数据库备份和个人学号。
- [ ] 核实当前账户及同名仓库用途；不存在才创建 private 仓库。
- [ ] 提交工程基础；核对本地/远程提交、私有属性及工作区状态。
- [x] 更新 STATUS 与下一阶段交接；最终报告区分已完成、本地提交及远程阻塞，保留附件缺失影响。

Task 3 远程部分受外部能力限制：当前 klzyd 连接器无创建仓库工具，浏览器自动化已停止；本机另一个 Git 账户不代替当前连接账户。详见 docs/evidence/github-delivery.md。本地检查与提交继续完成，远程项保留未完成。
