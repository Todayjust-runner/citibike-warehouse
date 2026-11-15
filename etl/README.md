# C：ETL与查询

代码来自C的`c-etl-delivery`，已接入整合分支，当前待联合验收。接入问题见[整合记录](../docs/review/c-integration.md)。

## 执行顺序

环境：Python 3.10+、Microsoft sqlcmd、Windows集成认证。默认本机`CitibikeDW_B_Test`；先按根README部署表结构。

```powershell
# 只读清点输入，不写数据库
python -X utf8 etl/load_ods.py --dry-run
# 以下命令会装载项目测试库；先取得load_ods打印的run_id
python -X utf8 etl/load_ods.py
python -X utf8 etl/build_dims.py
python -X utf8 etl/build_facts.py --run-id <run_id>
python -X utf8 etl/build_dws.py --run-id <run_id>
python -X utf8 etl/reconcile.py --run-id <run_id>
# 对账通过后发布
python -X utf8 etl/reconcile.py --run-id <run_id> --publish
python -X utf8 etl/query_results.py --result ride_overview
python -X utf8 etl/query_results.py --result trip_trend --granularity day
```

所有装载步骤使用同一数据库和run。正式重跑、发布及五种查询尚待本机验收；先处理整合记录中的问题。D的模块导入入口目前有已知错误。

输入规则见[需求](../docs/requirements.md)及[B→C契约](../docs/contracts/b-to-c-model-contract.md)，结果字段见[C→D契约](../docs/contracts/c-to-d-query-contract.md)。[展示样例](../dashboard/sample-results)是C提供的输出，供参考。
