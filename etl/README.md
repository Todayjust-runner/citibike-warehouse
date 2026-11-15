# ETL与查询入口

所有命令在工程根目录运行。需要Python 3.10+、Microsoft sqlcmd、Windows集成认证和本机SQL Server。默认库为`CitibikeDW_B_Test`，兼容级别150。

## 1. 首次建表

```powershell
python -X utf8 scripts/warehouse.py deploy
python -X utf8 scripts/warehouse.py verify
```

## 2. 装载并发布

以下PowerShell命令会自动取得新run_id，并在同一运行内依次加工：

```powershell
$run = python -X utf8 etl/load_ods.py | ConvertFrom-Json
python -X utf8 etl/build_dims.py
python -X utf8 etl/build_facts.py --run-id $run.run_id
python -X utf8 etl/build_dws.py --run-id $run.run_id
python -X utf8 etl/reconcile.py --run-id $run.run_id --publish
```

只读清点可先用`python -X utf8 etl/load_ods.py --dry-run`。同输入重跑会复用ODS、生成新run；发布后查询只选当前run，不累加历史运行。每步成功后再执行下一步。

## 3. 查看结果

```powershell
python -X utf8 etl/query_results.py --result ride_overview
python -X utf8 etl/query_results.py --result trip_trend --granularity day
python -X utf8 etl/query_results.py --result station_flow --granularity month --station-filter 0
python -X utf8 etl/query_results.py --result type_comparison --bike-filter 2
```

五种结果：ride_overview、trip_trend、weekday_hour、station_flow、type_comparison。默认Q3；`--start`含起点、`--end`不含终点，`--granularity`支持hour/day/month。

D可从工程根目录导入：

```python
from etl.query_results import get_result
result = get_result('trip_trend', {'granularity': 'day'})
```

完整字段见[查询契约](../docs/contracts/c-to-d-query-contract.md)，数据与规则见[需求](../docs/requirements.md)。测试命令见[测试入口](../tests/README.md)，实测结论见[验收报告](../docs/review/c-acceptance.md)。

换服务器时，各ETL/查询命令传`--server`；业务库CitibikeDW需显式传`--database CitibikeDW --allow-target`。建表工具的全局参数放在deploy/verify动作之前。
