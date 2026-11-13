# B 交付版本 v1.0

> 历史快照：本版及旧SHA清单对应966d774。当前公开源补充为[B v1.1](b-delivery-v1.1.md)，下方缺口是当时状态；旧SHA须读取原提交内容验证。

交付日：2026-11-13；范围：对话一至四 B0/B1/B2/B3 的工程基础、三级设计、DDL/结构验证、报告与最终交接。内部交付已完成，**外部签收和真实业务验收未取得**。

版本组合：逻辑1.0 / 业务A-1.0 / 处理B1-1.0 / 物理B2-1.1。B v1.0 是交付文档版本，与这些数据库字段版本分别管理。Git 提交以本文件所在提交及 private main 为准，`git log -1 --oneline` 可定位；不在文件中填自身提交哈希造成循环。

| 交付项 | 入口 / 内容 |
|---|---|
| 报告3/4/5章 | [报告索引](../report/README.md)，含正文、图表、实际验证和引用 |
| 概念/逻辑/物理源 | [设计入口](../design/README.md)，14表/132字段/31FK完整定义与两级字段字典 |
| 可编辑与插图文件 | [图件索引](../../diagrams/README.md)：3份Mermaid、配置、3 SVG+3 PNG、导出身份 |
| SQL与执行 | [编号DDL](../../sql/ddl/README.md)、[入口/配置说明](../../scripts/README.md)、.env.example、目录采集与真实边界测试 |
| 独立复核/精选证据 | [B3复核](../review/b3-final-review.md)、[执行摘要](../evidence/b3-execution-summary.json)、[当前目录](../evidence/b3-catalog.json)，B2历史仍保留 |
| C/D交接 | [B→C](b-to-c-final.md)、[B→D](b-to-d-final.md)、[联合验收清单](acceptance-checklist.md)及原v1.0契约 |
| 输入/决定/状态 | [输入](../../inputs/README.md)、[决定](../decisions/README.md)、[阶段STATUS](../planning/STATUS.md)、[下一步](next-stage.md) |
| 文件身份 | [交付SHA清单](b-delivery-checksums.json)，覆盖B核心产物，排除清单自身与持续变化的STATUS/发布记录；Git保存完整树 |

B3修正已验证来源仍可追加ODS的漏洞，受控更新一个触发器；表、字段、关系和六指标口径未变。10 Python + 50 SQL回归通过，实库与清单无漂移；除固定种子外无数据，业务库未创建。未进行第二空库全新安装、真实数据性能或并发压力测试。

A原始包/全部CSV、核验JSON、两个脚本/日志、完整月度/逐站基准仍缺。字段上限充分性、月份语义、真实ETL/六指标重跑、C/D接入与应用权限继续开放。`334332`、`72.66%`、净流出`1`等仍是A声明，不能从本交付版本推断已复现。

仓库为 [Todayjust-runner/citibike-warehouse](https://github.com/Todayjust-runner/citibike-warehouse)，要求private；只提交经过检查的工程和精选证据，不含课程原件、实际骑行/派生数据、备份、录屏和凭据。C/D完成后B参与真实联合验收；最终课程Word/PPT/录屏/整包由团队继续汇总。
