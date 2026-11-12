# 本机环境只读核验

核验日：2026-11-12（Asia/Shanghai）。仅查连接与版本，没有建项目数据库、改兼容级别、建表、导数或运行 ETL。

```powershell
sqlcmd -S localhost -E -l 5 -W -s '|' -Q "SET NOCOUNT ON; SELECT CAST(SERVERPROPERTY('ProductVersion') AS varchar(30)) AS ProductVersion, CAST(SERVERPROPERTY('ProductLevel') AS varchar(30)) AS ProductLevel, CAST(SERVERPROPERTY('Edition') AS varchar(60)) AS Edition;"
```

实际结果：

```text
ProductVersion|ProductLevel|Edition
15.0.2000.5|RTM|Developer Edition (64-bit)
```

结论：本机 `localhost` Windows 集成认证可连接 SQL Server 2019。尚未确认团队演示实例、项目数据库名与部署权限；项目兼容级别 150 是目标决定，尚无项目库级别核验结果。引擎版本可用不等于建表验收通过。

读取 PDF 使用现有 Python/PyMuPDF，报告模板只读取段落与表格；渲染/抽取临时文件在工程外 `D:\数据仓库\tmp\citibike-foundation-review`，不进入仓库。课程两页及 A 抽查页确认文字提取与表格没有遗漏关键内容；未更改源 PDF。
