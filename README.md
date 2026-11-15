# 共享单车运营分析数仓

使用Citi Bike官方JC历史数据，分析骑行时段、站点借还和会员/车型差异。技术环境：Python 3.10+、Microsoft sqlcmd、SQL Server 2019，兼容级别150。

**当前：固定快照上的B设计与C数据链路已验证；完整分析、展示、工程化和期末材料仍需完善。**

## 从哪里进入

| 要做什么 | 入口 |
|---|---|
| 理解业务、数据范围和六指标 | [需求说明](docs/requirements.md) |
| 首次建表、装载数据、查看结果 | [ETL运行入口](etl/README.md) |
| 运行测试、复查验收 | [测试入口](tests/README.md) |
| 查看本次结论与实测数值 | [C验收报告](docs/review/c-acceptance.md) |
| 中期汇报PPT与课程提纲对应 | [汇报入口](presentations/midterm/README.md) |
| 面向期末的改进方向 | [改进计划](docs/planning/final-improvement-plan.md) |
| D接入查询与下一阶段任务 | [查询契约](docs/contracts/c-to-d-query-contract.md)、[交接](docs/handoff/next-stage.md) |
| 查找数据和模型 | [数据目录](data/README.md)、[三级设计](docs/design/README.md) |
| 报告第3/4/5章 | [报告正文](docs/report/README.md) |

## 已装载后，直接看结果

在工程根目录（包含etl、scripts的目录）执行，默认读取本机CitibikeDW_B_Test中的当前已发布运行：

```powershell
python -X utf8 etl/query_results.py --result ride_overview
python -X utf8 etl/query_results.py --result trip_trend --granularity day
python -X utf8 tests/c_acceptance.py
```

目前提供命令行与Python查询入口，页面由D完成。克隆仓库会取得代码和数据；数据库需按运行入口在本机装载。

## 数据范围

五个官方ZIP覆盖2024年6—10月，共563874条原始记录；有效骑行563668条。默认分析2024年第三季度，跨期归还单独计算。固定输入和源核算CSV均已入[公开仓库](https://github.com/Todayjust-runner/citibike-warehouse)，课程原件保留原位。
