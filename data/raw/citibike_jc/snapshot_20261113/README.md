# Citi Bike JC 官方原始快照：2026-11-13

来源：[官方System Data](https://citibikenyc.com/system-data)指向的S3。原始文件按官方名称保留；每包含1个13列骑行CSV和1个经结构识别的AppleDouble元数据。CSV在ZIP内，不重复解压提交。全部10成员的哈希与下载UTC时间见[输入身份清单](../../../../inputs/public-source-snapshot.json)。

| 官方文件 | 业务结束月份 | 骑行CSV数据记录数 | 用途 |
|---|---|---:|---|
| [JC-202406-citibike-tripdata.csv.zip](JC-202406-citibike-tripdata.csv.zip) | 2024-06 | 111115 | 前边界核验 |
| [JC-202407-citibike-tripdata.csv.zip](JC-202407-citibike-tripdata.csv.zip) | 2024-07 | 112443 | Q3及边界 |
| [JC-202408-citibike-tripdata.csv.zip](JC-202408-citibike-tripdata.csv.zip) | 2024-08 | 106451 | Q3 |
| [JC-202409-citibike-tripdata.csv.zip](JC-202409-citibike-tripdata.csv.zip) | 2024-09 | 115558 | Q3及边界 |
| [JC-202410-citibike-tripdata.csv.zip](JC-202410-citibike-tripdata.csv.zip) | 2024-10 | 118307 | 后边界补齐 |

五ZIP共20311165字节、563874条源记录。下载快照ID为 `JC-202406-202410-public-20261113`；A原包同哈希仍未证实。输入集指纹保持 `0d4336292a1cf262c39cce13cce5a5bd93aef45c50f9163245b563a5391e7829`，目录调整未改变任何ZIP或源成员字节。

从工程根运行 `python -X utf8 scripts/audit_public_source.py` 会核验完整SHA与CSV成员。C只把真实骑行CSV计入source_member/ODS，不将.csv后缀AppleDouble当数据导入。范围是JC发布分区，不等同完整纽约网络。
