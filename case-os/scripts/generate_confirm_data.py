#!/usr/bin/env python3
"""
生成九步法确认表数据文件（九步法确认表-data.js）

从 _index.json + S1-S9 中间文件 + CLAUDE.md 生成，供 九步法确认表.html 加载。
用法:
    python3 generate_confirm_data.py [案件文件夹路径]
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent


def load_index(case_root: Path) -> dict:
    idx_path = case_root / "intermediate" / "_index.json"
    if idx_path.exists():
        with open(idx_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def extract_case_meta(case_root: Path) -> dict:
    """从 CLAUDE.md 提取案件元信息"""
    case_brain_path = case_root / "CLAUDE.md"
    meta = {
        "caseName": case_root.name,
        "caseType": "",
        "caseNumber": "",
        "court": "",
        "courtDate": "",
        "amount": "",
        "plaintiff": "",
        "defendant": "",
    }
    if not case_brain_path.exists():
        return meta

    text = case_brain_path.read_text(encoding="utf-8")

    # 案由
    m = re.search(r"\*\*案由\*\*[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        meta["caseType"] = m.group(1).strip()

    # 原告名称（从嵌套 #### 委托人 下提取）
    in_plaintiff = False
    for line in text.split("\n"):
        if "委托人" in line and "####" in line:
            in_plaintiff = True
            continue
        if in_plaintiff and line.strip().startswith("#### "):
            in_plaintiff = False
            continue
        if in_plaintiff and "**名称**" in line:
            m = re.search(r"\*\*名称\*\*[：:]\s*(.+?)$", line)
            if m:
                meta["plaintiff"] = m.group(1).strip()
            break

    # 被告名称
    in_defendant = False
    for line in text.split("\n"):
        if "对方当事人" in line and "####" in line:
            in_defendant = True
            continue
        if in_defendant and line.strip().startswith("#### "):
            in_defendant = False
            continue
        if in_defendant and "**名称**" in line:
            m = re.search(r"\*\*名称\*\*[：:]\s*(.+?)$", line)
            if m:
                meta["defendant"] = m.group(1).strip()
            break

    # 金额（支持表格和行内两种格式）
    for pattern in [
        r"诉讼主张欠款[^\d]*?([\d,，.]+)",
        r"\*\*诉讼主张欠款\*\*[^\d]*?([\d,，.]+)",
    ]:
        m = re.search(pattern, text)
        if m:
            meta["amount"] = m.group(1).strip() + "元"
            break

    # 法院
    m = re.search(r"\*\*受诉法院\*\*[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        meta["court"] = m.group(1).strip()

    # 开庭日期（从 CLAUDE.md 提取）
    m = re.search(r"(\d{4}\.\d{1,2}\.\d{1,2})[^\n]*开庭", text)
    if m:
        meta["courtDate"] = m.group(1)
    if not meta["courtDate"]:
        m = re.search(r"(?:开庭|庭审)[^\d]*(\d{4})[年.](\d{1,2})[月.](\d{1,2})", text)
        if m:
            meta["courtDate"] = f"{m.group(1)}.{int(m.group(2))}.{int(m.group(3))}"

    # 案件名称始终使用文件夹名（case_root.name），不覆盖为当事人拼接名
    # 全局规则：见 SKILL.md §9

    return meta


def _extract_points_from_md(content: str, max_points: int = 5) -> list:
    """从 Markdown 内容提取结构化要点"""
    points = []
    lines = content.split("\n")

    # 策略1: 提取 ## 标题作为 point title，下一段作为 body
    i = 0
    while i < len(lines) and len(points) < max_points:
        line = lines[i].strip()
        if line.startswith("## ") and not any(skip in line for skip in ("前置", "目录", "概述", "索引")):
            title = line.lstrip("# ").strip()
            # 找下一段非空非标题行
            body_parts = []
            j = i + 1
            while j < len(lines) and len(body_parts) < 3:
                nl = lines[j].strip()
                if nl.startswith("#"):
                    break
                if nl and not nl.startswith("|") and not nl.startswith("```"):
                    body_parts.append(nl)
                j += 1
            body = " ".join(body_parts)[:200]
            if body:
                # 判断类型
                ptype = "info"
                if any(k in title + body for k in ("🔴", "致命", "缺口", "风险", "不足")):
                    ptype = "danger"
                elif any(k in title + body for k in ("🟡", "注意", "待核实", "证据", "论证")):
                    ptype = "warn"
                elif any(k in title + body for k in ("🟢", "充分", "已确认", "完成")):
                    ptype = "safe"

                points.append({
                    "title": title[:60],
                    "body": body[:200],
                    "type": ptype,
                })
        i += 1

    # 策略2: 如果没有足够 points，从表格提取
    if len(points) < 2:
        in_table = False
        for line in lines:
            if "|" in line and "---" not in line and not in_table:
                if any(k in line for k in ("要件", "争点", "项目", "证据", "事实")):
                    in_table = True
                    continue
            if in_table and line.strip().startswith("|") and "---" not in line:
                cells = [c.strip() for c in line.split("|")]
                non_empty = [c for c in cells if c and not c.startswith(":")]
                if len(non_empty) >= 2:
                    title = non_empty[0][:60] if non_empty else ""
                    body = " | ".join(non_empty[1:])[:200]
                    points.append({
                        "title": title,
                        "body": body,
                        "type": "info",
                    })
                if len(points) >= max_points:
                    break

    return points


def _extract_todos(content: str) -> list:
    """提取待办事项"""
    todos = []
    for line in content.split("\n"):
        line = line.strip()
        if re.match(r"^[-*]\s*\[ \]", line):
            todos.append(line.lstrip("-* [ ]").strip()[:100])
        elif line.startswith("⚠️") or "待核实" in line or "缺失" in line or "补充" in line:
            if len(line) < 80:
                todos.append(line[:100])
    return todos[:5]


def _classify_risk(content: str) -> str:
    """根据内容判断风险等级"""
    risk_markers = content[:2000]
    if any(k in risk_markers for k in ("🔴", "致命缺口", "强对撞", "核心战场")):
        return "p0"
    if any(k in risk_markers for k in ("🟡", "中对撞", "次战场", "风险", "待核实", "缺口")):
        return "p1"
    return "p2"


_STEP_NAMES = {
    "S1": "固定权利请求", "S2": "请求权基础", "S3": "抗辩规范",
    "S4": "要件拆解", "S5": "主张检索", "S6": "争点矩阵",
    "S7": "举证责任", "S8": "事实认定", "S9": "要件归入与裁判预测",
}


def generate(case_root: Path):
    meta = extract_case_meta(case_root)

    steps = []
    for i in range(1, 10):
        sid = f"S{i}"
        sname = _STEP_NAMES.get(sid, sid)

        # 读取原告文件（兼容扁平结构和子目录结构）
        p_base = case_root / "intermediate" / "原告九步法"
        p_file_nested = p_base / f"{sid}-{sname}" / f"{sid}-{sname}.md"
        p_file_flat = p_base / f"{sid}-{sname}.md"
        p_file = p_file_flat if p_file_flat.exists() else p_file_nested
        p_points = []
        p_content = ""
        if p_file.exists():
            p_content = p_file.read_text(encoding="utf-8")
            p_points = _extract_points_from_md(p_content)

        # 读取被告文件（兼容扁平结构和子目录结构）
        d_base = case_root / "intermediate" / "被告九步法"
        d_file_nested = d_base / f"{sid}-{sname}" / f"{sid}-{sname}.md"
        d_file_flat = d_base / f"{sid}-{sname}.md"
        d_file = d_file_flat if d_file_flat.exists() else d_file_nested
        d_points = []
        d_content = ""
        if d_file.exists():
            d_content = d_file.read_text(encoding="utf-8")
            d_points = _extract_points_from_md(d_content)

        # 合并内容判断风险
        risk = _classify_risk(p_content) if p_content else "p2"

        # 提取待办
        todos = _extract_todos(p_content)
        if d_content:
            todos.extend(_extract_todos(d_content))
        todos = list(dict.fromkeys(todos))[:5]  # 去重

        # 提取结论（原告文件的最后一段或总结性内容）
        conclusion = ""
        for m in re.finditer(r"结论[：:](.+?)(?:\n|$)", p_content):
            conclusion = m.group(1).strip()[:200]

        steps.append({
            "id": sid,
            "name": sname,
            "risk": risk,
            "plaintiff": {"points": p_points},
            "defendant": {"points": d_points},
            "todos": todos,
            "conclusion": conclusion,
        })

    data = {
        "caseName": meta["caseName"],
        "caseType": meta["caseType"],
        "caseNumber": meta["caseNumber"],
        "courtDate": meta["courtDate"],
        "amount": meta["amount"],
        "steps": steps,
        "_meta": {
            "generatedAt": datetime.now().isoformat(),
        },
    }

    # 写入 JS 文件
    js_content = "// 九步法确认表数据\n// 生成时间: " + datetime.now().isoformat() + "\n"
    js_content += "window.CONFIRM_TABLE_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"

    output_path = case_root / "案件确认表-data.js"
    output_path.write_text(js_content, encoding="utf-8")
    print(f"✅ 生成确认表数据: {output_path.relative_to(case_root)}")

    point_count = sum(len(s["plaintiff"]["points"]) + len(s["defendant"]["points"]) for s in steps)
    print(f"📊 提取 {point_count} 个要点（{len(steps)} 步）")


if __name__ == "__main__":
    case_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    generate(case_root.resolve())
