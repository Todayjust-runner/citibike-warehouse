# 物理设计 B2-1.1

逻辑1.0的14表、132字段、31外键已落实到SQL Server 2019/150，并在CitibikeDW_B_Test验证。完整字段见[物理字典](physical-data-dictionary.md)，机器可读定义见[physical-model.json](physical-model.json)。

## 分层

| schema | 内容 |
|---|---|
| meta | 来源、运行、输入成员、源行去向、时间覆盖 |
| ods | trip_raw，13列原文与源记录位置 |
| dim | 日期、小时、站点、车型、会员类型 |
| dwd | fact_trip，一运行一条有效唯一ride_id |
| dws | trip_hourly、station_hourly，两张小时汇总 |
| ads | 预留查询结果schema，C/D查询尚未实现 |

## 主要类型和键

- run_id为UUID；事实主键(run_id,trip_key)，业务唯一键(run_id,ride_id_identity)。站点PK/FK含run_id，未知站点键0。
- 源/行/事实/覆盖代理键用bigint IDENTITY，标签键用int IDENTITY；日期YYYYMMDD、小时0—23。计算身份列由服务器生成。
- 原始字段nvarchar(max)；ID/标签nvarchar(200)、路径nvarchar(512)、站名nvarchar(512)。精确身份保存完整UTF-16LE字节，区分大小写/尾空格。
- 事件时间datetime2(7)并检查整微秒；duration_us为bigint，使用DATEDIFF_BIG。DWS总微秒decimal(38,0)，计数bigint。
- 坐标decimal(20,15)，结合质量状态与经纬度范围；原文始终保留。固定五包已全量剖析适配这些类型。

## 完整性与索引

实库有14 PK、8 UQ、31 FK、52 CHECK、26索引（含PK/UQ）及17过程/触发器。它们保证角色关联、唯一骑行、60秒—24小时、未知成员、坐标对和去向一致。

出发/归还索引分别服务两套时间查询；current过滤唯一索引保证一个当前发布运行。发布前检查来源/去向和DWS对事实，事务切换current；已发布运行保持稳定，重建使用新run。

## 部署和验证

入口[warehouse.py](../../scripts/warehouse.py)按编号执行六份DDL，新库部署在一个DDL事务内完成；固定种子为小时24行、两类型各3行。已有匹配结构直接返回，不重建或清表。业务库需显式指定。

verify直接比较实际目录与物理模型，包括列/键/约束/索引/模块；不再校验发布清单或DDL文件指纹。修改结构时同时更新模型和DDL，已有库的迁移单独执行。

命令与测试见[运行说明](../../scripts/README.md)，最近结果见[验证记录](../evidence/recent-checks.md)。C下一步按[装载契约](../contracts/b-to-c-model-contract.md)实现真实ETL。
