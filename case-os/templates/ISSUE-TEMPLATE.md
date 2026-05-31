---
id: 000
title: <Issue 标题>
type: 答辩点 | 检索 | 证据补强 | 文书段落 | 其他
status: open
created: YYYY-MM-DD
closed:
assignee: Claude Code | 主办律师 | 助理
---

## 问题描述
<What：这个 Issue 要解决什么问题？>

## 目标和验收标准
<Done when：满足什么条件可以关闭这个 Issue？>
- [ ] 条件 1
- [ ] 条件 2

## 关联材料
<指向案件仓库内的 Markdown 文件，使用相对路径>
- [起诉状](../../markdown/起诉状.md)
- [合同](../../markdown/合同.md)

## 讨论/进展
- YYYY-MM-DD [执行者]：[动作/发现/决策]

## 结果
<完成后填写：最终产出、存放位置、对主文书的影响>

---

**说明**：
- 此文件位于 `ISSUES/open/<编号-标题>.md`，完成后 `git mv` 到 `ISSUES/closed/`
- 对应工作应在独立分支（`issue-<编号>-<简短描述>`）完成，合并前审核 diff
- 跨案件的通用研究请走飞书待办，不走 Issue
