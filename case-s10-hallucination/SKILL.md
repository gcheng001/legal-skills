---
name: case-s10-hallucination
description: '九步法S10-幻觉校验和八个一致。法条幻觉校验 + 八个一致质量检查，发现幻觉自动阻断。TRIGGER when: 用户输入"幻觉校验"或由case-os总控调度。'
---

# case-s10-hallucination（S10）幻觉校验和八个一致

## 工作定位

独立校验S1-S9中所有法条引用，三层校验确认法条存在且内容匹配，发现幻觉自动阻断。同时执行八个一致质量检查，评估裁判文书质量。

**触发条件**：S1-S9完成后、FINAL前必须执行；无法条引用时记录“无引用”，仍执行八个一致和 blocking_result 门禁
**必须确认**：自动阻断
**执行后**：调用Hook脚本更新状态
**输出格式**：JSON frontmatter + Markdown 正文（JSON frontmatter 包含 eight_consistency_check 对象）

---

## S10 读取 S9 的多路径规范

S10 执行前需读取 S9 输出，按以下优先级尝试：

**原告 S9 路径（按优先级）**：
1. `intermediate/原告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md`
2. `intermediate/原告九步法/S9-要件归入与裁判预测.md`
3. `intermediate/原告九步法/S9-要件归入.md`

**被告 S9 路径（按优先级）**：
1. `intermediate/被告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md`
2. `intermediate/被告九步法/S9-要件归入与裁判预测.md`

**读取流程**：
1. 优先解析 JSON frontmatter（`^---\n(.*?)\n---\n` 匹配后 `json.loads()`）
2. 失败则回退 Markdown 正文提取，仍失败标记 `s9_consumption_check.s9_read_status = "unresolved"` 并 **CRITICAL 阻断**进入 FINAL
3. 不得补造 S9 结论

**S9→S10 字段映射（四个关键 EC）**：

| EC | S9 来源字段 | 用途 |
|----|------------|------|
| EC_02 | `element_imputation[].element_id` + `element_imputation[].fact_match` + S4/S2 构成要件 | 诉讼主张与基础规范一致 |
| EC_05 | `element_imputation[].matched_fact_ids` + S8.fact_findings | 认定事实与事实争点一致 |
| EC_06 | `rationale` + `syllogistic_reasoning[]` + `element_imputation[].gap_analysis` | 法律理由与法律争点一致 |
| EC_07 | `S1.fixed_claims` + `judgment_conclusion.judgment_content.draft_text` + `amount_recommendation` | 判决主文与诉讼请求一致 |

**阻断条件**：
- S9 unresolved → CRITICAL 阻断
- `predict_marker` 缺失 → CRITICAL 阻断
- `finalization_language_detected` (含 `confirmed`/`final`/`定论`/`胜诉`/`败诉`) → CRITICAL 阻断
- EC_02/EC_05/EC_06/EC_07 任一不合格 → CRITICAL 阻断

**S10 守门员原则**：S10 可以阻断进入 FINAL，但不得修改 S9 的 `pending_review`/`predict_marker` 或任何 S9 结论字段。

---

## 触发判断

扫描 intermediate/原告九步法/ 下所有已生成的 .md 文件
→ 检测是否包含法条引用模式（如"第X条""《XXX法》""依据XX规定"）
→ 有引用 → 触发 S10，执行法条校验和八个一致检查
→ 无引用 → 仍触发 S10，但法条校验记录为"无引用"，八个一致检查仍须执行
→ S10 blocking_result.is_blocked=false 且 can_enter_final=true 时方可进入 FINAL
→ S10 blocking_result.is_blocked=true 时阻断进入 FINAL

**重要**：进入 FINAL 或生成诉讼文书前必须执行 S10。无法条引用时只记录无引用，不得跳过八个一致检查或 blocking_result 门禁。

---

## 执行流程

### 第一步：收集法条引用

从S1/S2/S3/S4/S5/S7/S9中提取所有法条引用：

| 步骤 | 引用法条 | 原文 |
|------|----------|------|
| S2 | 《民法典》第577条 | "依据《民法典》第577条..." |
| S3 | 《民法典》第525条 | "根据《民法典》第525条..." |

### 第二步：三层校验

#### 第一层：元典平台复验（优先）

```bash
cd ~/.claude/skills/law-search
python3 scripts/yd_search.py search "民法典 第577条" --sxx 现行有效
python3 scripts/yd_search.py detail "民法典" --ft-name "第577条"
```

确认法条存在且内容匹配。

#### 第二层：北大法宝复验（备用，需手动启用）

> ⚠️ 北大法宝MCP当前已禁用。如需使用，请在 settings.local.json 中添加相应权限。

```python
# 需要先在 settings.local.json 中启用：
# "mcp__pkulaw-law-search__search_article"
# "mcp__pkulaw-law-search__get_article"

mcp__pkulaw-law-search__search_article(text="民法典 第577条")
mcp__pkulaw-law-search__get_article(title="中华人民共和国民法典", number="577")
```

#### 第三层：DeepSeek兜底

调用 `review_with_deepseek.py` 做独立质疑（仅在前两层有分歧时）。

### 第二步A：八个一致质量检查（新增）

**说明**：基于 live case-os 资源执行八个一致质量检查

#### 检查依据

- 引用资源（不复制）：`../case-os/references/eight_consistency_rules.json`
- 引用资源（不复制）：`../case-os/schema/eight_consistency_check_schema.json`
- 引用资源（不复制）：`../case-os/examples/nine_step_loan_case/expected_s10_consistency_check.json`

#### 八个一致检查项

1. **当事人诉辩一致**：检查原告的诉讼主张应与其起诉状一致，被告的诉讼主张应与其答辩状及笔录记载的相一致
2. **诉讼主张与基础规范一致**：检查原告诉讼主张应包含请求权基础规范涵盖的所有构成要件，被告抗辩主张应包含抗辩权基础规范涵盖的所有构成要件
3. **诉讼争点与诉讼主张一致**：检查判决书是否在全面反映当事人诉辩意见的基础上，准确概括当事人的争议焦点
4. **诉讼证据与诉讼主张一致**：检查所有要件事实是否均有证据证明，认诺和自认是否经当事人明示
5. **认定事实与事实争点一致**：检查裁判文书是否对事实争点作出认定，对事实争点的认定是否完整
6. **法律理由与法律争点一致**：检查对于当事人的法律争点，是否逐一写明法院是否采纳，并写明理由
7. **判决主文与诉讼请求一致**：检查判决主文是否与原告的诉讼请求完全对应
8. **引用条文与判决主文一致**：检查引用的法律条文是否与判决主文相对应

#### 执行方式

```python
# 引用 live case-os 资源执行八个一致检查
import json
from pathlib import Path

# 加载八个一致规则（引用，不复制）
rules_path = Path("../case-os/references/eight_consistency_rules.json")
with open(rules_path) as f:
    consistency_rules = json.load(f)

# 执行八个一致检查
consistency_check_results = {}
for rule_id, rule_content in consistency_rules["principles"]:
    rule_name = rule_content["name"]
    consistency_check_results[rule_name] = {
        "检查结果": check_consistency(rule_name, rule_content),
        "具体问题": identify_issues(rule_name)
    }

# 计算质量评分
quality_score = calculate_quality_score(consistency_check_results)
```

#### 输出格式

八个一致检查结果输出到 JSON frontmatter：

```json
{
  "eight_consistency_check": {
    "当事人诉辩一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "诉讼主张与基础规范一致": {
      "检查结果": "通过",
      "具体分析": []
    },
    "诉讼争点与诉讼主张一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "诉讼证据与诉讼主张一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "认定事实与事实争点一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "法律理由与法律争点一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "判决主文与诉讼请求一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "引用条文与判决主文一致": {
      "检查结果": "通过",
      "具体问题": []
    }
  },
  "quality_score": {
    "total_consistency_score": 85,
    "critical_rules_score": 90,
    "form_rules_score": 75
  },
  "recommendations": []
}
```

### 第三步：生成校验报告

**输出格式**：JSON frontmatter + Markdown 正文

**JSON frontmatter**（新增，包含八个一致检查）：

```json
{
  "step_id": "S10",
  "status": "pending_review",
  "input_refs": {
    "s1_path": "intermediate/原告九步法/S1-固定权利请求/S1-固定权利请求.md",
    "s2_path": "intermediate/原告九步法/S2-请求权基础/S2-请求权基础.md",
    "s4_path": "intermediate/原告九步法/S4-要件分析/S4-要件分析.md",
    "s8_path": "intermediate/原告九步法/S8-事实认定/S8-事实认定.md",
    "s9_path": "intermediate/原告九步法/S9-要件归入与裁判预测/S9-要件归入与裁判预测.md",
    "s9_reference_status": "resolved"
  },
  "hallucination_check": {
    "statute_accuracy": [],
    "case_consistency": [],
    "logic_validity": {
      "is_valid": true,
      "fallacy_detected": false,
      "fallacy_type": null
    }
  },
  "eight_consistency_check": {
    "当事人诉辩一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "诉讼主张与基础规范一致": {
      "检查结果": "通过",
      "具体分析": []
    },
    "诉讼争点与诉讼主张一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "诉讼证据与诉讼主张一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "认定事实与事实争点一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "法律理由与法律争点一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "判决主文与诉讼请求一致": {
      "检查结果": "通过",
      "具体问题": []
    },
    "引用条文与判决主文一致": {
      "检查结果": "通过",
      "具体问题": []
    }
  },
  "s9_consumption_check": {
    "s9_read_status": "resolved",
    "s9_json_parse": true,
    "s9_schema_validation": "passed",
    "pending_review_status": "pending_review",
    "predict_marker_present": true,
    "handoff_to_s10_exists": true,
    "handoff_required_fields_present": true,
    "finalization_language_detected": false,
    "input_read_errors": [],
    "unresolved_reason": null
  },
  "quality_score": {
    "total_consistency_score": 85,
    "critical_rules_score": 90,
    "form_rules_score": 75
  },
  "recommendations": [],
  "blocking_result": {
    "is_blocked": false,
    "blocking_level": null,
    "blocking_reasons": [],
    "statute_hallucination_blocked": false,
    "s9_unresolved_blocked": false,
    "s9_finalization_blocked": false,
    "ec_critical_failures": [],
    "can_enter_final": true
  },
  "review_required": {
    "hallucination_check_needs_review": true,
    "eight_consistency_check_needs_review": true,
    "s9_consumption_check_needs_review": true,
    "quality_score_needs_review": true
  }
}
```

> **JSON frontmatter 说明**：上方 JSON 块为 S10 输出格式示例，实际输出时前后各以 `---` 分隔符包裹形成有效 YAML frontmatter。

**Markdown 正文**（保留原有格式）：

```markdown
# S10 幻觉校验和八个一致质量检查报告

## 校验概要
- 扫描步骤：S1, S2, S3, S4, S5, S7, S9
- 法条引用总数：N 条
- 校验结果：✅ 全部通过 / ⚠️ 发现问题

## 法条幻觉校验

### 校验明细

| 步骤 | 引用法条 | 校验结果 | 说明 |
|------|----------|----------|------|
| S2 | 《民法典》第577条 | ✅ 通过 | 元典复验通过 |
| S3 | 《XX法》第XX条 | ❌ 幻觉 | 该法条不存在，建议修正为... |

## 八个一致质量检查

### 当事人诉辩一致
**检查结果**：通过/部分一致/不一致
**具体问题**：...

### 诉讼主张与基础规范一致
**检查结果**：通过/部分一致/不一致
**具体分析**：...

...（其余6项一致检查）

## 质量评分

- **总分**：XX/100
- **关键规则得分**：XX/100
- **形式规则得分**：XX/100

## 改进建议
1. ...
2. ...
```

保存到 `intermediate/原告九步法/S10-幻觉校验和八个一致报告.md`

### 第四步：幻觉处理（守门员模式）

- ❌ **发现幻觉** → 自动阻断，不放行进入 FINAL
- 输出阻断提示：`⛔ S10 发现法条幻觉，已阻断。请律师修正后重新校验。`
- 修正方式：律师人工修正，或调用元典平台检索真实法条替换
- 修正后重新执行 S10 校验，通过后方可进入 FINAL

### 第五步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S10
```

---

## 红线

- ❌ **发现幻觉自动阻断**
- ❌ 不放行进入 FINAL
- ✅ 修正后必须重新校验

---

## 工具依赖

**法条幻觉校验**：
- **元典Skill**（law-search）— 法条检索与内容获取
  ```bash
  python3 scripts/yd_search.py search "检索词"
  python3 scripts/yd_search.py detail "法律名" --ft-name "条号"
  ```

**备用选项**（需手动启用）：
- `mcp__pkulaw-law-search__search_article` — 法条检索（北大法宝MCP，当前已禁用）
- `mcp__pkulaw-law-search__get_article` — 法条内容获取（北大法宝MCP，当前已禁用）
- `~/.local/bin/review_with_deepseek.py` — DeepSeek辅模型质疑

**八个一致质量检查**（引用 live case-os 资源，不复制）：
- `../case-os/references/eight_consistency_rules.json` — 八个一致规则详解
- `../case-os/schema/eight_consistency_check_schema.json` — 八个一致检查 schema
- `../case-os/examples/nine_step_loan_case/expected_s10_consistency_check.json` — 完整输出示例

**本地资源**（新增）：
- `schema/s10_output_schema.json` — S10 输出结构定义（含 schema 级语义约束）
- `examples/s10_eight_consistency_example.md` — 八个一致检查示例

### Schema 语义约束（if-then 规则）

`s10_output_schema.json` 使用 JSON Schema Draft-07 的 `if`/`then` 实现语义约束。当以下条件满足时，`blocking_result` 必须设置对应阻断标志：

| 条件 | 要求的 blocking_result 状态 |
|------|---------------------------|
| `s9_consumption_check.s9_read_status = "unresolved"` | `is_blocked=true` + `s9_unresolved_blocked=true` + `can_enter_final=false` |
| `s9_consumption_check.finalization_language_detected = true` | `is_blocked=true` + `s9_finalization_blocked=true` + `can_enter_final=false` |
| `s9_consumption_check.predict_marker_present = false` | `is_blocked=true` + `can_enter_final=false` |
| `eight_consistency_check.诉讼主张与基础规范一致.检查结果 ≠ "通过"` | `is_blocked=true` + `can_enter_final=false` + `ec_critical_failures` 包含 `"EC_02"` |
| `eight_consistency_check.认定事实与事实争点一致.检查结果 ≠ "通过"` | `is_blocked=true` + `can_enter_final=false` + `ec_critical_failures` 包含 `"EC_05"` |
| `eight_consistency_check.法律理由与法律争点一致.检查结果 ≠ "通过"` | `is_blocked=true` + `can_enter_final=false` + `ec_critical_failures` 包含 `"EC_06"` |
| `eight_consistency_check.判决主文与诉讼请求一致.检查结果 ≠ "通过"` | `is_blocked=true` + `can_enter_final=false` + `ec_critical_failures` 包含 `"EC_07"` |

这些约束确保 S10 作为守门员：当 S9 unresolved、S9 finalization language、predict_marker 缺失或 EC_02/EC_05/EC_06/EC_07 任一失败时，输出必须被 schema 拒绝（jsonschema.validate 抛出 ValidationError），不会出现在 `can_enter_final=true` 的不一致状态。

---

## 九步法资源接入（强制）

执行 S10 前必须读取 live `case-os` 的九步法资源，引用而不复制：

1. 读取 `../case-os/references/nine_step_output_schemas.json` 中 `steps.S10` 的 `input_schema`、`output_schema`、`handoff_to_next` 与 `blocking_conditions`。
2. 读取 `../case-os/references/nine_step_checklist.json` 中 `steps.S10` 的检查清单，并在 Markdown 正文中逐项说明覆盖、缺失或不适用。
3. 读取 `../case-os/references/nine_step_failure_modes.json` 中 `failure_modes.S10` 的失败模式；命中 HIGH/CRITICAL 风险时必须阻断或标记待律师处理。
4. 按需读取 `../case-os/references/nine_step_chunks.jsonl` 中 `step_id == "S10"` 或 `skill_target` 指向本步骤的切片；未找到匹配切片时记录 `chunks_reference_status: "none_found"`，不得因此跳过步骤。
5. 读取 `../case-os/examples/nine_step_loan_case/expected_s10_consistency_check.json` 作为结构参考；如本 skill 有 `schema/s10_output_schema.json`，同时按本地 schema 校验输出。
- 本 skill 本地示例（如存在）：`examples/s10_*.md`。

输出必须采用合法 JSON frontmatter + Markdown 正文。JSON 顶层 `step_id`、`status`/`review_status`、引用来源、律师确认口径、hook 写回状态必须与 `case-os` 总控一致。
- S1/S5/S6/S8/S9 只能进入 `pending_review`；S2/S4/S7 需完成权威复验/律师确认口径后才可交接；S10 只作 FINAL 阻断门禁，不得改写 S9 结论。

## 输出

**输出文件**：
- `intermediate/原告九步法/S10-幻觉校验和八个一致报告.md`

**输出格式**：
- JSON frontmatter：包含 hallucination_check、eight_consistency_check、quality_score、recommendations
- Markdown 正文：保留原有格式，新增八个一致检查详细内容

**字段说明**：
- `eight_consistency_check` 包含 8 个一致性检查，字段名使用中文规则名
- `quality_score.total_consistency_score`：总分（0-100），critical 70% + form 30%
- `recommendations`：改进建议数组

---

## 操作入口

- `/幻觉校验` — 手动触发 S10 校验
- `/幻觉校验 --fix` — 校验并自动修正（律师确认后执行）
