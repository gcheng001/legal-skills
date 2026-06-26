---
name: paper-os
description: '论文写作操作系统总控。统一入口和调度器，按"选题→文献→写作→质检→答辩"主线调度8个独立Skill，支持断点续办。TRIGGER when: 用户输入包含"论文OS""论文写作OS""paper-os"（不区分大小写）。'
metadata:
  author: Legal Skills Project
  version: 2.0
  trigger:
    - 论文OS
    - 论文写作OS
    - paper-os
    - paper os
---

# paper-os 论文写作操作系统（总控）v2.0

## 工作定位

`paper-os` 是论文写作操作系统的**统一入口和调度器**，承担三件事：

1. **加载核心原则** — 七条写作原则（完整版 `references/soul.md`），所有子Skill必须遵守
2. **调度执行** — 判断当前论文项目状态，按流程表顺序内联执行子Skill
3. **独立触发保障** — 子Skill被单独调用时，强制先加载核心原则

**调度方式**：内联执行子Skill的SKILL.md逻辑（读取并按其流程执行），不使用Skill工具调用。

**定位**：法律论文为主，集成元典法律检索；通用学术论文亦可适用（法律检索部分按需跳过）。

---

## 核心原则（摘要）

> 完整内容见 `references/soul.md`

1. **人主导AI辅助** — 选题、观点、结论必须出自用户，AI不替代学术判断
2. **先研究后写作** — 没有认知差不动笔，认知差是论文价值的唯一衡量标准
3. **当场解决问题** — 自检/核查发现的问题在该步解决，不带病进下一步
4. **幽灵文献零容忍** — 所有引用必须过S6事实核查才能进终稿
5. **输出去AI味** — 论文正文类产出输出前强制执行去AI味检查（`references/de-ai-checklist.md`）
6. **确认门禁** — `status: pending_review` 只能由用户确认翻转，AI不得自改
7. **LOG.md同步更新** — 每个关键步骤完成后必须追加LOG.md

**学术诚信提示**：用户须遵守所在机构的AI使用规范，终稿建议按要求声明AI辅助情况。

---

## 流程表

| 步骤 | 子Skill | 职责 | 门禁 |
|------|---------|------|------|
| S1 | `paper-s1-topic` | 选题全流程 → 选题报告 | **硬**（确认后才进S2） |
| S2 | `paper-s2-literature` | 文献筛选/阅读/笔记 → 文献矩阵 | 软（汇报即可） |
| S3 | `paper-s3-writing` | 认知差定位+写作蓝图+分节起草 | **蓝图硬**，章节初稿软 |
| S4 | `paper-s4-discussion` | 讨论与结论专项写作 | 软 |
| S5 | `paper-s5-checklist` | 七问逆序自检 | **硬**（七项全过或用户明示接受） |
| S6 | `paper-s6-factcheck` | AI事实核查+元典法条案例核验 | **硬**（△/×逐条用户裁决） |
| S7 | `paper-s7-ppt` | 答辩PPT大纲与生成 | **硬**（大纲确认后才生成slides） |
| S8 | `paper-s8-defense` | 答辩表现辅导+模拟答辩 | 软 |

> 各步骤详细编排见 `references/workflow.md`
> 步骤间交接规范见 `references/handoff-protocol.md`

### 允许跳步规则

论文场景允许带警告跳步。例如用户拿着已写完的论文直接进S5/S6。

**唯一例外**：S3起草动作要求S1选题已确认，或用户明示豁免。

跳步时输出：`⚠️ 前置步骤S<X>未完成，已跳过。后续如需回溯请随时告知。`

---

## 断点续办

进入已有项目或用户说"继续论文"时：

1. 读 `PAPER.md` → 题目、研究问题、当前阶段
2. 读 `LOG.md` → 工作日志
3. 读 `state.json` → 权威断点状态（Schema: `schema/paper_os_state_schema.json`）
4. 检查 `outputs/` → 各步骤实际产物

输出断点摘要：
```
📌 论文：<题目>
✅ 已完成：S1-S3
⏳ 当前步骤：S4（讨论与结论）
📋 待确认：无
➡️ 下一步：继续S4 或 跳到S5自检
```

**红线**：不得重做已确认步骤。

---

## 首次进入：项目初始化

用户首次说"论文OS"且无已有项目时：

1. 询问论文短名（用于目录名）和保存位置（默认 `~/Documents/论文/<短名>/`）
2. 创建项目目录结构（见下方）
3. 从 `templates/PAPER.template.md` 初始化 PAPER.md
4. 从 `templates/state.template.json` 初始化 state.json
5. 创建空 LOG.md（首行 `# 论文工作日志`）
6. 创建 materials/ 和 outputs/ 目录
7. 进入S1选题

### 项目目录结构

```
<论文项目>/
├── PAPER.md            # 概览：题目、研究问题、认知差定位、当前阶段
├── LOG.md              # 工作日志（追加式）
├── state.json          # 权威断点状态
├── materials/          # 文献PDF、数据、导师意见等原料
└── outputs/
    ├── S1-选题/
    ├── S2-文献/
    ├── S3-写作/
    ├── S4-讨论结论/
    ├── S5-自检/
    ├── S6-核查/
    ├── S7-答辩PPT/
    └── S8-答辩/
```

---

## 子Skill独立触发协议

任何子Skill被直接调用时（如用户说"论文事实核查"）：

### 第一步：注入原则
读取 `~/.shared-skills/paper-os/references/soul.md`，注入当前会话。

### 第二步：定位项目
- 有论文项目目录 → 检查前置产物，缺失则提示但允许继续
- 无项目 → 进入**独立模式**：直接向用户索要输入，产出存用户指定位置（默认桌面），不建状态文件

### 第三步：执行
读取子Skill的SKILL.md，按流程执行。完成后更新 state.json + LOG.md（独立模式跳过）。

---

## 状态管理

### state.json

极简结构，AI直接读写。字段定义和枚举值见 `schema/paper_os_state_schema.json`。

**status 枚举**：`pending` → `in_progress` → `pending_review`（硬门禁）→ `confirmed`（用户翻转）/ `reported`（软确认）

**红线**：AI不得在没有用户明确确认语句时写入 `confirmed`。

### 产物文件 frontmatter

每个 outputs 产物头部带 YAML frontmatter，结构定义见 `schema/handoff_package_schema.json`。

---

## 生态集成

| 工具 | 步骤 | 方式 |
|------|------|------|
| 元典 MCP | S1选题验证、S2规范材料、S6法条案例核查 | S1沿用集成表；S6指定 ft_detail + qwal/ptal_search |
| de-ai-polish | S3/S4 **强制**，S1建议 | 执行流程倒数第二步 |
| md2word | 终稿导出 | `/导出Word` 命令，paper-os专属预设（题目二号宋体/正文四号仿宋，见 references/format-spec.md） |
| socratic-coach | S1 可选 | 选题模糊时触发 |
| frontend-slides / guizang-ppt-skill | S7 可选出口 | 与Gamma并列 |

---

## 终稿格式规范

论文终稿格式（字体版面 + 引注体例）统一遵循 [`references/format-spec.md`](references/format-spec.md)。

**字体版面**（已固化为 md2word 预设 `paper-os.yaml`）：
- 论文题目（H1）：二号宋体，加粗居中
- 正文：四号仿宋，首行缩进2字符，1.5倍行距，两端对齐
- 章节标题：黑体分级（H2三号 / H3四号 / H4四号加粗）

**引注体例**：脚注与参考文献遵循《中文引注体例》（纸质文献、网络/微信公众号、学位论文、法律文件、司法案例的引用格式）。**S3/S4 写作时即按此规范标注**，S6 事实核查据此核对引用准确性。

`/导出Word` 默认套用 md2word 的 `paper-os` 预设（`md2word/assets/presets/paper-os.yaml`），一键输出符合上述版面规范的 Word；目标期刊/学校要求不同时，按 format-spec.md 第四节调整入口修改。

---

## 命令映射表

| 命令 | 调用 | 说明 |
|------|------|------|
| `/论文OS` | paper-os（总控） | 进入总控，自动调度 |
| `/继续论文` | paper-os | 断点续办 |
| `/论文状态` | paper-os | 查看state.json进度 |
| `/论文选题` | paper-s1-topic | 单独执行S1 |
| `/读文献` | paper-s2-literature | 单独执行S2 |
| `/写作蓝图` | paper-s3-writing | 单独执行S3 |
| `/讨论结论` | paper-s4-discussion | 单独执行S4 |
| `/七问自检` | paper-s5-checklist | 单独执行S5 |
| `/论文事实核查` | paper-s6-factcheck | 单独执行S6 |
| `/答辩PPT` | paper-s7-ppt | 单独执行S7 |
| `/模拟答辩` | paper-s8-defense | 单独执行S8 |
| `/导出Word` | md2word | 终稿导出（默认套 paper-os 预设，字体版面+引注体例见 references/format-spec.md） |

---

## 文件结构

```
paper-os/
├── SKILL.md                           # 总控（本文件）
├── references/                        # 按需加载
│   ├── soul.md                        # 核心原则（七条）
│   ├── workflow.md                    # 编排流程（各步骤详细定义）
│   ├── handoff-protocol.md            # 交接契约（步骤间数据传递规范）
│   ├── evaluation-guide.md            # 评估指南（五层评估+硬失败条件）
│   ├── de-ai-checklist.md             # 去AI味自检清单
│   ├── format-spec.md                 # 终稿格式规范（字体版面+引注体例）
│   └── tools.md                       # 工具推荐（按步骤分组）
├── schema/                            # 数据结构定义
│   ├── paper_os_state_schema.json     # state.json schema
│   └── handoff_package_schema.json    # 产物frontmatter schema
└── templates/                         # 模板
    ├── PAPER.template.md              # 论文项目概览模板
    └── state.template.json            # 初始状态模板
```

---

## 方法论来源

本体系方法论蒸馏自《AI高质量论文写作法》（选题/文献/写作/答辩/工具推荐五篇）。
各子Skill的 references/ 目录保存逐字固化的关键资产（提示词模板、样例解析等）。
工具推荐精编见 `references/tools.md`。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.1 | 2026-06-26 | **新增终稿格式规范**：references/format-spec.md（字体版面+引注体例）；md2word 新增 paper-os.yaml 预设（题目二号宋体/正文四号仿宋），`/导出Word` 默认套用，SKILL.md 增「终稿格式规范」小节 |
| v2.0 | 2026-06-25 | **四件套改造**：按DEV/HANDOFF/ORCHESTRATION/EVALUATION规范重构，新增handoff-protocol.md、evaluation-guide.md、de-ai-checklist.md、schema/，SKILL.md精简到~200行 |
| v1.0 | 2026-06-11 | 初版：8步骤体系 + 总控 + 轻量状态管理 |
