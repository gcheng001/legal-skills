---
name: civil-case-os
description: '民事案件操作系统总控。统一入口和调度器，加载全局规则，调度民事案件独立Skill。TRIGGER when: 用户输入包含"民事OS"、"民事案件OS"、"民事案件 OS"、"civil-case-os"（不区分大小写）。刑事案件专项流程使用 criminal-case-os。'
metadata:
  author: Legal Skills Project
  trigger:
    - 民事OS
    - 民事案件OS
    - 民事案件 OS
    - civil-case-os
---

# civil-case-os 民事案件操作系统（总控）v11.1

## 工作定位

`civil-case-os` 是民事案件操作系统的**统一入口和调度器**，承担三件事：

1. **加载全局规则** — 灵魂文件（六大核心原则）+ 全局红线，所有独立Skill必须遵守
2. **调度执行** — 判断当前民事案件状态，按顺序调用对应的独立Skill
3. **独立触发保障** — 任何独立Skill被直接调用时，强制先加载全局规则

**系统层级**:
```
用户 → civil-case-os（总控：全局规则 + 调度）
         ↓
    民事独立Skill（具体执行逻辑）
         ↓
    Hook（后置脚本自动触发）
```

---

## 核心原则（摘要）

> 完整内容见 `references/soul.md`

1. **辩论贯穿全程** — 辩论不是单独步骤，是贯穿Phase B到案件结束的工作方式
2. **系统独立立场** — 系统不仅是办案助理，还是分析师和研究员
3. **当场解决问题** — 每步发现的问题必须在该步讨论解决，不带病进入下一步
4. **完整记录讨论过程** — 每次讨论必须记录：原方案、修改原因、讨论内容、最终结论
5. **起诉状/答辩状确认后才生成** — 不得自动生成，必须先和律师讨论确认要点
6. **输出去AI味** — 所有文书、分析、报告在输出给律师前，必须先经过去AI味处理

---

## 全局红线（摘要）

> 完整内容见 `references/redlines.md`

- **文件操作铁律**：未经用户明确允许，绝对禁止删除或替换任何文件
- **文件夹命名铁律**：只使用中文汉字、字母、数字、下划线、空格，禁止emoji和特殊字符
- **确认机制红线**：A4/S1/S5/S6/S8/S9必须律师确认，S2/S4/S7须北大法宝复验
- **Git管理铁律**：每个Phase A步骤完成后自动git提交，Phase B及之后每次修改后手动提交

---

## 触发机制

### 触发词（不区分大小写）

- `民事案件 OS` / `民事案件OS`
- `案件 OS` / `案件OS`
- `case-os` / `case os`

> 兼容规则：历史触发词"案件OS"默认指向本民事案件OS；刑事案件专项流程必须使用 `criminal-case-os` 或"刑事案件OS"触发。

### 双端独立运行与跨端断点接续（2026-05-24）

1. 民事案件OS可在当前调用端独立完整执行；Codex 与 Claude Code 是两个可互换入口
2. 进入已有案件或用户说"继续"时，先读共享状态文件，再判断下一未完成步骤：
   - `CLAUDE.md` → `LOG.md` → `_archive/case-os-state.json` → `intermediate/_index.json` → 当前待办步骤已生成产物
3. 续办前输出简短断点摘要；不得擅自重做已经完成或待律师确认的步骤

### 双模型会话工作流

| 阶段 | 模型 | 会话 | 负责内容 |
|------|------|------|----------|
| Phase A（A1-A6） | Kimi 2.6（通读位） | 会话1 | 材料扫描、OCR、信息提取、证据复核 |
| Phase B（S1-S10） | GLM 5.1（主推理） | 会话2 | 九步法分析、幻觉校验 |
| 辅质疑 | DeepSeek | 按需调用 | S2/S9质疑复核、S10幻觉校验兜底 |

**模型切换脚本**：`~/.local/bin/cc-switch-to.sh`

---

## 调度逻辑（摘要）

> 完整内容见 `references/workflow.md`

### Phase A（材料处理）

| 步骤 | 独立Skill | 职责 | 必须确认 |
|------|----------|------|----------|
| A1 | `case-git-init` + `case-core-files` | 案件初始化 | 否 |
| A2 | `case-ocr` | 材料扫描+OCR转换 | 否 |
| A3 | `case-archive` | 文件夹自动归档 | 否 |
| A4 | `case-info-extract` | 案件理解 | **是** |
| A5 | `case-feishu-sync` | 飞书同步 | **是** |
| A6 | `case-evidence-cards` | 证据卡片与关系复核 | **是** |
| A7（内部） | `manage_integration_state.py` | 本地状态汇总 | 否 |

**Phase A红线**：必须按 A1→A2→A3→A4→A5→A6 顺序依次执行

### Phase B（九步法）

| 步骤 | 独立Skill | 职责 | 北大法宝复验 | 必须确认 |
|------|----------|------|------------|----------|
| S1 | `case-s1-fixed-claim` | 固定权利请求 | — | **是** |
| S2 | `case-s2-claim-basis` | 请求权基础 | ✅ | **是** |
| S3 | `case-s3-defense` | 抗辩规范 | ✅ | **是** |
| S4 | `case-s4-elements` | 要件拆解 | ✅ | **是** |
| S5 | `case-s5-case-search` | 主张检索 | — | **是** |
| S6 | `case-s6-dispute-matrix` | 争点矩阵 | — | **是** |
| S7 | `case-s7-burden` | 举证责任分配 | ✅ | **是** |
| S8 | `case-s8-fact-finding` | 事实认定 | — | **是** |
| S9 | `case-s9-judgment-predict` | 要件归入与裁判预测 | — | **是** |
| S10 | `case-s10-hallucination` | 法条幻觉校验+门禁 | — | S10守门员 |

### Phase B之后（事件驱动）

| 事件 | 独立Skill | 触发条件 |
|------|----------|----------|
| 写起诉状/答辩状 | `case-filing-gen` | S10通过后，律师确认 |
| 法院短信 | `case-court-sms` | 收到法院短信 |
| 案件讨论 | `case-discussion` | 随时发起 |
| 定期扫描 | `case-scan` | 每周自动/手动触发 |
| 经验卡 | `case-experience-card` | S9完成/开庭后/判决后 |

---

## 交接契约

> 完整内容见 `references/handoff-protocol.md`
> Schema定义见 `schema/handoff_package_schema.json`

每个步骤完成后，必须输出标准 Handoff Package，包含：
- **上游判断摘要**：本步骤做了什么、得出什么结论、有哪些关键发现
- **原始输入材料**：具体依据、原文、文件路径
- **交接备注**：缺失信息、风险提醒、下一步提示

---

## Hooks机制

### 统一Hook脚本

**脚本位置**：`~/.claude/skills/case-os/scripts/case-post-step.sh`

**用法**：
```bash
case-post-step.sh <案件路径> [步骤名称]
```

**执行内容**：
1. Phase B 索引存在时运行 `sync_step_index.py` — 同步 `_index.json`
2. 运行 `manage_integration_state.py refresh` — 生成或刷新本地双文件
3. 运行 `manage_integration_state.py validate` — fail closed 校验状态与白名单摘要

### 每个独立Skill的Hook调用

每个独立Skill的SKILL.md最后一步必须包含：
```markdown
## 后置动作
执行统一Hook脚本：
```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] [步骤名称]
```
```

---

## 独立触发机制

任何独立Skill被直接调用时，系统必须：

### 第一步：强制加载全局规则
```
读取 ~/.claude/skills/case-os/SKILL.md
→ 提取灵魂文件（六大核心原则）
→ 提取全局红线（文件操作铁律、确认机制）
→ 注入当前会话上下文
```

### 第二步：检查前置步骤
```
读取 [案件路径]/_archive/case-os-state.json
读取 [案件路径]/intermediate/_index.json
→ 判断当前Skill的前置步骤是否完成
→ 未完成：提示用户"前置步骤XX未完成，建议先执行XX"
→ 已完成：继续执行
```

### 第三步：执行独立Skill
```
读取独立Skill的SKILL.md
→ 按Skill定义的流程执行
→ 完成后触发Hook（后置脚本）
```

---

## 评估体系

> 完整内容见 `references/evaluation-guide.md`

### 五层评估

| 层级 | 评估内容 | 案件OS对应 |
|------|----------|-----------|
| Trigger | 是否正确触发 | 触发词匹配、案由识别 |
| Intake | 是否识别信息缺失 | A4信息提取完整性 |
| Reasoning | 法律推理是否准确 | S2请求权基础、S9要件归入 |
| Output | 输出是否可用 | 诉讼文书质量 |
| Safety | 是否合规 | 确认机制、免责声明 |

### Hard Fail 条件

- 编造关键事实/证据/法条
- 未标注信息不足却给出确定性结论
- 跳过律师确认直接生成文书
- S10门禁被绕过
- 泄露案件敏感信息

---

## 操作入口

### 命令→Skill映射表

| 命令 | 调用Skill | 说明 |
|------|----------|------|
| `/民事OS` | civil-case-os（总控） | 进入民事总控，自动调度 |
| `/民事案件OS` | civil-case-os（总控） | 进入民事总控，自动调度 |
| `/证据提取` | case-evidence-cards | A5证据卡片与关系复核 |
| `/九步法` | case-s1 → ... → case-s10 | 依次执行九步法 |
| `/继续九步法` | 从上次中断处续跑 | 检查_index.json |
| `/立案材料` | case-filing-gen | 生成起诉状/答辩状 |
| `/请求权基础` | case-s2-claim-basis | 单独执行S2 |
| `/争点矩阵` | case-s6-dispute-matrix | 单独执行S6 |
| `/裁判预测` | case-s9-judgment-predict | 单独执行S9 |
| `/幻觉校验` | case-s10-hallucination | 手动触发S10 |
| `/工商查询 <企业名>` | case-cc-query | 企查查查询 |
| `/风险查询 <企业名>` | case-cc-query | 企查查风险查询 |
| `/状态` | civil-case-os | 查看本地权威状态与九步法进度 |
| `/案件备忘录` | case-discussion | 查看/编辑备忘录 |
| `/定期扫描` | case-scan | 手动触发扫描 |
| `/待处理` | case-scan | 查看待处理队列 |
| `/法院短信` | case-court-sms | 确认期限并写入本地状态 |
| `/经验卡` | case-experience-card | 查看/生成经验卡 |
| `/切换模型 <名称>` | — | 切换模型 |

---

## 文件结构

```
case-os/
├── SKILL.md                          # 总控（本文件）
├── references/                       # 按需加载
│   ├── soul.md                       # 灵魂文件（六大核心原则）
│   ├── redlines.md                   # 全局红线
│   ├── workflow.md                   # 编排流程（Phase A/B/B之后）
│   ├── handoff-protocol.md           # 交接契约协议
│   ├── de-ai-checklist.md            # 去AI味自检清单
│   └── evaluation-guide.md           # 评估指南
├── scripts/                          # 可执行脚本
│   ├── case-post-step.sh             # 统一Hook
│   ├── manage_integration_state.py   # 状态管理
│   └── sync_step_index.py            # 索引同步
├── schema/                           # 数据结构定义
│   ├── nine_step_core_schema.json
│   ├── eight_consistency_check_schema.json
│   ├── handoff_package_schema.json   # 交接包Schema
│   ├── case_os_state_schema.json
│   └── feishu_publish_schema.json
├── examples/                         # 验收样例
│   ├── nine_step_loan_case/
│   └── eight_consistency_quality_check/
├── templates/                        # 模板
│   ├── CLAUDE.template.md
│   └── ...
├── agents/                           # opt-in 子系统
├── data/                             # 数据文件
└── tests/                            # 测试
```

---

## 工具依赖

### 必需工具
- `/Applications/办案工具集/VisionOCR转Markdown.app` — 文件转 Markdown
- `/Applications/办案工具集/微信录屏取证导出.app` — 视频证据截图提取
- `~/.local/bin/qcc-query` — 企查查企业信息查询
- `~/.local/bin/cc-switch-to.sh` — 模型切换脚本

### 辅助工具
- `~/.local/bin/review_with_deepseek.py` — DeepSeek 辅模型质疑脚本
- 元典开放平台 API（open.chineselaw.com）— 类案检索、法条校验

---

## 版本历史

- v11.1 - **改名民事案件OS**：name改为civil-case-os，启动指令改为"民事OS"，消除与刑事OS的歧义
- v11.0 - **四件套改造**：按DEV/HANDOFF/ORCHESTRATION/EVALUATION规范重构，SKILL.md从758行精简到约350行，外迁6个references文件，新增handoff_package_schema.json和evaluation-guide.md
- v10.1-codex-20260604-sync-enhanced - **同步脚本增强**：sync-claude-md-to-feishu.py 新增自动计算举证期限、上诉期截止
- v10.1-codex-20260603-claude-md-sync - **CLAUDE.md 结构化 + 飞书同步**
- v10.0-codex-20260526-a6-internal - **A6 内部门禁纠偏**
- v10.0-codex-20260525-phase1 - **本地结构化集成第一阶段**
- v10.0-codex-20260519-2 - **证据门户与关系推理同步**
- v10.0-codex-20260519 - **GitHub agents 同步**
- v10.0-codex-20260516 - **Codex 视觉能力适配**
- v10.0 - **Phase A 极速化**：9步精简为6步
- v9.0 - **总控重构**：拆分为总控+22个独立Skill+Hook机制
- v8.2 - 证据卡片发言者识别
- v8.1 - 材料转化工具链修正
- v8.0 - Phase B之后流程重构
- v7.2 - 三模型分工 + S10幻觉校验
- v7.1 - Phase A 流程强化
- v6.2 - S0 证据卡片提取 + 五图可视化
- v6.1 - 确认方式双轨制
- v6.0 - 九步法重构
- v5.3 - 仪表盘自动打开
- v5.1 - Git 版本管理底座
- v5.0 - IMA 知识库闭环
- v4.0 - S4 自检阶段
- v3.0 - 统一文件结构
- v2.0 - 四阶段工作流
- v1.0 - 初始版本
