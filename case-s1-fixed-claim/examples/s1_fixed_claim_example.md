---
{
  "title": "S1 固定权利请求",
  "case_id": "CA-2026-0001",
  "party": "原告",
  "confidence": "high",
  "status": "pending_review",
  "fixed_claims": [
    {
      "id": "S1-C001",
      "content": "请求判令被告支付货款人民币100万元",
      "amount": {
        "extracted_amount": 1000000,
        "parsed_amount": 1000000,
        "review_status": "pending_review",
        "source_text": "货款人民币100万元"
      },
      "currency": "CNY",
      "stated_legal_basis": "《民法典》第577条",
      "source": "起诉状第3页第2项",
      "ocr_shadow": "",
      "status": "pending",
      "clarification_record": ""
    },
    {
      "id": "S1-C002",
      "content": "请求判令被告支付逾期付款利息（以100万元为基数，按年利率4.35%计算，自2025年1月1日起至实际清偿日止）",
      "amount": {
        "extracted_amount": null,
        "parsed_amount": null,
        "review_status": "pending_review",
        "source_text": "按年利率4.35%计算"
      },
      "currency": "CNY",
      "stated_legal_basis": "《民法典》第584条",
      "source": "起诉状第3页第3项",
      "ocr_shadow": "",
      "status": "pending",
      "clarification_record": ""
    }
  ],
  "clarification_records": [],
  "claim_completeness": {
    "checklist": [
      {
        "item": "合同履行争议是否有完整请求",
        "result": "covered",
        "claim_ids": ["S1-C001", "S1-C002"],
        "custom": false
      },
      {
        "item": "违约金/利息请求是否有依据",
        "result": "covered",
        "claim_ids": ["S1-C002"],
        "custom": false
      },
      {
        "item": "损失赔偿请求是否明确",
        "result": "missing",
        "claim_ids": [],
        "custom": false
      }
    ],
    "overall": "review_required"
  },
  "conflicts": [
    {
      "id": "S1-CONF-001",
      "claim_ids": ["S1-C001"],
      "type": "同一请求权可能存在竞合：合同违约vs侵权责任",
      "resolution": "pending_lawyer_choice",
      "note": "需律师判断是否同时主张侵权责任"
    }
  ]
}
---

# S1 固定权利请求

**案件**：CA-2026-0001
**方**：原告
**状态**：待律师确认

---

## 待律师确认事项

| ID | 请求内容 | 金额 | 法律依据 | 状态 |
|----|---------|------|----------|------|
| S1-C001 | 请求判令被告支付货款人民币100万元 | 待确认 | 《民法典》第577条 | 待确认 |
| S1-C002 | 请求判令被告支付逾期付款利息 | 待计算 | 《民法典》第584条 | 待确认 |

请确认以上诉讼请求清单是否准确，如有修改请告知。

---

## 完整性检查

- 合同履行争议请求：已覆盖（S1-C001、S1-C002）
- 违约金/利息请求：已覆盖（S1-C002）
- 损失赔偿请求：缺失

**结论**：请律师确认是否需要补充损失赔偿请求。

---

## 请求权竞合分析

| 竞合ID | 类型 | 涉及请求 | 解决方案 |
|--------|------|----------|----------|
| S1-CONF-001 | 合同违约vs侵权责任 | S1-C001 | 待律师选择 |

如需进一步说明或修改，请告知。