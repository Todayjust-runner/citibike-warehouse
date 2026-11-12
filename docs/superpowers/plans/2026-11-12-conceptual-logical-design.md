# B1 概念与逻辑设计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> 本次按用户授权在当前会话完成设计文档；上述模板子技能未提供，不据此阻塞或派发子代理。无数据库或 ETL 实现。

**Goal:** 完成四阶段方案中的对话二，形成 B1 可审阅模型与契约并更新阶段计划。

**Architecture:** 一个骑行事实，日期/小时/站点角色化；原始行通过每次运行的去向表关联有效事实。覆盖证据与计数分离，派生汇总不是新增业务过程。

**Tech Stack:** Markdown、Mermaid、JSON；未来 SQL Server 2019 / 150，当前不部署。

**Spec:** `docs/planning/b-four-conversations.md`，A v1.0 p3、5-7，已有需求审查及决定。

## Global Constraints

- 接续现有工程和私有仓库，不移动课程材料。
- B1 仅概念、逻辑和契约；B2 才做物理 DDL 与建表。
- 原始附件仍缺；A 数字保持待复现，不构造库存、身份或站点历史。
- 同输入全量可重建；有效事实不能预先裁为 Q3 出发集合。

## 执行清单

- [x] 读取用户方案、A 相关页、现有文件和 Kimball 四步法；确认 Git 无差异。
- [x] 完成概念图、总线矩阵与一个事实的角色化星型图。
- [x] 完成逻辑模型、字段字典、源映射、原始/去向/事实关系和覆盖证明要求。
- [x] 完成六指标映射、B→C 与 C→D 契约及属性待核实清单。
- [x] 静态复核模型/图/字段/契约一致，保存检查范围及结果。
- [x] 更新决定、STATUS、四阶段计划和 B2 交接，检查后提交并同步 private main。
