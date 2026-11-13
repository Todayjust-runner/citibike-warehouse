# B 设计入口

对话二完成概念/逻辑基线 v1.0，对话三完成物理设计，对话四复核并修订物理 B2-1.1，在独立测试库验证。不代表外部业务签收或真实指标通过。

| 文档 | 内容 / 状态 |
|---|---|
| [概念设计](conceptual-design.md) | 四步法、信息包、Q1-Q3、多维业务图，已设计 |
| [逻辑设计](logical-design.md) | 总线矩阵、一个事实的角色星型、14 个关系、治理血缘，已设计 |
| [逻辑 JSON](logical-model.json) / [字段字典](data-dictionary.md) | 132 字段、31 外键，完整逻辑定义，已设计 |
| [源映射](source-to-target.md) | 13 列、去向/排除/代表、源行守恒、覆盖证明，已设计 |
| [六指标支持](metric-model-mapping.md) | 计算、角色、分母、覆盖和未执行情境推演 |
| [属性与验收缺口](open-attributes.md) | 真实值域/精度与 A 算法差异等待确认 |
| [可编辑图](../../diagrams/README.md) | Mermaid 概念、星型、血缘图源 |
| [交接契约](../contracts/b-c-d-contract.md) | B→C 与 C→D v1.0 逻辑基线 |
| [物理设计](physical-design.md) | 类型/长度/精度、约束、索引、发布与重跑，B2 已实施 |
| [物理字段字典](physical-data-dictionary.md) / [物理 JSON](physical-model.json) | 全 132 字段及实际 SQL 编译基线，B2 已核对 |
| [B2 验证](../evidence/b2-validation.md) | 真实结构、10 个 Python 行为测试与 47 个事务回滚 SQL 用例 |

SQL2019 DDL 与执行入口已交付；业务库未部署，完整 ETL/查询还由 C 完成。B3 已完成[复核](../review/b3-final-review.md)、[报告正文](../report/README.md)与[最终交付](../handoff/b-delivery-v1.0.md)，当前10 Python + 50 SQL通过，图件已导出。下一步见 [C/D 接续](../handoff/next-stage.md)。
