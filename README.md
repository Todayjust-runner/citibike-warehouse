# 共享单车骑行运营分析数仓系统的设计与实现

本仓库是课程共享单车数仓项目的工程基础。当前阶段为 **B0：A 交付审查与工程初始化**；三级设计、DDL、建表验证、完整 ETL 和展示均未完成。事实、证据和待办以 [STATUS](STATUS.md) 为准。

分析依据为 A v1.0：官方 JC 分区历史骑行，主窗口 `[2024-07-01 00:00:00, 2024-10-01 00:00:00)`，6 月与 10 月用于边界核验。JC 文件不能等同于完整纽约网络。问题为时段需求、站点借还差、会员骑行类型与车型差异。

## 先读这些文件

1. [A 交付审查](docs/review/a-delivery-review.md)：文中声明、实际核验与缺失附件影响。
2. [课程要求映射](docs/review/course-requirements.md)：课程硬要求与组内建议的区别。
3. [输入清单](inputs/README.md)：原位材料、所需附件与尚未复现的 A 基准。
4. [决定记录](docs/decisions/README.md)、[B/C/D 交接契约](docs/contracts/b-c-d-contract.md)。
5. [下一阶段交接](docs/handoff/next-stage.md) 和 [AGENTS.md](AGENTS.md)。

## 角色与阶段

| 角色 | 交付职责 | 当前状态 |
|---|---|---|
| A | 立项、需求、来源、指标定义与源核算依据 | 收到 PDF；附件未收到 |
| B | 概念/逻辑/物理设计、DDL、环境方案、建表验证及交接契约 | 本阶段仅完成工程基础与约束整理 |
| C | 原始导入、清洗、维度/事实装载、汇总查询、质量与重跑 | 待实施 |
| D | 接入真实查询的展示、筛选、多维分析、录屏 | 待实施 |

`334,332` 等数值是 **A PDF 声明的核算基准，尚未复现**。官方页面与局部 CSV 表头核验不构成真实数据对账通过。

## 工程目录

```text
inputs/                    原位材料哈希、缺失输入与 A 声明值
docs/review/               A 交付审查、课程要求映射
docs/sources/              官方来源与字段核对
docs/decisions/            决定与开放问题
docs/contracts/            B/C/D 最低交接要求
docs/design/               下一阶段三级设计交付入口
docs/evidence/             有范围说明的核验证据与提交检查
docs/handoff/              下一阶段执行顺序与验收门槛
docs/superpowers/plans/    本阶段实施记录
sql/ddl/                   后续 B 的建库、分层与建表脚本
sql/validation/            后续 B 的结构及约束验证脚本
etl/                       后续 C 的完整加工链路
dashboard/                 后续 D 的展示工程
scripts/                   后续工程辅助脚本
tests/                     后续独立边界夹具与验证入口
data/                      本地数据说明；实际数据被忽略
```

目录 README 用于保存职责和准入要求，不代表已有实现。

## 环境与接续

目标为 **SQL Server 2019，T-SQL，数据库兼容级别 150**。本机只读核验连接 `localhost` 成功，版本 `15.0.2000.5`，Developer Edition；尚未创建项目数据库或执行 DDL。[环境记录](docs/evidence/environment-check.md) 提供可复查命令。

在现有根目录接续：

```powershell
Set-Location -LiteralPath 'D:\数据仓库\期末大作业\citibike-warehouse'
git status --short
git log -3 --oneline
```

新机器拉取仓库后，先阅读输入清单，再获取课程原件和 A 附件。`inputs/local-materials.json` 中的 `../` 路径相对于本仓库；远程克隆不会自动带上这些材料。当前没有 ETL、建表或页面启动命令。

## 数据与材料管理

课程材料保留在父目录原位；仓库仅记录相对路径与哈希，不复制 PDF、模板、参考书或学长作业。只使用必要的工程元数据与审查结论。原始骑行数据、结果数据、数据库文件、备份、录屏和凭据不入 Git。

官方 [System Data](https://citibikenyc.com/system-data) 提供数据入口与字段分类；使用条件见 [Data Sharing Policy](https://citibikenyc.com/data-sharing-policy)。本项目按非商业课程分析处理来源材料，不另行发布独立数据集，不暗示官方背书。具体核验边界见 [官方来源记录](docs/sources/official-sources.md)。

提交前检查 `git diff --cached --check`、`git diff --cached --stat` 与 `git ls-files`；禁止使用整个 `D:\数据仓库` 作为 Git 根目录。远程交付状态见 [GitHub 记录](docs/evidence/github-delivery.md)。
