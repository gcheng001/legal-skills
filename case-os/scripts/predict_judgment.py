#!/usr/bin/env python3
"""
S9 要件归入与裁判预测生成器
将 S8 事实归入 S2 构成要件，预测裁判结果

读取:
  - intermediate/原告九步法/S4-要件拆解.md（要件表）
  - intermediate/原告九步法/S6-争点矩阵.md（争点对撞）
  - intermediate/原告九步法/S7-举证责任.md（举证分配）

输出:
  - intermediate/原告九步法/S9-要件归入与裁判预测.md
"""

import os
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path


def parse_elements_from_s4(s4_path: Path) -> list:
    """从 S4 提取构成要件"""
    if not s4_path.exists():
        return []
    text = s4_path.read_text(encoding="utf-8")
    elements = []
    for m in re.finditer(
        r'\|\s*(\d+\.\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        text
    ):
        elements.append({
            "编号": m.group(1),
            "要件名称": m.group(2).strip(),
            "必要事实": m.group(3).strip(),
            "证据状态": m.group(6).strip(),
        })
    return elements


def parse_disputes_from_s6(s6_path: Path) -> list:
    """从 S6 提取争点"""
    if not s6_path.exists():
        return []
    text = s6_path.read_text(encoding="utf-8")
    disputes = []
    for m in re.finditer(
        r'\|\s*(\d+\.\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        text
    ):
        disputes.append({
            "要件编号": m.group(1),
            "要件名称": m.group(2).strip(),
            "证据状态": m.group(3).strip(),
            "对方抗辩": m.group(4).strip(),
            "重要性": m.group(5).strip(),
            "应对策略": m.group(6).strip(),
        })
    return disputes


def parse_burdens_from_s7(s7_path: Path) -> list:
    """从 S7 提取举证责任"""
    if not s7_path.exists():
        return []
    text = s7_path.read_text(encoding="utf-8")
    burdens = []
    for m in re.finditer(
        r'\|\s*(\d+\.\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        text
    ):
        burdens.append({
            "要件编号": m.group(1),
            "要件名称": m.group(2).strip(),
            "举证方": m.group(3).strip(),
            "举证说明": m.group(4).strip(),
            "证据状态": m.group(8).strip(),
            "缺口状态": m.group(9).strip(),
        })
    return burdens


def assess_element(elements: list, eid: str) -> dict:
    """评估单个要件的归入情况"""
    for e in elements:
        if e["编号"] == eid:
            status = e["证据状态"]
            if "✅" in status:
                return {"结论": "✅ 成立", "理由": "证据充分", "风险": "低"}
            elif "🔴" in status or "未找到" in status:
                return {"结论": "🔴 不成立", "理由": "证据缺失", "风险": "高"}
            elif "🟡" in status:
                return {"结论": "🟡 待定", "理由": "证据不足", "风险": "中"}
            else:
                return {"结论": "🟡 待定", "理由": "需律师确认", "风险": "中"}
    return {"结论": "🟡 未评估", "理由": "要件未找到", "风险": "中"}


def generate_prediction_md(
    case_type: str,
    elements: list,
    disputes: list,
    burdens: list,
    case_root: Path
) -> str:
    """生成 S9 裁判预测 Markdown"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 逐要件归入评估
    assessments = []
    for e in elements:
        a = assess_element(elements, e["编号"])
        assessments.append({**e, **a})

    # 统计
    total = len(assessments)
    established = sum(1 for a in assessments if "成立" in a["结论"] and "不" not in a["结论"])
    denied = sum(1 for a in assessments if "不成立" in a["结论"])
    pending = total - established - denied

    # 争点统计
    critical = sum(1 for d in disputes if "核心" in d.get("重要性", ""))
    major = sum(1 for d in disputes if "主要" in d.get("重要性", ""))

    # 证据缺口
    gaps = sum(1 for b in burdens if "🔴" in b.get("缺口状态", ""))

    # 裁判预测
    if established == total:
        prediction = "✅ 全部成立"
        confidence = "高"
        suggestion = "请求权基础成立，建议积极主张"
    elif denied >= total * 0.5:
        prediction = "🔴 多数不成立"
        confidence = "低"
        suggestion = "核心要件证据不足，建议补充证据或调整诉讼策略"
    elif critical > 0:
        prediction = "🟡 部分成立（核心争点待决）"
        confidence = "中"
        suggestion = f"存在 {critical} 个核心争点，需重点攻克"
    else:
        prediction = "🟡 部分成立"
        confidence = "中"
        suggestion = "多数要件成立，需补充次要证据"

    lines = [
        f"# S9 — 要件归入与裁判预测（原告九步法）",
        "",
        f"> **九步法第9步**：将 S8 事实归入 S2 构成要件，预测裁判结果",
        f"> **案由**: {case_type}",
        f"> **生成时间**: {now}",
        f"> **AI角色**: 草稿 → **律师必审**",
        "",
        "---",
        "",
        "## 9.1 要件归入总览",
        "",
        f"| 统计项 | 数量 |",
        f"|--------|------|",
        f"| 要件总数 | {total} |",
        f"| ✅ 成立 | {established} |",
        f"| 🔴 不成立 | {denied} |",
        f"| 🟡 待定 | {pending} |",
        f"| 争点总数 | {len(disputes)} |",
        f"| 🔴 核心争点 | {critical} |",
        f"| 🟠 主要争点 | {major} |",
        f"| 证据缺口 | {gaps} |",
        "",
        "---",
        "",
        "## 9.2 要件归入分析表",
        "",
        "| 要件编号 | 要件名称 | 归入结论 | 理由 | 风险等级 |",
        "|---------|---------|---------|------|---------|",
    ]

    for a in assessments:
        lines.append(
            f"| {a['编号']} | {a['要件名称']} | {a['结论']} "
            f"| {a['理由']} | {a['风险']} |"
        )

    lines.append("")

    # 争点归入
    if disputes:
        lines.append("---")
        lines.append("")
        lines.append("## 9.3 争点归入分析")
        lines.append("")
        lines.append("| 争点 | 对方抗辩 | 重要性 | 原告九步法应对 | 归入结论 |")
        lines.append("|------|---------|--------|---------|---------|")
        for d in disputes:
            # 简单归入：根据重要性判断
            if "核心" in d.get("重要性", ""):
                conclusion = "🔴 需攻克"
            elif "主要" in d.get("重要性", ""):
                conclusion = "🟠 需准备"
            elif "无争议" in d.get("重要性", ""):
                conclusion = "🟢 通过"
            else:
                conclusion = "🟡 待定"
            lines.append(
                f"| {d['要件名称']} | {d['对方抗辩']} | {d['重要性']} "
                f"| {d['应对策略']} | {conclusion} |"
            )
        lines.append("")

    # 裁判预测
    lines.append("---")
    lines.append("")
    lines.append("## 9.4 裁判结果预测")
    lines.append("")
    lines.append(f"### 预测结论")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| **预测结果** | {prediction} |")
    lines.append(f"| **置信度** | {confidence} |")
    lines.append(f"| **核心依据** | {established}/{total} 要件成立 |")
    lines.append(f"| **主要风险** | {critical} 个核心争点 + {gaps} 个证据缺口 |")
    lines.append("")

    lines.append(f"### 策略建议")
    lines.append("")
    lines.append(f"1. **总体策略**：{suggestion}")
    lines.append("")

    if gaps > 0:
        lines.append(f"2. **证据补充**：优先补充 {gaps} 个证据缺口中的核心要件证据")
    if critical > 0:
        lines.append(f"3. **争点攻克**：集中力量攻克 {critical} 个核心争点")
    lines.append("")

    # 金额预测（占位）
    lines.append("### 金额预测")
    lines.append("")
    lines.append("| 项目 | 金额 | 依据 |")
    lines.append("|------|------|------|")
    lines.append("| 本金/合同标的 | 待填写 | 合同约定 |")
    lines.append("| 利息/违约金 | 待填写 | 法律规定 |")
    lines.append("| 诉讼费 | 待填写 | 标的额计算 |")
    lines.append("")

    # 待确认清单
    lines.append("---")
    lines.append("")
    lines.append("## 9.5 待确认事项")
    lines.append("")
    lines.append("- [ ] 要件归入结论是否准确？")
    lines.append("- [ ] 争点归入是否遗漏？")
    lines.append("- [ ] 裁判预测是否合理？")
    lines.append("- [ ] 金额预测是否已填写？")
    lines.append("- [ ] 策略建议是否需要调整？")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**状态**: ⏳ 待律师确认")
    lines.append("**下一步**: 生成最终交付物（立案材料/代理词）")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="S9 要件归入与裁判预测")
    parser.add_argument("case_root", nargs="?", default=".", help="案件文件夹路径")
    parser.add_argument("--case-type", default="", help="案由名称")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    print(f"🔍 案件目录: {case_root}")

    # 检测案由
    case_type = args.case_type
    if not case_type:
        case_brain_path = case_root / "CLAUDE.md"
        if case_brain_path.exists():
            text = case_brain_path.read_text(encoding="utf-8")
            m = re.search(r"\|\s*案由\s*\|\s*([^|\n]+?)\s*\|", text)
            if m:
                case_type = m.group(1).strip()
    if not case_type:
        print("❌ 未检测到案由，请用 --case-type 指定")
        sys.exit(1)
    print(f"📋 案由: {case_type}")

    # 读取上游数据
    s4_path = case_root / "intermediate" / "原告九步法" / "S4-要件拆解.md"
    s6_path = case_root / "intermediate" / "原告九步法" / "S6-争点矩阵.md"
    s7_path = case_root / "intermediate" / "原告九步法" / "S7-举证责任.md"

    elements = parse_elements_from_s4(s4_path)
    disputes = parse_disputes_from_s6(s6_path)
    burdens = parse_burdens_from_s7(s7_path)

    print(f"📊 要件: {len(elements)} | 争点: {len(disputes)} | 举证: {len(burdens)}")

    # 生成
    md = generate_prediction_md(case_type, elements, disputes, burdens, case_root)

    # 写入（扁平化路径）
    output_dir = case_root / "intermediate" / "原告九步法"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "S9-要件归入与裁判预测.md"
    output_path.write_text(md, encoding="utf-8")
    print(f"✅ 生成 {output_path.relative_to(case_root)}")


if __name__ == "__main__":
    main()
