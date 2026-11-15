# C成果整合记录

日期：2026-11-15。当前分支：`integration/c-etl`，状态：已接入，待联合验收。

## 分支怎么安排

保留现有`main`作为稳定基线，C成果在整合分支检查和修复，通过后再合并到`main`。仓库按用户2026-11-15确认保留公开。无需把旧main改名，也无需覆盖历史；Git可以直接追溯B交付。

来源：[Terry2480/citibike-warehouse](https://github.com/Terry2480/citibike-warehouse/tree/c-etl-delivery)。C仓库的main仍是B交付；真正新增内容在`c-etl-delivery`。

共同基点：`d7a6d6cf3eafdff17ff4ebd40a0d8bed8a9239e9`。原作者三个提交完整保留：

| 提交 | 内容 |
|---|---|
| 508af03 | 部署工具允许SQL Server 15.x及以上，仍检查兼容级别150 |
| 32cc219 | ODS、维度、事实、汇总、对账与发布脚本 |
| dbc81d7 | 五种查询模块、9份展示JSON样例和覆盖证明 |

C新增17个文件，修改1个部署工具文件；原始数据、DDL和B设计未改动。本轮只整合代码并更新说明，不修改C实现。

## 本机已经核验

- 7个ETL Python文件编译通过，9份样例JSON可解析。
- ODS只读清点通过：5个CSV、563874行，输入标识与固定快照一致。
- 原有9项源核算测试通过。
- SQL Server 2019测试库结构检查通过：14表、132字段、31外键，无结构差异。
- 本机`meta.load_run`为空。本轮没有执行正式ETL、发布运行或重跑验收。

样例中的run_id为`1C38D12F-0CBD-4A50-A347-9BF316CD47A1`，属于C提交的结果；它们和覆盖证明不代表本机已复现完整ETL。

## 合并main前要解决

| 问题 | 影响及下一步 |
|---|---|
| 项目根目录执行`from etl.query_results import get_result`报`ModuleNotFoundError: common`（已复现） | 修正包导入，使D可以按说明调用；同时保留命令行入口 |
| `type_comparison`未应用`bike_filter`（代码审查） | 与其他图表筛选不一致；修复后用同一车型逐项对账 |
| 查询只读取角色的coverage_status，没有按请求窗口核对覆盖区间（代码审查） | 超出数据范围可能显示成真实0；补充窗口覆盖判定 |
| CLI未传granularity时传入None，覆盖内部day默认值（代码审查） | 趋势/站点结果可能按月分桶；统一默认粒度并核对返回值 |

这些是本次接入检查发现的问题，不是完整C验收清单。随后在项目测试库跑全链路、对账与同输入重跑，确认后再合并。运行顺序见[ETL说明](../../etl/README.md)，阶段任务见[交接](../handoff/next-stage.md)。
