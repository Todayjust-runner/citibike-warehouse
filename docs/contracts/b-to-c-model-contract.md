# B → C 建模契约 v1.0

状态：B1 逻辑基线加 B2-1.0 物理补充；**尚非 A/C 签收或真实数据验收**。业务规则 A-1.0，技术处理策略 B1-1.0，逻辑模型 1.0；B2 已在独立测试库验证，业务库未部署。C 发现真实输入不满足规则时提出差异，不为匹配 A 声明数字修数据。

## 交付与职责

B 提供[概念](../design/conceptual-design.md)、[逻辑](../design/logical-design.md)、[字段字典](../design/data-dictionary.md)、[机器可读模型](../design/logical-model.json)、[源映射](../design/source-to-target.md)、[六指标映射](../design/metric-model-mapping.md)及可编辑 Mermaid 图。完整 PK/FK 和可空性以 JSON 定义为准，Markdown/图必须保持一致。

B2 已提供 SQL Server 2019/150 物理 DDL、独立测试库和实际结构证据；业务库尚未部署。C 负责文件获取、原始导入、处理、维度/事实装载、汇总、覆盖证明、发布和真实对账；D 依据结果契约展示。B2 结构通过不等于真实指标通过。

## B2-1.0 物理补充

- [物理清单](../design/physical-model.json) / [SQL 字典](../design/physical-data-dictionary.md) 明确全部列；run_id 为 UUID，身份列为服务器持久化计算列，C 不写；源/行/事实/覆盖与标签 IDENTITY 通常由服务器分配。
- ID/标签上限 200 个 UTF-16 单元，路径 512；坐标 decimal(20,15)，原文在 ODS 大字段。C 先验证字节长和无损转换，超限停止，不裁短或先绑定成过小类型。
- 事件及覆盖时间 datetime2(7)+微秒对齐 CHECK。C 必须先证明源文本可精确表达为微秒；客户端若先舍入，数据库无法恢复原值。
- date/hour 固定属性，未知站点(当 run,0) 由 C 创建；固定种子仅小时和两标签维度。两个 DWS 物理表需与已装载 fact 精确一致，完整小时以外仍回事实精确筛选。
- 原始行和全局维度不可改写，VALIDATED/PUBLISHED 的 run 数据冻结；修改使用新 run。状态转 VALIDATED 前填全源成员、去向、覆盖与两个 DWS，再调用 `EXEC meta.usp_publish_run @run_id` 原子发布。过程内事务级应用锁协调 current；失败不清空旧 current。若在调用方事务中失败且 XACT_STATE=-1，调用方必须回滚。
- 元数据检查只能验证声明形状、关系及对账，不证明哈希、归档规则或 proof_ref 内容真实；C 仍需实际核验官方文件与六项指标。B2 的真实测试范围见验证记录。

## 输入与处理强约束

1. 按 `inputs/required-inputs.csv` 接收五个 JC ZIP、完整 CSV、A 哈希 JSON、两个复核脚本与逐站基准。原快照不可得时记录新输入身份及差异；同名下载不等于哈希匹配。
2. 每个 CSV 成员都进入 source_member/run_source，包含空成员；ODS 保留全部记录与 13 个原始字段，不先裁季度，不按 CSV 哈希跳过另一个归档中的源行。
3. 骑行事实是同 run 内通过规则的唯一 ride_id；只产生一种业务事实。源行去向覆盖全部读取量，算法及排除优先级见源映射。
4. 业务 ID/标签使用无损字符串和完整 UTF-16LE 身份；不依赖 SQL 默认大小写/尾空格比较。哈希仅可加速，不能代替实际字段一致。
5. 无偏移时间按源值分析，时长整微秒，60 秒和 24 小时包含；缺站点/坐标/车型或未知会员标签本身不删除有效骑行。
6. CSV 破损、字段数异常、读取不完整或精度无法无损表达是运行失败/发布阻塞，不擅自增加业务排除理由。失败运行不能接管 is_current。

## 装载依赖（设计顺序，当前无 ETL）

| 顺序 | 内容 | 必须满足 |
|---|---|---|
| 1 | source_member、load_run、run_source | 完整清单、输入指纹、版本/代码；RUNNING，不暴露给 D |
| 2 | ods.trip_raw | 原始不可变；源定位唯一；读取量/全成员对账 |
| 3 | 隔离加工区计算分组、去向与有效代表 | 冲突整组隔离，稳定代表；工作集不是第二张业务事实 |
| 4 | date/hour、bike/member_type、当 run station | 未知成员、精确标签、观察来源和两端日期齐备 |
| 5 | fact_trip | 代表源行 FK；全部有效输入，不限 Q3；角色关联唯一 |
| 6 | row_disposition | 接受/重复指同 run 已存在事实；排除不指事实；全源行覆盖 |
| 7 | coverage、DWS 与 ADS 查询实现 | 覆盖证明、双角色、精确窗口路由、同粒度聚合 |
| 8 | 校验后 VALIDATED，再事务发布 | 同 scope 唯一 current PUBLISHED；失败不损坏上次发布 |

FK 依赖要求先装事实再写指向它的去向表；B2 冻结实际装载/约束顺序。重复运行不能重复累加；旧运行可保留审计，消费方只选定一个 run。ODS 同来源成员可复用，已有源内容不得改写。

## 维度、守恒与发布

- date_key=YYYYMMDD，hour_key=0..23；两端分别映射，星期固定 ISO 编号。
- 站点 key=0 为每运行专用未知成员；站点 PK/FK 都含 run_id。名称与参考坐标分别按接受源观察选择，保留来源行及角色；没有 SCD2 业务有效期。
- 车型/会员类型维度保留精确原标签和缺失 key=0；代理键不可重新分配给其他标签，is_recognized 不得将新标签偷偷并入 member/casual。
- 每 run_source 读取完成；read_record_count 与 CSV 全记录数相等。N_raw = ACCEPTED + DUPLICATE_EXACT + REJECTED；N_fact = ACCEPTED。每事实一个接受代表；附属 warning 不能相加当排除量。
- 事实业务身份同 run 唯一；每个维度 join 前后行数、次数和总微秒不变，不用 DISTINCT 掩盖多匹配。
- complete 覆盖必须指向全成员/月包/输入指纹、检查代码及区间证明，不能用 min/max 或有行推断。两个角色分别证明；实际月份语义不符先修覆盖证明。
- 默认窗口出发/归还分别筛，事实允许包含窗口外骑行。is_current 原子切换与唯一性是 B2/C 的实现验收项。

## A 基准与签收边界

先对齐输入哈希、版本、精确次数/微秒、跨月源记录和完整逐站表，再比较舍入展示。A 的 334,332 次、72.66%、净流出 1 等全部保持待复现；真实来源、排除、窗口的分母不混用。

B2 负责结构验收，C 负责真实质量/重跑/六指标；A 确认业务变更。[属性清单](../design/open-attributes.md) 每项需有后续去向，不能以设计可支持替代真实已验证。
