# 本地数据，不入 Git

2026-11-13已按A PDF官方入口下载五个JC月包，保留于 `data/raw/public-jc-20261113/`；共20,311,165字节。原ZIP不改写，5份骑行CSV直接在ZIP内读取，另5个AppleDouble元数据成员只登记哈希，不能当骑行CSV。完整身份见 `inputs/public-source-snapshot.json`。

源核算派生的月度/逐站/边界CSV位于 `data/audit/public-jc-20261113/`，全量临时SQLite在每次结束后只清理本次创建的文件。本地数据和派生CSV均被忽略，不上传GitHub。提交的摘要属于报告分析证据，不能替代C的SQLServer ETL/发布。

新下载快照与A原包是否同哈希仍未知。重建下载、SHA校验和审计命令见 `docs/sources/public-snapshot-validation.md`。课程原件保持父目录原位，私有仓库也不提交原始/派生数据、备份或凭据。
