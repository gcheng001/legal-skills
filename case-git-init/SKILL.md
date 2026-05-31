---
author: Legal Skills Project

# case-git-init（A1）案件初始化

## 工作定位

一次性完成案件目录初始化：Git仓库 + 文件夹结构 + 核心文件（CLAUDE.md + LOG.md）。

**前置条件**：无（Phase A 第一步）
**必须确认**：否（自动执行，事后汇报）
**执行后**：调用Hook脚本更新状态

---
author: Legal Skills Project

## 执行流程

### 第一步：Git初始化

```bash
cd "[案件根目录]"

# 检查是否已初始化
if [ ! -d ".git" ]; then
    git init
    cp ~/.claude/skills/case-os/templates/gitignore.template .gitignore
    echo "✅ Git仓库已初始化（本地仓库，永不推送云端）"
else
    echo "⏭️ Git仓库已存在，跳过初始化"
fi
```

### 第二步：创建目录结构

```bash
mkdir -p ISSUES/open ISSUES/closed _archive
mkdir -p 原告材料 被告材料 法院文书 分析材料 截图证据
mkdir -p intermediate/原告九步法 intermediate/被告九步法 intermediate/FINAL
mkdir -p _archive/markdown
```

### 第三步：生成 CLAUDE.md

使用模板 `~/.claude/skills/case-os/templates/阶段追踪.md` 作为参考，在案件根目录创建：

```markdown
# [案件名称] 案件大脑

> *本文件由案件OS v10.0生成*

## 案件概览
| 项目 | 内容 |
|------|------|
| 案号 | （待A4提取） |
| 案由 | （待A4提取） |
| 原告 | （待A4提取） |
| 被告 | （待A4提取） |
| 案件金额 | （待A4提取） |
| 受诉法院 | （待A4提取） |
| 代理方 | （待确认） |

## 材料清单
（待A3归档后自动更新）

## 任务面板
- [ ] A1 案件初始化
- [ ] A2 材料OCR转换
- [ ] A3 材料归档
- [ ] A4 案件理解
- [ ] A5 证据卡片与关系复核
- [ ] A6 内部门禁（A5确认后自动完成）
- [ ] Phase B：九步法分析
- [ ] Phase B+：后续工作

## 操作入口
| 指令 | 功能 |
|------|------|
| `/九步法` | 执行S1-S10全流程分析 |
| `/立案材料` | 生成起诉状/答辩状 |
| `/案件扫描` | 定期扫描新增文件 |
| `/经验卡` | 生成经验卡 |
```

若CLAUDE.md已存在（续跑模式），跳过生成。

### 第四步：生成 LOG.md

```markdown
# [案件名称] 工作日志

## [当前日期]
- [当前时间] A1 案件初始化完成（Git + 目录结构 + 核心文件）
```

若LOG.md已存在（续跑模式），追加新条目而非覆盖。

### 第五步：Git提交

```bash
cd "[案件根目录]"
git add -A
git commit -m "chore: A1 案件初始化（Git仓库 + 目录结构 + 核心文件）"
```

### 第六步：初始化本地结构化状态

```bash
# 首次生成固定 case_id 和本地白名单摘要；不写旧状态文件，不访问外部系统
python3 ~/.claude/skills/case-os/scripts/manage_integration_state.py init "[案件路径]"
```

### 第七步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] A1
```

---
author: Legal Skills Project

## 红线

- ❌ **禁止** `git remote add`（永不关联远程仓库）
- ❌ **禁止** `git push`（永不推送云端）
- ❌ 不覆盖已有 CLAUDE.md / LOG.md（续跑模式追加）
- ✅ 目录结构必须完整创建

---
author: Legal Skills Project

## 输出

- `.git/` + `.gitignore` — 本地版本管理
- `ISSUES/open/`、`ISSUES/closed/` — 问题追踪
- `_archive/` — 归档目录
- `原告材料/` `被告材料/` `法院文书/` `分析材料/` `截图证据/` — 材料分类
- `intermediate/` — 中间产物（含九步法双视图目录）
- `CLAUDE.md` — 案件大脑
- `LOG.md` — 工作日志
- `_archive/case-os-state.json` — 本地机器权威状态
- `_archive/feishu-publish.json` — 本地白名单摘要（外发关闭）

---
author: Legal Skills Project

## 错误处理

- Git未安装 → 提示用户安装Git
- 目录无写入权限 → 提示用户检查权限
- `.git` 已存在 → 跳过Git初始化，仅创建缺失的目录和文件
