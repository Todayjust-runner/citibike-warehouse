# B2 真实数据库验证入口

运行：`python -X utf8 -m unittest discover -s tests -p test_b2.py -v`。先通过受保护入口部署 CitibikeDW_B_Test。使用 Python 标准库 unittest 和真实 sqlcmd，无模拟 SQL Server。

10 个测试覆盖目标白名单/显式业务开关、DDL 哈希、空 JSON、真实结构、停用 FK 检出且不自动修复、同正文 CREATE OR ALTER 等价、带合成标记的安全重跑和 50 个 SQL 行为用例（B2原47项，B3追加验证/发布来源追加拒绝及新来源可写3项）。

边界文件每例从明确标为 SYNTHETIC-B2 的隔离夹具开始，完整事务回滚；无原始/事实/运行残留。安全重跑测试临时提交一个独立 UUID 的 CREATED 标记，并只清除自己创建的标记；FK 漂移测试也在 finally 中恢复受信任状态。这些都是测试库内的专用测试流程，默认 deploy 没有数据清理动作。不要并发运行这个测试集。

本次不测试 C 的真实去重、排除算法、所有六查询或实际覆盖证明；跨月/均值/占比的完整指标验收仍由 C 后续实现。IDENTITY 在回滚测试后可能有空洞，不把它当真实业务数量。

真实 A 基准只有在输入快照核对并独立复现后才能作为已确认对照，来源为 inputs/a-claimed-baselines.json 的当前声明状态不得静默升级。
