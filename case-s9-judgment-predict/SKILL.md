---
name: case-s9-judgment-predict
description: 九步法S9-要件归入与裁判预测。将事实归入构成要件，预测裁判结果和金额。TRIGGER when: 用户输入"裁判预测"或由case-os总控调度。
---

# case-s9-judgment-predict（S9）要件归入与裁判预测

## 工作定位

将S8事实归入S2/S4构成要件，评估请求权是否成立，预测裁判结果和金额，输出风险清单和诉讼策略建议。

**前置条件**：S8（事实认定）完成
**必须确认**：**是**（律师必审）
**北大法宝复验**：不需要
**执行后**：调用Hook脚本更新状态

---

## 输出格式：JSON frontmatter + Markdown 正文

S9输出采用**合法 JSON frontmatter + Markdown 正文**格式：
- 文件开头为 `---` 行
- 之后为合法 JSON（可被 `json.loads()` 解析）
- JSON 结束后以 `---` 行闭合
- 剩余部分为 Markdown 正文

```markdown
---
{
  "step_id": "S9",
  "status": "pending_review",
  "case_id": "...",
  ...
}
---

# S9 要件归入与裁判预测

[Markdown 正文]
```

---

## 执行流程

### 第一步：读取S2/S4/S8文件

#### S8 读取路径（按优先级尝试）

**原告S8路径**：
```
intermediate/原告九步法/S8-事实认定/S8-事实认定.md
intermediate/原告九步法/S8-事实认定.md
intermediate/原告九步法/S8-事实认定/原告S8-事实认定.md
intermediate/原告九步法/原告S8-事实认定.md
```

**被告S8路径**：
```
intermediate/被告九步法/S8-事实认定/S8-事实认定.md
intermediate/被告九步法/S8-事实认定.md
intermediate/被告九步法/S8-事实认定/被告S8-事实认定.md
intermediate/被告九步法/被告S8-事实认定.md
```

**S4 路径（原告）**：
```
intermediate/原告九步法/S4-要件分析/S4-要件分析.md
intermediate/原告九步法/S4-要件分析.md
intermediate/原告九步法/S4-要件拆解/S4-要件拆解.md
intermediate/原告九步法/S4-要件拆解.md
intermediate/原告九步法/S4-要件分析/原告S4-要件分析.md
intermediate/原告九步法/原告S4-要件分析.md
```

**S4 路径（被告）**：
```
intermediate/被告九步法/S4-要件分析/S4-要件分析.md
intermediate/被告九步法/S4-要件分析.md
intermediate/被告九步法/S4-要件拆解/S4-要件拆解.md
intermediate/被告九步法/S4-要件拆解.md
```

**S2 路径**：
```
intermediate/原告九步法/S2-请求权基础/S2-请求权基础.md
intermediate/原告九步法/S2-请求权基础.md
intermediate/原告九步法/S2-请求权基础/原告S2-请求权基础.md
intermediate/原告九步法/原告S2-请求权基础.md
```

#### S8 JSON frontmatter 解析规则

1. **优先解析 JSON frontmatter**：从 `---\n` 开始捕获，调用 `json.loads()` 解析
2. **解析失败时回退 Markdown**：提取 Markdown 正文中的表格（如 fact_findings 表格、evidence_evaluation 表格、burden_result 表格），重构为兼容结构
3. **仍失败则标记 unresolved**：
   - `s8_reference_status: "unresolved"`
   - `fact_findings: []`（空数组）
   - `evidence_evaluation: []`
   - `burden_result: {}`
   - **不得补造 S8 事实**

#### S8 引用状态记录

```json
{
  "s8_reference_status": "resolved",
  "s8_source_paths": {
    "plaintiff": "intermediate/原告九步法/S8-事实认定/S8-事实认定.md",
    "defendant": "intermediate/被告九步法/S8-事实认定/S8-事实认定.md"
  },
  "s8_read_errors": []
}
```

### 第二步：要件归入（element_imputation）

将S8事实归入S4构成要件，生成 element_imputation 数组。

#### element_imputation 对象结构

每个 element 对象必须包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `element_id` | string | 格式：S4-E###（原告要件）或 S4-D###（抗辩要件） |
| `element_source` | string | 枚举：`claim_basis` / `defense` |
| `element_description` | string | 要件原文描述 |
| `matched_fact_ids` | array of string | 匹配的 S8 fact_id 列表，如 `["S8-F001", "S8-F002"]` |
| `matching_facts` | array of string | 匹配的 S8 事实内容（含 preliminary_finding 状态） |
| `fact_match` | string | 枚举：`supported` / `not_supported` / `unclear` / `undetermined` |
| `match_level` | string | 枚举：`high` / `medium` / `low` / `unclear` / `none` |
| `gap_analysis` | string | 缺口分析，说明要件是否满足及剩余缺口 |
| `review_status` | string | 必须为 `pending_review` |
| `basis` | string | 说明判断依据，引用 S8 字段 |

#### fact_match 与 match_level 的区别

- `fact_match`：基于 S8 的 `preliminary_finding`，判断事实是否支持该要件
- `match_level`：综合 S8 的 `evidence_evaluation[].weight` 和 `fact_match`，判断匹配强度

### 第三步：结构化三段论推理（syllogistic_reasoning）

#### 字段结构

```json
{
  "syllogistic_reasoning": [
    {
      "element_id": "S4-E001",
      "major_premise": "string",
      "minor_premise": "string",
      "preliminary_conclusion": "string",
      "review_status": "pending_review"
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `element_id` | 对应 element_imputation 中的要件编号 |
| `major_premise` | 大前提（法律规范） |
| `minor_premise` | 小前提（案件事实） |
| `preliminary_conclusion` | 初步结论（待律师确认） |
| `review_status` | 必须为 `pending_review` |

### 第四步：裁判结论（judgment_conclusion）

#### judgment_conclusion 对象结构

```json
{
  "judgment_type": "preliminary",
  "plaintiff_claim": {
    "preliminary_result": "string",
    "review_status": "pending_review",
    "basis": "string"
  },
  "defendant_defense": {
    "preliminary_result": "string",
    "review_status": "pending_review",
    "basis": "string"
  },
  "amount_recommendation": {
    "preliminary_amount": 150000,
    "currency": "CNY",
    "calculation": "string",
    "review_status": "pending_review",
    "basis": "string"
  },
  "judgment_content": {
    "draft_text": "string",
    "review_status": "pending_review",
    "basis": "string"
  },
  "review_status": "pending_review",
  "predict_marker": "predict"
}
```

**核心原则**：AI不得自主落定裁判结论。所有核心结论字段必须为 `pending_review` 或 `preliminary`。

**amount_recommendation.preliminary_amount 可以为 0**，但必须带 `review_status: pending_review`，含 `currency/calculation/basis`，不得作为终局裁判金额。

#### 禁止使用

以下形态属于违规：
- 将请求权/抗辩结论字段设为 boolean 终局值（直接写 `true`/`false`）
- 将 judgment_type 设为 `confirmed`
- plaintiff_claim / defendant_defense 使用裸字符串，不加对象封装

### 第五步：风险清单（risk_assessment）

**信息来源限制**：只能基于以下输入，不得凭空生成：
1. `element_imputation`（每个 element 的 match_level / gap_analysis）
2. `S8.evidence_evaluation`（各证据的 weight / probative_value）
3. `S8.burden_result`（party_sufficient / facts_undetermined）

#### risk_assessment 字段

```json
{
  "risk_id": "S9-R001",
  "risk_type": "factual_uncertainty",
  "risk_description": "string",
  "risk_level": "medium",
  "impact": "string",
  "source": "string",
  "mitigation": "string",
  "review_status": "pending_review"
}
```

### 第六步：诉讼策略建议（strategy_suggestions）

#### strategy_suggestions 字段

```json
{
  "strategy_type": "主攻方向",
  "strategy_content": "string",
  "basis": "string",
  "review_status": "pending_review"
}
```

### 第七步：生成S9文件

输出到 `intermediate/原告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md`

### 第八步：律师必审

**红线**：AI不得自主落定，结构化状态保持 `pending_review`。

展示裁判预测和策略建议，等用户确认。

### 第九步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md`

**被告版必须包含**：
```json
{
  "defendant_version_marker": "predict"
}
```

**禁止事项**：
- ❌ 不得在被告版中使用 `judgment_type: "confirmed"`
- ❌ 不得在被告版中省略 `predict_marker`
- ❌ 不得将被告版结论与原告版等同并列

### 第十步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S9
```

---

## handoff_to_s10 规范

### 必需字段

```json
{
  "handoff_to_s10": {
    "target_step": "S10",
    "output_fields": [
      "element_imputation.element_id",
      "element_imputation.fact_match",
      "judgment_conclusion.judgment_type",
      "judgment_conclusion",
      "rationale",
      "syllogistic_reasoning"
    ],
    "purpose": "S10基于裁判结果进行八个一致质量检查",
    "s10_check_items": [
      "EC_02: 诉讼主张与基础规范一致",
      "EC_05: 认定事实与事实争点一致",
      "EC_06: 法律理由与法律争点一致",
      "EC_07: 判决主文与诉讼请求一致"
    ],
    "blocking_conditions": [
      "judgment_conclusion.review_status != pending_review 时阻断",
      "judgment_conclusion.predict_marker 缺失时阻断",
      "judgment_conclusion.judgment_content.draft_text 或 plaintiff_claim.preliminary_result 字段出现 confirmed/final/boolean 等终局落定词汇时阻断",
      "element_imputation 存在 fact_match=unclear 且无 gap_analysis 说明时阻断"
    ]
  }
}
```

### blocking_conditions 正确理解

- S9 的 `review_status` 始终保持 `pending_review`，直到律师人工确认为止
- S10 的 blocking_conditions 用于检测 S9 输出是否符合规范，而非等待状态变更

---

## 红线

- ❌ **AI不得自主落定**
- ❌ 结构化状态不得自动越过 `pending_review`
- ❌ 不得使用 `rm` 删除文件
- ❌ 不得以 `confirmed` 作为 judgment_type
- ❌ 不得使用裸 boolean `claim_supported`/`defense_established` 作为结论字段

---

## 输出

- `intermediate/原告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md`
- `intermediate/被告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md`（被告版预判）
