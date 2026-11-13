# 工程协作规则

- 在现有citibike-warehouse工程接续。先读[需求](docs/requirements.md)、[进度](docs/planning/STATUS.md)和[交接](docs/handoff/next-stage.md)。
- B负责模型/DDL/建表与交接，C负责ETL/查询，D负责展示。当前B已完成，具体新任务以用户后续指令为准。
- 使用SQL Server 2019/T-SQL/兼容级别150；完整字段以docs/design/下的逻辑/物理模型为准。
- 保持一条有效ride_id的事实粒度；出发/归还和起点/终点角色分开。时长精确微秒，均值/占比由分子分母重算。
- 原始数据不裁季度；未知站点/坐标不丢有效骑行；同ID同内容留一、冲突整组排除。细则在需求和源映射中维护，不在多处重复。
- 五个固定ZIP和三个源核算CSV已入Git，分类见data/README.md，身份见inputs/public-source-snapshot.json。核算结果不等于完整ETL已经实现。
- 数据库默认CitibikeDW_B_Test；业务库CitibikeDW须显式--allow-target。部署不删除数据，不改课程实验库；测试夹具只在独立测试库运行。
- 更改代码运行相关测试；文档更改检查链接和事实即可，不为文案新增测试。不再维护交付版本副本、DDL文件指纹或重复的发布SHA清单，Git保留历史。
- README讲当前项目，STATUS讲当前进度，next-stage讲下一步；需求以docs/requirements.md为统一入口。
- 课程原件保留原位；密钥、备份、日志、临时SQLite和未列入数据目录的文件不入Git。
- 远程固定为Todayjust-runner/citibike-warehouse，保持private；不改全局Git身份，不代发组员消息。
