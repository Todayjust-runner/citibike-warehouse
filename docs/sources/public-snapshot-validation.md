# 官方公开快照获取与独立核验

日期：2026-11-13。用户补充授权根据 A PDF 公开链接获取数据并完善工程。本次新快照为 `JC-202406-202410-public-20261113`，不是 A 机器上的附件副本。官方入口仍为 [System Data](https://citibikenyc.com/system-data)→[S3下载列表](https://s3.amazonaws.com/tripdata/index.html)，字段与使用政策再次核对；[政策](https://citibikenyc.com/data-sharing-policy)原文仍需遵守。用户本轮追加要求将这批原ZIP及源核算CSV纳入既有私有课程工程；本目录保留来源政策与固定八文件清单，不作为独立数据集另行发布。

## 已取得的完整文件

五个对象均完整 HTTP 200 下载，校验字节数、ZIP CRC、全部非目录成员的 SHA-256；完整下载URL、UTC时间、ZIP/成员SHA与ETag/Last-Modified记录在[快照清单](../../inputs/public-source-snapshot.json)。ETag仅作响应元数据，不代替完整SHA。

| 月包 | ZIP字节数 | 骑行CSV数 | 骑行源记录数 | 其他成员 |
|---|---:|---:|---:|---|
| 202406 | 4413867 | 1 | 111115 | 1 AppleDouble |
| 202407 | 4198201 | 1 | 112443 | 1 AppleDouble |
| 202408 | 3530848 | 1 | 106451 | 1 AppleDouble |
| 202409 | 4140046 | 1 | 115558 | 1 AppleDouble |
| 202410 | 4028203 | 1 | 118307 | 1 AppleDouble |
| 合计 | 20311165 | 5 | 563874 | 5元数据成员 |

ZIP原样保存于 `data/raw/citibike_jc/snapshot_20261113/`。5个真实骑行CSV均有同顺序13列表头，排除表头后按CSV记录计数；它们仍在ZIP内，审计不依赖另行解压。记录号为表头1、首数据2。

### AppleDouble分类对C的影响

每包还包含 `__MACOSX/._JC-....csv`，虽以.csv结尾，内容是AppleDouble元数据。程序核验路径与实际CSV对应、magic `0x00051607`、版本 `0x00020000`、目录描述和偏移长度边界，排除Data Fork条目；不是只按文件名跳过。格式依据 [RFC1740附录B/C](https://www.rfc-editor.org/rfc/rfc1740)。全部10成员仍登记哈希，只有5个真实CSV进入source_member/run_source/ODS。每ZIP的 `zip_csv_member_count=1`，不能设为2；未知额外成员或不合法sidecar阻止审计，防止漏读。

## 实际核算及设计适配

可运行程序为 [audit_public_source.py](../../scripts/audit_public_source.py)，标准库逐CSV读取，以临时SQLite进行磁盘分组。它不读取A期望数生成实际值，也不连接SQL Server。按B1-1.0原文本/身份/优先级和稳定代表核算，所有输出来自完整5个CSV；接受563668、重复0、排除206（均时长>24h），全源守恒成立。

| 属性 | 全量实测 | 对B2-1.1的影响 |
|---|---|---|
| ride_id / 两端station_id最大UTF-16单元 | 16 / 7 | 现nvarchar(200)足够本快照；不把观测长度当未来上限 |
| 车型/会员code最大长度 | 13 / 6 | classic_bike/electric_bike；member/casual，无新标签 |
| 源站名最大长度 | 44 | nvarchar(512)足够；427个接受源观察站点ID中1个有多名称 |
| 起止小数秒 | 最大3位，全部可解析且无偏移文本 | 整微秒无损；不据此证明UTC或当地时区 |
| 纬度/经度最大小数位 | 15 / 14 | decimal(20,15)足够；不需DDL修订 |
| 坐标/缺站点 | 起点坐标全有效；结束坐标197对缺失；源缺起/终点ID 3/1877 | 坐标与站点缺失分开保留，Q3归还未知1026 |
| 站点参考属性 | 160个站点出现多个有效坐标对 | 保留按运行/最近接受观察/稳定并列规则，不能把CSV末行或首坐标当权威现状 |
| ended_at月份 | 全563874行均匹配所在月包 | 本快照全扫描支持结束月归档观察；不能外推所有年份文件 |

全部非空ID/code和源站名长度、路径、时间、坐标通过当前物理装载上限预检。该结论针对原始输入可表示性，客户端绑定、站点观察选择和SQL Server实际装载仍须C验证。

## A声明的独立数值对照

[38项逐项比较](../evidence/a-public-comparison.json)全部匹配，包括5包及汇总行数、7项质量数、六指标及精确分子分母、三个月显示结果、跨月10进入/11流出、HB102和未知归还。Q3核心结果如下：

| 项目 | 本次公开源实际核算 |
|---|---:|
| M01 / M04含未知 | 334332 / 334332 |
| 总微秒 / M02平均分钟 | 216990044333000 / 10.82 |
| member / known / M03 | 242927 / 334332 / 72.66% |
| M05 / M06 | 334331 / 1 |
| 会员类型识别覆盖率 | 100%（仅针对此运行窗口） |

已做到“在新下载官方快照上独立复算并匹配A数值”；未做到“A原ZIP/CSV同哈希”“A两个脚本复现”“完整逐站A附件对账”“数仓ETL/接口/展示验收”。A哈希JSON、两个脚本/依赖/日志、完整月度/逐站基准仍未收到。不能因为38项匹配推断源字节和全部处理细节相同。

全量逐月/逐站和跨月源定位CSV位于 `data/derived/source_audit/citibike_jc/snapshot_20261113/`；原先仅提交摘要，现按用户新授权将这三份CSV随私有工程版本管理，见[data目录说明](../../data/README.md)。整理前两次和整理后一次完整审计的语义摘要相同，记录见[执行验证](../evidence/public-source-validation.json)。完整[剖析JSON](../evidence/public-source-audit.json)可定位每成员表头/行数/时间范围、字段分布和精确月分子分母。

覆盖相对于本清单列出的官方JC快照与分析规则：已完成全部真实CSV读取并观察到结束月分区；若采用“每个所选月对象完整代表该月官方发布记录”的源契约，则归还候选完整范围为 `[2024-06-01,2024-11-01)`，最长24h下出发的保守候选范围为 `[2024-06-01,2024-10-31)`，包含Q3。C仍须将清单、归档观察和此充分条件写成coverage proof_ref，并在自己的真实运行验证，不能从fact min/max推定；这不保证现实所有骑行完整。

## 本机重跑

```powershell
python -X utf8 -m unittest discover -s tests -p test_source_audit.py -v
python -X utf8 scripts/audit_public_source.py
```

默认读取inputs/public-source-snapshot.json，SHA不符拒绝；默认派生CSV在data/derived/source_audit/citibike_jc/snapshot_20261113，摘要在docs/evidence。不同输出目录/摘要可用 `--output-dir`、`--summary`。命令仅做源审计，SQL Server不写入。返回0表示核算完成且物理适配，1表示物理上限不适配，2表示输入/格式/精度等阻断。源脚本先有10个失败测试，再实现并通过；小ZIP覆盖冲突/重复、角色、未知、精度、Unicode、完整成员与错误哈希，不使用A数值当测试期望。

## 克隆与缺失文件恢复

正常克隆已包含固定五个ZIP和三份CSV，先运行源审计核对SHA。只有文件缺失时才在工程根执行以下PowerShell片段；只下载清单中五个官方URL，不覆盖现有文件。下载后必须再执行上面的全量源审计，校验所有成员。若官方对象改变，停止并登记新快照，不能改旧SHA绕过检查。

```powershell
$taskRoot = (Get-Location).Path
$snapshot = Get-Content -LiteralPath 'inputs/public-source-snapshot.json' -Raw | ConvertFrom-Json
foreach ($archive in $snapshot.archives) {
    $target = [IO.Path]::GetFullPath((Join-Path $taskRoot $archive.path_from_repo))
    $rawRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'data/raw/'))
    if (-not $target.StartsWith($rawRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside data/raw' }
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $archive.sha256) { throw 'Existing SHA mismatch' }
        continue
    }
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
    $partial = $target + '.part'
    if (Test-Path -LiteralPath $partial) { throw 'Existing partial download needs inspection' }
    Invoke-WebRequest -Uri $archive.url -OutFile $partial
    if ((Get-Item -LiteralPath $partial).Length -ne $archive.bytes) { throw 'Length mismatch' }
    if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $archive.sha256) { throw 'SHA mismatch' }
    [IO.File]::Move($partial, $target)
}
```
