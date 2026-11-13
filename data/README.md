# 数据目录

固定数据已随私有工程保存，克隆即可取得。默认分析2024Q3，原始月包覆盖202406—202410以补跨期。

| 分类 | 路径 | 内容 |
|---|---|---|
| 原始来源 | [raw/citibike_jc/snapshot_20261113](raw/citibike_jc/snapshot_20261113/README.md) | 5个官方ZIP，563874条骑行源记录 |
| 源核算 | [derived/source_audit/citibike_jc/snapshot_20261113](derived/source_audit/citibike_jc/snapshot_20261113/README.md) | 月度、逐站、跨期3份CSV |
| 文件身份 | [catalog.json](catalog.json)、[输入清单](../inputs/public-source-snapshot.json) | 文件大小、SHA、来源和下载时间 |

命名按用途、数据源和取得日期分类，snapshot_20261113是取得日期，不是业务月份。官方ZIP保留原名/原字节，不重复提交解压CSV；Mac附属文件不作为骑行数据。

源侧CSV用于C的数仓对账，字段说明在各目录README。[源核算命令](../scripts/README.md)可重建相同结果。基本业务口径见[需求说明](../docs/requirements.md)。

来源为[Citi Bike](https://citibikenyc.com/system-data)，遵守[使用政策](https://citibikenyc.com/data-sharing-policy)。目录只保存固定8数据文件和说明；临时SQLite、日志、备份与未列明数据继续忽略。
