---
name: case-s4-elements
description: '九步法S4-要件拆解。将构成要件转化为需证明的具体事实，建立证据-要件映射表，标红证据缺口。验证S2法条性质，仅使用完全性法条。TRIGGER when: 用户输入"要件拆解"或由case-os总控调度。'
---

# case-s4-elements（S4）要件拆解

## 工作定位

将S2构成要件转化为需证明的具体事实，建立证据-要件映射表，标红证据缺口。

**法条性质要求**：仅使用 S2 筛选出的完全性法条进行要件拆解，不使用倡导性法条。

**前置条件**：S3（抗辩规范）完成
**必须确认**：**是**
**法条复验**：**必须**（优先使用元典）
**执行后**：调用Hook脚本更新状态

---

## 执行流程

### 第一步：读取S2文件

读取 `intermediate/原告九步法/S2-请求权基础/` 中的构成要件。

### 第一步A：验证法条性质（新增）

**验证依据**：从 S2 输出读取 `statute_nature` 字段

**验证流程**：
1. 读取 S2 输出的 `claim_basis_analysis.legal_articles[].statute_nature` 字段
2. 确认所有使用的法条均为"完全性法条"
3. 如发现"倡导性法条"，记录到 `advocatory_statutes_found` 列表
4. 仅对"完全性法条"进行要件拆解

**阻断机制**：
- ❌ 发现使用倡导性法条 → 自动阻断，提示律师替换为完全性法条
- 阻断提示：⛔ S4 发现倡导性法条，无法进行要件拆解。请律师在 S2 阶段替换为完全性法条。
- ✅ 所有法条均为完全性法条 → 进入第二步

**输出字段**：
```json
{
  "statute_nature_verification": {
    "verification_passed": true/false,
    "advocatory_statutes_found": [...],
    "blocking_reason": "..."
  }
}
```

### 第二步：转化为具体事实

将每个构成要件转化为需证明的具体事实：
- 要件：合同成立 → 事实：双方签订合同、合同内容
- 要件：违约行为 → 事实：未按约定履行、逾期时间

### 第三步：建立证据-要件映射表

将证据卡片（S0）与要件事实对应：

| 要件事实 | 证据编号 | 证据来源 | 置信度 | 缺口 |
|----------|----------|----------|--------|------|
| 合同成立 | SP001, SP002 | 合同文件 | 高 | 无 |
| 违约行为 | SP003, SP004 | 聊天记录 | 中 | ⚠️ 缺付款凭证 |

### 第四步：标红证据缺口

对证据缺口分级：
- **致命缺口**：无法证明请求权成立
- **风险缺口**：可能影响裁判结果
- **轻微缺口**：影响不大，可补充

### 第五步：法条复验（元典优先）

**优先使用元典Skill**：

```bash
cd ~/.claude/skills/law-search
python3 scripts/yd_search.py search "民法典 第577条 违约责任构成要件" --sxx 现行有效
```

**备用方案**（需手动启用北大法宝MCP）：

> ⚠️ 北大法宝MCP当前已禁用。如需使用，请在 settings.local.json 中添加相应权限。

```python
# 需要先在 settings.local.json 中启用：
# "mcp__pkulaw-law-search__search_article"

mcp__pkulaw-law-search__search_article(text="民法典 第577条 违约责任构成要件")
```

### 第六步：生成S4文件

**输出格式**：JSON frontmatter + Markdown 正文

**JSON frontmatter**（包含法条性质验证）：

```json
---
{
  "step_id": "S4",
  "legal_basis_analysis": {...},
  "statute_nature_verification": {
    "verification_passed": true,
    "advocatory_statutes_found": []
  },
  "elements_analysis_by_defendant": {
    "黄某": {
      "defendant": "黄某",
      "rights_basis": "违约责任请求权",
      "legal_articles": [
        {
          "article": "《合同法》第107条",
          "current_equivalent": "《民法典》第577条",
          "element_covered": "义务未履行",
          "note": "完全性法条（从S2读取statute_nature）",
          "statute_nature": "完全性法条"
        }
      ],
      "elements_summary": {
        "权利依据的要件事由": [...],
        "权利阻碍性事由": [],
        "权利消灭性抗辩事由": [...],
        "权利妨碍性抗辩事由": []
      }
    }
  }
}
---
```

**Markdown 正文**：

```markdown
# S4 要件拆解

## 法条性质验证
- ✅ 所有法条均为完全性法条

## 请求权1：[请求内容]
### 构成要件与事实对应
| 要件 | 需证明事实 | 证据 | 置信度 | 缺口 |
|------|------------|------|--------|------|
| ... | ... | ... | ... | ... |

### 证据缺口分析
- ⚠️ 致命缺口：[说明]
- ⚠️ 风险缺口：[说明]
```

保存到 `intermediate/原告九步法/S4-要件拆解/`

**MD-JSON 双向同步（强制执行）**：
- JSON 中的 `statute_nature_verification` 对象必须同步到 MD 正文的“法条性质验证”章节。
- MD 正文中必须包含法条性质验证表格（法条名称、法条性质、来源），并与 JSON 中 `statute_nature_verification.已验证法条` 数组一致。
- 常见错误：JSON 中有完整的 `statute_nature_verification`，但 MD 正文遗漏该章节；必须补全。
- 生成完成后自检：JSON 中 `verification_passed` 的值与 MD 中的验证结论一致。

### 第七步：律师确认

展示要件拆解和证据缺口，等用户确认。

### 第八步：同步生成被告九步法预判版

生成 `intermediate/被告九步法/S4-要件拆解/`

### 第九步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] S4
```

---

## 红线

- ❌ **必须法条复验**（优先使用元典）
- ❌ **仅使用完全性法条进行要件拆解**（从 S2 读取 statute_nature）
- ❌ **发现倡导性法条自动阻断**
- ❌ OCR低置信度信息强制核对（<0.85）

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

**法条性质验证**（读取 S2 输出）：
- S2 输出文件：`intermediate/原告九步法/S2-请求权基础/`
- 读取字段：`claim_basis_analysis.legal_articles[].statute_nature`

**引用资源**（引用 live case-os 资源，不复制）：
- `../case-os/schema/nine_step_core_schema.json` — s4_elements_analysis 字段定义
- `../case-os/examples/nine_step_loan_case/expected_s4_elements.json` — 完整输出示例

**本地资源**（新增）：
- `schema/s4_output_schema.json` — S4 输出结构定义
- `examples/s4_elements_example.md` — 要件拆解示例

---

## 九步法资源接入（强制）

执行 S4 前必须读取 live `case-os` 的九步法资源，引用而不复制：

1. 读取 `../case-os/references/nine_step_output_schemas.json` 中 `steps.S4` 的 `input_schema`、`output_schema`、`handoff_to_next` 与 `blocking_conditions`。
2. 读取 `../case-os/references/nine_step_checklist.json` 中 `steps.S4` 的检查清单，并在 Markdown 正文中逐项说明覆盖、缺失或不适用。
3. 读取 `../case-os/references/nine_step_failure_modes.json` 中 `failure_modes.S4` 的失败模式；命中 HIGH/CRITICAL 风险时必须阻断或标记待律师处理。
4. 按需读取 `../case-os/references/nine_step_chunks.jsonl` 中 `step_id == "S4"` 或 `skill_target` 指向本步骤的切片；未找到匹配切片时记录 `chunks_reference_status: "none_found"`，不得因此跳过步骤。
5. 读取 `../case-os/examples/nine_step_loan_case/expected_s4_elements.json` 作为结构参考；如本 skill 有 `schema/s4_output_schema.json`，同时按本地 schema 校验输出。
- 本 skill 本地示例（如存在）：`examples/s4_*.md`。

输出必须采用合法 JSON frontmatter + Markdown 正文。JSON 顶层 `step_id`、`status`/`review_status`、引用来源、律师确认口径、hook 写回状态必须与 `case-os` 总控一致。
- S1/S5/S6/S8/S9 只能进入 `pending_review`；S2/S4/S7 需完成权威复验/律师确认口径后才可交接；S10 只作 FINAL 阻断门禁，不得改写 S9 结论。

## 输出

**输出文件**：
- `intermediate/原告九步法/S4-要件拆解/`
- `intermediate/被告九步法/S4-要件拆解/`

**输出格式**：
- JSON frontmatter：包含完整的要件拆解分析数据
- Markdown 正文：展示要件拆解过程和结果

**顶层结构**（对齐 expected_s4_elements.json）：
- `legal_basis_analysis`：法律基础分析
- `statute_nature_verification`：法条性质验证结果
- `elements_analysis_by_defendant`：各被告构成要件分析

**关键字段**：
- `statute_nature_verification`：法条性质验证结果
- `elements_analysis_by_defendant`：各被告构成要件分析
- `legal_articles`：法条列表（包含 article、current_equivalent、element_covered、note、statute_nature）
- `elements_summary`：要件汇总（权利依据/阻碍性/消灭性/妨碍性事由）
- `statutes_used_for_analysis`：实际用于要件拆解的法条列表（覆盖所有 legal_articles 中的 current_equivalent）

**法条性质说明**：
- **完全性法条**：可用于要件拆解
- **倡导性法条**：不可用，自动阻断
