# Version Data Directory Implementation Plan

> **For agentic workers:** 用户已明确授权数据目录上传Git，当前会话顺序完成，不重复确认。

**Goal:** 将已核验的五个原ZIP和三份源核算CSV按来源/用途/快照日期分类，纳入既有私有工程并验证远程内容。

**Architecture:** 原ZIP保留官方文件名和字节；raw与derived分层，快照日期放目录，输入身份继续由inputs清单定义。Git仅放行固定八个数据文件、目录说明及数据目录清单，其余数据/临时文件保持忽略。

**Tech Stack:** PowerShell原生文件移动、Python标准库哈希/JSON/既有源审计、Git普通对象（单ZIP小于5MB，不引入LFS）。

**Spec:** 用户“数据目录也上传git，做好分类和命名”；[固定快照](../../../inputs/public-source-snapshot.json)与[源核验](../../sources/public-snapshot-validation.md)。

## Global Constraints

- 接续现有根目录；用户本轮授权覆盖旧的“所有原始/派生数据不入Git”工程约定，仅放行本批已核验数据。
- 保持原ZIP字节、源成员身份、38项数值和物理B2-1.1不变，不部署/写入SQLServer。
- 文件移动前校验绝对源/目标均在工程data内，目标已存在则拒绝覆盖；只移动明确列出的八个文件。
- 课程原件、备份、密钥、日志、临时SQLite及未来未批准数据继续忽略；目标仓库必须private。

### Task 1: 分类与路径同步

**Files:** `data/raw/citibike_jc/snapshot_20261113/`、`data/derived/source_audit/citibike_jc/snapshot_20261113/`；更新input清单、源脚本默认输出、当前文档/AGENTS和忽略/属性规则。
**Interfaces:** 消费既有五ZIP/三CSV及SHA；产出保留字节的分类路径与可运行默认审计。

- [x] 在旧路径逐项核验8文件SHA，验证绝对路径后原生移动，不复制多份原始数据。
- [x] 同步input路径、脚本默认输出及当前README/契约；原官方ZIP文件名和三个核算CSV名称保留，说明中列出范围/粒度/字段。
- [x] 修改Git规则为精确白名单，ZIP明确二进制、CSV固定LF；其他临时/未知文件不能进入暂存。

### Task 2: 数据目录说明、身份与回归

**Files:** 新增raw/derived/快照README和`data/catalog.json`；更新执行验证与B交付v1.2、决定/STATUS/计划。
**Interfaces:** 消费新路径和原SHA；产出8文件分类清单、重跑验证和当前交付索引。

- [x] 10个既有源测试通过；在新默认路径完整审计一次，确认语义摘要与此前两次完全相同。
- [x] 校验ZIP/CSV在移动和重跑后SHA不变，CSV行数/列/总量一致；保留v1.0/1.1清单在各自历史提交核验。
- [x] 更新当前说明和状态，不把数据入Git当完整ETL/页面完成。

### Task 3: 私有Git发布

**Files:** 新版交付SHA、提交检查和GitHub发布记录。
**Interfaces:** 消费固定八数据文件与说明；产出普通提交和远程完整树一致结果。

- [x] 检查白名单/凭据/材料哈希、当前链接/JSON/暂存差异；核实private及远程基线。
- [x] 普通提交推送，逐blob核对本地/远程，确认5个ZIP+3个CSV确实入库、无临时文件且工作区干净。
