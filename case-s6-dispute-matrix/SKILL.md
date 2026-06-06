---
name: case-s6-dispute-matrix
description: 九步法S6-争点矩阵。对比原告与被告主张，形成事实争点和法律争点，排序优先级。TRIGGER when: 用户输入"争点矩阵"或由case-os总控调度。
---

# case-s6-dispute-matrix（S6）争点矩阵

## 工作定位

对比双方诉辩主张，形成争点对撞，区分事实争点与法律争点，并建立争点与 S4 要件、S2/S3 法条的映射。S6 为双方共用同一份争点矩阵，不生成互相矛盾的镜像版本。

**前置条件**：S5（主张检索）完成
**必须确认**：**是**（律师必审）
**北大法宝复验**：不需要
**双方共用**：S6争点矩阵双方共用同一份
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取双方文件

- 读取 `intermediate/原告九步法/` 下 S1-S5 所有文件
- 读取 `intermediate/被告九步法/` 下 S1-S5 所有文件
- 优先解析 JSON frontmatter；解析失败时回退 Markdown 表格并标记 `upstream_parse_status`

### 第二步：识别争议焦点

争点分类仅保留两类：

1. **事实争点**：法律关系发生、变更、消灭的事实，民事主体、行为及请求权基础规范相关事实。
2. **法律争点**：实体法律适用争点和程序法律适用争点。管辖、诉讼时效、程序性异议等不得单列为第三类“程序争议”，应归入 `law_disputes[].dispute_type = "程序法律适用"`。

### 第三步：形成争点对撞

每个争点必须有稳定 ID：
- 事实争点：`S6-FD###`
- 法律争点：`S6-LD###`

事实争点尽量映射到 S4 `related_element`；法律争点尽量映射到 S2/S3 `related_statute`。上游结构缺失时不得补造，记录 `mapping_status: "unresolved"`。

### 第四步：排序优先级

| 优先级 | 标准 | 庭审精力分配 |
|--------|------|--------------|
| P0 | 决定胜负或决定主要责任/金额 | 60% |
| P1 | 影响结果但非唯一胜负点 | 30% |
| P2 | 辅助说明、影响较小或可替代 | 10% |

非争点排除：双方一致认可、与要件无关、对裁判结果无实质影响的内容，不得强行争点化。

### 第五步：生成 S6 文件

输出采用合法 JSON frontmatter + Markdown 正文：

```markdown
---
{
  "step_id": "S6",
  "status": "pending_review",
  "fact_disputes": [],
  "law_disputes": [],
  "non_dispute_exclusions": [],
  "priority_allocation": []
}
---

# S6 争点矩阵

[Markdown 正文]
```

保存到 `intermediate/原告九步法/S6-争点矩阵/S6-争点矩阵.md`（双方共用）

### 第六步：律师必审

**红线**：AI不得自主落定，结构化状态保持 `pending_review`。争点排序、争点分类、非争点排除均须律师复核。

### 第七步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S6
```

---

## 红线

- ❌ **AI不得自主落定**
- ❌ 结构化状态不得自动越过 `pending_review`
- ❌ 不得将程序法律适用争点单列为第三类争点
- ❌ 不得把双方无争议内容争点化
- ✅ S6双方共用，不生成被告九步法镜像

## 九步法资源接入（强制）

执行 S6 前必须读取 live `case-os` 的九步法资源，引用而不复制：

1. 读取 `../case-os/references/nine_step_output_schemas.json` 中 `steps.S6` 的 `input_schema`、`output_schema`、`handoff_to_next` 与 `blocking_conditions`。
2. 读取 `../case-os/references/nine_step_checklist.json` 中 `steps.S6` 的检查清单，并在 Markdown 正文中逐项说明覆盖、缺失或不适用。
3. 读取 `../case-os/references/nine_step_failure_modes.json` 中 `failure_modes.S6` 的失败模式；命中 HIGH/CRITICAL 风险时必须阻断或标记待律师处理。
4. 按需读取 `../case-os/references/nine_step_chunks.jsonl` 中 `step_id == "S6"` 或 `skill_target` 指向本步骤的切片；未找到匹配切片时记录 `chunks_reference_status: "none_found"`，不得因此跳过步骤。
5. 读取 `../case-os/examples/nine_step_loan_case/expected_s6_issues.json` 作为结构参考；同时按 `schema/s6_output_schema.json` 校验输出，并参考 `examples/s6_dispute_matrix_example.md`。

输出必须采用合法 JSON frontmatter + Markdown 正文。JSON 顶层 `step_id`、`status`/`review_status`、引用来源、律师确认口径、hook 写回状态必须与 `case-os` 总控一致。
- S1/S5/S6/S8/S9 只能进入 `pending_review`；S2/S4/S7 需完成权威复验/律师确认口径后才可交接；S10 只作 FINAL 阻断门禁，不得改写 S9 结论。

## 输出

- `intermediate/原告九步法/S6-争点矩阵/S6-争点矩阵.md`（双方共用）
- 文件必须含 JSON frontmatter + Markdown 正文
