# C成果整合计划

**Goal:** 将C成果接入现有仓库的独立分支，保留提交历史并明确验收状态。

**Architecture:** main保留B基线；integration/c-etl接续C的c-etl-delivery，再提交当前说明。验收后正常合并，不改写main历史。

**Tech Stack:** Git、Python、SQL Server 2019，兼容级别150。

**Spec:** [整合记录](../../review/c-integration.md)及用户本轮整合指令。

- [x] 比较两库分支、共同基点与文件变化，确认真实C交付分支。
- [x] 接入原作者提交；执行只读数据清点、源测试、结构检查与入口检查。
- [x] 更新README、STATUS和交接，记录已发现问题，提交并推送独立分支。

本轮不执行正式ETL、不覆盖main。待C修复查询接入问题并完成联合验收后再合并。
