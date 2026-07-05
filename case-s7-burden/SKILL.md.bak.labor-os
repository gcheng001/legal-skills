---
name: case-s7-burden
description: '九步法S7-举证责任。分配每个争点的举证责任，评估举证状态，心证公开，证明资源审查。TRIGGER when: 用户输入"举证责任"或由case-os总控调度。'
---

# case-s7-burden（S7）举证责任

## 工作定位

分配每个争点的举证责任，评估原告九步法举证状态，标红"举证而不能"，进行心证公开促使当事人补充证据，审查证明资源用尽情况。

**前置条件**：S6（争点矩阵）完成
**必须确认**：**是**
**法条复验**：**必须**（优先使用元典）
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取S6文件

读取 `intermediate/原告九步法/S6-争点矩阵/` 中的争点清单。

### 第二步：分配举证责任

对每个争点分配举证责任：

| 争点 | 举证责任方 | 法律依据 | 说明 |
|------|------------|----------|------|
| 争点1 | 原告 | 《民诉法》第64条 | 谁主张谁举证 |
| 争点2 | 被告 | 《民法典》第XXX条 | 举证责任倒置 |

### 第三步：评估原告举证状态

| 争点 | 举证责任 | 证据状态 | 风险等级 |
|------|----------|----------|----------|
| 争点1 | 原告 | ✅ 有充分证据 | 低 |
| 争点2 | 原告 | ⚠️ 证据不足 | 高 |
| 争点3 | 原告 | ❌ 举证而不能 | 致命 |

### 第四步：心证公开（新增）

**心证公开依据**：《最高人民法院关于民事诉讼证据的若干规定》

**心证公开目的**：促使当事人围绕心证结论收集和补充证据

**概念区分（重要）**：
- **心证公开（judicial_disclosure）**：法官基于现有证据形成初步心证（临时判断），公开心证促使当事人补充证据、避免证据突袭。内容包括：初步心证结论、哪些争点举证不足、补证方向、当事人回应。
- **司法公开信息核查（public_record_check）**：在公开平台（裁判文书网、庭审公开网、执行信息网、破产重整网）排查双方当事人涉诉、被执行、破产信息。这是完全不同的概念，不得占用 `judicial_disclosure` 字段。

**心证公开内容**：
1. 根据现有证据形成初步心证
2. 指出证据不足或举证不能的争点
3. 要求当事人围绕心证结论补充证据

**心证公开记录**（按争点逐一记录）：
- 争点名称
- 初步心证（当前证据下的临时判断）
- 举证不足方
- 补证方向

**输出字段**：
```json
{
  "judicial_disclosure": {
    "disclosure_made": true/false,
    "disclosure_content": "心证公开内容",
    "disclosure_purpose": "促使当事人补充证据",
    "party_response": "当事人回应",
    "additional_evidence_prompted": true/false,
    "disclosure_records": [
      {
        "争点": "争点名称",
        "初步心证": "当前证据下的临时判断",
        "举证不足方": "原告/被告/双方",
        "补证方向": "具体建议"
      }
    ]
  },
  "public_record_check": {
    "description": "司法公开信息核查，可选独立字段，不得混入 judicial_disclosure",
    "checked_platforms": [],
    "findings": {},
    "note": "建议开庭前完成核查"
  }
}
```

### 第五步：证明资源审查（新增）

**审查依据**：《最高人民法院关于民事诉讼证据的若干规定》

**审查目的**：确认当事人是否已用尽证明资源及证明方法

**审查内容**：
1. 当事人是否已申请调查取证
2. 当事人是否已申请证据保全
3. 当事人是否已申请司法鉴定
4. 当事人是否已提供所有相关证人

**可用证明方法**：
- 申请调查取证（去银行调取还款记录）
- 申请证据保全（固定录音证据）
- 申请司法鉴定（笔迹、时间鉴定）
- 提供证人证言

**进一步指导**：
- 对原告：建议补充的证据和方法
- 对被告：建议补充的证据和方法

**输出字段**：
```json
{
  "proof_resource_review": {
    "review_conducted": true/false,
    "proof_methods_exhausted": true/false,
    "available_proof_methods": [...],
    "unused_proof_methods": [...],
    "review_conclusion": "审查结论",
    "additional_guidance": "进一步指导"
  }
}
```

### 第六步：法条复验（元典优先）

**优先使用元典Skill**：

```bash
cd ~/.claude/skills/law-search
python3 scripts/yd_search.py search "举证责任倒置 建设工程" --sxx 现行有效
```

**备用方案**（需手动启用北大法宝MCP）：

> ⚠️ 北大法宝MCP当前已禁用。如需使用，请在 settings.local.json 中添加相应权限。

```python
# 需要先在 settings.local.json 中启用：
# "mcp__pkulaw-law-search__search_article"

mcp__pkulaw-law-search__search_article(text="举证责任倒置 建设工程")
```

### 第七步：生成S7文件

**输出格式**：JSON frontmatter + Markdown 正文

**JSON frontmatter**（包含心证公开和证明资源审查）：

```json
---
{
  "step_id": "S7",
  "burden_allocation": {...},
  "evidence_status_assessment": {...},
  "judicial_disclosure": {
    "disclosure_made": true,
    "disclosure_content": "...",
    "disclosure_purpose": "促使当事人补充证据",
    "party_response": "...",
    "additional_evidence_prompted": true,
    "disclosure_records": [...]
  },
  "proof_resource_review": {
    "review_conducted": true,
    "proof_methods_exhausted": false,
    "available_proof_methods": [...],
    "unused_proof_methods": [...],
    "review_conclusion": "...",
    "additional_guidance": "..."
  }
}
---
```

**Markdown 正文**：

```markdown
# S7 举证责任分配

## 举证责任分配
| 争点 | 举证责任方 | 法律依据 | 证据状态 | 风险等级 |
|------|------------|----------|----------|----------|
| ... | ... | ... | ... | ... |

## 证据状态评估
[评估内容]

## 心证公开
[心证公开内容、当事人回应、补充证据情况]

## 证明资源审查
[可用证明方法、未使用方法、进一步指导]

## ⚠️ 举证而不能
[致命缺口说明]
```

保存到 `intermediate/原告九步法/S7-举证责任/`

### 第八步：律师确认

展示举证责任分配、心证公开、证明资源审查和风险评估，等用户确认。

### 第九步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S7-举证责任/`

### 第十步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S7
```

---

## 红线

- ❌ **必须法条复验**（优先使用元典）
- ❌ **标红"举证而不能"的致命缺口**
- ❌ **必须进行心证公开促使当事人补充证据**
- ❌ **必须进行证明资源审查确认当事人是否已用尽证明资源**

---

## 工具依赖

**法条检索与复验**：
- **元典Skill**（law-search）— 法条检索与内容获取
  ```bash
  python3 scripts/yd_search.py search "检索词"
  python3 scripts/yd_search.py detail "法律名" --ft-name "条号"
  ```

**备用选项**（需手动启用）：
- `mcp__pkulaw-law-search__search_article` — 法条检索（北大法宝MCP，当前已禁用）
- `mcp__pkulaw-law-search__get_article` — 法条内容获取（北大法宝MCP，当前已禁用）

**引用资源**（引用 live case-os 资源，不复制）：
- `../case-os/schema/nine_step_core_schema.json` — s7_proof_matrix 字段定义
- `../case-os/examples/nine_step_loan_case/` — 完整输出示例参考

**本地资源**（新增）：
- `schema/s7_output_schema.json` — S7 输出结构定义
- `examples/s7_disclosure_example.md` — 心证公开和证明资源审查示例

---

## 九步法资源接入（强制）

执行 S7 前必须读取 live `case-os` 的九步法资源，引用而不复制：

1. 读取 `../case-os/references/nine_step_output_schemas.json` 中 `steps.S7` 的 `input_schema`、`output_schema`、`handoff_to_next` 与 `blocking_conditions`。
2. 读取 `../case-os/references/nine_step_checklist.json` 中 `steps.S7` 的检查清单，并在 Markdown 正文中逐项说明覆盖、缺失或不适用。
3. 读取 `../case-os/references/nine_step_failure_modes.json` 中 `failure_modes.S7` 的失败模式；命中 HIGH/CRITICAL 风险时必须阻断或标记待律师处理。
4. 按需读取 `../case-os/references/nine_step_chunks.jsonl` 中 `step_id == "S7"` 或 `skill_target` 指向本步骤的切片；未找到匹配切片时记录 `chunks_reference_status: "none_found"`，不得因此跳过步骤。
5. 读取 `../case-os/examples/nine_step_loan_case/expected_s7_proof_matrix.json` 作为结构参考；如本 skill 有 `schema/s7_output_schema.json`，同时按本地 schema 校验输出。
- 本 skill 本地示例（如存在）：`examples/s7_*.md`。

输出必须采用合法 JSON frontmatter + Markdown 正文。JSON 顶层 `step_id`、`status`/`review_status`、引用来源、律师确认口径、hook 写回状态必须与 `case-os` 总控一致。
- S1/S5/S6/S8/S9 只能进入 `pending_review`；S2/S4/S7 需完成权威复验/律师确认口径后才可交接；S10 只作 FINAL 阻断门禁，不得改写 S9 结论。

## 输出

**输出文件**：
- `intermediate/原告九步法/S7-举证责任/`
- `intermediate/被告九步法/S7-举证责任/`

**输出格式**：
- JSON frontmatter：包含完整的举证责任分配、心证公开和证明资源审查数据
- Markdown 正文：展示举证责任分配、心证公开和证明资源审查过程和结果

**关键字段**：
- `burden_allocation`：举证责任分配
- `evidence_status_assessment`：证据状态评估
- `fatal_gaps`：致命缺口列表
- `judicial_disclosure`：心证公开（新增）
- `proof_resource_review`：证明资源审查（新增）

**心证公开说明**：
- 目的：促使当事人补充证据
- 内容：初步心证结论、证据不足提示
- 效果：提高事实认定准确性

**证明资源审查说明**：
- 目的：确认当事人是否已用尽证明资源及证明方法
- 内容：可用证明方法、未使用方法、进一步指导
- 效果：促使当事人用尽可用证明资源
