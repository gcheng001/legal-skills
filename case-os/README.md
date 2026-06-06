# 民事案件OS (Civil Case OS)

民事案件操作系统 — 民事案件分析、文书起草、诉讼策略一站式工具。

## 功能

- 案件材料智能分析
- 诉讼请求自动生成
- 答辩规范数据库（12类纠纷）
- 原告/被告九步法办案模板
- 证据卡片库管理

> 兼容说明：目录名和 skill 名继续保留 `case-os`，历史触发词“案件OS”仍可使用，但语义上指向“民事案件OS”。刑事案件专项流程使用 `criminal-case-os`。

## 目录结构

```
case-os/
├── SKILL.md          # 技能定义文档
├── AGENTS.md         # Agent角色定义
├── scripts/          # Python分析脚本
├── templates/        # 案件模板
│   ├── elements/     # 纠纷要素定义
│   ├── intermediate/  # 中间文书模板
│   └── 案件仪表盘.html
└── data/
    └── defenses/     # 答辩规范数据
```

## 使用方式

将本仓库克隆到 `~/.claude/skills/case-os/` 即可。

```bash
git clone https://github.com/goacheng001/case-os.git ~/.claude/skills/case-os
```
