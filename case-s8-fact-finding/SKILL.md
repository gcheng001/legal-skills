---
name: case-s8-fact-finding
description: 九步法S8-事实认定。结合证据和举证责任，预判法院认定结果。TRIGGER when: 用户输入"事实认定"或由case-os总控调度。
---

# case-s8-fact-finding（S8）事实认定

## 工作定位

结合证据和举证责任，预判法院认定结果，梳理事实认定逻辑链，标注真伪不明事项。

**前置条件**：S7（举证责任）完成
**必须确认**：**是**（律师必审）
**北大法宝复验**：不需要
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取S7文件

按优先级尝试读取以下路径的 S7 文件：

**原告九步法路径**（优先顺序）：
1. `intermediate/原告九步法/S7-举证责任/S7-举证责任.md`
2. `intermediate/原告九步法/S7-举证责任.md`

**被告九步法路径**（优先顺序）：
1. `intermediate/被告九步法/S7-举证责任/S7-举证责任.md`
2. `intermediate/被告九步法/S7-举证责任.md`

读取后解析 JSON frontmatter；如解析失败则尝试 Markdown 表格；如仍失败则 `s7_reference_status: unresolved`。

### 第二步：预判法院认定结果

对每个争点预判法院认定结果：

| 争点 | 举证责任 | 证据状态 | 法院认定预判 | 置信度 |
|------|----------|----------|--------------|--------|
| 争点1 | 原告 | 充分 | 支持原告 | 高 |
| 争点2 | 被告 | 不足 | 支持原告 | 中 |
| 争点3 | 原告 | 真伪不明 | 由负有举证责任的当事人承担不利后果 | 低 |

### 第三步：梳理事实认定逻辑链

```
证据A + 证据B → 事实C → 法律要件D → 认定结果E
```

### 第四步：标注真伪不明事项

真伪不明事项的结论表述必须使用：**"由负有举证责任的当事人承担不利后果"**

**禁止使用**：不利推定、承担不利后果（单独使用）、推定其败诉

| 事项 | 举证责任 | 证据状态 | 影响 |
|------|----------|----------|------|
| 事项1 | 原告 | 真伪不明 | 由负有举证责任的当事人承担不利后果 |

### 第五步：生成S8文件（JSON frontmatter + Markdown 正文）

S8 案件产物必须采用以下格式：

```json
{
  "step_id": "S8",
  "status": "pending_review",
  "case_id": "string",
  "case_name": "string",
  "generated_at": "datetime",
  "fact_findings": [
    {
      "fact_id": "S8-F001",
      "fact_content": "string",
      "preliminary_finding": "supported|not_supported|unclear|undetermined",
      "review_status": "pending_review",
      "finding_basis": "string",
      "evidence_support": [
        {"evidence_id": "string", "evidence_description": "string"}
      ],
      "related_issue": "string"
    }
  ],
  "evidence_evaluation": [
    {
      "evidence_id": "string",
      "source_evidence_ids": ["string"],
      "admissibility": {
        "preliminary_value": "admissible|conditionally_admissible|inadmissible",
        "review_status": "pending_review",
        "basis": "string"
      },
      "relevance": {
        "preliminary_value": "highly_relevant|moderately_relevant|marginally_relevant|irrelevant",
        "review_status": "pending_review",
        "basis": "string"
      },
      "probative_value": {
        "preliminary_value": "strong|moderate|weak|very_weak",
        "review_status": "pending_review",
        "basis": "string"
      },
      "weight": {
        "weight_level": "high|medium|low|none|unclear",
        "suggested_score": null,
        "review_status": "pending_review",
        "basis": "string"
      },
      "evaluation_notes": "string"
    }
  ],
  "burden_result": {
    "party_sufficient": {
      "plaintiff": {
        "preliminary_sufficiency": "sufficient|insufficient|unclear",
        "review_status": "pending_review",
        "notes": "string"
      },
      "defendant": {
        "preliminary_sufficiency": "sufficient|insufficient|unclear",
        "review_status": "pending_review",
        "notes": "string"
      }
    },
    "facts_undetermined": [
      {
        "fact_id": "string",
        "fact_content": "string",
        "burden_bearer": "plaintiff|defendant",
        "burden_rule_applied": "string",
        "consequence_statement": "由负有举证责任的当事人承担不利后果"
      }
    ],
    "burden_applied_summary": "string"
  },
  "review_required": {
    "evidence_evaluation_needs_review": true,
    "burden_result_needs_review": true,
    "facts_undetermined_needs_review": true
  },
  "references": {
    "s7_burden_allocation_ref": "string",
    "s7_judicial_disclosure_ref": "string",
    "s7_proof_resource_review_ref": "string",
    "s7_reference_status": "resolved|unresolved"
  }
}
```

保存到 `intermediate/原告九步法/S8-事实认定/S8-事实认定.md`

### 第六步：律师必审

**红线**：AI不得自主落定，结构化状态保持 `pending_review`。

展示预判结果，等用户确认。

### 第七步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S8-事实认定/S8-事实认定.md`，所有状态标记为 `predict` / `pending_review`，不得作为事实结论。

### 第八步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S8
```

---

## 红线

- ❌ **AI不得自主落定**
- ❌ 结构化状态不得自动越过 `pending_review`
- ❌ 不得使用 `confirmed` 作为 `preliminary_finding` 枚举值
- ❌ 不得使用 "不利推定" 作为真伪不明事项的结论表述
- ❌ burden_result.party_sufficient 不得使用 boolean 终局判断
- ❌ weight.suggested_score 不得作为 S9 要件归入的最终依据

---

## 枚举值规范

### fact_findings[].preliminary_finding

| 枚举值 | 说明 | 使用场景 |
|--------|------|----------|
| `supported` | 初步支持 | 证据充分，支持该事实 |
| `not_supported` | 初步不支持 | 证据不足或反驳证据充分 |
| `unclear` | 真伪不明 | 证据穷尽后仍无法判定 |
| `undetermined` | 待定 | 证据尚未穷尽或需进一步调查 |

**不得使用**：`confirmed`（AI 不得自主落定）

### evidence_evaluation 各维度

**admissibility.preliminary_value**：`admissible` / `conditionally_admissible` / `inadmissible`

**relevance.preliminary_value**：`highly_relevant` / `moderately_relevant` / `marginally_relevant` / `irrelevant`

**probative_value.preliminary_value**：`strong` / `moderate` / `weak` / `very_weak`

**weight.weight_level**：`high` / `medium` / `low` / `none` / `unclear`
- `suggested_score` 仅供辅助参考，不得作为最终权重结论

### burden_result.party_sufficient

每个当事人使用对象结构 `{preliminary_sufficiency, review_status}`：

- preliminary_sufficiency：`sufficient` / `insufficient` / `unclear`
- review_status：必须为 `pending_review`

---

## S7 引用机制

### 兼容路径（按优先级）

1. `intermediate/原告九步法/S7-举证责任/S7-举证责任.md`
2. `intermediate/原告九步法/S7-举证责任.md`
3. `intermediate/被告九步法/S7-举证责任/S7-举证责任.md`
4. `intermediate/被告九步法/S7-举证责任.md`

### 兼容格式

- JSON frontmatter（优先解析）
- Markdown 表格（JSON 解析失败时回退）

### 解析结果处理

- 解析成功：`s7_reference_status: resolved`
- 解析失败：`s7_reference_status: unresolved`，不得自动补造 S7 数据，必须在 burden_result 中标记 party_sufficient 为 unclear

---

## 输出

- `intermediate/原告九步法/S8-事实认定/S8-事实认定.md`
- `intermediate/被告九步法/S8-事实认定/S8-事实认定.md`
