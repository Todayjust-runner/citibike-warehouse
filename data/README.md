# 课程工程数据目录

用户2026-11-13明确要求数据目录也上传Git。本目录现将固定五个官方ZIP和三份对应源核算CSV纳入既有私有课程工程；数据按用途、来源和取得日期分类。原始文件保留官方名称和字节，不重复提交解压CSV。

```text
data/
  catalog.json                                  八个数据文件分类、字节数及SHA
  raw/
    citibike_jc/
      snapshot_20261113/                         202406—202410五个官方ZIP
  derived/
    source_audit/
      citibike_jc/
        snapshot_20261113/                       monthly / station-flow / boundary-records CSV
```

- [原始来源目录](raw/README.md)：20,311,165字节、563874源记录，ZIP内含5真实CSV及5个AppleDouble元数据。
- [派生核算目录](derived/README.md)：三份Q3源侧对照CSV，共10655字节；不是SQLServer DWS/ADS已发布结果。
- [完整文件清单](catalog.json)与[输入身份](../inputs/public-source-snapshot.json)：目录移动不改变文件SHA、输入集指纹或38项数值。
- [重跑说明](../docs/sources/public-snapshot-validation.md)：克隆后数据已经在对应目录，先校验SHA即可运行；官方恢复下载仅供文件缺失时使用。

命名规则：`raw/<source>/snapshot_YYYYMMDD/<official_filename>`；`derived/<purpose>/<source>/snapshot_YYYYMMDD/<result_name>`。快照日期是取得日期，业务月份和查询窗口在各目录README/输入清单中明确。原ZIP官方名不改，派生名使用小写英文和连字符。

数据仅作为本非商业课程分析工程的来源及核算材料，保留[Citi Bike来源](https://citibikenyc.com/system-data)与[Data Sharing Policy](https://citibikenyc.com/data-sharing-policy)，源许可不因放入工程而改变。仓库保持private。Git白名单只放行本批8个数据文件和说明/清单；课程原件、备份、凭据、日志、临时SQLite及其他未列明数据仍忽略。
