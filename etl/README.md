# C：ETL与查询

固定数据已在仓库内。本目录下一步实现：

1. 读取五包全部真实CSV，导入ODS并记录来源。
2. 按规则去重/排除，生成维度、事实和源行去向。
3. 生成两张小时汇总，与源核算对账并验证重跑。
4. 发布运行，提供五种查询结果给D。

入口：[需求说明](../docs/requirements.md)、[B→C契约](../docs/contracts/b-to-c-model-contract.md)、[验收清单](../docs/handoff/acceptance-checklist.md)。
