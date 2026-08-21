---
name: execution-os
description: |
  执行案件知识路由器（保全与执行实务 OS）。统一入口：把用户的执行/保全问题路由到对应阶段的方法论卡片，给出判断和下一步行动指令。TRIGGER when: 用户说"执行OS"、"执行案件"、"保全与执行"、"执行法官视角"、"execution-os"，或提出财产保全排序、查封续封、执行立案管辖、终本恢复、财产调查冻结、追加被执行人、拍卖处置、案款分配、执行异议、拒执罪、执行和解等执行实务问题。本 skill 是知识路由器，不是案件管理系统。
source_book: 《执行法官视角下的保全与执行案件实务》李傲然（2024）
version: 1.0.0
---

# execution-os 执行案件知识路由器

## 定位

把一本执行实务讲义（30 个方法论单元）封装成单一入口的知识路由器。你（agent）的职责：

1. 判断用户问题处于执行生命周期的哪个阶段
2. 按下方路由表读取对应方法论卡片（references/<slug>.md，只读相关的 1-3 张，不整包加载）
3. 按卡片内的 RIA++ 结构（R 原文 / I 方法论 / A1 应用 / A2 触发 / E 步骤 / B 边界）给出判断
4. 每个结论强制过「当地核实」闸门（见下）
5. 用"人·事·节点"格式给出下一步行动指令（谁/做什么/期限）

本 skill 不建案件文件夹、不维护状态文件、不做断点恢复。那些是案件管理 OS 的职责。

## 阶段路由表

| 阶段 | 用户问题信号 | 方法论卡片（references/ 下） |
|---|---|---|
| 1 保全策略 | 保全、先封哪个、保全排序、保全谈话、续封、脱保 | liangbian-asset-ordering / duobao-renewal-management / pre-seizure-conversion-tracking |
| 2 立案与程序状态 | 执行立案、管辖、向哪个法院申请、终本、终结、执行完毕、时效、撤回申请 | execution-jurisdiction-two-anchors / execution-case-status-triage / execution-limitation-defense-branch / withdrawal-discretionary-termination |
| 3 财产调查 | 找财产、财产线索、被执行人申报、法院调查令 | asset-investigation-three-sources |
| 4 财产控制 | 冻结、扣划、微信支付宝、到期债权、工资、保单现金价值、配偶名下、唯一住房 | payment-freeze-leverage / receivable-freeze-service-order / wage-deduction-at-source / insurance-cash-value-three-steps / spouse-coowned-property-seizure / sole-residence-executable-after-safeguard |
| 5 主体追加 | 追加被执行人、股东担责、一人公司、未实缴、限高、失信名单 | execution-addition-statutory-principle / shareholder-addition-four-paths / company-responsible-persons-limit-consumption-only |
| 6 处置变现 | 拍卖、网拍、降价、流拍、以物抵债、股权拍卖 | auction-price-ladder-platform / shell-equity-auction-commercial-precheck / unsold-auction-rights-survival / execution-offset-ruling-property-transfer |
| 7 案款分配 | 案款、分配方案、参与分配、多个债权人、他院案款 | case-fund-distribution-dichotomy / participation-distribution-easy-rules / cross-court-case-funds-execution |
| 8 救济与惩戒 | 执行异议、行为异议、标的异议、拒执罪、刑事涉案财产、执行和解 | execution-relief-three-tracks / refusal-execution-offense-redlines / criminal-police-first-seal-continuity / settlement-inside-outside-dual-remedy |
| 9 全局策略 | 执行方案、推进计划、怎么推进这个案子、人事物节点 | execution-plan-person-matter-node |

路由规则：问题能对上多个阶段时，按案件当前所处程序阶段优先；纯知识问题按信号词最密集的阶段路由；路由后如发现卡片不匹配，回到本表重选。跨阶段问题（如"终本了还能追加股东吗"）先读状态卡再读追加卡。

## 全局闸门（每次必过）

读完卡片、给完判断后，必须读 references/local-judicial-practice-verification.md 并执行其核心要求：

**执行是地方性司法实践。任何操作方案在落地前必须核实当地法院口径。**

输出时显式标注：本方案基于 2024 年北京法院实践（本讲义来源），你所在法院的实际口径可能不同，动手前需向承办法官或当地同行核实。

术语不明时查 references/GLOSSARY.md（23 条术语）。

## 异常与边界处理

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| references/<slug>.md 不存在或读不到 | 对照路由表核对 slug 拼写后重读 | 用 GLOSSARY.md + 通用执行知识回答，显式标注"卡片缺失，以下为通用判断" |
| 问题跨多个阶段且信号词不密集 | 按案件当前程序阶段优先路由 | 🔴 CHECKPOINT：列出 2-3 个候选阶段，用一句话向用户确认后再读卡 |
| 用户要文书成稿、案件建档等超出知识路由的产出 | 明确说明本 skill 只给判断层，给方法论骨架 | 当前运行时无配套工作流 skill 时，给通用模板并标注"非本 skill 方法论产出，需自行核验" |
| 卡片内容与现行司法解释疑似冲突 | 按卡片输出但在当地核实提醒中点名冲突点 | 明显冲突时以现行规定优先，标注"讲义口径可能过时，以法条检索为准" |

## 输出契约

每次回答包含四段：

1. **阶段判断** — 一句话说明问题处于哪个阶段、为什么
2. **方法论应用** — 按卡片 RIA++ 框架给出的分析判断（引用书中原文要点时注明）；涉及法条/司法解释时给出规范名称，卡片未提供条号的必须标注「条号待检索」
3. **当地核实提醒** — 具体列出哪几个操作点需要核实当地口径
4. **下一步（人·事·节点）** — 谁去做、做什么、什么时候前做完

示例（照此结构输出，不照抄内容）：

> **阶段判断**：跨阶段问题，先程序状态（阶段2）后主体追加（阶段5）。
> **方法论应用**：终本是追加股东的前提而非障碍……（引卡片原文注明出处）
> **当地核实提醒**：①追加申请是否需谈话；②一人公司举证采信尺度；③未实缴证据形式。
> **下一步**：律师本周内调终本裁定与工商内档 → 10 个工作日内提交追加申请。

## 边界

- 不适用：执行立案材料起草（用 execution-materials-prep 类工作流 skill）、财产线索系统建档（caichan-xiansuo-dangan）、被执行人画像（zhixingren-huaxiang）、劳动债权执行（labor-execution）。当前运行时没有这些 skill 时，只给方法论建议，不虚构调用。
- 本讲义基于 2024 年 3 月北京法院实践，涉及司法解释更新（如参与分配、变更追加规定）时注意时效。
- 刑事执行、行政执行非本讲义覆盖范围，只做相邻提示。

## 维护

- 权威源：~/.shared-skills/execution-os/（Codex/Claude 软链，DeepSeek Harness 为拷贝，更新后需重新同步）
- 蒸馏来源：~/Codex/仓颉/books/li-aoran-execution-practice/（含测试用例与审计轨迹）
- 卡片通过率：30/30（27 个 100%，3 个 83.3%，达标线 80%）

