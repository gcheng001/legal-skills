---
{
  "step_id": "S5",
  "status": "pending_review",
  "case_id": "sample-loan-case",
  "claim_completeness_check": {
    "corresponds_to_basis": false,
    "missing_claims": [
      {
        "element_id": "S4-E002",
        "missing_element": "借款交付事实",
        "clarification_needed": "补充转账凭证或收款确认"
      }
    ],
    "contradictory_claims": [],
    "needs_supplement": true,
    "upstream_parse_status": "resolved"
  },
  "supplement_records": [
    {
      "timestamp": "2026-05-31T00:00:00+08:00",
      "missing_element": "借款交付事实",
      "clarification_content": "要求律师确认转账记录和收款主体",
      "party_response": "pending_review"
    }
  ],
  "references": {
    "schema_ref": "schema/s5_output_schema.json",
    "checklist_ref": "../case-os/references/nine_step_checklist.json#S5"
  }
}
---

# S5 主张检索示例

本示例仅用于结构校验，真实案件必须结合案卷材料并经律师复核。
