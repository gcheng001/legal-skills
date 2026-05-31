#!/usr/bin/env python3
"""
A7 证据卡片提取脚本 — 材料扫描 + 模板初始化 + 解析入库 + 双视图输出

功能:
  1. scan   — 扫描 markdown/ 目录，生成材料清单，初始化模板
  2. parse  — AI 填写模板后，解析 Markdown 表格为结构化 JSON
  3. all    — scan + parse + 双视图生成（默认）

用法:
    python3 extract_snippets.py [案件文件夹路径] [--action scan|parse|all]

输出（v7.1 双视图）:
    intermediate/证据卡片库-按来源.md    — 按来源材料文件分组（核对用）
    intermediate/证据卡片库-按来源.json  — 来源视图结构化数据
    intermediate/证据卡片库-按目的.md    — 按证明目的标签分组（分析用）
    intermediate/证据卡片库-按目的.json  — 目的视图结构化数据
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# ===== 常量 =====
SKILL_DIR = Path(__file__).parent.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "intermediate" / "S0-证据卡片库.md"

# 证明目的标签（用于分类片段）
PROOF_PURPOSE_LABELS = [
    "承认欠款/债务确认",
    "确认事实/行为经过",
    "时间节点/期间",
    "金额记录/款项往来",
    "身份关系/当事人确认",
    "合同约定/权利义务",
    "其他",
]

SCAN_DIRS = ["markdown", "_archive/markdown"]


def scan_markdown(case_root: Path) -> list[dict]:
    """扫描案件目录下的 Markdown 文件，返回文件清单"""
    files = []
    for rel_dir in SCAN_DIRS:
        scan_dir = case_root / rel_dir
        if not scan_dir.exists():
            continue
        for f in sorted(scan_dir.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".md", ".txt", ".markdown"):
                ext = f.suffix.lower().lstrip(".")
                try:
                    stat = f.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                except Exception:
                    size = 0
                    mtime = datetime.now()
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(case_root)),
                    "ext": ext,
                    "size": size,
                    "mtime": mtime,
                })
    # 按时间排序
    files.sort(key=lambda x: x["mtime"])
    return files


def _truncate_preview(text: str, max_chars: int = 60) -> str:
    """取文本首段作为摘要预览"""
    text = text.strip()
    # 去掉 frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            text = text[end + 3:].strip()
    # 取第一个非空段落
    for paragraph in re.split(r"\n\s*\n", text):
        clean = paragraph.strip()
        clean = re.sub(r"[#*`\[\]>|]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) > 10:
            text = clean
            break
    if len(text) > max_chars:
        return text[:max_chars] + "…"
    return text


def _get_markdown_type(fname: str) -> str:
    """根据文件名推断材料类型"""
    name = fname.lower()
    if any(k in name for k in ("聊天", "微信", "对话", "短信", "messenger")):
        return "聊天记录"
    if any(k in name for k in ("合同", "协议", "合约", "契", "agreement")):
        return "合同"
    if any(k in name for k in ("回单", "转账", "流水", "账单", "银行")):
        return "银行凭证"
    if any(k in name for k in ("照片", "截图", "图片", "photo", "screenshot")):
        return "图片"
    if any(k in name for k in ("判决", "裁定", "决定", "判决书", "裁定书")):
        return "法院文书"
    if any(k in name for k in ("催收", "催款", "对账", "结算")):
        return "催收/对账"
    if any(k in name for k in ("邮件", "email", "邮件")):
        return "邮件"
    if any(k in name for k in ("录音", "语音", "电话")):
        return "录音转写"
    return "其他"


def init_s0_template(case_root: Path) -> str:
    """扫描材料，生成填充了材料清单的 S0 模板"""
    files = scan_markdown(case_root)

    if not files:
        return "⚠️  未找到 Markdown 文件，请先执行 OCR 转换"

    inter_dir = case_root / "intermediate"
    inter_dir.mkdir(exist_ok=True)

    # 读取模板
    if TEMPLATE_PATH.exists():
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    else:
        template = "# S0 证据卡片库\n\n（模板文件不存在，使用默认结构）\n"

    # 生成材料清单表格
    material_rows = []
    total_chars = 0
    for i, f in enumerate(files, 1):
        # 读取文件前 500 字作摘要
        preview = ""
        try:
            full_path = case_root / f["path"]
            content = full_path.read_text(encoding="utf-8")
            total_chars += len(content)
            preview = _truncate_preview(content)
        except Exception:
            pass
        file_type = _get_markdown_type(f["name"])
        size_str = f"{f['size'] / 1024:.1f} KB" if f['size'] >= 1024 else f"{f['size']} B"
        material_rows.append(
            f"| {i} | {f['name']} | {file_type} | {size_str} | {preview} |"
        )

    material_table = (
        "| 序号 | 文件名 | 类型 | 大小 | 内容摘要 |\n"
        "|------|--------|------|------|---------|\n"
        + "\n".join(material_rows)
    )

    # 替换模板中的材料清单部分
    content = re.sub(
        r"(?<=\| 序号 \| 文件名 \| 类型 \| 字数 \| 关键内容摘要 \|\n\|------\|--------\|------\|------\|-------------\|\n).*?(?=\n---\n\n## 证据卡片列表)",
        material_table,
        template,
        flags=re.DOTALL,
    )

    # 如果模板格式不匹配，直接追加
    if content == template:
        content = re.sub(
            r"## 材料清单\n\n.*?(?=\n---\n\n## 证据卡片列表)",
            f"## 材料清单\n\n{material_table}\n",
            template,
            flags=re.DOTALL,
        )

    # 写入
    output_path = inter_dir / "S0-证据卡片库.md"
    output_path.write_text(content, encoding="utf-8")
    count = len(files)
    print(f"📄 已扫描 {count} 个 Markdown 文件（{total_chars // 1024} KB）")
    print(f"📝 生成 {output_path.relative_to(case_root)}")
    return str(output_path)


# ===== 解析 =====


def _parse_table_sections(md_content: str) -> list[dict]:
    """从 Markdown 的表格中解析证据卡片"""
    snippets = []
    current_label = "其他"
    lines = md_content.split("\n")

    for i, line in enumerate(lines):
        # 检测证明目的分类标题
        label_match = re.match(r"^### 证明目的[：:]\s*(.+)", line.strip())
        if label_match:
            current_label = label_match.group(1).strip()

        # 检测表格行
        if line.strip().startswith("| SP") or line.strip().startswith("| SP"):
            cells = [c.strip() for c in line.split("|")]
            # 表格格式: |编号|来源|位置|原文|发言者|当事人|时间|金额|置信度|待确认|
            if len(cells) >= 10:
                snippet = {
                    "id": cells[1],
                    "source": cells[2],
                    "location": cells[3],
                    "text": cells[4],
                    "speaker": cells[5] if len(cells) > 5 else "",
                    "parties": cells[6] if len(cells) > 6 else "",
                    "time": cells[7] if len(cells) > 7 else "",
                    "amount": cells[8] if len(cells) > 8 else "",
                    "confidence": cells[9] if len(cells) > 9 else "",
                    "pending_review": "⚠️" in cells[10] if len(cells) > 10 else False,
                    "purpose_label": current_label,
                    "confirmed": not ("⚠️" in cells[10] if len(cells) > 10 else False),
                }
                snippets.append(snippet)
            elif len(cells) >= 9:
                # 兼容旧版格式（无发言者列）
                snippet = {
                    "id": cells[1],
                    "source": cells[2],
                    "location": cells[3],
                    "text": cells[4],
                    "speaker": "",
                    "parties": cells[5],
                    "time": cells[6],
                    "amount": cells[7],
                    "confidence": cells[8],
                    "pending_review": "⚠️" in cells[9] if len(cells) > 9 else False,
                    "purpose_label": current_label,
                    "confirmed": not ("⚠️" in cells[9] if len(cells) > 9 else False),
                }
                snippets.append(snippet)

    return snippets


def parse_s0(case_root: Path) -> list[dict]:
    """从 AI 填写后的证据卡片库.md 解析结构化数据"""
    s0_path = case_root / "intermediate" / "证据卡片库.md"
    if not s0_path.exists():
        # 兼容旧版文件名
        s0_path = case_root / "intermediate" / "S0-证据卡片库.md"
        if not s0_path.exists():
            print(f"❌ 证据卡片库文件不存在")
            return []

    content = s0_path.read_text(encoding="utf-8")
    snippets = _parse_table_sections(content)

    # 统计
    total = len(snippets)
    high_conf = sum(1 for s in snippets if s["confidence"] == "高")
    mid_conf = sum(1 for s in snippets if s["confidence"] == "中")
    low_conf = sum(1 for s in snippets if s["confidence"] == "低")
    need_review = sum(1 for s in snippets if s.get("pending_review"))

    # 输出 JSON
    json_data = {
        "cards": snippets,
        "meta": {
            "total_count": total,
            "high_confidence": high_conf,
            "medium_confidence": mid_conf,
            "low_confidence": low_conf,
            "need_review": need_review,
            "last_parsed": datetime.now().isoformat(),
        },
        "purpose_distribution": {},
    }

    # 统计各证明目的标签的片段数
    for snip in snippets:
        label = snip["purpose_label"]
        json_data["purpose_distribution"][label] = (
            json_data["purpose_distribution"].get(label, 0) + 1
        )

    # 写入 JSON（兼容旧版）
    json_path = case_root / "intermediate" / "证据卡片库.json"
    json_path.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✅ 解析完成: {total} 条证据卡片")
    print(f"   高置信度: {high_conf} | 中: {mid_conf} | 低: {low_conf} | 待确认: {need_review}")
    print(f"📊 生成 {json_path.relative_to(case_root)}")
    return snippets


# ===== 双视图生成 =====


def generate_source_view(snippets: list[dict], case_root: Path) -> None:
    """生成按来源材料分组的视图"""
    inter_dir = case_root / "intermediate"

    # 按来源分组
    source_groups: dict[str, list[dict]] = {}
    for sp in snippets:
        source = sp.get("source", "未知来源")
        if source not in source_groups:
            source_groups[source] = []
        source_groups[source].append(sp)

    # 生成 Markdown
    md_lines = ["# 证据卡片库 — 按来源分组\n\n> 用于材料核对，每份文件的所有卡片集中展示。\n\n"]
    for source, cards in source_groups.items():
        md_lines.append(f"## 来源：{source}\n\n")
        md_lines.append("| 编号 | 原文摘要 | 发言者 | 证明目的 | 时间 | 金额 | 置信度 |\n")
        md_lines.append("|------|----------|--------|----------|------|------|--------|\n")
        for card in cards:
            text_preview = card.get("text", "")[:50] + "…" if len(card.get("text", "")) > 50 else card.get("text", "")
            md_lines.append(f"| {card.get('id', '')} | {text_preview} | {card.get('speaker', '')} | {card.get('purpose_label', '')} | {card.get('time', '')} | {card.get('amount', '')} | {card.get('confidence', '')} |\n")
        md_lines.append("\n")

    # 写入文件
    source_md_path = inter_dir / "证据卡片库-按来源.md"
    source_md_path.write_text("".join(md_lines), encoding="utf-8")

    # 生成 JSON
    source_json_data = {
        "view": "source",
        "groups": {k: [dict(s) for s in v] for k, v in source_groups.items()},
        "meta": {
            "source_count": len(source_groups),
            "card_count": len(snippets),
            "generated_at": datetime.now().isoformat(),
        }
    }
    source_json_path = inter_dir / "证据卡片库-按来源.json"
    source_json_path.write_text(json.dumps(source_json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"📝 生成来源视图: {len(source_groups)} 个来源文件")


def generate_purpose_view(snippets: list[dict], case_root: Path) -> None:
    """生成按证明目的分组的视图"""
    inter_dir = case_root / "intermediate"

    # 按证明目的分组
    purpose_groups: dict[str, list[dict]] = {}
    for sp in snippets:
        purpose = sp.get("purpose_label", "其他")
        if purpose not in purpose_groups:
            purpose_groups[purpose] = []
        purpose_groups[purpose].append(sp)

    # 生成 Markdown
    md_lines = ["# 证据卡片库 — 按证明目的分组\n\n> 用于九步法分析，按证明目的集中展示。\n\n"]
    for purpose, cards in purpose_groups.items():
        md_lines.append(f"### 证明目的：{purpose}\n\n")
        md_lines.append("| 编号 | 来源 | 原文摘要 | 发言者 | 时间 | 金额 | 置信度 |\n")
        md_lines.append("|------|------|----------|--------|------|------|--------|\n")
        for card in cards:
            text_preview = card.get("text", "")[:50] + "…" if len(card.get("text", "")) > 50 else card.get("text", "")
            md_lines.append(f"| {card.get('id', '')} | {card.get('source', '')} | {text_preview} | {card.get('speaker', '')} | {card.get('time', '')} | {card.get('amount', '')} | {card.get('confidence', '')} |\n")
        md_lines.append("\n")

    # 写入文件
    purpose_md_path = inter_dir / "证据卡片库-按目的.md"
    purpose_md_path.write_text("".join(md_lines), encoding="utf-8")

    # 生成 JSON
    purpose_json_data = {
        "view": "purpose",
        "groups": {k: [dict(s) for s in v] for k, v in purpose_groups.items()},
        "meta": {
            "purpose_count": len(purpose_groups),
            "card_count": len(snippets),
            "generated_at": datetime.now().isoformat(),
        }
    }
    purpose_json_path = inter_dir / "证据卡片库-按目的.json"
    purpose_json_path.write_text(json.dumps(purpose_json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"📝 生成目的视图: {len(purpose_groups)} 个证明目的分类")


def generate_dual_views(snippets: list[dict], case_root: Path) -> None:
    """生成双视图输出"""
    if not snippets:
        print("⚠️ 无证据卡片，跳过双视图生成")
        return

    generate_source_view(snippets, case_root)
    generate_purpose_view(snippets, case_root)
    print(f"✅ 双视图生成完成")


def main():
    parser = argparse.ArgumentParser(description="A7 证据卡片提取")
    parser.add_argument("case_root", nargs="?", default=".", help="案件文件夹路径")
    parser.add_argument(
        "--action", default="all", choices=["scan", "parse", "all", "dual"],
        help="执行动作（默认 all）",
    )
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    print(f"🔍 案件目录: {case_root}")

    action = args.action

    if action in ("scan", "all"):
        result = init_s0_template(case_root)

    snippets = []
    if action in ("parse", "all"):
        snippets = parse_s0(case_root)

    if action in ("dual", "all"):
        if not snippets:
            snippets = parse_s0(case_root)
        generate_dual_views(snippets, case_root)

    print("\n✅ A7 证据卡片提取完成")


if __name__ == "__main__":
    main()
