# 输入与证据等级

更新2026-11-13。A交付仍只有PDF；用户后续授权直接获取公开源，现已下载并完整核验新的官方JC五包。两者分开登记，不再把公开可得数据笼统标为缺失。

| 文件 | 当前用途 / 等级 |
|---|---|
| [local-materials.json](local-materials.json) | 10份课程原位材料身份，仍全部一致；不复制原件 |
| [public-source-snapshot.json](public-source-snapshot.json) | 5 ZIP、10成员SHA/分类、URL/UTC下载时间、CSV行数与输入集指纹；可用新快照 |
| [required-inputs.csv](required-inputs.csv) | 10项输入状态；公开ZIP可用，A原哈希/脚本/完整逐站附件仍缺 |
| [a-claimed-baselines.json](a-claimed-baselines.json) | A转录原数值保留；新状态为数值在公开快照匹配、A原身份未证实 |
| [实际源核算](../docs/evidence/public-source-audit.json) / [38项比较](../docs/evidence/a-public-comparison.json) | 全量剖析与精确核算，不能替代SQLServer ETL验收 |
| [旧官方对象检查](../docs/evidence/official-object-check.json) | B0 HEAD/局部表头历史，非当前核验上限 |

现有原ZIP在data/raw/public-jc-20261113，5份骑行CSV仍在ZIP内。每包另1个AppleDouble元数据，其后缀虽.csv，但经文件头/条目/对应关系验证后不进入骑行CSV计数或ODS；全部10成员仍保留SHA。实际5 CSV共563874条，60秒—24小时规则接受563668，206条超24小时排除，重复/冲突0。

源审计重复运行两次，语义结果一致，38项A可比数值匹配。仍未收到A原数据核验结果.json、两个脚本/环境/日志、全量月份/逐站基准，故不能确认下载字节等同A原包或全部处理细节相同。C可先使用本次锁定输入，不必等待公开数据本身；接到A哈希后再比身份。

[获取/重跑说明](../docs/sources/public-snapshot-validation.md)给出SHA固定的恢复命令。CSV定位按表头记录1/首数据2，多行字段按解析记录号；该定义由新核验程序明确实现，不代表已证明A原脚本相同行号规则。
