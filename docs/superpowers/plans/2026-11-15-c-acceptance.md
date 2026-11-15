# C验收与合并计划

**Goal:** 修复接入问题、复现完整ETL和重跑，验收通过后正常合并main。

**Architecture:** 保留C原提交，修复在integration/c-etl完成；SQL2019测试库执行实测，固定源数据和DDL不变。

**Tech Stack:** Python标准库、sqlcmd、SQL Server 2019/150。

**Spec:** [需求](../../requirements.md)、[C→D契约](../../contracts/c-to-d-query-contract.md)。

- [x] 为查询导入、默认粒度、车型和覆盖问题写失败测试，最小修复并通过回归。
- [x] 运行既有测试；执行完整ODS→维度→事实→汇总→对账发布及同输入重跑。
- [x] 检查五种查询、跨期/边界/空值，形成简短验收报告和运行测试入口。
- [x] 检查待提交内容，正常合并并推送main，核对远程提交。
