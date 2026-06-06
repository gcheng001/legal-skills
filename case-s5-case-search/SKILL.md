---
name: case-s5-case-search
description: 九步法S5-主张检索。审查诉讼主张与基础规范/构成要件的对应性，检索法规、类案、学理并输出完备性检查。TRIGGER when: 用户输入"主张检索"或由case-os总控调度。
---

# case-s5-case-search（S5）主张检索

## 工作定位

围绕 S4 构成要件检索当事人诉讼主张，检查主张是否覆盖基础规范全部要件，并补充法规、类案、学理支持。S5 的核心不是简单找案例，而是形成 `claim_completeness_check`，交给 S6 整理争点。

**前置条件**：S4（要件拆解）完成
**必须确认**：**是**（律师必审）
**北大法宝复验**：不需要
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取上游结构化文件

- 读取 S1 `fixed_claims`
- 读取 S2 `legal_articles` / `claim_basis_statutes`
- 读取 S4 `claim_basis_analysis.constitutive_elements` 与 `defense_basis_analysis.constitutive_elements`
- 优先解析 JSON frontmatter；解析失败时可回退 Markdown 表格，但必须标记 `upstream_parse_status`

### 第二步：诉讼主张与基础规范对应性检查

逐项对照 S4 要件，判断诉讼主张是否覆盖：

| 检查对象 | 要求 |
|----------|------|
| `corresponds_to_basis` | 主张与请求权基础、抗辩基础存在可解释对应关系 |
| `missing_claims` | 未覆盖的构成要件、遗漏主张、需要释明事项 |
| `contradictory_claims` | 相互矛盾、互斥或与请求权基础不匹配的主张 |
| `needs_supplement` | 是否需要补充或明确诉讼主张 |

### 第三步：检索支持材料

针对每个要件事实和争议主张检索：
- 法律条文、司法解释、部门规章
- 类案裁判观点
- 学理或实务观点

类案检索优先使用元典开放平台：

```python
mcp__yuandian-law-search__search_case(text="建设工程合同纠纷 结算争议")
```

### 第四步：生成 S5 文件

输出采用合法 JSON frontmatter + Markdown 正文：

```markdown
---
{
  "step_id": "S5",
  "status": "pending_review",
  "claim_completeness_check": {
    "corresponds_to_basis": false,
    "missing_claims": [],
    "contradictory_claims": [],
    "needs_supplement": true
  },
  "supplement_records": [],
  "references": {
    "s4_elements_ref": "intermediate/原告九步法/S4-要件拆解/S4-要件拆解.md",
    "schema_ref": "schema/s5_output_schema.json"
  }
}
---

# S5 主张检索

[Markdown 正文]
```

保存到 `intermediate/原告九步法/S5-主张检索/S5-主张检索.md`

### 第五步：律师必审

**红线**：AI不得自主落定，结构化状态保持 `pending_review`。发现遗漏、矛盾或不匹配时，必须列入 `supplement_records` 并提示律师释明。

### 第六步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S5-主张检索/S5-主张检索.md`，状态保持 `predict` / `pending_review`，不得作为终局判断。

### 第七步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S5
```

---

## 红线

- ❌ **AI不得自主落定**
- ❌ 结构化状态不得自动越过 `pending_review`
- ❌ 不得只做类案检索而遗漏 `claim_completeness_check`
- ❌ S4 结构化解析失败时不得补造要件，必须标记 unresolved 并提示补正

## 工具依赖

- `mcp__yuandian-law-search__search_case` — 类案检索

## 九步法资源接入（强制）

执行 S5 前必须读取 live `case-os` 的九步法资源，引用而不复制：

1. 读取 `../case-os/references/nine_step_output_schemas.json` 中 `steps.S5` 的 `input_schema`、`output_schema`、`handoff_to_next` 与 `blocking_conditions`。
2. 读取 `../case-os/references/nine_step_checklist.json` 中 `steps.S5` 的检查清单，并在 Markdown 正文中逐项说明覆盖、缺失或不适用。
3. 读取 `../case-os/references/nine_step_failure_modes.json` 中 `failure_modes.S5` 的失败模式；命中 HIGH/CRITICAL 风险时必须阻断或标记待律师处理。
4. 按需读取 `../case-os/references/nine_step_chunks.jsonl` 中 `step_id == "S5"` 或 `skill_target` 指向本步骤的切片；未找到匹配切片时记录 `chunks_reference_status: "none_found"`，不得因此跳过步骤。
5. 读取 `../case-os/examples/nine_step_loan_case/expected_s5_assertions.json` 作为结构参考；同时按 `schema/s5_output_schema.json` 校验输出，并参考 `examples/s5_case_search_example.md`。

输出必须采用合法 JSON frontmatter + Markdown 正文。JSON 顶层 `step_id`、`status`/`review_status`、引用来源、律师确认口径、hook 写回状态必须与 `case-os` 总控一致。
- S1/S5/S6/S8/S9 只能进入 `pending_review`；S2/S4/S7 需完成权威复验/律师确认口径后才可交接；S10 只作 FINAL 阻断门禁，不得改写 S9 结论。

## 输出

- `intermediate/原告九步法/S5-主张检索/S5-主张检索.md`
- `intermediate/被告九步法/S5-主张检索/S5-主张检索.md`
- 文件必须含 JSON frontmatter + Markdown 正文
