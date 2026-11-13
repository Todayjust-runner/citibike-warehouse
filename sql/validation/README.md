# 结构与数据检查

[010_catalog.sql](010_catalog.sql)采集实际字段、键/约束、索引和模块；warehouse.py verify直接与物理模型比较。行为用例在[boundary_cases.sql](../../tests/sql/boundary_cases.sql)，使用独立测试库并逐例回滚。

实际装载完成后，usp_assert_run_ready核对来源/去向和汇总，usp_publish_run切换已发布运行。C还需执行完整ETL和六指标对账，见[验收清单](../../docs/handoff/acceptance-checklist.md)。
