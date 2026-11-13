# 官方来源

| 来源 | 用途 |
|---|---|
| [Citi Bike System Data](https://citibikenyc.com/system-data) | 官方下载入口、当前13类字段说明；大月包可能含多个CSV |
| [S3列表](https://s3.amazonaws.com/tripdata/index.html) | JC月包原始文件 |
| [Data Sharing Policy](https://citibikenyc.com/data-sharing-policy) | 源数据使用条件 |
| [SQL2019兼容级别](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level?view=sql-server-ver15) | compatibility level 150 |
| [datetime2](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime2-transact-sql?view=sql-server-ver15)、[DATEDIFF_BIG](https://learn.microsoft.com/en-us/sql/t-sql/functions/datediff-big-transact-sql?view=sql-server-ver15) | 无偏移事件时间与整数微秒时长 |

本项目固定取得202406—202410五个JC包，全部真实CSV已读完并核对数值，见[快照说明](public-snapshot-validation.md)。源字段含骑行ID、车型、起止时间、两端站名/ID/坐标、member_casual；完整转换见[源映射](../design/source-to-target.md)。

官方已作部分预处理，项目仍按自己的60秒—24小时分析口径核算。JC分区不代表完整纽约网络，会员标签不代表可识别用户身份。
