# 案件OS — Claude Code 智能案件操作系统

一套基于 Claude Code 的完整法律案件分析系统，涵盖材料处理、九步法分析、文书生成的全流程。

## 系统架构

```
案件OS（总控 case-os）
├── Phase A：材料处理（A1-A9）
│   ├── A1 Git初始化（case-git-init）
│   ├── A2 材料扫描+OCR（case-ocr）
│   ├── A3 自动归档（case-archive）
│   ├── A4 信息提取（case-info-extract）
│   ├── A5 笔记检索（case-notes-search）
│   ├── A6 案件摘要（case-summary）
│   ├── A7 证据卡片（case-evidence-cards）
│   ├── A8 核心文件（case-core-files）
│   └── A9 仪表盘（case-dashboard）
│
├── Phase B：九步法分析（S1-S10）
│   ├── S1 固定权利请求（case-s1-fixed-claim）
│   ├── S2 请求权基础（case-s2-claim-basis）
│   ├── S3 抗辩规范（case-s3-defense）
│   ├── S4 要件拆解（case-s4-elements）
│   ├── S5 主张检索（case-s5-case-search）
│   ├── S6 争点矩阵（case-s6-dispute-matrix）
│   ├── S7 举证责任（case-s7-burden）
│   ├── S8 事实认定（case-s8-fact-finding）
│   ├── S9 要件归入与裁判预测（case-s9-judgment-predict）
│   └── S10 幻觉校验（case-s10-hallucination）
│
└── 事件驱动
    ├── 起诉/答辩状生成（case-filing-gen）
    ├── 法院短信处理（case-court-sms）
    ├── 案件讨论（case-discussion）
    ├── 定期扫描（case-scan）
    └── 经验卡（case-experience-card）
```

## 目录结构

```
case-os/
├── skills/
│   ├── case-os/              # 主控skill
│   │   ├── SKILL.md          # 主控定义
│   │   ├── AGENTS.md         # 四角色内阁系统
│   │   ├── scripts/          # 23个Python/Shell脚本
│   │   ├── templates/        # 模板文件（HTML/MD/YAML/MMD）
│   │   │   ├── intermediate/ # 九步法中间产物模板
│   │   │   ├── elements/     # 12种纠纷类型要件定义（YAML）
│   │   │   ├── input-cards/  # 输入卡模板
│   │   │   ├── 经验卡/       # 经验卡模板（v1/v2/v3）
│   │   │   └── 可视化/       # 作战地图/对抗矩阵/决策树模板
│   │   ├── data/
│   │   │   └── defenses/     # 12种纠纷类型抗辩数据（JSON）
│   │   └── agents/
│   └── case-s*/              # 22个子skill（各含SKILL.md）
│
├── references/               # 参考文件
│   ├── format-guide.md       # 输出格式规范（官职映射、仪式感格式）
│   └── omc-guide.md          # OMC多Agent命令速查
│
├── config/
│   └── CLAUDE.md.example     # 全局配置示例
│
├── install.sh                # 一键安装脚本
└── README.md                 # 本文件
```

## 安装

### 方式一：一键安装（推荐）

```bash
git clone https://github.com/goacheng001/case-os.git /tmp/case-os-install
cd /tmp/case-os-install
chmod +x install.sh
./install.sh
```

### 方式二：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/goacheng001/case-os.git /tmp/case-os-install

# 2. 复制 skills 到 Claude Code 技能目录
cp -r /tmp/case-os-install/skills/* ~/.claude/skills/

# 3. 复制参考文件
mkdir -p ~/.claude/references
cp /tmp/case-os-install/references/* ~/.claude/references/

# 4. 配置全局CLAUDE.md（可选）
# 将 config/CLAUDE.md.example 的内容合并到 ~/.claude/AGENTS.md
# 或参考其内容自行配置
```

### Claude Code 适配

Claude Code 使用相同目录结构，确保 `~/.claude/skills/` 和 `~/.claude/references/` 下有对应文件即可。

## 使用方法

### 触发案件OS

在 Claude Code 中输入以下任意触发词：

```
案件OS
case-os
case os
```

### 工作流程

1. **初始化案件**：在案件目录下触发案件OS，自动创建 Git 仓库和目录结构
2. **Phase A（材料处理）**：放入材料文件，系统自动 OCR、归档、提取信息、生成证据卡片
3. **Phase B（九步法分析）**：按 S1→S10 逐步分析，每步完成后自动更新仪表盘
4. **事件驱动**：随时可用起诉状生成、法院短信处理、案件讨论等功能

### 案件目录结构

```
案件目录/
├── CLAUDE.md              # 案件大脑（概览 + 任务面板 + 操作入口）
├── LOG.md                 # 工作日志
├── 案件仪表盘.html         # 可视化仪表盘
├── 案件确认表.html         # 九步法确认表
├── _archive/              # 归档文件
├── 原告材料/              # 原告方材料
├── 被告材料/              # 被告方材料
├── 法院文书/              # 法院文件
├── 分析材料/              # 分析报告
├── 截图证据/              # 视频截图PDF
├── ISSUES/                # 问题追踪
├── intermediate/          # 九步法中间产物
│   ├── S0-证据卡片库.md
│   ├── 原告九步法/        # S1-S10各步分析
│   ├── 被告九步法/        # S1-S10各步分析
│   └── _index.json        # 18格进度索引
└── 案件备忘录.md          # 讨论记录
```

## 依赖说明

### MCP 服务器（可选但推荐）

| MCP 服务 | 用途 | 影响范围 |
|----------|------|----------|
| `mcp__pkulaw-*`（北大法宝） | 法条验证、案例检索 | S2/S3/S4/S7/S10 需用法条校验；无此服务时法条验证功能不可用 |
| `mcp__gbrain-*`（知识库） | 经验卡写入知识库 | 仅影响经验卡持久化；无此服务时经验卡功能不可用 |

> **无MCP时**：九步法核心流程仍可正常运行，但法条校验和经验卡功能降级。

### 本地工具（可选）

| 工具 | 路径 | 用途 | 缺失影响 |
|------|------|------|----------|
| 微信取证 | `/Applications/办案工具集/微信录屏取证导出.app` | 微信录屏取证 | 微信取证功能不可用 |
| 企查查 | `~/.local/bin/qcc-query` | 企业信息查询 | 企业背调需手动进行 |
| 模型切换 | `~/.local/bin/cc-switch-to.sh` | Phase A/B模型切换 | 需手动切换模型 |
| DeepSeek校验 | `~/.local/bin/review_with_deepseek.py` | S10幻觉交叉校验 | S10仅用单模型校验 |

> **缺失本地工具不影响核心九步法流程**，仅对应特定功能降级。

### 支持的纠纷类型（12种）

买卖合同纠纷、侵权责任纠纷、劳动争议、建设工程合同纠纷、房屋租赁合同纠纷、服务合同纠纷、机动车交通事故责任纠纷、民间借贷纠纷、离婚纠纷、竞业限制纠纷、继承纠纷、股权转让纠纷

## 核心原则

1. **全程辩论**：大理寺从对立面质疑，确保分析全面
2. **系统独立立场**：不代表任何一方，客观分析
3. **当场解决问题**：发现问题立即处理，不留技术债
4. **完整讨论记录**：超过3轮讨论自动记录到备忘录
5. **确认后才出诉状**：必须完成九步法确认后才生成起诉/答辩状

## License

MIT
