#!/usr/bin/env python3
"""
S4 要件拆解 — 三段式要件矩阵生成器
Step A: 加载 YAML 模板（基础要件）
Step B: AI 补充案情特色（由 Codex 调用时动态填充）
Step C: 北大法宝复验标记（由 Codex 调用 MCP 后回写）

用法:
    python3 build_element_matrix.py [案件文件夹路径] [--case-type 案由名称]

输出:
    intermediate/原告九步法/S4-要件拆解.md
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


ELEMENTS_DIR = Path(__file__).parent.parent / "templates" / "elements"


def load_yaml_template(case_type: str) -> dict:
    """Step A: 加载指定案由的 YAML 要件模板"""
    # 尝试精确匹配
    yaml_path = ELEMENTS_DIR / f"{case_type}.yaml"
    if yaml_path.exists():
        return _parse_yaml(yaml_path)

    # 模糊匹配：案由名包含关键词
    for f in ELEMENTS_DIR.glob("*.yaml"):
        stem = f.stem
        if case_type in stem or stem in case_type:
            print(f"✅ 模糊匹配: {case_type} → {stem}")
            return _parse_yaml(f)

    # 未找到模板
    print(f"⚠️ 未找到案由「{case_type}」的 YAML 模板，将使用通用模板")
    return _generic_template(case_type)


def _parse_yaml(path: Path) -> dict:
    """解析 YAML 模板文件"""
    if yaml is None:
        # 简易解析（无 PyYAML 时的降级方案）
        return _simple_yaml_parse(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "案由": data.get("案由", ""),
        "案由编号": data.get("案由编号", ""),
        "请求权基础": data.get("请求权基础", []),
        "常见抗辩": data.get("常见抗辩", []),
        "举证责任": data.get("举证责任", []),
        "source": "yaml_template",
    }


def _simple_yaml_parse(path: Path) -> dict:
    """简易 YAML 解析（降级方案）"""
    text = path.read_text(encoding="utf-8")
    # 提取案由名
    m = re.search(r"案由:\s*(.+)", text)
    case_type = m.group(1).strip() if m else path.stem
    return {
        "案由": case_type,
        "案由编号": "",
        "请求权基础": [],
        "常见抗辩": [],
        "举证责任": [],
        "source": "yaml_template_degraded",
    }


def _generic_template(case_type: str) -> dict:
    """通用模板（未匹配到特定案由时使用）"""
    return {
        "案由": case_type,
        "案由编号": "",
        "请求权基础": [{
            "法律依据": "待检索",
            "构成要件": [{
                "要件名称": "待AI推导",
                "说明": "需根据案情推导构成要件",
                "必要事实": [],
                "证据类型": [],
            }],
        }],
        "常见抗辩": [],
        "举证责任": [],
        "source": "generic_template",
    }


def detect_case_type(case_root: Path) -> str:
    """从 CLAUDE.md 自动识别案由"""
    case_brain_path = case_root / "CLAUDE.md"
    if not case_brain_path.exists():
        return ""
    text = case_brain_path.read_text(encoding="utf-8")

    # 优先从表格中提取案由
    m = re.search(r"\|\s*案由\s*\|\s*([^|\n]+?)\s*\|", text)
    if m:
        return m.group(1).strip()

    # 其次从 key-value 格式提取
    m = re.search(r"案由[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        return m.group(1).strip()

    # 从案件类型推断
    m = re.search(r"案件类型[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        return m.group(1).strip()

    return ""


def generate_element_matrix_md(template: dict, case_root: Path) -> str:
    """生成 S4 要件拆解 Markdown 文档"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    case_type = template["案由"]

    lines = [
        f"# S4 — 要件拆解（原告九步法）",
        "",
        f"> **九步法第4步**：将 S2 请求权基础拆解为需证明的具体事实，逐一检索证据",
        f"> **案由**: {case_type}",
        f"> **生成时间**: {now}",
        f"> **数据来源**: {template['source']}",
        "",
        "---",
        "",
        "## 4.1 请求权构成要件表",
        "",
    ]

    # 请求权基础 + 构成要件
    req_idx = 0
    for req in template.get("请求权基础", []):
        req_idx += 1
        law = req.get("法律依据", "待检索")
        lines.append(f"### 请求权基础 {req_idx}: {law}")
        lines.append("")
        lines.append("| 要件编号 | 构成要件 | 必要事实 | 证据类型 | 证据来源 | 证据状态 |")
        lines.append("|---------|---------|---------|---------|---------|---------|")

        elem_idx = 0
        for elem in req.get("构成要件", []):
            elem_idx += 1
            eid = f"{req_idx}.{elem_idx}"
            name = elem.get("要件名称", "待定")
            facts = "、".join(elem.get("必要事实", [])) or "待补充"
            etypes = "、".join(elem.get("证据类型", [])) or "待补充"
            # 证据来源和状态由 AI/律师补充
            source = "待检索"
            status = "🔴 未找到"
            lines.append(f"| {eid} | **{name}** | {facts} | {etypes} | {source} | {status} |")

        lines.append("")

    # 常见抗辩
    defenses = template.get("常见抗辩", [])
    if defenses:
        lines.append("---")
        lines.append("")
        lines.append("## 4.2 预判对方抗辩要件")
        lines.append("")
        lines.append("| 编号 | 抗辩名称 | 类型 | 法律依据 | 证明事项 | 证据类型 |")
        lines.append("|------|---------|------|---------|---------|---------|")
        for i, d in enumerate(defenses, 1):
            dtype = d.get("类型", "待定")
            dname = d.get("抗辩名称", "待定")
            dlaw = d.get("法律依据", "待检索")
            ditems = "、".join(d.get("证明事项", [])) or "待补充"
            detypes = "、".join(d.get("证据类型", [])) or "待补充"
            lines.append(f"| D{i} | {dname} | {dtype} | {dlaw} | {ditems} | {detypes} |")
        lines.append("")

    # 举证责任
    burdens = template.get("举证责任", [])
    if burdens:
        lines.append("---")
        lines.append("")
        lines.append("## 4.3 举证责任分配预判")
        lines.append("")
        lines.append("| 要件 | 举证方 | 说明 |")
        lines.append("|------|--------|------|")
        for b in burdens:
            bname = b.get("要件", "待定")
            bparty = b.get("举证方", "待定")
            bnote = b.get("说明", "")
            lines.append(f"| {bname} | {bparty} | {bnote} |")
        lines.append("")

    # 待律师确认清单
    lines.append("---")
    lines.append("")
    lines.append("## 4.4 待确认事项")
    lines.append("")
    lines.append("- [ ] 构成要件是否完整？是否遗漏隐含要件？")
    lines.append("- [ ] 证据来源是否已逐一检索？")
    lines.append("- [ ] 证据状态标红是否准确？")
    lines.append("- [ ] 北大法宝复验是否通过？")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**状态**: ⏳ 待律师确认")
    lines.append("**下一步**: S5-主张检索")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="S4 要件拆解 — 三段式要件矩阵生成")
    parser.add_argument("case_root", nargs="?", default=".", help="案件文件夹路径")
    parser.add_argument("--case-type", default="", help="案由名称（不指定则自动检测）")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    print(f"🔍 案件目录: {case_root}")

    # 检测案由
    case_type = args.case_type or detect_case_type(case_root)
    if not case_type:
        print("❌ 未检测到案由，请用 --case-type 指定")
        sys.exit(1)
    print(f"📋 案由: {case_type}")

    # Step A: 加载 YAML 模板
    template = load_yaml_template(case_type)
    print(f"✅ Step A 完成: {template['source']}")

    # 生成 Markdown
    md_content = generate_element_matrix_md(template, case_root)

    # 写入 S4（扁平化路径）
    output_dir = case_root / "intermediate" / "原告九步法"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "S4-要件拆解.md"
    output_path.write_text(md_content, encoding="utf-8")
    print(f"✅ 生成 {output_path.relative_to(case_root)}")

    # Step B/C 提示
    print()
    print("📝 Step B: 请让 Codex 根据案情材料补充证据来源和证据状态")
    print("📝 Step C: 请让 Codex 调用北大法宝 MCP 复验法律依据")


if __name__ == "__main__":
    main()
