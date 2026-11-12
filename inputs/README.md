# 输入与证据等级

核对日期：2026-11-12（Asia/Shanghai）。工程初始不存在；父目录课程材料原位保留。当前收到的 A 交付仅 PDF。

| 文件 | 用途 | 使用限制 |
|---|---|---|
| [local-materials.json](local-materials.json) | 10 份本地材料路径、字节数、SHA-256、实际阅读范围 | 路径相对仓库；课程/书籍本体未入库 |
| [required-inputs.csv](required-inputs.csv) | 必要附件、状态、设计及验收影响、补齐责任 | `missing` 表示当前未收到，不能推断文件不存在于 A 机器 |
| [a-claimed-baselines.json](a-claimed-baselines.json) | 从 PDF 逐项转录的核算声明 | `a_claimed_not_reproduced`，仅供后续对照，不能当实际运行结果 |
| [官方对象检查](../docs/evidence/official-object-check.json) | 五个月 HEAD 元数据和 7 月局部表头 | 无完整包哈希、CSV 行数或基准复现 |

A 声明的预计本地输入路径为 `data/raw/citibike_jc_2024Q3/`，涵盖 202406-202410 五份 JC ZIP。此目录名并不说明只存 Q3 文件。当前未创建或填入数据。新增输入按清单接收，不把整份 A PDF 拆出的数值冒充附件。

附件到位时由 C 建立独立的源文件清单，至少包括 ZIP 下载 URL/日期/字节数/SHA-256、所有 CSV 成员名及 SHA-256、表头、数据记录数（排除表头）、起止时间范围与精度、各文件月份覆盖结论。先比对 A 的哈希，再决定是否仍属于口径 v1.0 的同一快照；不匹配则记录差异与版本。

源行定位中 A 的“CSV 实际行号”尚需澄清：建议固定表头为第 1 条 CSV 记录、首条数据为第 2 条，另保留需要时的物理行范围。该建议未冻结为已验证的 A 附件实现。
