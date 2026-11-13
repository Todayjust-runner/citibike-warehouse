# GitHub 交付记录

当前目标：[Todayjust-runner/citibike-warehouse](https://github.com/Todayjust-runner/citibike-warehouse)，GitHub 仓库 ID `1455379867`，必须为 private。用户在后续消息提供该地址并确认已创建，授权用此目标完成工程基础发布；取代最初的 klzyd 目标。

## 用户明确授权数据目录：B v1.2（2026-11-13）

用户本轮要求“数据目录也上传git，做好分类和命名”，覆盖此前全部数据仅本地的工程约定。本次把固定5原ZIP/3源核算CSV按raw/derived、来源和快照日期纳入既有private课程工程，数据catalog、说明、精确白名单和二进制/LF属性同步；全8文件20,321,820字节，SHA/数值未变。见[交付v1.2](../handoff/b-delivery-v1.2.md)。

发布前再次通过已授权本机Git认证/API确认账户Todayjust-runner/241897350、仓库1455379867、private=true及push权限，本地HEAD/追踪分支/远程main均726b35c163eb948bd56733d2a2ce9c2fc2dd0bde。普通提交推送，提交候选110文件，后验门槛为远程完整树/blob与HEAD一致、8数据真实字节大小一致、无LFS指针及工作区干净。不强推、不改全局身份/代理，令牌不输出或入盘。课程原件、非白名单数据和临时文件未上传；[提交检查](submission-check.md)记录数据例外及所有核验范围。

## 用户补充公开源：B v1.1（2026-11-13）

在966d774之后，按用户新授权取得官方完整五包并独立源核算；38项A数值匹配、10源测试及两次完整同输入核算通过。更新输入、报告、属性/交接、STATUS/计划及当前SHA，见[B v1.1](../handoff/b-delivery-v1.1.md)。没有SQLServer真实加载或完整ETL/页面，A原哈希/脚本仍缺。

继续使用用户指定Todayjust-runner/citibike-warehouse，本机已授权Git认证/API再次核实账户ID241897350、仓库ID1455379867、private=true、push权限及远程main=966d774a01e035643bb3b2dc439b7804b13c2b7c，与本地/追踪分支相同。普通提交/推送，令牌仅进程内使用，不改全局身份/代理、不强推。发布候选94文件，原ZIP/CSV/本地派生CSV未提交，提交检查见[检查记录](submission-check.md)。最终门槛为HEAD=private main、完整树/所有blob一致及工作区干净；提交号从Git读取，避免文件自引用。

## 对话四 B3 最终 B 交付（2026-11-13）

延续 ee2d762 基线与同一main，交付B报告3/4/5章、图源/SVG/PNG、复核矩阵、C/D交接及联合清单。修正已验证/发布来源仍可追加ODS的问题，物理B2-1.1；10 Python+50 SQL通过，业务库未部署，A附件/真实ETL/数值/展示仍未验。B交付版本与核心文件SHA清单见[最终索引](../handoff/b-delivery-v1.0.md)。

发布前GitHub连接器账户读目标返回404；沿用用户已明确指定目标及前阶段核实的本机Git认证，不更换所有者。API再次核实Todayjust-runner账户ID241897350、仓库ID1455379867、private=true、push权限及main=ee2d7620ddd450ec1207a1debdbe163f80f73bd7，与本地/追踪分支一致。认证只在进程内使用，无令牌输出或写盘，未改全局代理/身份。文件检查范围见[本轮检查](submission-check.md)。

发布采用普通提交/推送；最终复核以本文件所在提交的HEAD、远程main和完整Git树/所有blob一致、工作区干净为门槛。最新提交号用Git读取，不在提交内部自引用自身哈希。旧B0/B1/B2数量与结果保留各自时点含义，不代表当前文件总量。PNG/SVG是精选模型插图，未上传实际骑行数据或课程原件。

## 对话三 B2 物理与结构交付

本次继续同一工程/main，交付物理字典/编译清单、编号 DDL、受保护入口、配置示例、真实目录与合成行为证据，并更新阶段计划和 B3 交接。测试库实际为 CitibikeDW_B_Test；业务库未创建。10 个 Python 测试与 47 个 SQL 用例通过；默认部署无清空/重建，选定标记数据重跑保留，测试夹具不作为真实数据。见 [B2 验证](b2-validation.md)。发布前检查文件及 private/基线，发布后核对 HEAD/树/文件哈希；旧 28/45 文件数量分别是 B0/B1 历史快照，不是当前文件总量。

## 对话二 B1 设计交付

本次沿用相同仓库和 main，在基础提交之后增加概念/逻辑、三份 Mermaid 图、逻辑 JSON/字段字典、源映射、六指标检查、B→C/C→D 契约与四阶段计划。候选共 45 个工程文本文件，26 项静态检查通过；范围见 [B1 复核](b1-design-review.md)。本阶段没有数据库部署、ETL/页面或真实数据验收。提交前再次核实 private 属性及远程 main 基线，发布后比对 HEAD、树与文件哈希；最新提交号从 Git main 读取。

## 2026-11-12 实际发布核验

- 连接器读到目标描述为“数据仓库期末大作业”，默认分支 `main`，初始为 public、size=0；连接器对它只有读取权限。
- 使用本机已保存的 Git 认证调用 GitHub API `/user`，确认账户为 `Todayjust-runner` / `241897350`；该账户对目标具有 admin/push 权限。认证信息仅在进程内用于请求，未输出或写入项目文件、远程 URL。
- 上传前读取仓库分支与内容：分支为空，内容接口返回 404；没有 README 或既有提交。结合用户明确提供的地址与描述，确认这是本项目新建空仓库，不存在需接续的其他工程。
- 按用户原先的私有要求，将 `private` 设为 `true`；随后再次读取，确认 `private=true`、`visibility=private`，之后才上传工程。
- 本地 `origin` 为 `https://github.com/Todayjust-runner/citibike-warehouse.git`，`main` 跟踪 `origin/main`。首次基础提交 `0fca37c8435e9fe705911c0edc1e5e453649d44f` 已成功推送；保留原提交，不重写历史。
- 本次后续记录提交使用仓库级 `Todayjust-runner` 及其 GitHub noreply 邮箱；未更改全局 Git 身份。Git 原代理配置失效，发布命令使用与当前会话一致的临时代理参数；未更改全局代理或关闭 TLS 验证。
- 发布仅涉及经过检查的 28 个工程文本文件，未上传课程原件、实际骑行数据、数据库备份或凭据。下一阶段和证据边界保持原约定。

**状态：私有仓库已有工程基础提交，原远程阻塞已解决。** 本记录随发布说明更新；最新提交号可在 `git log -1 --oneline` 和仓库 `main` 查看。最终同步需核对本地 HEAD、远程 main 和完整文件树相同，工作区干净。

## 初始阻塞的历史

最初连接账户为 `klzyd` / `184755525`，其同名仓库读取返回 404；连接器没有建仓接口，浏览器因无法可靠识别当前 Windows URL 停止。本机另有 Todayjust-runner 账户，当时未获用户指定，因此未擅自切换。用户后续明确给出当前仓库后，依据新授权完成上述发布，详见 ADR-013/014。
