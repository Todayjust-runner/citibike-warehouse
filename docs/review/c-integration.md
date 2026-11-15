# C成果整合记录

来源：[Terry2480/citibike-warehouse / c-etl-delivery](https://github.com/Terry2480/citibike-warehouse/tree/c-etl-delivery)。共同基点为d7a6d6c。

| 保留的C提交 | 内容 |
|---|---|
| 508af03 | SQL Server 15.x及以上部署支持，兼容级别150 |
| 32cc219 | ODS、维度、事实、汇总与对账发布 |
| dbc81d7 | 五种查询、9份JSON样例与覆盖证明 |

成果先进入integration/c-etl，修复接入问题并验收后正常合并main；不覆盖原有历史。仓库按用户确认保持公开。

接入时发现的导入、车型筛选、覆盖和默认粒度问题已经修复。当前实测结论统一见[C验收报告](c-acceptance.md)，运行与测试见[ETL入口](../../etl/README.md)及[测试入口](../../tests/README.md)。

C原样例属于C提供的运行，继续作为格式参考；本机验收结果另存验收数据，不把样例当作本机执行证据。
