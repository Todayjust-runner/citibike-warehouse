# B 交付版本 v1.1：公开输入与源侧验证补充

> 历史快照：本版/旧SHA清单对应726b35c。用户后续明确要求数据目录入Git，当前分类路径及授权范围见[B v1.2](b-delivery-v1.2.md)；下方旧路径与不入Git状态按历史保留。

日期2026-11-13，依据用户“可直接获取公开数据并进一步完善项目”的补充授权。B0—B3产物继续有效，逻辑1.0 / 业务A-1.0 / 处理B1-1.0 / 物理B2-1.1均不变，本轮不需DDL修改。

## 已完成

- 完整获取官方五个202406—202410 JC ZIP，20,311,165字节；5真实骑行CSV共563874行，另5个AppleDouble元数据成员经过结构识别。全部ZIP/成员SHA、URL/UTC时间和分类固定在[快照清单](../../inputs/public-source-snapshot.json)。本地ZIP在data/raw/public-jc-20261113，不入Git。
- 新增[可重跑源核验程序](../../scripts/audit_public_source.py)及[10个小ZIP行为测试](../../tests/test_source_audit.py)。标准库/临时SQLite独立核算，两个完整运行语义摘要一致，原始和逐站/边界派生CSV只在data，不写SQLServer。
- [38项A数值逐项匹配](../evidence/a-public-comparison.json)：含563874源行、206超24h、334332骑行、216990044333000微秒、10.82分钟、242927/334332=72.66%、334331归还、净流出1、跨期10/11和未知归还1026。
- 全字段长度/时间/坐标精度适配现有物理上限，结束月关系全量成立；真实属性补入设计与报告3/4/5章。427个接受观察站点中1站多名、160站多坐标，保留确定性快照，不臆造SCD2。
- 输入清单、证据等级、决定、阶段计划和C/D交接已更新；C可直接使用固定公开快照及本地源核算对照开展ETL，无需等待公开文件本身。

## 入口

| 交付 | 当前入口 |
|---|---|
| 获取/核验范围、恢复与重跑命令 | [公开快照说明](../sources/public-snapshot-validation.md) |
| 全量剖析和真实分子分母 | [源审计JSON](../evidence/public-source-audit.json) |
| 新测试/两次核算/只读SQL状态 | [执行验证](../evidence/public-source-validation.json) |
| 报告与设计 | [第3/4/5章](../report/README.md)、[设计入口](../design/README.md) |
| C/D接续 | [B→C v1.1](b-to-c-final.md)、[B→D v1.1](b-to-d-final.md)、[联合清单](acceptance-checklist.md)、[下一步](next-stage.md) |
| 当前核心文件SHA | [v1.1清单](b-delivery-checksums-v1.1.json)，Git记录完整树 |

## 必须分开的结论

| 项目 | 当前证据 |
|---|---|
| 官方新公开快照获取/源核算 | 已完成，全文件SHA与38项数值匹配 |
| A原ZIP/CSV同字节身份 | 未确认，仍缺A原数据核验JSON |
| A两个脚本/完整逐站附件复现 | 未完成，仍缺脚本、依赖/日志和附件；不能由汇总相等推断 |
| SQLServer结构 | B2-1.1只读verify仍匹配；本轮没有写表，测试库仅种子、业务库不存在 |
| 完整ETL/DWS/ADS/API/页面与签收 | 待C/D实施和B联合验收，源侧成功不代替仓库对源 |

v1.0产物与旧SHA清单对应提交 `966d774a01e035643bb3b2dc439b7804b13c2b7c`；需要复查旧清单时读取该提交的文件，不能用旧SHA判断当前v1.1修改后的文件。B1/B2/B3实际证据JSON保留历史，不覆盖为新源结果。当前版本普通提交到既有private main，不分发原始/派生数据，不修改课程原件。
