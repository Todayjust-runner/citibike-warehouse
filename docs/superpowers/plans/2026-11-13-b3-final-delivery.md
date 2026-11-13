# B3 Final Delivery Implementation Plan

> **For agentic workers:** 按下列检查点在当前会话顺序执行；用户已授权继续 B3，不另开项目或代理。

**Goal:** 完成 B 的独立复核、报告 3/4/5 章、图件和 C/D 交接，并发布可审阅版本。

**Architecture:** 沿用逻辑 1.0 与既有 SQL2019 工程。先核验现库和源材料，再以事务回滚夹具复现实际问题；只对确认缺陷作最小修正。报告与交接分别引用设计、结构行为和真实验收证据。

**Tech Stack:** Markdown、Mermaid/SVG/PNG、Python 标准库、sqlcmd、SQL Server 2019 / 150、Git。

**Spec:** 用户四对话工作方案；[四阶段方案](../../planning/b-four-conversations.md)；[课程要求](../../review/course-requirements.md)。

## Global Constraints

- 工程根目录固定为 `D:\数据仓库\期末大作业\citibike-warehouse`。
- B 负责三级设计、DDL、建表验证和交接；完整 ETL/业务查询由 C、展示由 D 实施。
- 只在已核验的 `CitibikeDW_B_Test` 验证；业务库不默认部署，不重置或删除现有数据。
- 课程原件原位保留；A 附件缺失、PDF 数值未复现，不能用合成夹具替代。
- 当前会话顺序执行，无需新增线程、代理或重复确认。

---

### Task 1: 独立复核与最小缺陷修正

**Files:** 读取三级设计、契约、SQL、测试和原 PDF；如复现缺陷，修改 `tests/sql/boundary_cases.sql`、`sql/ddl/050_integrity.sql`、`scripts/warehouse.py`、`docs/design/physical-model.json`；记录 `docs/review/b3-final-review.md` 和 `docs/evidence/b3-execution-summary.json`。

**Interfaces:** 消费 `warehouse.inspect_database/verify/boundaries`、物理清单及实际目录；产出修订版本和真实检查结果供报告引用。

- [x] 读取只读 inspect/verify，确认无漂移，检查非种子行数和业务库存在性。
- [x] 复读 A p3、5-8、课程要求与报告模板，核对六指标、血缘、时间/站点角色、精度、发布和覆盖。
- [x] 对已发现的“验证后仍可给源成员追加原始行”写回滚负例；分别测试 VALIDATED/PUBLISHED，另测新成员仍可正常插入。运行 `python -X utf8 scripts/warehouse.py boundaries`，先确认负例因未拒绝插入而失败。
- [x] 在既有 `ods.TR_trip_raw_immutable` 增加 INSERT 检查：来源被 VALIDATED/PUBLISHED 运行引用时拒绝追加；保持其他成员可写。将物理修订为 B2-1.1，记录原版指纹与受控测试库补丁，不加入自动迁移或重建。
- [x] 重跑全部 10 Python 与扩展 SQL 用例，读取目录并确认只有预期模块变化，测试后各表计数回到前值。

### Task 2: 报告正文与图件

**Files:** 新增 `docs/report/README.md`、`03-conceptual-design.md`、`04-logical-design.md`、`05-physical-design.md`；更新 `diagrams/README.md`，新增 `diagrams/exports/` 图件和渲染配置。

**Interfaces:** 消费逻辑/物理清单、三份 Mermaid 源和 Task 1 证据；产出可合入课程报告的正文及可编辑/可插图文件。

- [x] 逐章写完整正文、图表、公式、来源和验证范围，章 3 表达信息包，章 4 表达粒度/关系/加工契约，章 5 表达 SQL 类型/约束/索引/安全执行与实测。
- [x] 使用 Mermaid 渲染器导出三个图的 SVG/PNG，保留工具版本和配置；逐图目视检查中文、箭头、边框和可读性。
- [x] 对照 14 表/132 字段/31 FK 清单检查正文，保证不将 ADS 契约或 A 基准称为已实现。

### Task 3: 最终交接与阶段更新

**Files:** 新增 `docs/handoff/b-to-c-final.md`、`b-to-d-final.md`、`acceptance-checklist.md`、`b-delivery-v1.0.md`；更新 README、AGENTS、根/详细 STATUS、四阶段计划、next-stage、设计/契约入口、决定和证据索引。

**Interfaces:** 消费 Task 1/2 产物；产出 B v1.0 交付清单、C 加载顺序、D 结果依赖和逐项真实验收门槛。

- [x] 明确 C 的预检/键/计算列/去向/汇总/发布，D 的字段/过滤/NULL/覆盖/元信息，列出真实输入与 A 基准待验项目及责任人。
- [x] B3 标记为 B 产物完成，外部签收、真实 ETL/六查询/展示、应用权限和课程汇总仍开放。
- [x] 更新下一阶段为 C/D 实施与 B 联合验收，不代发组员消息，不擅自实现后续范围。

### Task 4: 提交与私有仓库同步

**Files:** 更新 `docs/evidence/submission-check.md`、`github-delivery.md`，生成 B 交付文件哈希清单。

**Interfaces:** 消费全部可提交文件；产出普通 Git 提交及私有 main 对齐证据。

- [x] 检查 Markdown 本地链接、JSON、Mermaid 同步、原材料 10 个哈希、忽略规则、敏感信息和暂存内容；运行 `git diff --cached --check`。
- [x] 核验指定 GitHub 仓库 owner/private/main 与本地祖先一致；提交并普通推送，逐文件比较远程树/本地 blob，确认工作区干净。
- [x] 最终答复给出报告、交付索引和下一步入口，说明实际验证与真实业务验收边界。
