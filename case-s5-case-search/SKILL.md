---
author: Legal Skills Project

# case-s5-case-search（S5）主张检索

## 工作定位

围绕要件事实检索有利法规、类案、学理，评估每项检索结果的综合支持度。

**前置条件**：S4（要件拆解）完成
**必须确认**：**是**（律师必审）
**北大法宝复验**：不需要
**执行后**：调用Hook脚本更新状态

---
author: Legal Skills Project

## 执行流程

### 第一步：读取S4文件

读取 `intermediate/原告九步法/S4-要件拆解/` 中的要件事实和证据缺口。

### 第二步：检索有利法规

针对每个要件事实，检索支持性法规：
- 法律条文
- 司法解释
- 部门规章

### 第三步：检索类案

调用元典开放平台API检索类案：

```python
# 类案检索
mcp__yuandian-law-search__search_case(text="建设工程合同纠纷 结算争议")
```

### 第四步：检索学理

检索学术观点、法律评论等支持性文献。

### 第五步：评估支持度

对每项检索结果评估：
1. **相关性**：与本案要件的匹配程度
2. **权威性**：来源的权威程度
3. **时效性**：是否最新规定
4. **综合支持度**：高/中/低

### 第六步：生成S5文件

```markdown
# S5 主张检索

## 要件1：[要件事实]
### 法规支持
| 法规名称 | 条款 | 内容摘要 | 支持度 |
|----------|------|----------|--------|
| ... | ... | ... | 高 |

### 类案支持
| 案号 | 法院 | 裁判观点 | 相关度 |
|------|------|----------|--------|
| ... | ... | ... | 高 |

### 学理支持
[学术观点]
```

保存到 `intermediate/原告九步法/S5-主张检索/`

### 第七步：律师必审

**红线**：AI不得自主落定，结构化状态保持 `pending_review`。

展示检索结果，等用户确认。

### 第八步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S5-主张检索/`

### 第九步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S5
```

---
author: Legal Skills Project

## 红线

- ❌ **AI不得自主落定**
- ❌ 结构化状态不得自动越过 `pending_review`

---
author: Legal Skills Project

## 工具依赖

- `mcp__yuandian-law-search__search_case` — 类案检索

---
author: Legal Skills Project

## 输出

- `intermediate/原告九步法/S5-主张检索/`
- `intermediate/被告九步法/S5-主张检索/`
