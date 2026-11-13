# SQL2019 DDL顺序

目标 SQL Server 2019 / T-SQL / 150。按 [运行入口](../../scripts/README.md) 执行，不手工把文件当有数据数据库的迁移或重置包。

| 顺序 | 文件 | 作用 |
|---|---|---|
| 1 | [010_schemas.sql](010_schemas.sql) | 六个分层 schema 与目标保护 |
| 2 | [020_tables.sql](020_tables.sql) | 14 表、132 字段、PK/UQ 与 52 CHECK |
| 3 | [030_foreign_keys.sql](030_foreign_keys.sql) | 31 条同 run/角色/来源外键，无级联删除 |
| 4 | [040_indexes.sql](040_indexes.sql) | current 过滤唯一、出发/归还和血缘索引 |
| 5 | [050_integrity.sql](050_integrity.sql) | 覆盖、不可改写、验证/发布门槛和事务发布过程 |
| 6 | [060_seeds.sql](060_seeds.sql) | 24 小时及车型/会员类型各 3 个固定成员；无事实数据 |

通过warehouse.py部署：新库按以上顺序建表，已有匹配结构直接返回，不清空数据。结构变更单独安排迁移。

类型与字段见[物理设计](../../docs/design/physical-design.md)，最近结果见[验证记录](../../docs/evidence/recent-checks.md)。
