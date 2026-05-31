---
name: case-s2-claim-basis
description: '九步法S2-请求权基础。确定每项请求权所依据的法律规范，鉴别法条性质（完全性vs倡导性），拆解构成要件。TRIGGER when: 用户输入"请求权基础"或由case-os总控调度。'
---

# case-s2-claim-basis（S2）请求权基础

## 工作定位

确定每项请求权所依据的法律规范（精确到条款号），鉴别法条性质（完全性法条 vs 倡导性法条），拆解构成要件。

**法条性质要求**：对应的法律条文应当首先是含有实体权利处理的完全性法条（具有构成要件及法律效果的规定），而不是倡导性法条。

**前置条件**：S1（固定权利请求）确认
**必须确认**：**是**（律师终选）
**法条复验**：**必须**（优先使用元典）
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取S1文件

读取 `intermediate/原告九步法/S1-固定权利请求/` 中的诉讼请求清单。

### 第二步：确定法律规范

**红线**：针对每项请求权，都必须确定所依据的法律规范，全部录入 `legal_articles` 数组。

**操作步骤**：
1. 读取 S1 的所有诉讼请求
2. 针对每项请求权，确定所依据的法律规范：
   - 法律名称（如《民法典》）
   - 条款号（如第577条）
   - 具体内容
3. **所有法律依据都必须进入 `legal_articles` 数组**
4. 不得只在正文中写法条，JSON 中遗漏

**多请求权案件必须覆盖**：
- 追偿权请求权：《民法典》第1191条或其他追偿权规范
- 保险合同 / 交通事故保险赔付请求权：《民法典》第1213条或其他保险合同规范
- 其他请求权基础：根据具体案情确定

### 第三步：拆解构成要件

将每条法律规范拆解为构成要件：
1. 主体要件
2. 行为要件
3. 结果要件
4. 因果关系要件
5. 其他要件

### 第三步A：法条性质鉴别（新增）

**鉴别依据**：引用 live case-os 资源
- `../case-os/references/nine_step_checklist.json` 第 16、17 项
- `../case-os/schema/nine_step_core_schema.json` s2_claim_bases 定义

**鉴别标准**：
- **完全性法条**：具有构成要件及法律效果的规定（可作为请求权基础）
  - ✅ 包含构成要件要素（主体、行为、结果、因果关系）
  - ✅ 包含法律效果要素（权利、义务、责任）
  - ✅ 可以作为司法裁判的直接依据
- **倡导性法条**：仅宣示价值或原则，无具体构成要件（不可作为请求权基础）
  - ❌ 宣示性、原则性规定
  - ❌ 无具体构成要件
  - ❌ 无明确法律效果
  - ❌ 需要通过其他完全性法条实现

**鉴别流程**：
1. 读取法条内容（来自元典检索结果）
2. 判断是否包含构成要件要素
3. 判断是否包含法律效果要素
4. 标注法条性质：`statute_nature: "完全性法条"` 或 `"倡导性法条"`
5. 如为倡导性法条，设置 `needs_replacement: true` 并提示律师寻找替代性完全性法条

**输出字段**（供 S4 读取）：
- `statute_nature`：法条性质（完全性法条/倡导性法条）
- `constitutive_elements`：构成要件数组
- `legal_effect`：法律效果数组
- `needs_replacement`：是否需要替换（true/false）

### 第四步：法条复验（元典优先）

**优先使用元典Skill**：

```bash
cd ~/.claude/skills/law-search
python3 scripts/yd_search.py search "民法典 第577条" --sxx 现行有效
python3 scripts/yd_search.py detail "民法典" --ft-name "第577条"
```

**备用方案**（需手动启用北大法宝MCP）：

> ⚠️ 北大法宝MCP当前已禁用。如需使用，请在 settings.local.json 中添加相应权限。

```python
# 需要先在 settings.local.json 中启用：
# "mcp__pkulaw-law-search__search_article"
# "mcp__pkulaw-law-search__get_article"

mcp__pkulaw-law-search__search_article(text="民法典 第577条")
mcp__pkulaw-law-search__get_article(title="中华人民共和国民法典", number="577")
```

**复验内容**：
- 法条是否存在
- 法条内容是否正确
- 是否有最新司法解释

### 第五步：生成S2文件

**输出格式**：JSON frontmatter + Markdown 正文

**JSON frontmatter**（包含法条性质字段）：

```json
---
{
  "step_id": "S2",
  "claim_basis_analysis": {
    "identified_rights_bases": {
      "defendant_1": {
        "party": "被告名称",
        "legal_relationship": "法律关系",
        "role": "角色",
        "rights_basis": "权利基础"
      }
    },
    "legal_articles": [
      {
        "法律名称": "民法典",
        "条款号": "第577条",
        "法条内容": "...",
        "法条性质": "完全性法条",
        "statute_nature": "完全性法条",
        "constitutive_elements": ["构成要件1", "构成要件2"],
        "legal_effect": ["法律效果1", "法律效果2"],
        "needs_replacement": false,
        "元典复验结果": {
          "exists": true,
          "content_match": true,
          "source": "元典"
        }
      }
    ],
    "basis_confirmation_records": {
      "法官释明过程": [...],
      "最终确认": "确认结果"
    }
  }
}
---
```

**Markdown 正文**：

```markdown
# S2 请求权基础

## 请求权1：[请求内容]
### 法律依据
- 《民法典》第577条：[内容]
- 法条性质：✅ 完全性法条
- 法条复验：✅ 通过（元典）

### 构成要件
1. [要件1]
2. [要件2]
...

## 法条性质鉴别说明
### 完全性法条
- 具有构成要件及法律效果的规定
- 可作为请求权基础

### 倡导性法条
- 仅宣示价值或原则
- 不可作为请求权基础
```

保存到 `intermediate/原告九步法/S2-请求权基础/`

**⚠️ MD-JSON 双向同步（强制执行）**：
- JSON 中的 `statute_nature` 字段必须同步到 MD 正文的"法条性质验证"章节
- MD 正文中不得出现 JSON 未包含的法条引用（如 MD 额外引用了民法典791条、793条，但 JSON 未包含 → 必须在 JSON 中补充对应条目，或从 MD 中移除）
- 生成完成后必须自检：JSON 中的每个法条都能在 MD 中找到对应行，反之亦然
- 常见错误：法条性质验证数据在 JSON 中完整，但 MD 正文遗漏"法条性质验证"章节 → 必须补全

### 第六步：律师终选确认

展示法律依据和构成要件，等用户确认最终选择。

### 第七步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S2-请求权基础/`

### 第八步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S2
```

---

## 红线

- ❌ **必须法条复验**（优先使用元典），复验徽章方可 ✅
- ❌ 律师终选确认后才能进入下一步

### 多请求权结构化红线（新增）

**绝对要求**：所有请求权基础必须结构化到 JSON frontmatter 的 `legal_articles` 数组中。

1. **读取 S1 所有诉讼请求**：
   - 必须完整读取 S1 中的每一项诉讼请求
   - 不得遗漏任何一项请求权

2. **每项请求权基础都必须进入 `legal_articles`**：
   - 追偿权请求：《民法典》第1191条
   - 保险合同请求：《民法典》第1213条
   - 其他请求权基础：根据案情确定
   - **正文出现的核心法条，JSON `legal_articles` 中必须同步出现**

3. **每条法律依据必须包含完整字段**：
   - `法律名称`
   - `条款号`
   - `法条内容`
   - `法条性质`
   - `statute_nature`
   - `constitutive_elements`
   - `legal_effect`
   - `needs_replacement`
   - `元典复验结果`

4. **自检要求**：
   - 生成后检查 JSON `legal_articles` 数组
   - 确认所有请求权基础都已录入
   - 确认正文核心法条与 JSON 一致
   - 不一致必须修复，否则 S2 不得完成

---

## 工具依赖

**法条检索与复验**：
- **元典Skill**（law-search）— 法条检索与内容获取
  ```bash
  python3 scripts/yd_search.py search "检索词"
  python3 scripts/yd_search.py detail "法律名" --ft-name "条号"
  ```

**备用选项**（需手动启用）：
- `mcp__pkulaw-law-search__search_article` — 法条检索（北大法宝MCP，当前已禁用）
- `mcp__pkulaw-law-search__get_article` — 法条内容获取（北大法宝MCP，当前已禁用）

**法条性质鉴别**（引用 live case-os 资源，不复制）：
- `../case-os/references/nine_step_checklist.json` — 法条性质鉴别依据（第 16、17 项）
- `../case-os/schema/nine_step_core_schema.json` — s2_claim_bases 字段定义
- `../case-os/examples/nine_step_loan_case/expected_s2_claim_bases.json` — 完整输出示例

**本地资源**（新增）：
- `schema/s2_output_schema.json` — S2 输出结构定义
- `examples/s2_statute_nature_example.md` — 法条性质鉴别示例

---

## 输出

**输出文件**：
- `intermediate/原告九步法/S2-请求权基础/`
- `intermediate/被告九步法/S2-请求权基础/`

**输出格式**：
- JSON frontmatter：包含 claim_basis_analysis 对象
- Markdown 正文：展示法条性质鉴别过程和结果

**关键字段**（供 S4 读取）：
- `statute_nature`：法条性质（完全性法条/倡导性法条）
- `constitutive_elements`：构成要件数组
- `legal_effect`：法律效果数组
- `needs_replacement`：是否需要替换（true/false）
- `basis_confirmation_records`：请求权基础确认记录

**法条性质说明**：
- **完全性法条**：S4 可用于要件拆解
- **倡导性法条**：S4 不可用，需替换

---

## 错误处理

- 法条检索失败 → 提示用户手动指定
- 构成要件拆解不确定 → 列出可能性，让用户判断
