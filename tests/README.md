# 测试入口

在工程根目录执行。

## 日常回归：不写数据库

```powershell
python -X utf8 -m unittest discover -s tests -p "test_c_*.py" -v
python -X utf8 -m unittest discover -s tests -p test_source_audit.py -v
```

前者检查ETL判定及查询入口、筛选、覆盖、空值、补零和时间边界；后者用小ZIP检查源加工口径。

## 数据装载后的验收：只读测试库

```powershell
python -X utf8 tests/c_acceptance.py
```

需先按[ETL入口](../etl/README.md)装载并发布。检查六指标、月度与逐站源对照、五种查询一致性、车型/站点筛选、跨期、部分小时和空值。默认localhost/CitibikeDW_B_Test。

## 建表测试：在ETL装载前执行

```powershell
python -X utf8 -m unittest discover -s tests -p test_b2.py -v
```

10项建表测试包含50个SQL回滚用例，使用独立测试库。已有真实ETL数据时，使用上面的只读验收入口；不要混跑建表夹具。

批量写入往返检查：`python -X utf8 tests/c_batch_acceptance.py`，仅使用连接内临时表。

本次结果见[验收报告](../docs/review/c-acceptance.md)。
