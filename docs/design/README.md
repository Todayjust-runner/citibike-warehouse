# 设计入口

B的三级设计和SQL2019测试库已完成。先读[需求说明](../requirements.md)，再按需要查下面的技术文档。

| 文档 | 用途 |
|---|---|
| [概念设计](conceptual-design.md) | 四步法、信息包和三个业务问题 |
| [逻辑设计](logical-design.md) | 总线/星型、14个关系、粒度和角色 |
| [逻辑模型](logical-model.json)、[字段字典](data-dictionary.md) | 132字段、31外键完整定义 |
| [源映射](source-to-target.md) | 13字段转换、重复/排除、血缘和覆盖 |
| [指标映射](metric-model-mapping.md) | 六指标从哪些字段计算 |
| [物理设计](physical-design.md)、[物理字典](physical-data-dictionary.md)、[物理模型](physical-model.json) | SQL类型、约束、索引与实际结构 |
| [模型图](../../diagrams/README.md) | Mermaid源和SVG/PNG |
| [真实属性](open-attributes.md) | 固定数据的实测长度/精度和剩余接入事项 |

装载见[B→C契约](../contracts/b-to-c-model-contract.md)，报告见[第3/4/5章](../report/README.md)。
