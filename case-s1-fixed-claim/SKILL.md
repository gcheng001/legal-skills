---
name: case-s1-fixed-claim
description: "九步法S1-固定权利请求。从起诉状提取诉讼请求清单，分析请求权竞合。TRIGGER when: 用户输入固定权利请求或由case-os总控调度。"
---

# case-s1-fixed-claim（S1）固定权利请求

## 工作定位

从起诉状/仲裁申请书中提取诉讼请求清单，分析请求权竞合可能性。

**前置条件**：A5（证据卡片与关系复核）复核完成且 A6 本地状态校验通过
**必须确认**：**是**（律师必审）
**北大法宝复验**：不需要
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取材料

- 读取 `CLAUDE.md` 案件概览
- 读取 `_archive/markdown/` 全部材料
- 重点识别起诉状/仲裁申请书

### 第二步：提取诉讼请求清单

从起诉状中提取每项诉讼请求：
1. 请求内容（如"请求判令被告支付货款100万元"）
2. 请求金额（如有）
3. 请求法律依据（如有）

### 第三步：分析请求权竞合

分析每项请求是否存在竞合可能性：
- 合同违约 vs 侵权责任
- 不当得利 vs 合同无效
- 多种请求权基础并存

### 第四步：生成S1文件

生成文件使用 JSON frontmatter 格式：

```markdown
---
{
  "title": "S1 固定权利请求",
  "case_id": "<案件ID>",
  "party": "原告|被告",
  "confidence": "high|medium|low",
  "status": "pending_review",
  "fixed_claims": [...],
  "clarification_records": [...],
  "claim_completeness": {...},
  "conflicts": [...]
}
---

# S1 固定权利请求

**案件**：<案件ID>
**方**：<原告|被告>
**状态**：⏳ 待律师确认
...
```

保存到 `intermediate/<方>九步法/S1-固定权利请求/`

### 第五步：律师必审

**红线**：AI不得自主落定，结构化状态保持 `pending_review`。

展示请求清单，等用户确认。

### 第六步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S1-固定权利请求/`

### 第七步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S1
```

---

## S1 JSON frontmatter 输出规范

### 顶层字段

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `title` | String | 是 | 固定值 "S1 固定权利请求" |
| `case_id` | String | 是 | 案件唯一标识符 |
| `party` | String | 是 | "原告" 或 "被告" |
| `confidence` | String | 是 | high/medium/low |
| `status` | String | 是 | 固定为 pending_review |
| `fixed_claims` | Array | 是 | 固定请求权清单 |
| `clarification_records` | Array | 是 | 律师确认记录（持久化到 frontmatter） |
| `claim_completeness` | Object | 是 | 完整性检查结果 |
| `conflicts` | Array | 否 | 请求权竞合分析 |

### fixed_claims 字段结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `id` | String | 是 | 唯一标识符，格式 S1-CNNN |
| `content` | String | 是 | 请求内容（律师确认后版本） |
| `amount` | Object | 否 | 金额对象（非null时必须含review_status） |
| `amount.extracted_amount` | Number | 否 | AI提取的金额（待人工确认） |
| `amount.parsed_amount` | Number | 否 | 解析后金额 |
| `amount.review_status` | String | 是 | pending_review / confirmed / rejected |
| `amount.source_text` | String | 否 | 原始金额文本 |
| `currency` | String | 否 | 币种，ISO 4217 |
| `stated_legal_basis` | String | 否 | 当事人**明示**引用的法律依据（不得AI补全） |
| `source` | String | 是 | 来源（起诉状位置） |
| `ocr_shadow` | String | 否 | OCR原始文本（用于审计） |
| `status` | String | 是 | 固定为 pending |
| `clarification_record` | String | 否 | 释明摘要 |

### clarification_records 字段结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `id` | String | 是 | 格式 S1-CLAR-NNN |
| `claim_id` | String | 是 | 关联的 fixed_claims ID |
| `type` | String | 是 | modified/confirmed/rejected/added |
| `original` | String | 否 | 修改前内容 |
| `final` | String | 否 | 修改后内容 |
| `lawyer` | String | 是 | 律师标识 |
| `timestamp` | String | 是 | ISO 8601 时间戳 |
| `note` | String | 否 | 备注 |

### claim_completeness 字段结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `checklist` | Array | 是 | 检查项清单 |
| `checklist[].item` | String | 是 | 检查项描述 |
| `checklist[].result` | String | 是 | covered/missing/unclear/not_applicable |
| `checklist[].claim_ids` | Array | 是 | 关联的请求ID |
| `checklist[].custom` | Boolean | 否 | 是否为自定义检查项 |
| `overall` | String | 是 | 固定为 review_required（不得自动落定为complete） |

### conflicts 字段结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `id` | String | 是 | 格式 S1-CONF-NNN |
| `claim_ids` | Array | 是 | 涉及的请求ID |
| `type` | String | 是 | 竞合类型描述 |
| `resolution` | String | 是 | 6个枚举值之一 |
| `note` | String | 否 | 说明 |

### conflict.resolution 枚举值（6个）

- `pending_lawyer_choice` — 待律师选择
- `simultaneous_claim` — 同时主张
- `alternative_claim` — 选择主张
- `subsidiary_claim` — 补充/备用
- `mutually_exclusive` — 互相排斥
- `withdrawn_or_rejected` — 已撤回或拒绝

---

## 红线

- ❌ **AI不得自主落定**
- ❌ 结构化状态不得自动越过 `pending_review`
- ❌ 所有 fixed_claims[].status 默认 pending，不得自动确认
- ❌ amount.review_status 必须为 pending_review，不得自动 confirmed
- ❌ claim_completeness.overall 只能为 review_required，不得自动落定为 complete
- ❌ stated_legal_basis 只记录当事人原文，不得由 AI 补全法律依据

---

## 九步法资源接入（强制）

执行 S1 前必须读取 live `case-os` 的九步法资源，引用而不复制：

1. 读取 `../case-os/references/nine_step_output_schemas.json` 中 `steps.S1` 的 `input_schema`、`output_schema`、`handoff_to_next` 与 `blocking_conditions`。
2. 读取 `../case-os/references/nine_step_checklist.json` 中 `steps.S1` 的检查清单，并在 Markdown 正文中逐项说明覆盖、缺失或不适用。
3. 读取 `../case-os/references/nine_step_failure_modes.json` 中 `failure_modes.S1` 的失败模式；命中 HIGH/CRITICAL 风险时必须阻断或标记待律师处理。
4. 按需读取 `../case-os/references/nine_step_chunks.jsonl` 中 `step_id == "S1"` 或 `skill_target` 指向本步骤的切片；未找到匹配切片时记录 `chunks_reference_status: "none_found"`，不得因此跳过步骤。
5. 读取 `../case-os/examples/nine_step_loan_case/expected_s1_claims.json` 作为结构参考；如本 skill 有 `schema/s1_output_schema.json`，同时按本地 schema 校验输出。
- 本 skill 本地示例（如存在）：`examples/s1_*.md`。

输出必须采用合法 JSON frontmatter + Markdown 正文。JSON 顶层 `step_id`、`status`/`review_status`、引用来源、律师确认口径、hook 写回状态必须与 `case-os` 总控一致。
- S1/S5/S6/S8/S9 只能进入 `pending_review`；S2/S4/S7 需完成权威复验/律师确认口径后才可交接；S10 只作 FINAL 阻断门禁，不得改写 S9 结论。

## 输出

- `intermediate/<方>九步法/S1-固定权利请求/`
- 文件使用 JSON frontmatter 格式

---

## 错误处理

- 起诉状中无法识别诉讼请求 → 提示用户手动补充
- 请求权竞合分析不确定 → 列出可能性，让用户判断
