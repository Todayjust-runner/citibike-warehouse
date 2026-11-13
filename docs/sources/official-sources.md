# 官方来源与字段核对

> 更新2026-11-13：本页下方HEAD/局部表头为B0历史范围。现已完整下载五个官方包并全量核验，最新见[公开快照核验](public-snapshot-validation.md)及inputs/public-source-snapshot.json；38项A数值在新快照匹配，仍不证明A原包同哈希或完整ETL。

核验日：2026-11-12。入口为 Citi Bike [System Data](https://citibikenyc.com/system-data)，其下载链接指向[官方 S3 列表](https://s3.amazonaws.com/tripdata/index.html)。官方概览列出 13 类当前骑行字段；历史版本字段另列，不应混用旧版的用户年龄、性别或 Bike ID。

官方说明会预处理短于 60 秒等部分记录，也说明大月份可能拆为多个 CSV；不能因此省略项目自身的边界检查或只读取一个 CSV。官方概览未给出 A 所用五包的完整字段长度、NULL、毫秒精度、时间偏移或按结束月归档的保证。

## 实际核验范围

- 202406-202410 五个 JC 对象均 HEAD 返回 200。文件名、URL、字节数、Last-Modified 和 ETag 见[机器可读证据](../evidence/official-object-check.json)。
- 对 202407 对象发送 `Range: bytes=0-65535`，返回 206，读取 65,536 字节；从 ZIP 首个本地文件头识别 `JC-202407-citibike-tripdata.csv` 并解压局部内容，只保存表头元数据。
- 实际表头为以下顺序的 13 列。没有保存或发布样本业务行；未下载完整 ZIP；未计算 ZIP/CSV SHA-256；未核验全成员、行数、月份归属、缺失量或指标。
- 这些是 **本次可达对象的元数据/局部表头**，未与缺失的 A 哈希比对；ETag 不等于已验证的 SHA-256。

## 字段与项目使用约定

| 源字段 | 官方字段类别 / 本项目含义 | B 设计注意 |
|---|---|---|
| ride_id | Ride ID / 骑行标识 | 字符串；粒度和重复检查，不充当用户 ID |
| rideable_type | Rideable type / 车型 | A 声称 classic_bike、electric_bike，完整枚举待数据核验 |
| started_at | Started at / 出发时间 | 无偏移语义待核验；出发事件筛选，保留原文本及精度 |
| ended_at | Ended at / 结束时间 | 归还事件独立筛选，不能附加窗口内出发限制 |
| start_station_name | Start station name / 源起点名 | 展示属性，不能当关联键 |
| start_station_id | Start station ID / 起点标识 | 字符串，允许未知，站点维度起点角色 |
| end_station_name | End station name / 源终点名 | 源文本保留，名称变化策略待定 |
| end_station_id | End station ID / 终点标识 | 字符串，允许未知，站点维度终点角色 |
| start_lat | Start latitude / 起点纬度 | 校验坐标，不因缺失删除有效骑行 |
| start_lng | Start longitude / 起点经度 | 地图准入策略和精度待定 |
| end_lat | End latitude / 终点纬度 | 经纬度有效范围与成对缺失规则待定 |
| end_lng | End Longitude / 终点经度 | 坐标不能代表轨迹或实际路程 |
| member_casual | Member or casual ride / 本次骑行类型 | member/casual/未知的记录分类；不能去重人数 |

表头已在 **7 月局部成员** 核对；含义以官方字段类别结合 A 口径解释，最后一列是设计约束。不得写成五包值域和类型剖析均已通过。

## 使用条件记录

已读取官方 [Data Sharing Policy](https://citibikenyc.com/data-sharing-policy)。政策允许在其条件下分析使用，限制以独立数据集形式再发布，并对非商业分析报告中的来源材料有约定；同时限制身份关联和暗示背书等行为。本工程只提交说明及元数据，原始和派生数据排除于 Git。此处为项目操作选择，后续使用仍需查阅原政策。

## SQL Server 官方依据

- [兼容级别说明](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level?view=sql-server-ver15)：SQL Server 2019 对应 150。
- [datetime2](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime2-transact-sql?view=sql-server-ver15)：可指定小数秒精度，不保存时区偏移；本项目至少保留源毫秒。
- [DATEDIFF_BIG](https://learn.microsoft.com/en-us/sql/t-sql/functions/datediff-big-transact-sql?view=sql-server-ver15)：返回 bigint，支持微秒；比 int 微秒差适合本项目时长中间量。

这些资料支持后续技术选择；当前未执行建表，不宣称兼容级别已在项目数据库设置。

## B1 补充核对：精确字符串身份

本阶段另查 Microsoft [字符串比较规则](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/string-comparison-assignment?view=sql-server-ver15)、[CAST/CONVERT](https://learn.microsoft.com/en-us/sql/t-sql/functions/cast-and-convert-transact-sql?view=sql-server-ver15) 和 [binary/varbinary](https://learn.microsoft.com/en-us/sql/t-sql/data-types/binary-and-varbinary-transact-sql?view=sql-server-ver15)。普通字符串等值会受到补齐尾空格的比较规则影响，字符转二进制长度不足也可能截断。因此 B1 明确定义原文与完整 UTF-16LE 身份，B2 再验证长度和无损等值实现；本次没有执行 SQL 证明物理实现已通过。

## B2 补充：物理语法与实际执行

查阅 Microsoft [CREATE TABLE](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql?view=sql-server-ver15) 的持久化计算列语法、[CREATE INDEX](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-index-transact-sql?view=sql-server-ver15) 的键宽与过滤唯一索引，以及 [sqlcmd](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility?view=sql-server-ver15) 的编码/错误退出选项。物理实现不只依赖说明页，已在本机 15.x 执行并保存 [B2 证据](../evidence/b2-validation.md)。上节“未执行”保留为 B1 时点结论，当前 B2 结构通过仍不代表真实来源/指标通过。
