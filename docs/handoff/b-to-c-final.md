# B → C 最终工程交接 v1.1

2026-11-13。B 已交付模型与结构，C 尚未签收或完成真实加载。工程根目录不变。版本组合：业务 A-1.0 / 处理 B1-1.0 / 逻辑 1.0 / 物理 B2-1.1；报告/打包版本 B v1.1，不把它写进 load_run.model_version。

先读[设计入口](../design/README.md)、[物理字典](../design/physical-data-dictionary.md)、[源映射](../design/source-to-target.md)、[B→C 契约](../contracts/b-to-c-model-contract.md)和[复核结论](../review/b3-final-review.md)。本页给执行依赖，不另定义一套字段。

## 接续前检查

```powershell
Set-Location -LiteralPath 'D:\数据仓库\期末大作业\citibike-warehouse'
git status --short --branch
python -X utf8 scripts/warehouse.py inspect
python -X utf8 scripts/warehouse.py verify
```

默认 localhost/CitibikeDW_B_Test；本次只在测试库验证，CitibikeDW 仍不存在。不要把本页行数当永久环境事实；已有 C 数据时不要直接运行假定空测试库的集成夹具。部署白名单、参数和业务库显式开关见[脚本说明](../../scripts/README.md)。未标记/漂移库停止，默认无修复或重建。

遇 B2-1.0：旧 main 基线为 ee2d762，缺少冻结源成员的 INSERT 保护。B3 本机仅对完全匹配旧清单、非种子表为空的测试库作受控触发器补丁，完整过程见复核/JSON；不提供对任意旧库自动升级。不能只改标记绕过目录校验，不能用 DROP 换升级。

## 当前可用输入与源侧核验

用户授权后已获取 `data/raw/public-jc-20261113/` 的五个官方ZIP，完整身份见[public-source-snapshot.json](../../inputs/public-source-snapshot.json)，input_set_sha256=`0d4336292a1cf262c39cce13cce5a5bd93aef45c50f9163245b563a5391e7829`。五CSV/563874行，源规则接受563668、排除206、重复/冲突0；38项A数值在新快照匹配，两次源核算一致。可用现有公开快照开始C工作，不再等待公开文件本身。A原哈希/脚本/全逐站附件仍缺，见[来源与恢复/重跑](../sources/public-snapshot-validation.md)。

每ZIP实际1骑行CSV+1.csv后缀AppleDouble；全部成员哈希登记，只有真实CSV进入source_member/run_source/ODS，zip_csv_member_count=1。必须验证AppleDouble文件头/描述/对应关系，不能盲按名字跳过，未知额外成员阻断。源核算月/逐站/边界CSV在data/audit/public-jc-20261113，仅本地，不上传Git；可作为同清单仓库验收对照。

当前列长/时间/坐标精度全部适配B2-1.1；427个观察站点，1站多名、160站多坐标，确定性观察策略不能省略。该源核验不证明C实际绑定、去向/维度选择、DWS/ADS实现和重跑正确，C仍需对自己的运行逐项验收。

## 输入预检必须先于绑定

1. 先使用已锁定公开快照，按[必需输入清单](../../inputs/required-inputs.csv)继续接收A原JSON、两个脚本及逐站基准。对完整本地 ZIP/CSV 求 SHA-256、列全成员（含空文件）、表头/记录数、记录取得时间与 URL。新下载若不匹配 A 原快照，单独记录差异，不能冒称补回原包。
2. CSV 使用正确解析器，严格 13 列/固定顺序；空字段为 `""`，表头为记录 1、第一数据记录 2，多行字段不能按物理行数定位。不能将损坏/未读取数据当普通业务排除。
3. 对原文本先检查 UTF-16LE 字节长与字段上限（ID/code 400 字节，路径 1024；其他列按物理字典），时间可精确表达为整微秒，坐标在 decimal(20,15) 无损；再绑定 SQL 参数。超限/不可表示停止发布并回报 B，不裁短/舍入。SQL 接到已舍入值无法补救。
4. 本清单已全扫描确认结束月观察；C换输入或装载时仍核对所有成员及归档的结束月语义、实际值域/精度和未知标签；不提前裁到 Q3。coverage 根据证据生成，不用文件名、min/max或“查无记录”代替完整性证明。

input_set_sha256 按源映射固定：成员三元数组 `[zip_sha256, member_path, csv_sha256]`，以 ZIP 小写 ASCII、路径 UTF-8 字节序排序；UTF-8 无 BOM、紧凑 JSON、ensure_ascii=false、不规范化 Unicode，最后 SHA-256。不包含取得时间。同 CSV 出现在不同 ZIP 仍保留各自源记录。

## 装载表、键与顺序

| 顺序 | C 加载/使用的表 | 键与注意事项 |
|---|---|---|
| 1 | meta.source_member | 服务器 source_member_id；ZIP+成员路径精确唯一；完整哈希/CSV数量/表头/记录数不可改写，inventory_verified 仅0→1 |
| 2 | meta.load_run、meta.run_source | C 生成新 UUID、版本/代码/输入指纹，CREATED→RUNNING；逐成员登记，包含空成员 |
| 3 | ods.trip_raw | 服务器 source_row_id；成员+CSV记录号唯一，13原文/raw_values一致；同来源复用，不反复插入 |
| 4 | 加工工作区 | 按精确 ID 分组、13 原文本比较、固定优先级和稳定代表；工作区不成为第二张业务事实 |
| 5 | dim.date/hour、dim.bike_type/member_type、dim.station | 小时/两标签已有种子；补两端日期及新标签；每 run 创建未知站点0，站点键由C分配，观察来源在ODS已存在 |
| 6 | dwd.fact_trip | 服务器 trip_key；run+ride_id_identity唯一；代表源行、起终角色及质量；覆盖全部有效输入 |
| 7 | meta.row_disposition | run+source_row_id唯一；接受/重复必须指已存在同run事实及代表；排除不指事实 |
| 8 | meta.coverage、dws.trip_hourly、dws.station_hourly | 双角色证据；两 DWS 按冻结粒度从事实精确派生；站点借还两侧独立汇总 |
| 9 | 真正质量/指标查询与发布 | 自检/就绪检查→VALIDATED→usp_publish_run；发布前完成真实验收，不把过程形状校验当真实证明 |

循环依赖的处理：站点观察源 FK 指 ODS，先建站点再建事实，后建去向；“观察来自同 run ACCEPTED 代表”的校验在 VALIDATED 门槛执行。所有精确身份计算列由服务器生成，C 不 INSERT/UPDATE；IDENTITY 不自行重排，不保证连续。站点键、日期/小时键由 C 按定义赋值。

## 加工、守恒与发布约束

- 仅空/ASCII空白 ID 按缺失；非空不 trim/casefold。冲突组全隔离；无效同内容组全 REJECTED；有效同内容组1 ACCEPTED，其余 DUPLICATE_EXACT。具体优先级和代表排序不得用数据库默认文本序替代。
- `读取量=ACCEPTED+DUPLICATE_EXACT+REJECTED`、`事实量=ACCEPTED`，范围是全部选定成员。核验 CSV记录号/13命名列与raw_values逐项一致、排除原因真实、重复确实同内容；数据库门槛不逐项证明这些语义。
- 日期/小时/站点分别按两端映射。站点0不删除事实，坐标问题不删有效骑行；站名/坐标选择按确定性观察策略，不伪造SCD2。
- COUNT_BIG 计数，原子微秒用 bigint，SUM 前转换 decimal(38,0)；均值/占比最后由精确分子分母计算。M05 独立归还窗口，M06 聚合后键并集。部分小时回事实，不取整请求窗口。
- 就绪过程检查读取/清单/去向/代表/覆盖声明/DWS相容，不证明内容哈希或 proof_ref。C 完成真实检查后设置 finished_at_utc 并进入 VALIDATED，再 `EXEC meta.usp_publish_run @run_id=...`。完整 ETL/ADS 不在 B 中实现。
- 验证/发布后 run 数据冻结；B2-1.1 还禁止向其来源追加 ODS。新构建使用新 UUID，已完整来源可复用。失败构建不接管 current，不重新累加旧事实；在外部事务调用发布失败且 XACT_STATE=-1 时由调用方回滚。
- 单次查询固定一个 PUBLISHED run；缓存也含 run/版本/筛选。团队应用账号和业务部署方案另行确认，不能沿用 sysadmin 作为页面账号。

## C 的完成门槛

交付可运行 ETL/依赖说明、输入身份与全成员日志、无损剖析、全源去向/质量、同输入重跑差异、覆盖证明、事实与两汇总守恒、五种查询输出，以及[联合验收清单](acceptance-checklist.md)证据。与 A 基准先比完整哈希/规则和精确整数，再比舍入显示；不匹配开差异单，不为凑数修改数据。

共享工程只提交代码和精选元数据；数据包、派生数据、课程原件、机器日志、连接秘密与备份不提交。A/C/D 外部签收尚未取得，后续在 STATUS 逐项记录实际证据。
