# 工程基础待提交检查

检查日：2026-11-12（Asia/Shanghai）。检查范围为本工程内候选 Git 文件，课程原件仍位于父目录；本记录不属于真实骑行数据验收。

候选内容为 README、AGENTS、忽略/换行规则、材料/输入/声明基准清单、审查/来源/决定/契约/交接与证据文档、目录职责说明和 STATUS。本阶段没有业务代码、DDL、ETL、网页或实际数据。

## 检查结果

文件检查结果（候选 28 个文本文件；3 个 JSON，1 个输入 CSV）：

- UTF-8 可读取，Markdown 本地链接目标存在，JSON/CSV 可解析；CSV 共 10 项输入记录。
- 10 份原位材料的字节数和 SHA-256 复核一致，未复制或修改原件。
- 18 项忽略探针覆盖原始/派生数据、归档、PDF、备份、密钥与环境文件；工程文档、输入 CSV、示例配置名及未来 SQL 路径保留。
- 逐项候选文件检查只包含 Markdown、JSON、CSV 和 Git 规则；没有实际数据、课程原件、数据库备份、二进制输出或个人学号。
- 常见 GitHub/AWS 凭据、私钥、硬编码口令与学号模式检查未发现命中；同时人工核对清单及本次文件内容。模式扫描不能证明不存在一切形式敏感信息。
- A 转录值的文件总和、月骑行数总和和站点差值内部算术一致；这不是实际输入数据的行数或指标复现。
- 首次检查发现 3 个 JSON 使用 CRLF，已统一为 LF；最终检查在修正后执行。

`git diff --cached --check` 通过；暂存清单共 28 个文件，逐项确认与上述范围一致。本地提交形成后可用 `git log -1 --oneline` 读取提交号。GitHub 远程创建与推送未完成，原因单列于 [远程记录](github-delivery.md)。

## 复查命令

在工程根目录使用：

```powershell
git status --short
git diff --cached --check
git diff --cached --stat
git ls-files
git check-ignore --no-index data/raw/probe.csv .env probe.bak course.pdf archive.zip
```

最终检查应包括 UTF-8/换行、JSON/CSV 可解析、Markdown 相对链接、原位材料哈希、候选文件类型/大小、凭据模式与个人信息、忽略规则和实际暂存差异。只比较 PDF 声明值内部算术不能算作源数据复现。
