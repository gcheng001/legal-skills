# Legal Skills for Claude Code

[中文文档](#中文) | English

A comprehensive collection of **27 Claude Code skills** for Chinese legal professionals, covering civil litigation analysis, criminal defense workflows, and document automation.

## Why This Matters

Chinese lawyers spend 60%+ of their time on repetitive document processing, case analysis, and procedural compliance. This project brings the **power of agentic AI coding tools to legal practice**, turning Claude Code into a legal workflow engine.

Unlike generic legal AI tools, these skills encode **proven legal methodology** (the "Nine-Step Trial Method" from China's Supreme People's Court) into structured, deterministic workflows that Claude Code executes with human oversight at every decision point.

## Architecture

```
legal-skills/
├── case-os/                      # Civil Case OS (orchestrator, 29KB)
│   ├── scripts/                  # 25+ Python scripts
│   ├── schema/                   # JSON Schema validation
│   ├── templates/                # Visualization & document templates
│   ├── references/               # Legal knowledge bases
│   └── data/defenses/            # 12 case-type defense libraries
│
├── case-s1 ~ case-s10/           # Nine-Step Method (core analysis pipeline)
│   ├── S1: Fixed Claim           # Extract claims, analyze concurrence
│   ├── S2: Claim Basis           # Map to legal provisions
│   ├── S3: Defense               # Identify defenses & counterclaims
│   ├── S4: Elements              # Decompose into provable facts
│   ├── S5: Case Search           # Research favorable authorities
│   ├── S6: Dispute Matrix        # Plaintiff vs defendant collision
│   ├── S7: Burden of Proof       # Allocate & assess proof status
│   ├── S8: Fact Finding          # Predict court findings
│   ├── S9: Judgment Predict      # Predict outcome & amount
│   └── S10: Hallucination Gate   # Anti-hallucination verification
│
├── case-git-init/                # Case directory initialization
├── case-ocr/                     # Document OCR pipeline
├── case-evidence-cards/          # Structured evidence extraction
├── case-filing-gen/              # Generate filing documents
│
├── criminal-case-os/             # Criminal Case OS (orchestrator)
│   └── references/               # Criminal law references
├── criminal-case-review/         # Case file review (legal aid / retained)
├── criminal-meeting/             # Client meeting question lists
├── criminal-defense-strategy/    # Defense path selection
├── criminal-defense-statement/   # Defense statement drafting
├── criminal-investigation/       # Pre-trial documents (bail, etc.)
├── criminal-case-visualization/  # Case visualization charts
├── criminal-non-prosecution/     # Non-prosecution opinions
├── criminal-plea-bargain/        # Plea bargaining strategy
├── criminal-client-comm/         # Client communication
├── criminal-trial-examination/   # Trial questioning & evidence review
│
└── court-sms/                    # Court SMS document downloader
    ├── scripts/                  # Python download automation
    └── references/               # SMS parsing patterns
```

## Civil Case OS — The Nine-Step Method

The core of this project is a complete implementation of the **"Nine-Step Trial Method"** (要件审判九步法), a structured legal analysis framework promoted by China's Supreme People's Court. The workflow:

1. **Fixed Claim** → Extract all claims from the complaint, analyze concurrence
2. **Claim Basis** → Map each claim to its legal provisions, decompose elements
3. **Defense** → Identify all possible defenses, assess threat levels
4. **Elements** → Convert legal elements into provable facts, map evidence gaps
5. **Case Search** → Research favorable laws, precedents, and scholarly views
6. **Dispute Matrix** → Collide plaintiff/defendant analyses, prioritize disputes
7. **Burden of Proof** → Assign burden to each dispute, assess proof status
8. **Fact Finding** → Predict court findings based on evidence and burden
9. **Judgment Predict** → Predict outcome, amount, and reasoning
10. **Hallucination Gate** → Verify all legal citations against real databases, block on hallucination

Each step has **precondition dependencies** — you cannot skip ahead. Most steps require **explicit lawyer confirmation** before proceeding.

### Anti-Hallucination System (S10)

The S10 step is a mandatory quality gate that:
- Verifies every legal citation against the Yuandian legal database API
- Runs "Eight Consistency Checks" across all analytical outputs
- Automatically blocks progression when hallucinations are detected
- Produces a structured audit report

## Criminal Case OS

A parallel system for criminal defense attorneys, covering the full lifecycle:

- **Pre-trial**: Bail applications, non-arrest opinions, detention necessity reviews
- **Review**: Structured case file review (supports both legal aid and retained cases)
- **Strategy**: Defense path selection with strength assessment
- **Trial**: Questioning outlines, evidence examination, defense statements
- **Negotiation**: Plea bargaining strategy with sentencing prediction
- **Communication**: Client-facing reports (with red-line protection of defense strategy)

## Court SMS — Document Downloader

Automates processing of Chinese court delivery notifications:
- Parses SMS from 3 major court delivery platforms
- Downloads all legal documents via API
- Extracts key dates from summons and hearing notices
- Optional: writes to Feishu/Lark bitable

## Quick Start

```bash
# Clone the collection
git clone https://github.com/goacheng001/legal-skills.git

# Copy a skill to your Claude Code skills directory
cp -r legal-skills/case-os ~/.claude/skills/
cp -r legal-skills/criminal-case-os ~/.claude/skills/

# Start Claude Code and invoke
claude
# Then type: /case-os or /criminal-case-os
```

## Dependencies

| Dependency | Purpose | Install |
|------------|---------|---------|
| Python 3.9+ | Script execution | System |
| `requests` | API calls | `pip install requests` |
| `poppler` | PDF text extraction | `brew install poppler` |
| `lark-cli` | Feishu integration (optional) | `npm install -g @larksuiteoapi/lark-cli` |
| Yuandian API | Legal database (S10 verification) | API key required |

## For Codex for Open Source

This project is a demonstration of what's possible when agentic coding tools are applied to **domain-specific professional workflows**. Key metrics:

- **27 skills** covering the full lifecycle of Chinese civil and criminal legal work
- **100,000+ lines** of structured legal workflow instructions
- **25+ Python scripts** for automation (document download, analysis, report generation)
- **12 defense knowledge bases** covering major Chinese civil case types
- **Anti-hallucination system** with real legal database verification
- **Active production use** in real legal practice

The project demonstrates that Claude Code is not just a coding tool — it's a **general-purpose agent platform** capable of encoding and executing complex domain expertise with appropriate human oversight.

## Contributing

Contributions welcome! Please see individual skill directories for their specific documentation.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## 中文

### 项目概述

一套为律师和法律从业者设计的 Claude Code 技能集合，共 27 个技能，覆盖：

**民事案件OS（16个技能）**：
- 总控调度器（case-os）+ 九步法分析流水线（S1-S10）
- 案件生命周期管理（初始化/OCR/归档/信息提取/证据卡片/起诉状生成）

**刑事案件OS（11个技能）**：
- 总控调度器（criminal-case-os）
- 全流程覆盖：侦查→阅卷→会见→辩护策略→辩护词→庭审→认罪认罚→不起诉
- 可视化图表生成

**独立技能**：
- 法院短信文书自动下载（court-sms）

### 核心设计理念

1. **前置条件依赖链**：不可跳跃执行，确保分析完整性
2. **律师确认机制**：关键步骤必须律师显式确认
3. **幻觉阻断**：S10 幻觉校验门禁，法条引用逐条核验
4. **职责分离**：每个技能专注单一功能，总控负责调度

### 安装

```bash
git clone https://github.com/goacheng001/legal-skills.git
cp -r legal-skills/case-os ~/.claude/skills/
```
