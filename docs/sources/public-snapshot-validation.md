# 固定公开快照与核算

来源为Citi Bike [System Data](https://citibikenyc.com/system-data)提供的[官方S3下载](https://s3.amazonaws.com/tripdata/index.html)，使用条件见[Data Sharing Policy](https://citibikenyc.com/data-sharing-policy)。数据作为本私有课程分析工程的来源材料保存。

## 文件和范围

| 月包 | 源记录数 | 用途 |
|---|---:|---|
| 202406 | 111115 | 前边界核验 |
| 202407 | 112443 | Q3 |
| 202408 | 106451 | Q3 |
| 202409 | 115558 | Q3 |
| 202410 | 118307 | 后边界补齐 |

五ZIP已在[data/raw](../../data/raw/README.md)，共563874条。每包1个真实CSV和1个Mac附属文件；13列表头一致，所有行ended_at月份与月包相符。身份/下载时间见[inputs清单](../../inputs/public-source-snapshot.json)，文件大小/SHA见[data/catalog](../../data/catalog.json)。

原始文件在取得时已完整核验。日常源核算只对每ZIP检查一次身份，跳过__MACOSX/._附属文件，不重复哈希每个成员或解析二进制元数据头。

## 实测结果

- 接受563668、排除206（均超24小时），重复/冲突0，源行守恒。
- Q3六指标及A的38个可比项全部匹配，详见[需求中的结果表](../requirements.md)和[逐项对照](../evidence/a-public-comparison.json)。
- 时间最大小数秒3位；ID最多16、站点ID7、站名44个UTF-16单元；纬度/经度最多15/14位小数，适配现有SQL类型。
- 接受源观察有427个真实站点ID，1站多名、160站多坐标；保留确定性观察快照规则。
- 终点坐标197对缺失，五包源缺起/终点ID为3/1877；Q3未知归还1026次，均保留核算。

这些是源侧独立核算，C还需验证数仓加载结果。A原文件是否同哈希、原脚本细节可后续追溯，不影响使用本固定快照开发。

## 使用

克隆已包含数据，需要重新核算时运行：

```powershell
python -X utf8 scripts/audit_public_source.py
```

月度、逐站和跨期CSV在[data/derived](../../data/derived/README.md)，完整统计在[public-source-audit.json](../evidence/public-source-audit.json)。源脚本使用标准库和临时SQLite，不写SQLServer。参数/退出码见[运行说明](../../scripts/README.md)。
