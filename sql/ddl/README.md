# B2 编号 DDL

目标 SQL Server 2019 / T-SQL / 150。按 [受保护入口](../../scripts/README.md) 执行，不手工把文件当有数据数据库的迁移或重置包。

| 顺序 | 文件 | 作用 |
|---|---|---|
| 1 | [010_schemas.sql](010_schemas.sql) | 六个分层 schema 与目标保护 |
| 2 | [020_tables.sql](020_tables.sql) | 14 表、132 字段、PK/UQ 与 52 CHECK |
| 3 | [030_foreign_keys.sql](030_foreign_keys.sql) | 31 条同 run/角色/来源外键，无级联删除 |
| 4 | [040_indexes.sql](040_indexes.sql) | current 过滤唯一、出发/归还和血缘索引 |
| 5 | [050_integrity.sql](050_integrity.sql) | 覆盖、不可改写、验证/发布门槛和事务发布过程 |
| 6 | [060_seeds.sql](060_seeds.sql) | 24 小时及车型/会员类型各 3 个固定成员；无事实数据 |

入口在目标不存在时创建受管理库，再在一个连接事务内执行以上文件。已有匹配结构直接无操作，因此不会重复执行种子。单文件中的 IF NOT EXISTS 不是完整漂移检测；直接重播 050/060 不等于受保护重跑。默认流程不包含 DROP/TRUNCATE 或清空记录，未来变更另行设计迁移。

物理设计与完整字典见 docs/design；真实执行证据见 [B2 验证](../../docs/evidence/b2-validation.md)。

当前新建定义为B2-1.1；B3只修正既有ODS触发器的冻结来源追加保护，没有新增模块。当前10 Python + 50 SQL证据见[B3复核](../../docs/review/b3-final-review.md)。旧版库不由默认入口自动升级。
