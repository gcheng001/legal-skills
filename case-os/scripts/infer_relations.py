#!/usr/bin/env python3
"""
A7.5 证据关系推断脚本 — AI推断提示生成+结构化解析+复核清单生成

工作流程（配合AI）:
  1. scan   — 读取证据卡片库.json，扫描材料文件，生成推断提示词供AI推断
  2. parse  — AI输出推断结果后，解析为结构化的 S0-证据关系.json
  3. review — 生成 S0-证据关系复核.md（供律师逐条确认）
  4. stats  — 输出关系统计信息

用法:
    python3 infer_relations.py [案件文件夹路径] --action scan
    python3 infer_relations.py [案件文件夹路径] --action parse --ai-output /path/to/ai_output.md
    python3 infer_relations.py [案件文件夹路径] --action review
    python3 infer_relations.py [案件文件夹路径] --action stats
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path


# ===== 关系类型定义
RELATION_TYPES = {
    "timeline": {
        "id": "timeline",
        "label": "时间线关联",
        "description": "同一时间节点或连续时间段上的事件关联",
        "color": "#4A90D9",
    },
    "corroborate": {
        "id": "corroborate",
        "label": "印证关联",
        "description": "不同来源的证据相互印证同一事实主张",
        "color": "#50B86C",
    },
    "contradict": {
        "id": "contradict",
        "label": "矛盾关联",
        "description": "证据之间就同一事项存在内容冲突或矛盾",
        "color": "#E74C3C",
    },
    "chain": {
        "id": "chain",
        "label": "链条关联",
        "description": "按事态发展顺序形成从因到果的证据链",
        "color": "#F39C12",
    },
}


def load_evidence(case_root: Path) -> dict:
    """加载证据卡片库 JSON"""
    paths_to_try = [
        case_root / "intermediate" / "S0-证据卡片库.json",
        case_root / "intermediate" / "证据卡片库.json",
    ]
    for p in paths_to_try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    print("❌ 未找到证据卡片库文件")
    print(f"   搜索路径: {[str(p) for p in paths_to_try]}")
    sys.exit(1)


def load_markdown_source(case_root: Path, source_filename: str) -> str:
    """根据来源文件名读取对应材料的 Markdown 内容"""
    search_dirs = [
        case_root / "_archive" / "markdown",
        case_root / "markdown",
        case_root / "_archive",
    ]
    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.name == source_filename or f.name == source_filename.replace("/", "_"):
                try:
                    return f.read_text(encoding="utf-8")
                except Exception:
                    pass
    return ""


def generate_inference_prompt(evidence_data: dict, case_root: Path) -> str:
    """生成 AI 推断提示词"""
    cards = evidence_data.get("cards", [])
    meta = evidence_data.get("meta", {})

    prompt_parts = [
        "# 证据关系推断任务\n\n",
        f"## 案件概况\n",
        f"- 总证据数: {meta.get('total_count', len(cards))} 条\n",
        f"- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n",
        "## 关系类型定义\n\n",
    ]

    for rt_id, rt in RELATION_TYPES.items():
        prompt_parts.append(
            f"### {rt['label']} ({rt_id})\n"
            f"- 说明: {rt['description']}\n\n"
        )

    prompt_parts.append("## 推断原则\n\n")
    prompt_parts.append("1. **精确定位**：每条关系必须标注到具体段落/位置，不得泛泛而谈\n")
    prompt_parts.append("2. **有据可依**：basis 字段必须写明推断依据（共享金额/日期/实体/矛盾点）\n")
    prompt_parts.append("3. **宁缺毋滥**：只有确实存在关联才标记，不强行关联\n")
    prompt_parts.append('4. **质量优先**：置信度实事求是，不确定的标注"中"或"低"\n')
    prompt_parts.append("5. **链条完整**：链条关联需确保从因到果步骤完整\n\n")

    prompt_parts.append("## 证据卡片列表\n\n> 以下为依据所有材料提取的结构化证据卡片：\n\n")

    for card in cards:
        card_text = card.get("text", "")
        prompt_parts.append(f"### {card.get('id', 'N/A')}: {card_text[:100]}…\n")
        prompt_parts.append(f"- 来源文件: {card.get('source', 'N/A')}\n")
        prompt_parts.append(f"- 原文摘要: {card_text}\n")
        prompt_parts.append(f"- 发言者: {card.get('speaker', 'N/A')}\n")
        prompt_parts.append(f"- 证明目的: {card.get('purpose_label', 'N/A')}\n")
        prompt_parts.append(f"- 时间: {card.get('time', 'N/A')}\n")
        prompt_parts.append(f"- 金额: {card.get('amount', 'N/A')}\n")
        prompt_parts.append(f"- 置信度: {card.get('confidence', 'N/A')}\n\n")

        # 如材料存在则加载原文供精确定位
        source_file = card.get("source", "")
        if source_file:
            full_text = load_markdown_source(case_root, source_file)
            if full_text and card_text and len(card_text) > 20:
                idx = full_text.find(card_text[:50])
                if idx >= 0:
                    start = max(0, idx - 200)
                    end = min(len(full_text), idx + len(card_text) + 200)
                    context = full_text[start:end]
                    prompt_parts.append(f"  > 原文上下文（{source_file}）:\n")
                    prompt_parts.append(f"  ```\n{context}\n```\n\n")

    prompt_parts.append("## 输出格式\n\n")
    prompt_parts.append("请严格按以下 JSON 格式输出推断结果（只输出 JSON，不要其他内容）：\n\n")
    prompt_parts.append("""{  "relations": [
    {
      "from": "SP001",
      "to": "SP003",
      "type": "timeline",
      "label": "简短标签如'同一日催收款'",
      "description": "详细描述关联原因",
      "from_anchor": "来源证据精确锚点，如'第2页第3段：2024年1月15日催款'",
      "to_anchor": "目标证据精确锚点，如'第1页第5段：截止2024.1.15未还款'",
      "confidence": "高",
      "basis": ["共享金额:500000", "共享日期:2024-01-15", "共享人姓名:张三"],
      "visible_in": ["lawyer", "client", "judge"]
    }
  ]
}""")

    prompt_parts.append("\n\n## 关键要求\n\n")
    prompt_parts.append("1. from_anchor 和 to_anchor 必须**精确到段落级**，引用原文关键字\n")
    prompt_parts.append("2. 链条关联(chain)的 relations 必须按时间先后排列\n")
    prompt_parts.append("3. 矛盾关联(contradict) 要明确写明矛盾的具体内容\n")
    prompt_parts.append("4. 一条证据可以与多条证据产生关联\n")
    prompt_parts.append("5. visible_in: lawyer=全量可见, client=仅律师+客户, judge=三层均可见\n")
    prompt_parts.append("6. 只输出 JSON，不要加 ```json 包裹\n")
    prompt_parts.append("7. **特别注意**：JSON 中不要出现注释（// 或 /* */），字段名称必须完全匹配上面的格式\n")

    return "".join(prompt_parts)


def parse_relations(ai_output: str, evidence_data: dict) -> dict | None:
    """从 AI 输出中解析结构化关系数据"""
    # 尝试多种方式提取 JSON
    json_str = None
    for pattern in [
        r'``(?:`json)?\s*\n(.+?)\n``',
        r'(\{[\s\S]*?"relations"[\s\S]*?\})',
    ]:
        match = re.search(pattern, ai_output, re.DOTALL)
        if match:
            json_str = match.group(1)
            break

    if not json_str:
        # 直接尝试全文
        json_str = ai_output.strip()
        if ai_output.count("```") >= 2:
            print("⚠️ 检测到包裹但未匹配到模式，自动尝试提取非包裹部分")
            # 取第一个 ``` 之后到最后一个 ``` 之前的内容
            parts = ai_output.split("```")
            for i, p in enumerate(parts):
                if p.strip().startswith("{") or p.strip().startswith("["):
                    json_str = p.strip()
                    if json_str.startswith("json"):
                        json_str = json_str[4:].strip()
                    break

    if not json_str:
        print("❌ 无法从 AI 输出中提取 JSON")
        return None

    # 清理 JSON 中的注释和尾随逗号
    json_str = re.sub(r'//.*?(\n|$)', '', json_str)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = json_str.strip()

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"   前 200 字符: {json_str[:200]}")
        return None

    relations = parsed.get("relations", [])
    if not relations:
        print("⚠️ 未提取到任何关系")
        return None

    # 建立卡片索引（支持两种数据格式）
    cards = {}
    raw_cards = evidence_data.get("cards", [])
    for c in raw_cards:
        cid = c.get("id", "")
        if cid:
            cards[cid] = c

    enriched = []
    for i, rel in enumerate(relations, 1):
        rel_id = rel.get("id", f"REL{i:03d}")
        from_id = rel.get("from", "")
        to_id = rel.get("to", "")
        from_card = cards.get(from_id, {})
        to_card = cards.get(to_id, {})

        enriched_rel = {
            "id": rel_id,
            "from": from_id,
            "to": to_id,
            "type": rel.get("type", "corroborate"),
            "label": rel.get("label", ""),
            "description": rel.get("description", ""),
            "precision": "paragraph",
            "from_detail": {
                "card_id": from_id,
                "source_file": from_card.get("source", ""),
                "anchor": rel.get("from_anchor", ""),
                "summary": (from_card.get("text", "") or "")[:120],
            },
            "to_detail": {
                "card_id": to_id,
                "source_file": to_card.get("source", ""),
                "anchor": rel.get("to_anchor", ""),
                "summary": (to_card.get("text", "") or "")[:120],
            },
            "inference": {
                "confidence": rel.get("confidence", "中"),
                "basis": rel.get("basis", []),
                "extracted_by": "AI推断",
                "extracted_at": datetime.now().isoformat(),
            },
            "status": "pending",
            "review_note": None,
            "visible_in": rel.get("visible_in", ["lawyer", "client", "judge"]),
        }
        enriched.append(enriched_rel)

    # 统计
    type_counts = {"timeline": 0, "corroborate": 0, "contradict": 0, "chain": 0}
    for rel in enriched:
        rt = rel["type"]
        if rt in type_counts:
            type_counts[rt] += 1

    result = {
        "meta": {
            "version": "1.0",
            "inferred_at": datetime.now().isoformat(),
            "confirmed": False,
            "confirmed_at": None,
            "confirmed_by": None,
            "total_relations": len(enriched),
            "relation_stats": type_counts,
            "status_stats": {"pending": len(enriched), "confirmed": 0, "rejected": 0, "modified": 0},
        },
        "relation_types": list(RELATION_TYPES.values()),
        "relations": enriched,
    }

    return result


def generate_review_doc(relation_data: dict, evidence_data: dict) -> str:
    """生成关系复核 Markdown 清单"""
    meta = relation_data.get("meta", {})
    relations = relation_data.get("relations", [])
    type_labels = {rt["id"]: rt["label"] for rt in relation_data.get("relation_types", [])}

    # 建立卡片索引
    cards = {}
    for c in evidence_data.get("cards", []):
        cid = c.get("id", "")
        if cid:
            cards[cid] = c

    lines = [
        "# S0 证据关系复核清单\n",
        f"\n> **状态**: 待复核 | 共 {meta.get('total_relations', len(relations))} 条关系 | "
        f"待确认: {meta.get('status_stats', {}).get('pending', 0)}\n",
        f"> **推断时间**: {(meta.get('inferred_at', '') or '')[:19]}\n",
        f"> **复核指引**: 逐条确认 ✅ / 驳回 ❌ / 修改 ✎\n\n",
    ]

    # 按关系类型分组
    grouped = {}
    for rel in relations:
        rt = rel.get("type", "corroborate")
        if rt not in grouped:
            grouped[rt] = []
        grouped[rt].append(rel)

    for rt_id in ["timeline", "corroborate", "contradict", "chain"]:
        rels = grouped.get(rt_id, [])
        if not rels:
            continue

        type_label = type_labels.get(rt_id, rt_id)
        lines.append(f"## {type_label}\n\n")
        lines.append("| 编号 | 证据A | 证据B | 关系标签 | 精确锚点 | 置信度 | 推断依据 | 复核 | 备注 |\n")
        lines.append("|------|--------|--------|----------|---------|--------|----------|------|------|\n")

        for rel in rels:
            from_id = rel.get("from", "")
            to_id = rel.get("to", "")
            from_card = cards.get(from_id, {})
            to_card = cards.get(to_id, {})
            from_text = (from_card.get("text", "") or "")[:40]
            to_text = (to_card.get("text", "") or "")[:40]
            from_anchor = (rel.get("from_detail", {}).get("anchor", "") or "")[:60]
            to_anchor = (rel.get("to_detail", {}).get("anchor", "") or "")[:60]
            conf = rel.get("inference", {}).get("confidence", "中")
            basis = "; ".join(rel.get("inference", {}).get("basis", []))[:80]
            visible = rel.get("visible_in", [])
            vis_str = "三层可见" if len(visible) == 3 else ("律师+客户" if "judge" not in visible else "仅律师")

            lines.append(
                f"| {rel.get('id', '')} "
                f"| {from_id}: {from_text}… "
                f"| {to_id}: {to_text}… "
                f"| {rel.get('label', '')} "
                f"| A: {from_anchor}… <br>B: {to_anchor}… "
                f"| {conf} "
                f"| {basis} "
                f"| [✅/❌/✎] "
                f"| [{vis_str}] |\n"
            )

        lines.append("\n")

    # 统计
    stats = meta.get("relation_stats", {})
    lines.append("---\n\n## 统计\n\n")
    lines.append(f"- 时间线关联: {stats.get('timeline', 0)} 条\n")
    lines.append(f"- 印证关联: {stats.get('corroborate', 0)} 条\n")
    lines.append(f"- 矛盾关联: {stats.get('contradict', 0)} 条\n")
    lines.append(f"- 链条关联: {stats.get('chain', 0)} 条\n")
    lines.append(f"- 总关系数: {meta.get('total_relations', 0)} 条\n")

    return "".join(lines)


def print_stats(relation_data: dict) -> None:
    """输出关系统计"""
    meta = relation_data.get("meta", {})
    stats = meta.get("relation_stats", {})
    status = meta.get("status_stats", {})

    print(f"\n📊 证据关系统计")
    print(f"{'=' * 40}")
    print(f"总关系数: {meta.get('total_relations', 0)}")
    print()
    print("关系类型分布:")
    for rt_id in ["timeline", "corroborate", "contradict", "chain"]:
        label = RELATION_TYPES[rt_id]["label"]
        count = stats.get(rt_id, 0)
        bar = "█" * count + "░" * max(0, 10 - count)
        print(f"  {label}: {count}  {bar}")
    print()
    print("复核状态:")
    print(f"  待确认: {status.get('pending', 0)}")
    print(f"  已确认: {status.get('confirmed', 0)}")
    if status.get("rejected", 0) > 0:
        print(f"  已驳回: {status.get('rejected', 0)}")
    if status.get("modified", 0) > 0:
        print(f"  已修改: {status.get('modified', 0)}")


def main():
    parser = argparse.ArgumentParser(description="A7.5 证据关系推断")
    parser.add_argument("case_root", nargs="?", default=".", help="案件文件夹路径")
    parser.add_argument(
        "--action", default="all",
        choices=["scan", "parse", "review", "stats", "all"],
        help="执行动作（默认 all=scan）",
    )
    parser.add_argument("--ai-output", help="AI 输出的推断结果文件（parse 模式用）")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    print(f"🔍 案件目录: {case_root}")

    evidence_data = load_evidence(case_root)

    if args.action in ("scan", "all"):
        prompt = generate_inference_prompt(evidence_data, case_root)
        prompt_path = case_root / "intermediate" / "S0-关系推断提示词.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        print(f"📝 推断提示词已生成: {prompt_path.relative_to(case_root)}")
        print(f"   请将上述提示词交给 AI 推断，然后将 AI 输出保存后使用 --action parse --ai-output <文件> 解析")
        if args.action == "scan":
            return

    if args.action == "parse":
        if not args.ai_output:
            print("❌ parse 模式需要 --ai-output 参数")
            sys.exit(1)
        ai_output_path = Path(args.ai_output)
        if not ai_output_path.exists():
            print(f"❌ AI 输出文件不存在: {ai_output_path}")
            sys.exit(1)
        ai_output = ai_output_path.read_text(encoding="utf-8")
        result = parse_relations(ai_output, evidence_data)
        if result:
            output_dir = case_root / "intermediate"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / "S0-证据关系.json"
            output_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"✅ 关系数据已保存: {output_path.relative_to(case_root)}")
            print_stats(result)
        else:
            print("❌ 关系解析失败")
            sys.exit(1)

    if args.action == "review":
        relation_path = case_root / "intermediate" / "S0-证据关系.json"
        if not relation_path.exists():
            print("❌ 关系数据不存在，请先执行 parse")
            sys.exit(1)
        relation_data = json.loads(relation_path.read_text(encoding="utf-8"))
        review_doc = generate_review_doc(relation_data, evidence_data)
        review_path = case_root / "intermediate" / "S0-证据关系复核.md"
        review_path.write_text(review_doc, encoding="utf-8")
        print(f"✅ 复核清单已生成: {review_path.relative_to(case_root)}")
        print(f"   逐条确认后更新 S0-证据关系.json 中的 status 字段即可")

    if args.action == "stats":
        relation_path = case_root / "intermediate" / "S0-证据关系.json"
        if not relation_path.exists():
            print("❌ 关系数据不存在，请先执行 parse")
            sys.exit(1)
        relation_data = json.loads(relation_path.read_text(encoding="utf-8"))
        print_stats(relation_data)


if __name__ == "__main__":
    main()