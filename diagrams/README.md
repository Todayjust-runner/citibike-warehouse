# B1 可编辑模型图

- [conceptual-model.mmd](conceptual-model.mmd)：业务信息包与 Q1-Q3。
- [star-schema.mmd](star-schema.mmd)：一个骑行事实的日期/小时/站点角色与基数。
- [source-lineage.mmd](source-lineage.mmd)：原始、主去向、事实和覆盖证据的关系。

图源为 Mermaid。完整图也嵌入概念/逻辑设计 Markdown，GitHub 可直接显示。图只展示核心关系，完整字段/外键以 `docs/design/logical-model.json` 与字段字典为准；模型变更同时更新图源及 Markdown 图块。导出 SVG/PNG 供报告使用在对话四统一处理，本阶段没有宣称已导出或实际建表。
