# 提交检查

每次只检查本次修改涉及的内容：

- 代码运行相关测试，文档检查链接、JSON和口径。
- 数据改动对照data/catalog；本次原ZIP和三个核算CSV均未改变。
- 暂存内容包含预期文件，不带凭据、备份、课程原件或临时SQLite。
- `git diff --cached --check`通过，再提交并推送既有private main。

不再重复生成发布SHA清单、逐历史版本重新验算或要求文档修改重跑整套数据。最近实际测试结果见[recent-checks](recent-checks.md)。
