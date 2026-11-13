# 共享单车骑行运营分析数仓系统的设计与实现

使用Citi Bike官方JC历史数据，分析骑行时段、站点借还和会员/车型差异。采用SQL Server 2019（兼容级别150）。

**当前：数据和B的设计/建表已完成，下一步由C实现ETL与查询，再由D接入展示。**

## 从这里开始

| 想了解什么 | 看哪里 |
|---|---|
| 目标、范围、六指标、分工与验收 | [需求说明](docs/requirements.md) |
| 当前进度与下一步 | [STATUS](docs/planning/STATUS.md)、[交接](docs/handoff/next-stage.md) |
| 五个原ZIP、三个核算CSV及分类 | [数据目录](data/README.md) |
| 概念/逻辑/物理模型、字段和DDL | [设计入口](docs/design/README.md) |
| C装载与D查询接口 | [契约入口](docs/contracts/b-c-d-contract.md) |
| 报告第3/4/5章 | [报告正文](docs/report/README.md) |

## 运行

Python 3.10+、Microsoft sqlcmd、Windows集成认证。默认使用本机独立测试库CitibikeDW_B_Test：

```powershell
python -X utf8 scripts/warehouse.py deploy
python -X utf8 scripts/warehouse.py verify
```

需要重新核算源数据时运行：

```powershell
python -X utf8 scripts/audit_public_source.py
```

详细参数和测试命令见[运行说明](scripts/README.md)。完整ETL和页面尚未实现。

## 数据与结果

默认分析2024年第三季度；源文件取2024年6—10月以覆盖跨期。五包共563874行，38项A数值已在固定公开快照上匹配；数仓加载后的结果仍需C对账。数据、代码和说明均在既有[私有仓库](https://github.com/Todayjust-runner/citibike-warehouse)管理，课程原件保留原位。
