# 输入清单

| 文件 | 内容 |
|---|---|
| [public-source-snapshot.json](public-source-snapshot.json) | 固定五包URL、取得时间、ZIP/成员身份和数据路径 |
| [a-claimed-baselines.json](a-claimed-baselines.json) | A PDF的原数值及公开快照核对状态 |
| [required-inputs.csv](required-inputs.csv) | A附件和团队信息的补充事项 |
| [local-materials.json](local-materials.json) | 原位课程材料/参考书的身份与阅读范围 |

五个真实骑行CSV在ZIP内，共563874行；Mac附属文件不导入。原ZIP和三个核算CSV已随私有工程保存，分类见[data目录](../data/README.md)。现有数据可直接用于C的ETL和数仓对账。

A原哈希JSON、两个脚本和完整逐站附件尚未收到；公开快照的38项可比数值已独立匹配。这些附件可后续补充追溯，不是开发阻塞项。业务要求统一见[需求说明](../docs/requirements.md)。
