# B2 结构与一致性验证

[010_catalog.sql](010_catalog.sql) 只读采集真实 schemas、字段/精度/NULL/计算/IDENTITY、PK/UQ/FK/CHECK、索引状态及模块正文；`warehouse.py verify` 与物理清单和数据库管理标记/版本比对。禁用或不受信任的约束、缺字段、变更定义均是漂移，默认部署不会自动修复。

行为测试在 [tests/sql/boundary_cases.sql](../../tests/sql/boundary_cases.sql)，只允许 CitibikeDW_B_Test，逐例完整回滚。测试包括错误输入实际被 SQL Server 拒绝、正例保留精度与未知、覆盖/发布/冻结、失败发布和安全切换。

`meta.usp_assert_run_ready` 是已经装载后的相容性门槛，`meta.usp_publish_run` 负责原子元数据切换；两者不获取文件、不清洗、不生成事实，不能替代 C 的完整 ETL 或真实源证明。当前结构通过不等于 A 指标通过。
