# Public Source Validation Implementation Plan

> **For agentic workers:** 在当前会话顺序执行；用户已授权直接获取公开源并完善项目。

**Goal:** 获取官方五个JC月包，独立核验真实输入和A数值声明，用证据完善B设计与C/D交接。

**Architecture:** 原始ZIP和逐行/逐站派生结果只保存在被忽略的data目录；提交来源身份、统计与比较摘要及可重跑源核验脚本。使用临时SQLite作磁盘分组核算，不写SQL Server业务表，不把源核算称完整ETL验收。

**Tech Stack:** Python标准库（urllib/zipfile/csv/datetime/decimal/sqlite3/unittest）、Markdown/JSON、既有SQL2019只读verify与Git。

**Spec:** 用户2026-11-13补充指令；A PDF p2—3、5—8；[源映射](../../design/source-to-target.md)及[验收清单](../../handoff/acceptance-checklist.md)。

## Global Constraints

- 原工程接续，课程原件不移动；数据包/行级及逐站结果不入Git。
- 新下载快照不能证明与A原包同哈希；把“数值对上”“A身份一致”“数仓ETL通过”分开记录。
- 按13字段原文、完整CSV成员、精确UTF-16身份、整微秒、冲突整组隔离和双事件角色核验。
- 不为凑A数值修改数据/算法；物理不足须明确修订，SQL Server不默认部署/清空。

### Task 1: 官方来源与完整获取

**Files:** 新建 `inputs/public-source-snapshot.json`；ZIP只落 `data/raw/public-jc-20261113/`。
**Interfaces:** 消费PDF明确的官方入口；产出URL/UTC取得时间/响应元数据、ZIP/全部成员SHA与清单供源核算。

- [x] 复读PDF链接和现有规则，浏览官方字段说明与使用政策。
- [x] 下载五个完整对象，拒绝206/长度不符/CRC损坏，保留字节原样、全部成员和SHA。

### Task 2: 可重跑源核验

**Files:** 创建 `tests/test_source_audit.py`、`scripts/audit_public_source.py`；摘要 `docs/evidence/public-source-audit.json`，本地核算明细 `data/audit/public-jc-20261113/`。
**Interfaces:** 输入带SHA的快照清单；输出全量字段/质量/月份/源行去向计数、Q3六指标、月份/站点核算和字段上限适配报告。

- [x] 先以独立小ZIP夹具测试：重复/冲突优先级、归还独立窗口、未知、毫秒/微秒、空分母、超精度阻断、损坏哈希/多CSV/多行字段；观察测试因入口缺失失败。
- [x] 实现标准库磁盘核算，核验清单SHA/表头/全行，原始文本比较且确定性代表；计数/微秒精确，输出分子分母，派生CSV只在data。
- [x] 测试通过后运行真实五包，独立与A转录值比较；同输入重跑比对语义结果摘要，不能用A期望生成实际数值。

### Task 3: 设计、报告与交接补充

**Files:** 输入/来源/开放属性/复核、报告3/4/5章、B→C/D及验收清单、README/AGENTS/STATUS/四阶段计划/决定，新增B交付v1.1及其SHA清单。
**Interfaces:** 消费实际核算证据；产出已知属性、逐项匹配/差异和C可用输入版本；v1.0保留为966d774历史。

- [x] 按实测更新字段上限、时间/坐标精度、真实标签/站点属性、结束月与Q3边界，并明确未装载SQL Server。
- [x] 将数值已核对与A身份/脚本仍缺分开，补当前清单和C加载入口，不再把公开可得数据笼统标全部缺失。
- [x] 更新B交付v1.1和当前SHA；旧版清单只在原提交验证，保持历史可定位。

### Task 4: 检查与发布

**Files:** 本轮提交检查和发布记录。
**Interfaces:** 消费源核验测试/重跑、只读SQL目录与候选文件；产出可审阅提交和private main一致结果。

- [x] 检查源核验测试、同输入语义重跑、JSON/链接/材料/忽略/敏感信息与暂存文件；只读verify现库。
- [x] 核实既有private仓库及远程基线，普通提交/推送，核对完整树/blob与干净工作区。
