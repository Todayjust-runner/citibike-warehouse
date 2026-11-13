# 共享单车骑行运营分析数仓系统的设计与实现

本仓库是课程共享单车数仓项目工程。当前已完成 **B0—B3：工程基础、三级设计、DDL/结构验证、独立复核、报告与 B 最终交接**；完整 ETL、真实指标验收和展示仍未完成。本次补充已获取五个官方JC包并完成独立全量源核算，B交付更新为v1.1。详细状态以 [阶段 STATUS](docs/planning/STATUS.md) 为准。

工程基础已发布到用户指定的私有仓库 [Todayjust-runner/citibike-warehouse](https://github.com/Todayjust-runner/citibike-warehouse)，默认分支 `main`。

分析依据为 A v1.0：官方 JC 分区历史骑行，主窗口 `[2024-07-01 00:00:00, 2024-10-01 00:00:00)`，6 月与 10 月用于边界核验。JC 文件不能等同于完整纽约网络。问题为时段需求、站点借还差、会员骑行类型与车型差异。

## 先读这些文件

1. [A 交付审查](docs/review/a-delivery-review.md)：文中声明、实际核验与缺失附件影响。
2. [课程要求映射](docs/review/course-requirements.md)：课程硬要求与组内建议的区别。
3. [输入清单](inputs/README.md)：原位材料、已取得公开快照、A附件缺口与数值对照。
4. [设计入口](docs/design/README.md)、[六指标映射](docs/design/metric-model-mapping.md)、[B/C/D 契约](docs/contracts/b-c-d-contract.md)。
5. [物理设计](docs/design/physical-design.md)、[B2 验证](docs/evidence/b2-validation.md)及[执行入口](scripts/README.md)。
6. [公开快照/下载与重跑](docs/sources/public-snapshot-validation.md)、[源核算证据](docs/evidence/public-source-audit.json)。
7. [B 最终交付](docs/handoff/b-delivery-v1.1.md)、[报告正文](docs/report/README.md)、[B3 复核](docs/review/b3-final-review.md)。
8. [四阶段计划](docs/planning/b-four-conversations.md)、[决定记录](docs/decisions/README.md)、[C/D 下一步](docs/handoff/next-stage.md) 和 [AGENTS.md](AGENTS.md)。

## 角色与阶段

| 角色 | 交付职责 | 当前状态 |
|---|---|---|
| A | 立项、需求、来源、指标定义与源核算依据 | 收到PDF；公开五包已获取，A原哈希/脚本附件未收到 |
| B | 概念/逻辑/物理设计、DDL、环境方案、建表验证及交接契约 | B 交付 v1.1 完成，公开源核算38项匹配，物理 B2-1.1；外部签收/真实联合验收待做 |
| C | 原始导入、清洗、维度/事实装载、汇总查询、质量与重跑 | 待实施 |
| D | 接入真实查询的展示、筛选、多维分析、录屏 | 待实施 |

[公开快照核验](docs/sources/public-snapshot-validation.md)已全量检查563874条源记录，38项A数值全部匹配，含334332次、精确总微秒与净流出1；[逐项证据](docs/evidence/a-public-comparison.json)。这是独立源核算，A原快照同哈希、SQLServer ETL/查询与页面验收仍未完成。

## 工程目录

```text
inputs/                    原位材料哈希、缺失输入与 A 声明值
docs/review/               A/课程审查与 B3 独立复核
docs/report/               可合入报告的第 3/4/5 章 Markdown
docs/sources/              官方来源与字段核对
docs/decisions/            决定与开放问题
docs/planning/             四阶段计划和唯一详细 STATUS
docs/contracts/            B→C 建模与 C→D 查询契约
docs/design/               概念/逻辑模型、字段字典、映射与待核实属性
diagrams/                  可编辑 Mermaid、配置及 SVG/PNG 导出
docs/evidence/             有范围说明的核验证据与提交检查
docs/handoff/              下一阶段执行顺序与验收门槛
docs/superpowers/plans/    本阶段实施记录
sql/ddl/                   B2 编号结构/约束/索引/发布门槛 SQL
sql/validation/            真实目录采集与结构一致性检查
etl/                       后续 C 的完整加工链路
dashboard/                 后续 D 的展示工程
scripts/                   受保护的 SQLcmd 部署/验证入口
tests/                     标准库行为测试与事务回滚合成夹具
data/                      五个本地原ZIP和源核算CSV，均被忽略
```

设计入口列出已完成设计；各实现目录的 README 仅保存后续职责，不代表已有实现。

## 环境与接续

目标为 **SQL Server 2019，T-SQL，数据库兼容级别 150**。本机 `localhost` 版本 `15.0.2000.5`，Developer Edition。已新建并验证 `CitibikeDW_B_Test`；`CitibikeDW` 未创建，课程库未被本阶段写入。[B3 证据](docs/evidence/b3-execution-summary.json)记录 10 Python + 50 SQL 通过、目录无漂移、测试前后计数一致；B2 历史仍保留。B2-1.1 修正验证/发布来源仍可追加 ODS 的漏洞，结构/合成行为与真实数据验收分别记录。

在现有根目录接续：

```powershell
Set-Location -LiteralPath 'D:\数据仓库\期末大作业\citibike-warehouse'
git status --short
git log -3 --oneline
```

新机器先读输入清单，按公开快照说明恢复固定ZIP并验证SHA；A原哈希/脚本与课程原件仍需另取得。`inputs/local-materials.json` 中的 `../` 路径相对于仓库，克隆不会带上材料。建表/验证使用下列命令；部署默认测试库，有漂移则拒绝，不重置已有数据。

```powershell
python -X utf8 scripts/warehouse.py inspect
python -X utf8 scripts/warehouse.py deploy
python -X utf8 scripts/warehouse.py verify
python -X utf8 scripts/warehouse.py boundaries
```

前提为 Python 3.10+、已安装的 Microsoft sqlcmd 和 Windows 集成认证。参数及 `.env.example` 用法见 scripts/README；本阶段没有完整 ETL 或页面启动命令。

## 数据与材料管理

课程材料保留在父目录原位；仓库仅记录相对路径与哈希，不复制 PDF、模板、参考书或学长作业。只使用必要的工程元数据与审查结论。原始骑行数据、结果数据、数据库文件、备份、录屏和凭据不入 Git。

官方 [System Data](https://citibikenyc.com/system-data) 提供数据入口与字段分类；使用条件见 [Data Sharing Policy](https://citibikenyc.com/data-sharing-policy)。本项目按非商业课程分析处理来源材料，不另行发布独立数据集，不暗示官方背书。具体核验边界见 [官方来源记录](docs/sources/official-sources.md)。

提交前检查 `git diff --cached --check`、`git diff --cached --stat` 与 `git ls-files`；禁止使用整个 `D:\数据仓库` 作为 Git 根目录。远程交付状态见 [GitHub 记录](docs/evidence/github-delivery.md)。
