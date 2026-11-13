# 测试

```powershell
python -X utf8 -m unittest discover -s tests -v
```

- test_b2.py：10项建表行为，覆盖目标库、模型读取、实际目录、约束和重跑；其中调用50个SQL回滚用例。
- test_source_audit.py：9项小ZIP用例，覆盖重复/冲突、独立归还窗口、会员分母、精确ID/时间、Mac附属文件、错ZIP身份、多行CSV与字段适配。

建表测试使用CitibikeDW_B_Test，测试前确认没有ETL数据；源测试使用临时目录。真实五包的源对照见docs/evidence/public-source-audit.json，最近结果见docs/evidence/recent-checks.md。文档修改只做链接/内容检查。
