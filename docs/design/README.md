# B 设计入口

对话二完成概念与逻辑设计，当前均为 B 设计基线 v1.0，不代表外部签收、实际建表或真实指标通过。

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

物理设计、SQL2019 DDL 和实际建表证据属于对话三（B2），尚未交付；不以 JSON 或 Mermaid 代替物理设计。下一步见 [B2 交接](../handoff/next-stage.md)。
