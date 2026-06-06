# CLAUDE.md — 案件大脑

---

## 📋 案件信息

```yaml
案件名称: {{case_name}}
案号: {{case_number}}
案件类型: {{case_type}}
案由: {{case_cause}}
案件状态: {{case_status}}
当前阶段: {{current_stage}}
收案日期: {{accept_date}}
```

## 👥 当事人

```yaml
我方:
  名称: {{our_name}}
  曾用名: {{our_former_name}}
  简称: {{our_short_name}}
  地位: {{our_role}}
  类型: {{our_type}}
  统一社会信用代码: {{our_credit_code}}
  法定代表人: {{our_legal_rep}}
  职务: {{our_title}}
  地址: {{our_address}}
  联系电话: {{our_phone}}

对方:
  名称: {{other_name}}
  简称: {{other_short_name}}
  地位: {{other_role}}
  类型: {{other_type}}
  统一社会信用代码: {{other_credit_code}}
  法定代表人: {{other_legal_rep}}
  地址: {{other_address}}
  联系电话: {{other_phone}}
```

## 🏛️ 管辖

```yaml
受理机关: {{court_name}}
管辖依据: {{jurisdiction_basis}}
工程项目: {{project_name}}
```

## 💰 金额

```yaml
涉案金额: {{total_amount}}
金额构成:
  送审合计: {{audit_total}}
  审计结算价: {{audit_settlement}}
  核减金额: {{deduction_amount}}
  累计已付: {{paid_amount}}
  已付比例: {{paid_ratio}}
  尚欠总额: {{outstanding_amount}}
  质保金暂扣: {{retention_amount}}
  质保金比例: {{retention_ratio}}
  房抵已抵: {{property_offset}}
  诉讼主张: {{claim_amount}}
  备注: {{amount_remark}}
```

## ⏰ 时间节点

```yaml
开庭日期: {{hearing_date}}
举证期限: {{evidence_deadline}}
上诉期截止: {{appeal_deadline}}
收到判决时间: {{judgment_date}}
```

## ⚔️ 争议焦点

```yaml
核心争议:
{{#each disputes}}
  - item: {{this.item}}
    风险: {{this.risk}}
    说明: {{this.description}}
{{/each}}
```

## ⚠️ 风险评估

```yaml
胜诉率预估: {{win_rate}}
致命风险:
{{#each fatal_risks}}
  - {{this}}
{{/each}}
其他风险:
{{#each other_risks}}
  - {{this}}
{{/each}}
```

## 📁 证据清单

```yaml
已有:
{{#each existing_evidence}}
  - name: {{this.name}}
    形式: {{this.form}}
    状态: {{this.status}}
{{/each}}

缺失:
{{#each missing_evidence}}
  - name: {{this.name}}
    重要性: {{this.importance}}
    影响: {{this.impact}}
{{/each}}
```

## 📝 办案策略

```yaml
策略: {{strategy}}
推荐路径: {{recommended_path}}
客户目标: {{client_goal}}
```

## ✅ 待办事项

```yaml
待办:
{{#each todos}}
  - {{this}}
{{/each}}

已完成:
{{#each completed}}
  - {{this}}
{{/each}}
```

## 📅 操作日志

```yaml
日志:
{{#each logs}}
  - date: {{this.date}}
    内容: {{this.content}}
{{/each}}
```

---

## 📖 案情概要

{{case_summary}}

## 🔬 证据分析

{{evidence_analysis}}

## 🛠️ 可用技能

| 技能 | 描述 | 状态 |
|-----|------|------|
| 材料分析 | 分析全部材料，生成Word报告（含截图） | ⭐推荐 |
| 立案材料生成 | 生成起诉状、委托手续等 | ⭐推荐 |
| 补充事实 | 添加案件背景信息 | 可用 |
| 案件可视化 | 将判决书转成美观的HTML可视化网页 | 可用 |
| 案件时间轴 | 生成单/双/多主体行为时间轴 | 可用 |
| 合同审查 | 全面审查合同风险（四维度） | 可用 |

---

*本文件由民事案件OS {{version}}生成*
