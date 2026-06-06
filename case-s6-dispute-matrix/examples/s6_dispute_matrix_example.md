---
{
  "step_id": "S6",
  "status": "pending_review",
  "case_id": "sample-loan-case",
  "fact_disputes": [
    {
      "dispute_id": "S6-FD001",
      "dispute_content": "借款是否实际交付",
      "related_element": "S4-E002",
      "party_positions": {
        "plaintiff_position": "已通过银行转账交付",
        "defendant_position": "否认收到款项"
      },
      "mapping_status": "resolved",
      "priority": "P0"
    }
  ],
  "law_disputes": [
    {
      "dispute_id": "S6-LD001",
      "dispute_type": "实体法律适用",
      "dispute_content": "民间借贷关系是否成立",
      "related_statute": "《民法典》第667条",
      "mapping_status": "resolved",
      "priority": "P0"
    }
  ],
  "non_dispute_exclusions": [],
  "priority_allocation": [
    {
      "priority": "P0",
      "focus": "借款交付与法律关系成立"
    }
  ]
}
---

# S6 争点矩阵示例

本示例仅用于结构校验，真实案件必须结合案卷材料并经律师复核。
