# 专人派发协议（Specialist Dispatch Protocol）v1.0

> 依据 ADR-0004（case-os × SuitAgent 融合，2026-08-19）。本协议定义案件OS的**干活方式**：每个动脑环节由一位专职师傅（subagent）执行，带着明确的岗位说明书上场，脑子里只有一件事。
>
> **不变的东西**：律师确认门禁、S10幻觉校验、北大法宝复验、状态契约（state.json/_index.json）、Hook、LOG.md——派发只换"干活的分身"，不拆"质检的墙"。所有门禁规则对专职师傅同样生效，且必须写进每次派发的 prompt。

---

## 一、派发边界（铁律）

| 类别 | 环节 | 执行方式 |
|------|------|----------|
| **机器活** | A1 建档、A2 扫描OCR、A3 归档、A5 飞书同步、A7 状态汇总、Hook | 总控直接调工具/脚本执行，**不派师傅**（SuitAgent 自身实践一致：机械工作不派 subagent，架构决策 #047） |
| **动脑活** | A4 起：案件理解、证据卡片、九步法 S1-S10、立场出口、文书起草、交付前质检 | **一律派专职师傅**（subagent 派发） |

### 派发硬闸（2026-08-19 真案验证缺陷修复，莘意vs顺富案实证）

**问题**：v11.4 首真案验证中，总控在开庭压力下 0 次派发，动脑产物（质证意见/A4确认表/S2补正/庭前手册）全部直写，派发协议沦为纸面劝导。

**硬闸规则**：
1. **动脑活产物未经师傅派发，总控不得直接写入案件目录**——生成任何分析/文书类产物前，先派对应师傅；写文件前自问"这是机器活还是动脑活"，动脑活无派发记录即停手；
2. **唯一豁免**：subagent 工具不可用，或律师明示"跳过派发"——此时必须在 LOG.md 写入一行「日期｜产物名｜未派发原因」，无记录的直写视为绕闸（Hard Fail，等同编造法条级别）；
3. **质检闸同理**：对外文书未经 Reviewer 派发质检，不得呈律师确认；
4. 本闸不约束：核对表、状态同步、LOG.md、CLAUDE.md、git 提交等机器活。

**为什么是硬闸**：S10 门禁的经验——写在纸上的规矩遇到时间压力必然让路，必须做成"不做就过不去"的结构约束。派发体制的价值（专人专岗=用户实测的质量优势）只有在真实派发时才存在。

---

## 二、专职师傅派发总表

**SuitAgent 借调师傅**（岗位说明书 = SuitAgent 原件，只读引用，永不修改）：

| 案件OS环节 | 借调师傅 | 岗位说明书（只读） |
|------------|----------|--------------------|
| A4 案件理解 | DocAnalyzer | `~/.agents/skills/suitagent/references/agents/DocAnalyzer.md` |
| A6 证据卡片与关系复核 | EvidenceAnalyzer | `~/.agents/skills/suitagent/references/agents/EvidenceAnalyzer.md` |
| S5 主张检索（法规/类案/学理） | Researcher | `~/.agents/skills/suitagent/references/agents/Researcher.md` |
| S6 争点矩阵 | IssueIdentifier | `~/.agents/skills/suitagent/references/agents/IssueIdentifier.md` |
| 立场出口（S10后） | Strategist | `~/.agents/skills/suitagent/references/agents/Strategist.md` |
| 文书起草（起诉状/答辩状等） | Writer | `~/.agents/skills/suitagent/references/agents/Writer.md` |
| 交付前质检（对外文书） | Reviewer | `~/.agents/skills/suitagent/references/agents/Reviewer.md` |

**内部提拔师傅**（岗位说明书 = `references/promoted-specialists.md`，用案件OS自己的九步法文档立岗，配最接近的SuitAgent师傅经验作参考）：

| 案件OS环节 | 内部师傅 | 岗位说明书 | 经验参考（SuitAgent，只读） |
|------------|----------|------------|------------------------------|
| S1 固定权利请求 | 诉请固定师 | promoted-specialists.md §1 | DocAnalyzer（结构化提取纪律） |
| S2 请求权基础 | 请求权基础师 | promoted-specialists.md §2 | Researcher（检索式思维） |
| S3 抗辩规范与反诉 | 抗辩分析师 | promoted-specialists.md §3 | Researcher |
| S4 要件拆解 | 要件拆解师 | promoted-specialists.md §4 | IssueIdentifier（争点分层） |
| S7 举证责任分配 | 举证责任师 | promoted-specialists.md §5 | EvidenceAnalyzer（证明力评估） |
| S8 事实认定 | 事实认定师 | promoted-specialists.md §6 | EvidenceAnalyzer |
| S9 要件归入与裁判预测 | 裁判预测师 | promoted-specialists.md §7 | Strategist（**仅经验参考，严禁立场渗入**） |

**留用原岗**（不派发）：

| 环节 | 说明 |
|------|------|
| S10 幻觉校验 | 门禁守门员，沿用 `case-s10-hallucination`，由总控执行。与 Reviewer 分工：S10 管"法条真假"，Reviewer 管"文书成品质量"，一横一竖两道关 |
| 案件讨论（case-discussion） | 律师交互环节，主会话进行，不派发 |
| 法院短信/扫描/经验卡 | 事件驱动，维持原样 |

**SuitAgent 未采用角色**：Scheduler（期限由 case-court-sms/TimeRules 承接）、CaseSync（飞书同步由 case-feishu-sync 承接）、Summarizer（摘要职能并入 Reporter，2026-08-19 复议采纳 Reporter 后单一出口）。

**报告整合师（Reporter，2026-08-19 复议采纳）**：

| 时机 | 派发 | 产出 |
|------|------|------|
| 九步法 S10 通过后 | Reporter（吃 S1-S10 全链产物） | **案件分析报告**（深研报告：案情/争点/证据评估/裁判预测/风险，整合散落各步产物为一份完整叙事） |
| 开庭前（收到传票/庭审准备时） | Reporter | **庭前报告**（争点+证据+质证意见+预案整合） |
| 判决后/结案时 | Reporter | **结案报告**（结果复盘+经验卡素材） |
| 律师随时点名要"报告/汇报/整合" | Reporter | 按需整合 |

岗位说明书只读引用：`~/.agents/skills/suitagent/references/agents/Reporter.md`。产出写案件目录 `分析材料/`。报告是整合件（不改各步结论，只汇编+查漏），各步产物仍是唯一事实源。

---

## 三、派发执行规范

每次派发使用 DSH `subagent` 工具，prompt **必须包含四段**：

1. **岗位说明书全文**（先 read 师傅的说明书文件，原文注入）；
2. **本环节的案件OS规则**：对应步骤 Skill 的流程要求 + 律师确认门禁 + 输出去AI味要求；
3. **案件上下文**：案件路径、前序 Handoff Package 摘要、相关材料路径（不整卷重读，只给本环节需要的）;
4. **输出契约**：产物写入案件目录的约定位置，返回标准 Handoff Package（上游判断摘要/原始输入材料/交接备注）。

**并行与串行**：无依赖的环节可并行派发（如 S5 检索与 S4 无交叉时）；有依赖的必须串行并在 prompt 中注入前序产物。Strategist 类立场师傅不得与 S1-S9 中性分析并行。

**门禁时序**：师傅完成 ≠ 步骤完成。需要律师确认的步骤（A4/S1/S5/S6/S8/S9），师傅产物先呈律师确认，确认后才算过门；S2/S4/S7 产物须北大法宝复验。确认/复验由总控执行，不派发。

---

## 四、质检闸（Reviewer，对外文书一票否决）

**适用对象**：将交付法院或客户的正式文书——起诉状、答辩状、上诉状、代理词、质证意见、法律意见书等。

**闸位**：文书生成（Writer/`case-filing-gen`）→ **Reviewer 质检** → 律师最终确认 → 交付。

**权力**：
- 对外文书：质检不通过即**打回重写**，律师看到的必须是过了 Reviewer+S10 两道关的版本；
- 内部分析报告（九步法产物、摘要）：只出意见清单，不拦截。

**质检维度**（Review 师傅说明书 + 下列本地规则）：
1. 法条引用与 S10 校验结果一致（不重复校验真伪，只查引用规范）；
2. 事实陈述可溯源到证据卡片/材料，无编造、无放大；
3. 结构完整（诉求/事实/理由/法律依据齐备）、逻辑自洽；
4. 语言去过AI味（对照 `references/de-ai-checklist.md`）；
5. 与律师确认的思路和结构要求一致。

**打回流程**：Reviewer 输出问题清单 → 原师傅限期修改 → 复检 → 通过才呈律师。打回记录写入 LOG.md。

---

## 五、策略师傅（Strategist）双轨制

**正轨（唯一正式岗位）**：立场出口。S10 通过后，Strategist 基于 S2/S4/S8/S9 中性结论出立场打法（进攻/防守/折中、SWOT、胜诉评估），承接 `case-stance-exit` 的交付要求。立场产物**只从末端出口**，不回写中性分析链。

**召见轨（随时可召）**：九步法进行中，律师可随时单独召见 Strategist 答疑（"这个案子怎么打""胜率多少"）。召见产物**必须标注【立场参考】**，写入案件目录 `intermediate/` 或讨论备忘录，**不得**作为 S1-S9 任何步骤的输入，不得影响裁判预测。

**墙的规则**：S9 裁判预测师的 prompt 中严禁注入任何立场参考产物；召见轨产物带【立场参考】标签就是为这道墙服务的。

---

## 六、与 SuitAgent 本体的关系

- SuitAgent 原件（`~/.agents/skills/suitagent/references/`）**只读引用，永不修改**，保留上游 GitHub 更新通道；
- 直接喊「SuitAgent」办案时，按其接入说明（SKILL.md）的本地规矩：产出写入案件OS案件目录，**不新建12层档案柜**（ADR-0004 决定 #6）；
- 本协议是案件OS的干活方式，SuitAgent 本体的独立运行不受本协议约束。
