# 受保护的 B2 执行入口

使用 Python 3.10+ 标准库和已安装的 Microsoft sqlcmd；Windows 集成认证，不保存用户名/密码。[warehouse.py](warehouse.py) 默认 `localhost / CitibikeDW_B_Test`，从工程根运行：

```powershell
python -X utf8 scripts/warehouse.py inspect
python -X utf8 scripts/warehouse.py deploy
python -X utf8 scripts/warehouse.py verify
python -X utf8 scripts/warehouse.py boundaries
python -X utf8 -m unittest discover -s tests -p test_b2.py -v
```

全局参数放动作前，例如 `python -X utf8 scripts/warehouse.py --server localhost --database CitibikeDW_B_Test verify`。退出码：0 成功，1 验证发现漂移，2 目标拒绝/环境/SQL/部署错误。所有正常报告及受控错误为 JSON。`verify` 含完整结构，通常重定向到被忽略的 artifacts 目录；精选证据另整理到 docs/evidence。

参数还可来自 `CITIBIKE_SQL_SERVER`、`CITIBIKE_SQL_DATABASE`、`SQLCMD_PATH` 环境变量。`.env.example` 仅作参考，不自动加载 `.env`；PowerShell 可用 `$env:CITIBIKE_SQL_SERVER='localhost'`。本机使用现有 sqlcmd，不新增 pyodbc、SSAS 或分布式组件。

业务库部署必须明确执行 `python -X utf8 scripts/warehouse.py --database CitibikeDW --allow-target deploy`；**本阶段未运行此命令**。boundaries 永远只允许测试库。不要为运行测试授予更多项目外权限；当前验证账户与实例权限在环境证据中记录。

默认部署：拒绝其他数据库；拒绝现有未标记数据库；新库事务建表和种子；已匹配则无操作；有漂移停止，不自动删除/修复。没有 reset 命令。SQLcmd 输入临时文件仅含本次 SQL，并逐文件清理，不写认证信息。

完整 ETL 仍由 C 实现；A 的两个预审/复核脚本尚未收到，本入口不冒充其替代品。

## 当前物理修订 B2-1.1

B3 在既有 ODS 触发器增加验证/发布来源的 INSERT 保护，其余结构不变。10 Python + 50 SQL通过，见[B3复核](../docs/review/b3-final-review.md)。旧B2-1.0会按版本/指纹/模块漂移被拒绝；本机只对已核验空的测试库作一个触发器的受控补丁，未增加自动迁移。遇旧库需对照旧版清单另行审阅，禁止只改扩展属性或默认重建。

## 真实公开源审计（用户补充授权）

`python -X utf8 scripts/audit_public_source.py` 校验已锁定五个公开ZIP及所有成员SHA，区分真正CSV与AppleDouble，独立全量核算字段、去向和六指标。只使用Python标准库/临时SQLite，不连接或装载SQLServer。默认派生CSV在data/derived/source_audit/citibike_jc/snapshot_20261113，摘要在docs/evidence/public-source-audit.json；源核验测试为 `python -X utf8 -m unittest discover -s tests -p test_source_audit.py -v`。下载恢复、参数/退出码与证据边界见[公开快照说明](../docs/sources/public-snapshot-validation.md)。
