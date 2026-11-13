# 派生分析结果

目录按 `加工用途 / 数据源 / snapshot_来源取得日期 / 结果文件名` 分类。

- [source_audit / citibike_jc / snapshot_20261113](source_audit/citibike_jc/snapshot_20261113/README.md)：基于固定官方快照的独立源核算，含Q3月度、逐站、跨期记录。

这些文件是源侧验收对照，不是已发布的SQLServer DWS/ADS结果。与原始输入通过快照ID、输入集指纹、代码SHA和文件SHA关联；不得把其他运行结果直接覆盖到同一快照中。临时SQLite和未列入白名单的派生文件不入Git。
