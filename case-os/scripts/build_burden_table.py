#!/usr/bin/env python3
"""
S7 举证责任表生成器
分配各要件举证责任，标红证据缺口

读取:
  - intermediate/原告九步法/S4-要件拆解.md（要件表）
  - templates/elements/<案由>.yaml（举证责任分配）
  - data/defenses/<案由>.json（抗辩武器库·举证方信息）

输出:
  - intermediate/原告九步法/S7-举证责任.md
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SKILL_DIR = Path(__file__).parent.parent
ELEMENTS_DIR = SKILL_DIR / "templates" / "elements"
DEFENSES_DIR = SKILL_DIR / "data" / "defenses"


def load_yaml_burden(case_type: str) -> list:
    """从 YAML 模板加载举证责任分配"""
    yaml_path = ELEMENTS_DIR / f"{case_type}.yaml"
    if not yaml_path.exists():
        for f in ELEMENTS_DIR.glob("*.yaml"):
            if case_type in f.stem or f.stem in case_type:
                yaml_path = f
                break
        else:
            return []

    if yaml is None:
        return []

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("举证责任", [])


def parse_elements_from_s4(s4_path: Path) -> list:
    """从 S4 要件拆解文件中提取构成要件列表"""
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
            "证据类型": m.group(4).strip(),
            "证据来源": m.group(5).strip(),
            "证据状态": m.group(6).strip(),
        })

    return elements


def load_defense_library(case_type: str) -> dict:
    """加载抗辩武器库"""
    json_path = DEFENSES_DIR / f"{case_type}.json"
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    for f in DEFENSES_DIR.glob("*.json"):
        if case_type in f.stem or f.stem in case_type:
            with open(f, encoding="utf-8") as fp:
                return json.load(fp)
    return {}


def build_burden_rows(elements: list, yaml_burdens: list, defense_lib: dict) -> list:
    """构建举证责任行"""
    rows = []

    # YAML 举证责任映射
    burden_map = {}
    for b in yaml_burdens:
        burden_map[b.get("要件", "")] = {
            "举证方": b.get("举证方", "原告"),
            "说明": b.get("说明", ""),
        }

    for elem in elements:
        ename = elem["要件名称"]
        estate = elem["证据状态"]

        # 匹配 YAML 举证责任
        burden = burden_map.get(ename, {})
        party = burden.get("举证方", "原告")
        note = burden.get("说明", "")

        # 证据缺口判定
        has_gap = "🔴" in estate or "未找到" in estate or "待" in estate
        gap_status = "🔴 证据缺失" if has_gap else "✅ 已有证据"

        # 举证难度评估
        if has_gap:
            difficulty = "高"
        elif "待补充" in elem.get("证据来源", ""):
            difficulty = "中"
        else:
            difficulty = "低"

        rows.append({
            "要件编号": elem["编号"],
            "要件名称": ename,
            "举证方": party,
            "举证说明": note,
            "必要事实": elem["必要事实"],
            "证据类型": elem["证据类型"],
            "证据来源": elem["证据来源"],
            "证据状态": estate,
            "缺口状态": gap_status,
            "举证难度": difficulty,
        })

    return rows


def generate_burden_table_md(
    case_type: str,
    rows: list,
    defense_lib: dict,
    case_root: Path
) -> str:
    """生成 S7 举证责任 Markdown"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 统计
    total = len(rows)
    gaps = sum(1 for r in rows if "🔴" in r["缺口状态"])
    my_burden = sum(1 for r in rows if r["举证方"] == "原告")
    their_burden = sum(1 for r in rows if r["举证方"] == "被告")

    lines = [
        f"# S7 — 举证责任（原告九步法）",
        "",
        f"> **九步法第7步**：分配各要件举证责任，标红证据缺口",
        f"> **案由**: {case_type}",
        f"> **生成时间**: {now}",
        f"> **数据来源**: YAML模板 + S4要件表",
        "",
        "---",
        "",
        "## 7.1 举证责任分配总览",
        "",
        f"| 统计项 | 数量 |",
        f"|--------|------|",
        f"| 要件总数 | {total} |",
        f"| 原告九步法举证（原告） | {my_burden} |",
        f"| 对方举证（被告） | {their_burden} |",
        f"| 🔴 证据缺口 | {gaps} |",
        "",
        "---",
        "",
        "## 7.2 举证责任分配表",
        "",
        "| 要件编号 | 要件名称 | 举证方 | 举证说明 | 必要事实 | 证据类型 | 证据来源 | 证据状态 | 缺口 | 难度 |",
        "|---------|---------|--------|---------|---------|---------|---------|---------|------|------|",
    ]

    for r in rows:
        lines.append(
            f"| {r['要件编号']} | {r['要件名称']} | {r['举证方']} "
            f"| {r['举证说明']} | {r['必要事实']} | {r['证据类型']} "
            f"| {r['证据来源']} | {r['证据状态']} | {r['缺口状态']} | {r['举证难度']} |"
        )

    lines.append("")

    # 证据缺口清单
    if gaps > 0:
        lines.append("---")
        lines.append("")
        lines.append("## 7.3 🔴 证据缺口清单（需补充）")
        lines.append("")
        lines.append("| 要件 | 缺口事实 | 建议补充证据 | 补充难度 |")
        lines.append("|------|---------|------------|---------|")
        for r in rows:
            if "🔴" in r["缺口状态"]:
                lines.append(
                    f"| {r['要件名称']} | {r['必要事实']} "
                    f"| {r['证据类型']} | {r['举证难度']} |"
                )
        lines.append("")

    # 对方举证要件（原告九步法质证重点）
    if their_burden > 0:
        lines.append("---")
        lines.append("")
        lines.append("## 7.4 对方举证要件（原告九步法质证重点）")
        lines.append("")
        lines.append("| 要件 | 对方举证内容 | 原告九步法质证策略 |")
        lines.append("|------|------------|------------|")
        for r in rows:
            if r["举证方"] == "被告":
                lines.append(f"| {r['要件名称']} | {r['必要事实']} | 待补充 |")
        lines.append("")

    # 待确认清单
    lines.append("---")
    lines.append("")
    lines.append("## 7.5 待确认事项")
    lines.append("")
    lines.append("- [ ] 举证方分配是否正确？")
    lines.append("- [ ] 证据缺口是否已逐一补充？")
    lines.append("- [ ] 对方举证要件的质证策略是否已准备？")
    lines.append("- [ ] 北大法宝复验是否通过？")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**状态**: ⏳ 待律师确认")
    lines.append("**下一步**: S8-事实认定")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="S7 举证责任 — 举证分配与缺口标红")
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

    # 读取 S4 要件
    s4_path = case_root / "intermediate" / "原告九步法" / "S4-要件拆解.md"
    elements = parse_elements_from_s4(s4_path)
    print(f"📊 提取要件: {len(elements)} 个")

    # 加载 YAML 举证责任
    yaml_burdens = load_yaml_burden(case_type)
    print(f"📜 YAML 举证分配: {len(yaml_burdens)} 条")

    # 加载抗辩武器库
    defense_lib = load_defense_library(case_type)

    # 构建举证行
    rows = build_burden_rows(elements, yaml_burdens, defense_lib)

    # 生成 Markdown
    md = generate_burden_table_md(case_type, rows, defense_lib, case_root)

    # 写入（扁平化路径）
    output_dir = case_root / "intermediate" / "原告九步法"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "S7-举证责任.md"
    output_path.write_text(md, encoding="utf-8")
    print(f"✅ 生成 {output_path.relative_to(case_root)}")

    # 统计
    gaps = sum(1 for r in rows if "🔴" in r["缺口状态"])
    print(f"\n📊 举证责任: {len(rows)} 个要件 | 🔴 缺口 {gaps} 个")


if __name__ == "__main__":
    main()
