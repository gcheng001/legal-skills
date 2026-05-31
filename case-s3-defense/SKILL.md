---
name: case-s3-defense
description: '九步法S3-抗辩规范和反诉识别。梳理三类抗辩（权利阻碍性/消灭性/妨碍性），评估威胁等级，识别潜在反诉。TRIGGER when: 用户输入"抗辩规范"或由case-os总控调度。'
---

# case-s3-defense（S3）抗辩规范和反诉识别

## 工作定位

梳理三类抗辩（权利阻碍性抗辩、权利消灭性抗辩、权利妨碍性抗辩），评估被告实际提出概率和威胁等级，识别潜在反诉。

**前置条件**：S2（请求权基础）完成
**必须确认**：**是**（律师战术确认）
**法条复验**：**必须**（优先使用元典）
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取S2文件

读取 `intermediate/原告九步法/S2-请求权基础/` 中的法律依据和构成要件。

### 第二步：梳理三类抗辩

**抗辩类型修正**（对齐 nine_step_core_schema.json）：

| 抗辩类型 | 说明 | 示例 |
|----------|------|------|
| **权利阻碍性抗辩** | 阻碍权利发生的抗辩 | 无代理权、无权处分、明知无代理权 |
| **权利消灭性抗辩** | 消灭已存在权利的抗辩 | 已清偿、抵销、免除、提存 |
| **权利妨碍性抗辩** | 妨碍权利行使的抗辩 | 同时履行抗辩、不安抗辩、诉讼时效抗辩 |

**修正说明**：原"权利阻止抗辩"修正为"权利阻碍性抗辩"，对齐 schema 枚举值。

### 第三步：反诉识别（新增）

**识别依据**：《民事诉讼法》关于反诉的规定

**反诉条件**：
1. 反诉被告必须是本诉原告
2. 反诉请求与本诉请求基于同一法律关系
3. 反诉请求与本诉请求有牵连关系
4. 法院可以合并审理

**识别流程**：
1. 分析被告陈述中是否包含针对原告的独立请求
2. 判断该请求是否符合反诉条件
3. 如符合条件，进行释明并记录

**释明内容**：
- 询问被告是否需要提起反诉
- 告知反诉与本诉的关系
- 说明反诉的法律后果

**输出字段**：
```json
{
  "counterclaim_identification": {
    "has_counterclaim": true/false,
    "counterclaim_claims": [...],
    "clarification_needed": true/false,
    "clarification_record": "..."
  }
}
```

### 第四步：法条复验（元典优先）

**优先使用元典Skill**：

```bash
cd ~/.claude/skills/law-search
python3 scripts/yd_search.py search "同时履行抗辩权" --sxx 现行有效
```

**备用方案**（需手动启用北大法宝MCP）：

> ⚠️ 北大法宝MCP当前已禁用。如需使用，请在 settings.local.json 中添加相应权限。

```python
# 需要先在 settings.local.json 中启用：
# "mcp__pkulaw-law-search__search_article"

mcp__pkulaw-law-search__search_article(text="同时履行抗辩权")
```

### 第五步：评估威胁等级

对每项抗辩评估：
1. **实际提出概率**：高/中/低
2. **威胁等级**：致命/严重/一般/轻微
3. **应对策略**：如何反驳

### 第六步：生成S3文件

**输出格式**：JSON frontmatter + Markdown 正文

**JSON frontmatter**（包含抗辩分析和反诉识别）：

```json
---
{
  "step_id": "S3",
  "defense_analysis": {
    "initial_defense_statements": {...},
    "identified_defense_claims": {
      "defense_1": {
        "defendant": "被告名称",
        "defense_type": "权利阻碍性抗辩/权利消灭性抗辩/权利妨碍性抗辩",
        "defense_claim": "抗辩主张",
        "legal_basis": "法律依据",
        "提出概率": "高/中/低",
        "威胁等级": "致命/严重/一般/轻微",
        "应对策略": "如何反驳"
      }
    }
  },
  "counterclaim_identification": {
    "has_counterclaim": true/false,
    "counterclaim_claims": [...],
    "clarification_needed": true/false,
    "clarification_record": "..."
  }
}
---
```

**Markdown 正文**：

```markdown
# S3 抗辩规范和反诉识别

## 抗辩分析

### 权利阻碍性抗辩
| 抗辩事由 | 法律依据 | 提出概率 | 威胁等级 | 应对策略 |
|----------|----------|----------|----------|----------|
| ...

### 权利消灭性抗辩
...

### 权利妨碍性抗辩
...

## 反诉识别
...
```

保存到 `intermediate/原告九步法/S3-抗辩规范/`

### 第七步：律师战术确认

展示抗辩分析和应对策略，等用户确认战术方案。

### 第八步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S3-抗辩规范/`

### 第九步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S3
```

---

## 红线

- ❌ **必须法条复验**（优先使用元典）
- ❌ **抗辩类型必须使用修正后的枚举值**（权利阻碍性抗辩/权利消灭性抗辩/权利妨碍性抗辩）
- ❌ **不得使用"权利阻止抗辩"**
- ❌ 律师战术确认后才能进入下一步

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

**引用资源**（引用 live case-os 资源，不复制）：
- `../case-os/schema/nine_step_core_schema.json` — defense_type 枚举值定义
- `../case-os/examples/nine_step_loan_case/expected_s4_elements.json` — 抗辩类型使用示例

**本地资源**（新增）：
- `schema/s3_output_schema.json` — S3 输出结构定义
- `examples/s3_counterclaim_example.md` — 抗辩规范和反诉识别示例

---

## 输出

**输出文件**：
- `intermediate/原告九步法/S3-抗辩规范/`
- `intermediate/被告九步法/S3-抗辩规范/`

**输出格式**：
- JSON frontmatter：包含完整的抗辩分析和反诉识别数据
- Markdown 正文：展示抗辩分析和反诉识别过程和结果

**关键字段**：
- `defense_analysis`：抗辩分析
- `identified_defense_claims`：识别的抗辩权主张
- `defense_type`：抗辩类型（权利阻碍性抗辩/权利消灭性抗辩/权利妨碍性抗辩）
- `counterclaim_identification`：反诉识别（新增）

**抗辩类型说明**（修正后）：
- **权利阻碍性抗辩**：阻碍权利发生的抗辩
- **权利消灭性抗辩**：消灭已存在权利的抗辩
- **权利妨碍性抗辩**：妨碍权利行使的抗辩
