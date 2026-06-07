# 交接契约协议

> 本文档定义刑事案件OS各步骤间的交接契约规范，确保上下游Skill之间信息传递的完整性和可追溯性。

---

## 核心定义

### 什么是 Handoff？

在刑事案件OS中，**handoff** 指的是一个步骤（如C2）将处理结果、判断结论和原始输入材料，按约定格式交给下一个步骤（如C3）的过程。

它不是普通的"几条提示词补充"，而是：
- 步骤之间的接口契约
- 数据流转的结构化包
- 人和机器都能读的任务交接单

### 为什么 Handoff 很重要？

如果没有 handoff，步骤之间只能靠模糊自然语言接力，会出现：
- 上下游边界不清，重复思考
- 关键原文材料在传递中丢失
- 下游只能消费结论，无法校验依据
- 很难做调试、回放、评估和自动化编排

---

## 标准 Handoff Package 结构

### 推荐骨架

````markdown
## Handoff Package

```yaml
handoff_version: "1.0"
source_skill: case-info-extract
target_skill: criminal-case-review
package_type: criminal_analysis
content_format: markdown
contains_original_materials: true
material_count: 3
```

### 1. 上游判断摘要
- 步骤：C2-案件基础信息提取
- 结论：涉嫌盗窃罪，金额约5万元
- 关键发现：
  - 被告人有前科（2019年盗窃罪）
  - 涉案金额存在争议（被害人称8万，被告人称3万）
  - 作案时间与监控视频时间吻合
- 待确认事项：涉案金额需进一步核实
- pending_review: true

### 2. 原始输入材料
#### 材料 1
```yaml
material_id: basic-info-01
material_type: court_document
title: "起诉意见书"
file_path: "案卷材料/起诉意见书.pdf"
use_mode: primary
```

#### 材料 2
```yaml
material_id: basic-info-02
material_type: evidence
title: "被告人讯问笔录（第一次）"
file_path: "案卷材料/讯问笔录-第一次.pdf"
use_mode: primary
```

### 3. 交接备注
- 缺失信息：被害人陈述待阅卷补充
- 风险提醒：涉案金额争议可能影响量刑档次
- 下一步提示：阅卷时重点关注盗窃金额的证据链
````

### 头信息字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `handoff_version` | 是 | 交接协议版本号 |
| `source_skill` | 是 | 上游步骤名称 |
| `target_skill` | 是 | 下游步骤名称 |
| `package_type` | 是 | 包类型，固定为 `criminal_analysis` |
| `content_format` | 是 | 当前固定为 `markdown` |
| `contains_original_materials` | 是 | 是否包含原始输入材料 |
| `material_count` | 是 | 原始材料数量 |

### 正文区块

**上游判断摘要**回答：
- 本步骤做了什么
- 得出什么结论
- 有哪些关键发现
- 有哪些待确认事项

**原始输入材料**回答：
- 具体依据是什么
- 原文是什么
- 文件在哪
- 哪段是主要材料

**交接备注**回答：
- 哪些信息缺失
- 哪些地方有风险
- 下游执行时需要特别注意什么

---

## 步骤间交接映射

| 上游 | 下游 | 交接内容 |
|------|------|----------|
| case-info-extract | criminal-case-review | 案件基础信息、案号、罪名、当事人信息 |
| criminal-case-review | criminal-defense-strategy | 阅卷笔录、证据分析、疑点清单 |
| criminal-defense-strategy | criminal-defense-statement | 辩护方案、辩点矩阵、主攻方向 |
| criminal-defense-strategy | criminal-non-prosecution | 辩护方案、不起诉理由 |
| criminal-case-review | criminal-meeting | 阅卷笔录、待核实问题清单 |
| criminal-case-review | criminal-trial-examination | 阅卷笔录、证据清单、质证要点 |
| criminal-defense-strategy | criminal-trial-examination | 辩护方案、发问策略 |
| criminal-defense-strategy | criminal-defense-statement | 辩护方案、辩点强度评估 |

---

## 强交接与弱交接

### 强交接

满足以下条件时，视为**强交接**：
- 有完整头信息
- 有明确的上游判断摘要
- 有至少 1 份原始输入材料
- 下游能直接开始执行

### 弱交接

满足以下情况时，视为**弱交接**：
- 只有上游结论，没有原始材料
- 没有版本信息
- 目标步骤不明确
- 材料只有模糊一句"见上文"

弱交接可以继续执行，但下游必须明确提示：
- 判断精度会受影响
- 哪些信息是推定的
- 哪些结论缺少原文支撑

---

## 设计原则

### 统一字段命名

同一语义尽量固定字段名，不要混用：
- `target_skill`
- `main_task`
- `material_id`
- `material_type`
- `file_path`

### 版本化

所有 handoff package 都应带：
- `handoff_version`

后续若字段有重大变化，通过版本号而不是自然语言备注来处理兼容问题。

---

## 变更历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-06-07 | 初始版本，定义步骤间交接契约规范 |
