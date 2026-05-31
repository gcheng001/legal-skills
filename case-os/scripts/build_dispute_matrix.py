#!/usr/bin/env python3
"""
S6 争点矩阵生成器
双方争点对撞，确定主次战场

读取:
  - intermediate/原告九步法/S4-要件拆解.md（要件表）
  - intermediate/被告九步法/S3-抗辩规范.md（被告九步法抗辩预判）
  - data/defenses/<案由>.json（抗辩武器库）

输出:
  - intermediate/原告九步法/S6-争点矩阵.md（双方共用）
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
DEFENSES_DIR = SKILL_DIR / "data" / "defenses"

# 争点重要性等级
PRIORITY_CRITICAL = "🔴 核心争点"
PRIORITY_MAJOR = "🟠 主要争点"
PRIORITY_MINOR = "🟡 次要争点"
PRIORITY_CONCEDED = "🟢 无争议"


def load_defense_library(case_type: str) -> dict:
    """加载抗辩武器库 JSON"""
    # 精确匹配
    json_path = DEFENSES_DIR / f"{case_type}.json"
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)

    # 模糊匹配
    for f in DEFENSES_DIR.glob("*.json"):
        if case_type in f.stem or f.stem in case_type:
            print(f"✅ 模糊匹配: {case_type} → {f.stem}")
            with open(f, encoding="utf-8") as fp:
                return json.load(fp)

    print(f"⚠️ 未找到案由「{case_type}」的抗辩武器库")
    return {}


def parse_elements_from_s4(s4_path: Path) -> list:
    """从 S4 要件拆解文件中提取构成要件列表"""
    if not s4_path.exists():
        return []
    text = s4_path.read_text(encoding="utf-8")
    elements = []

    # 匹配表格行：| 要件编号 | 构成要件 | 必要事实 | 证据类型 | 证据来源 | 证据状态 |
    for m in re.finditer(
        r'\|\s*(\d+\.\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        text
    ):
        elements.append({
            "编号": m.group(1),
            "要件名称": m.group(2).strip(),
            "必要事实": m.group(3).strip(),
            "证据类型": m.group(4).strip(),
            "证据来源": m.group(5).strip(),
            "证据状态": m.group(6).strip(),
        })

    return elements


def parse_defenses_from_s3(s3_path: Path) -> list:
    """从被告九步法 S3 抗辩规范文件中提取抗辩列表"""
    if not s3_path.exists():
        return []
    text = s3_path.read_text(encoding="utf-8")
    defenses = []

    # 匹配抗辩表格行
    for m in re.finditer(
        r'\|\s*(D\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        text
    ):
        defenses.append({
            "编号": m.group(1),
            "抗辩名称": m.group(2).strip(),
            "类型": m.group(3).strip(),
            "法律依据": m.group(4).strip(),
            "证明事项": m.group(5).strip(),
            "证据类型": m.group(6).strip(),
        })

    return defenses


def build_dispute_rows(elements: list, defenses: list, defense_lib: dict) -> list:
    """构建争点行：要件 vs 抗辩 对撞"""
    rows = []
    all_defenses = []
    for cat in ["权利消灭", "权利妨碍", "权利阻止"]:
        all_defenses.extend(defense_lib.get("抗辩分类", {}).get(cat, []))

    for elem in elements:
        eid = elem["编号"]
        ename = elem["要件名称"]
        estate = elem["证据状态"]

        # 匹配可能攻击该要件的抗辩
        matched_defenses = []
        for d in all_defenses:
            # 简单关键词匹配：抗辩名称/证明事项包含要件名称关键词
            d_text = d.get("抗辩名称", "") + " ".join(d.get("证明事项", []))
            # 提取要件名称中的关键词（去掉常见词）
            keywords = [w for w in ename if len(w) >= 2]
            if any(kw in d_text for kw in keywords):
                matched_defenses.append(d)

        # 判定争点重要性
        if "🔴" in estate or "未找到" in estate:
            priority = PRIORITY_CRITICAL
        elif matched_defenses:
            priority = PRIORITY_MAJOR
        elif "✅" in estate:
            priority = PRIORITY_CONCEDED
        else:
            priority = PRIORITY_MINOR

        defense_names = "、".join(d["抗辩名称"] for d in matched_defenses[:3]) or "无匹配抗辩"

        rows.append({
            "要件编号": eid,
            "要件名称": ename,
            "证据状态": estate,
            "被告九步法可能抗辩": defense_names,
            "重要性": priority,
            "原告九步法应对": "待补充",
            "律师确认": "⏳",
        })

    return rows


def generate_dispute_matrix_md(
    case_type: str,
    elements: list,
    defenses: list,
    rows: list,
    case_root: Path
) -> str:
    """生成 S6 争点矩阵 Markdown"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 统计争点分布
    critical = sum(1 for r in rows if PRIORITY_CRITICAL in r["重要性"])
    major = sum(1 for r in rows if PRIORITY_MAJOR in r["重要性"])
    minor = sum(1 for r in rows if PRIORITY_MINOR in r["重要性"])
    conceded = sum(1 for r in rows if PRIORITY_CONCEDED in r["重要性"])

    lines = [
        f"# S6 — 争点矩阵（双方共用）",
        "",
        f"> **九步法第6步**：双方争点对撞，确定主次战场",
        f"> **案由**: {case_type}",
        f"> **生成时间**: {now}",
        f"> **语义**: 双方共用（S6 为对撞结果）",
        "",
        "---",
        "",
        "## 6.1 争点重要性分布",
        "",
        f"| 等级 | 数量 | 说明 |",
        f"|------|------|------|",
        f"| 🔴 核心争点 | {critical} | 证据缺失或直接冲突，庭审必须攻克 |",
        f"| 🟠 主要争点 | {major} | 被告九步法有抗辩针对，需重点准备 |",
        f"| 🟡 次要争点 | {minor} | 有争议但非决定性 |",
        f"| 🟢 无争议 | {conceded} | 证据充分且被告九步法无有效抗辩 |",
        "",
        "---",
        "",
        "## 6.2 争点对撞矩阵",
        "",
        "| 要件编号 | 要件名称 | 原告九步法证据状态 | 被告九步法可能抗辩 | 重要性 | 原告九步法应对策略 | 律师确认 |",
        "|---------|---------|------------|------------|--------|------------|---------|",
    ]

    for r in rows:
        lines.append(
            f"| {r['要件编号']} | {r['要件名称']} | {r['证据状态']} "
            f"| {r['被告九步法可能抗辩']} | {r['重要性']} | {r['原告九步法应对']} | {r['律师确认']} |"
        )

    lines.append("")

    # 主次战场分析
    lines.append("---")
    lines.append("")
    lines.append("## 6.3 主次战场分析")
    lines.append("")

    if critical > 0:
        lines.append("### 🔴 核心战场（必须攻克）")
        lines.append("")
        for r in rows:
            if PRIORITY_CRITICAL in r["重要性"]:
                lines.append(f"- **{r['要件名称']}**（{r['要件编号']}）：{r['被告九步法可能抗辩']}")
        lines.append("")

    if major > 0:
        lines.append("### 🟠 主要战场（重点准备）")
        lines.append("")
        for r in rows:
            if PRIORITY_MAJOR in r["重要性"]:
                lines.append(f"- **{r['要件名称']}**（{r['要件编号']}）：被告九步法可能以「{r['被告九步法可能抗辩']}」抗辩")
        lines.append("")

    if conceded > 0:
        lines.append("### 🟢 无争议要件（快速通过）")
        lines.append("")
        for r in rows:
            if PRIORITY_CONCEDED in r["重要性"]:
                lines.append(f"- {r['要件名称']}（{r['要件编号']}）")
        lines.append("")

    # 庭审策略建议
    lines.append("---")
    lines.append("")
    lines.append("## 6.4 庭审策略建议")
    lines.append("")
    lines.append("### 举证顺序建议")
    lines.append("")
    lines.append("1. 先举证无争议要件（快速建立事实基础）")
    lines.append("2. 再举证核心争点要件（集中火力攻克）")
    lines.append("3. 最后补充次要争点（查漏补缺）")
    lines.append("")
    lines.append("### 质证重点")
    lines.append("")
    for r in rows:
        if PRIORITY_CRITICAL in r["重要性"] or PRIORITY_MAJOR in r["重要性"]:
            lines.append(f"- **{r['要件名称']}**：重点质证被告九步法「{r['被告九步法可能抗辩']}」的证据")
    lines.append("")

    # 待确认清单
    lines.append("---")
    lines.append("")
    lines.append("## 6.5 待确认事项")
    lines.append("")
    lines.append("- [ ] 争点重要性分级是否准确？")
    lines.append("- [ ] 被告九步法抗辩预判是否遗漏？")
    lines.append("- [ ] 原告九步法应对策略是否已补充？")
    lines.append("- [ ] 主次战场划分是否符合庭审策略？")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**状态**: ⏳ 待律师确认")
    lines.append("**下一步**: S7-举证责任")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="S6 争点矩阵 — 双方争点对撞")
    parser.add_argument("case_root", nargs="?", default=".", help="案件文件夹路径")
    parser.add_argument("--case-type", default="", help="案由名称（不指定则自动检测）")
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

    # 读取 S4 要件拆解
    s4_path = case_root / "intermediate" / "原告九步法" / "S4-要件拆解.md"
    elements = parse_elements_from_s4(s4_path)
    print(f"📊 提取要件: {len(elements)} 个")

    # 读取被告九步法 S3 抗辩
    s3_path = case_root / "intermediate" / "被告九步法" / "S3-抗辩规范.md"
    defenses = parse_defenses_from_s3(s3_path)
    print(f"🛡 提取被告九步法抗辩: {len(defenses)} 条")

    # 加载抗辩武器库
    defense_lib = load_defense_library(case_type)
    lib_count = sum(len(v) for v in defense_lib.get("抗辩分类", {}).values())
    print(f"📚 抗辩武器库: {lib_count} 条")

    # 构建争点行
    rows = build_dispute_rows(elements, defenses, defense_lib)

    # 生成 Markdown
    md = generate_dispute_matrix_md(case_type, elements, defenses, rows, case_root)

    # 写入 S6（扁平化路径，原告九步法目录，双方共用）
    output_dir = case_root / "intermediate" / "原告九步法"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "S6-争点矩阵.md"
    output_path.write_text(md, encoding="utf-8")
    print(f"✅ 生成 {output_path.relative_to(case_root)}")

    # 同步到被告九步法目录
    t_dir = case_root / "intermediate" / "被告九步法"
    t_dir.mkdir(parents=True, exist_ok=True)
    t_path = t_dir / "S6-争点矩阵.md"
    if not t_path.exists():
        import shutil
        shutil.copy2(output_path, t_path)
        print(f"✅ 同步到 {t_path.relative_to(case_root)}")

    # 统计
    critical = sum(1 for r in rows if PRIORITY_CRITICAL in r["重要性"])
    major = sum(1 for r in rows if PRIORITY_MAJOR in r["重要性"])
    print(f"\n📊 争点分布: 🔴核心 {critical} | 🟠主要 {major} | 🟡次要 {len(rows)-critical-major}")


if __name__ == "__main__":
    main()
