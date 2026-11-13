# 运行说明

在工程根执行，使用Python 3.10+标准库；建表另需Microsoft sqlcmd和Windows集成认证。

## 建表与结构检查

```powershell
python -X utf8 scripts/warehouse.py inspect
python -X utf8 scripts/warehouse.py deploy
python -X utf8 scripts/warehouse.py verify
```

默认localhost/CitibikeDW_B_Test，SQL Server 2019/150。deploy在新库建表，已有结构匹配则直接返回；不删除数据。有结构差异时由开发者调整，入口不自动修复。

全局参数放动作前，如 `--server localhost --database CitibikeDW_B_Test verify`。业务库CitibikeDW需要`--allow-target`。环境变量可用CITIBIKE_SQL_SERVER、CITIBIKE_SQL_DATABASE、SQLCMD_PATH，.env.example不自动加载。

verify直接比较表/字段、键/约束、索引和过程/触发器；不再要求DDL文件或发布清单的自指纹。

## 源核算

```powershell
python -X utf8 scripts/audit_public_source.py
```

数据已在仓库内。程序对每ZIP核对一次来源身份，读取全部真实CSV并按业务规则核算，Mac元数据按目录跳过。结果CSV默认写入data/derived/source_audit/citibike_jc/snapshot_20261113，摘要写入docs/evidence/public-source-audit.json；可用`--manifest`、`--output-dir`、`--summary`改路径。它不写SQLServer。

## 测试

```powershell
python -X utf8 -m unittest discover -s tests -v
```

含10项建表行为、9项源核算测试；建表测试调用50个SQL回滚用例，仅用独立测试库。测试库已有ETL数据时先安排独立测试环境。一般文档编辑只检查链接，无需重跑全部数据。
