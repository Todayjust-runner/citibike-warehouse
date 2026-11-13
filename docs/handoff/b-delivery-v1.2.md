# B 交付版本 v1.2：分类数据随工程交付

2026-11-13，依据用户“数据目录也上传git，做好分类和命名”的新指令，取代此前全部数据仅本地的工程选择。本轮只将已经核验的固定8数据文件纳入既有私有课程工程，不扩展SQLServer/ETL/页面范围。

## 数据分类与命名

| 分类 | Git目录 | 文件 |
|---|---|---|
| 官方原始快照 | data/raw/citibike_jc/snapshot_20261113 | 202406—202410五个JC ZIP，保留官方文件名及字节 |
| 源侧核算结果 | data/derived/source_audit/citibike_jc/snapshot_20261113 | monthly.csv、station-flow.csv、boundary-records.csv |
| 分类与身份 | [data/README](../../data/README.md)、[catalog.json](../../data/catalog.json) | 用途、业务范围、字段、文件字节数/SHA及目录约定 |

原始快照以取得日期分类，业务月由官方文件名/输入清单确定；派生结果以用途/数据源/快照日期分类，窗口为2024Q3。克隆即有固定数据，先校验SHA；不重复提交约123MB的解压CSV，不重打包原ZIP。5个ZIP共20311165字节，3个CSV共10655字节，总8文件20321820字节。

## 实际验证

- 八文件移动前后和新目录重跑后SHA一致；ZIP内全部成员身份及input_set_sha256不变。
- 源脚本默认路径与输入清单同步，10个源审计测试通过。新默认目录完整核算一次，与v1.1的两次结果完全一致，累计三次语义SHA `f24dc1a2f38a56849fde0360a5eab9874ecc0b7851637862f82146d60abacefe`。
- 38项A数值继续匹配，物理B2-1.1、逻辑1.0、业务A-1.0与处理B1-1.0不变，没有SQLServer写入或完整ETL/查询/展示实现。
- Git精确放行五ZIP、三CSV和说明/清单；ZIP binary、CSV UTF-8/LF，其余数据/临时SQLite/凭据/备份/课程材料仍忽略。每ZIP小于5MB，普通Git保存实际字节，不引入LFS。

## 当前入口与历史

[源核验/重跑](../sources/public-snapshot-validation.md)、[输入清单](../../inputs/public-source-snapshot.json)、[执行验证](../evidence/public-source-validation.json)、[C交接](b-to-c-final.md)、[D交接](b-to-d-final.md)、[当前SHA清单](b-delivery-checksums-v1.2.json)。原始源政策与来源保留在data说明，工程仓库保持private。

v1.1/其SHA清单对应 `726b35c163eb948bd56733d2a2ce9c2fc2dd0bde`，v1.0对应 `966d774a01e035643bb3b2dc439b7804b13c2b7c`；旧清单读取原提交内容校验。A原哈希身份/脚本、完整仓库对源与C/D签收仍未完成。旧本地空目录保留，Git不记录空目录，远程只呈现新的分类结构。
