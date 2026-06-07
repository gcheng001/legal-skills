# 民事案件OS 编排流程

> 本文档定义民事案件OS的完整编排流程，包括Phase A、Phase B和Phase B之后的事件驱动机制。

---

## 系统层级

```
用户 → civil-case-os（总控：全局规则 + 调度）
         ↓
    民事独立Skill（具体执行逻辑）
         ↓
    Hook（后置脚本自动触发）
```

---

## Phase A（材料处理）

> **核心目标**：快速整理材料 + 快速了解基本案情。深度分析留给 Phase B 九步法展开。

### 步骤流程

| 步骤 | 独立Skill | 职责 | 前置条件 | 必须确认 |
|------|----------|------|----------|----------|
| A1 | `case-git-init` + `case-core-files` | 案件初始化（Git + 目录结构 + 核心文件 + 初始状态写入） | 无 | 否 |
| A2 | `case-ocr` | 材料扫描+OCR转换（Mineru优先） | A1完成 | 否（视频截图需人工审阅） |
| A3 | `case-archive` | 文件夹自动归档 | A2完成 | 否（事后汇报） |
| A4 | `case-info-extract` | 案件理解（信息提取 + 案情概要，一次确认） | A3完成 | **是**（信息确认点） |
| A5 | `case-feishu-sync` | 飞书同步（CLAUDE.md→云文档 + 案件池更新） | A4确认 | **是**（同步结果确认） |
| A6 | `case-evidence-cards` | 证据卡片与关系复核（双视图） | A5确认 | **是**（律师复核） |
| A7（内部） | `manage_integration_state.py` | 本地状态汇总与发布准备 | A6复核后自动触发 | 否（不得作为单独人工步骤） |

### 关键规则

- **A1 统一初始化边界**：A1 必须统一完成 Git 初始化、核心文件生成、目录结构与 `_archive/case-os-state.json` 初始状态写入
- **Phase A红线**：用户操作步骤必须按 A1→A2→A3→A4→A5→A6 顺序依次执行
- **A6 内部门禁**：A5 明确确认后自动完成 A6 状态校验，A6 不再作为用户待执行步骤暴露
- **每个步骤完成后 git 提交**

### A5 飞书同步机制（贯穿始终）

**首次执行**：A4 律师确认后，执行独立的飞书同步步骤（`case-feishu-sync`）

**后续自动同步**：在整个案件OS流程中（Phase A + Phase B + FINAL），CLAUDE.md 任何更新后，必须重新执行 A5 同步

**触发时机**：
- A4 确认后（首次同步）
- S1-S9 任一步骤确认后
- S10 幻觉校验完成后
- FINAL 诉讼文书生成后
- 手动更新 CLAUDE.md 后

### Phase A→B切换

A6 复核后自动通过 A7 门禁时，输出切换提示：
```
✅ Phase A 全部完成（7步）。
📌 下一步：请切换到 GLM 5.1 模型执行 Phase B（九步法分析）。
执行命令：cc-switch-to.sh glm
然后重新启动 Claude Code 会话，输入"民事案件 OS"或"案件 OS"继续。
```

---

## Phase B（九步法）

> **核心目标**：深度法律分析，形成诉讼策略和裁判预测。

### 步骤流程

| 步骤 | 独立Skill | 职责 | 前置条件 | 北大法宝复验 | 必须确认 |
|------|----------|------|----------|------------|----------|
| S1 | `case-s1-fixed-claim` | 固定权利请求 | A6复核后内部A7自动通过 | — | **是** |
| S2 | `case-s2-claim-basis` | 请求权基础 | S1确认 | ✅ 必须 | **是**（终选） |
| S3 | `case-s3-defense` | 抗辩规范 | S2完成 | ✅ 必须 | **是**（战术） |
| S4 | `case-s4-elements` | 要件拆解 | S3完成 | ✅ 必须 | **是** |
| S5 | `case-s5-case-search` | 主张检索 | S4完成 | — | **是** |
| S6 | `case-s6-dispute-matrix` | 争点矩阵（双方共用） | S5完成 | — | **是** |
| S7 | `case-s7-burden` | 举证责任分配 | S6完成 | ✅ 必须 | **是** |
| S8 | `case-s8-fact-finding` | 事实认定 | S7完成 | — | **是** |
| S9 | `case-s9-judgment-predict` | 要件归入与裁判预测 | S8完成 | — | **是** |
| S10 | `case-s10-hallucination` | 法条幻觉校验+八个一致+FINAL阻断门禁 | S1-S9完成 | — | S10守门员阻断 |

### 双视图

- 原告九步法（execute）：实际执行每一步
- 被告九步法（predict）：预判被告会怎么做
- S6争点矩阵双方共用

### S10 守门员机制

**FINAL放行门禁**（S10自动阻断）：
- S10输出必须满足 `blocking_result.can_enter_final=true` 且 `is_blocked=false`
- S9状态须为 `pending_review`，含 `predict_marker`
- EC_02/EC_05/EC_06/EC_07 任一失败 → **CRITICAL阻断**
- 法条幻觉检测失败 → **CRITICAL阻断**

**S10阻断条件**：
- S9 `s9_read_status = unresolved`
- S9 含终局化语言（`confirmed`/`final`/`胜诉`/`败诉`等）
- `predict_marker` 缺失
- EC_02/EC_05/EC_06/EC_07 任一检查结果 ≠ "通过"
- 法条幻觉检测失败

---

## Phase B之后（事件驱动）

| 事件 | 独立Skill | 触发条件 |
|------|----------|----------|
| 写起诉状/答辩状 | `case-filing-gen` | S10通过后，律师确认 |
| 法院短信 | `case-court-sms` | 收到法院短信 |
| 案件讨论 | `case-discussion` | 随时发起 |
| 定期扫描 | `case-scan` | 每周自动/手动触发 |
| 经验卡 | `case-experience-card` | S9完成/开庭后/判决后 |

---

## 双模型会话工作流

| 阶段 | 模型 | 会话 | 负责内容 |
|------|------|------|----------|
| Phase A（A1-A6） | Kimi 2.6（通读位） | 会话1 | 材料扫描、OCR、信息提取、证据复核（200万token长上下文） |
| Phase B（S1-S10） | GLM 5.1（主推理） | 会话2 | 九步法分析、幻觉校验（推理能力最强） |
| 辅质疑 | DeepSeek | 按需调用 | S2/S9质疑复核、S10幻觉校验兜底 |

**模型切换脚本**：`~/.local/bin/cc-switch-to.sh`
- `cc-switch-to.sh kimi` — 切换到 Kimi 2.6（Phase A 用）
- `cc-switch-to.sh glm` — 切换到 GLM 5.1（Phase B 用）
- `cc-switch-to.sh mimo` — 切回默认 MiMo
- `cc-switch-to.sh deepseek` — 切换到 DeepSeek（辅模型）

---

## 续跑模式判断

**判断依据**：
1. **版本号检查**：CLAUDE.md 包含 `*本文件由民事案件OS v10.0生成*` 字样
2. **权威状态检查**：`_archive/case-os-state.json` 存在且 schema 为 `case-os-state-v1`

**判断流程**：
```
if case-os-state.json 存在 && schema == "case-os-state-v1":
    → 续跑模式：从权威状态记录的 current_step 继续
elif CLAUDE.md存在 || phase-a-status.json存在:
    → 兼容模式：运行 manage_integration_state.py scan-existing
else:
    → 初始化模式：A1 建立固定 case_id 后执行完整流程
```

---

## 变更历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-06-07 | 从SKILL.md外迁，独立为workflow.md |
