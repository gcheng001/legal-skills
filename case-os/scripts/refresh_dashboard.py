#!/usr/bin/env python3
"""
案件仪表盘数据刷新脚本
扫描案件文件夹，解析核心文件，生成 案件仪表盘-data.js

用法:
    python3 refresh_dashboard.py [案件文件夹路径]
    不带参数时默认当前目录

输出:
    案件仪表盘-data.js  (与 index.html 同目录)
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# ===== 常量 =====
STAGE_EMOJI = {
    "S0": "🔍",
    "S1": "📋", "S2": "📜", "S3": "🛡", "S4": "🔬", "S5": "🔍",
    "S6": "⚖", "S7": "📊", "S8": "🧩", "S9": "🎯",
}
STATUS_MAP = {
    "⏳": "pending",
    "🔄": "in_progress",
    "✅": "completed",
    "❌": "blocked",
    "📝": "draft",
    "待启动": "pending",
    "进行中": "in_progress",
    "完成": "completed",
    "阻塞": "blocked",
    "草拟待审": "draft",
}
STATUS_LABEL_MAP = {
    "pending": "待启动",
    "in_progress": "进行中",
    "completed": "完成",
    "blocked": "阻塞",
    "draft": "草拟待审",
}
FILE_TYPE_ICON = {
    "md": "📝",
    "pdf": "📄",
    "docx": "📃",
    "doc": "📃",
    "txt": "📄",
    "jpg": "🖼",
    "jpeg": "🖼",
    "png": "🖼",
    "mp4": "🎬",
    "mp3": "🎵",
    "xlsx": "📊",
    "xls": "📊",
    "pptx": "📽",
    "ppt": "📽",
}


def get_file_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lstrip(".").lower()


def format_file_size(bytes_size: int) -> str:
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def format_time(iso_str: str) -> str:
    """将 ISO 时间字符串转换为 MM/DD HH:MM 格式"""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%m/%d %H:%M")
    except Exception:
        return iso_str


def parse_claim_amount(text: str) -> Optional[str]:
    """从文本中提取金额信息"""
    patterns = [
        r"诉讼标的[：:]\s*([^\n，。]+)",
        r"金额[：:]\s*([^\n，。]+)",
        r"请求[^\d]*([\d,，．]+元)",
        r"([\d,，．]+)\s*元",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None


def _table_val(text: str, key: str) -> str:
    """从 Markdown 表格中提取 | key | value | 格式的值"""
    m = re.search(r"\|\s*" + re.escape(key) + r"\s*\|\s*([^|\n]+?)\s*\|", text)
    return m.group(1).strip() if m else ""


def _extract_name_from_nested(text: str, section_marker: str) -> str:
    """从嵌套格式中提取名称：找到 section_marker 行，然后找下一行 **名称**: XXX"""
    lines = text.split("\n")
    in_section = False
    for line in lines:
        if section_marker in line:
            in_section = True
            continue
        if in_section:
            m = re.search(r"\*\*名称\*\*[：:]\s*(.+?)$", line)
            if m:
                name = m.group(1).strip()
                # 去掉括号内的曾用名
                name = re.sub(r"[（(][^)）]*[）)]", "", name).strip()
                return name
            # 如果遇到下一个 ###/#### 标题，退出
            if line.strip().startswith("#"):
                in_section = False
    return ""


def parse_meta_from_case_brain(text: str) -> dict:
    """从 CLAUDE.md 解析案件元信息（兼容 key:value、表格、嵌套三种格式）"""
    meta = {
        "caseName": "",
        "caseType": "",
        "caseNumber": "",
        "court": "",
        "ourSide": "",
        "generatedAt": datetime.now().isoformat(),
    }

    # === 当事人提取（嵌套格式优先） ===
    plaintiff = _extract_name_from_nested(text, "委托人（我方）")
    if not plaintiff:
        plaintiff = _extract_name_from_nested(text, "委托人")
    defendant = _extract_name_from_nested(text, "对方当事人")
    if not defendant:
        defendant = _extract_name_from_nested(text, "被告一") or _extract_name_from_nested(text, "被告")

    # 表格格式兜底
    if not plaintiff:
        plaintiff = _table_val(text, "原告")
    if not defendant:
        defendant = (_table_val(text, "我方当事人") or _table_val(text, "被告一（我方）") or
                     _table_val(text, "被告一（原告九步法）") or _table_val(text, "被告一") or
                     _table_val(text, "被告"))

    # key-value 兜底
    if not plaintiff:
        m = re.search(r"原告[：:]\s*(.+?)(?:\n|$)", text)
        if m: plaintiff = m.group(1).strip()
    if not defendant:
        m = re.search(r"被告[：:]\s*(.+?)(?:\n|$)", text)
        if m: defendant = m.group(1).strip()

    meta["plaintiff"] = plaintiff
    meta["defendant"] = defendant

    # === 案件类型/案由 ===
    m = re.search(r"\*\*案由\*\*[：:]\s*(.+?)$", text, re.MULTILINE)
    if m:
        meta["caseType"] = m.group(1).strip()
    if not meta["caseType"]:
        meta["caseType"] = _table_val(text, "案由") or _table_val(text, "案件类型")
    if not meta["caseType"]:
        m = re.search(r"案件类型[：:]\s*(.+?)(?:\n|$)", text)
        if m: meta["caseType"] = m.group(1).strip()

    # === 案号 ===
    m = re.search(r"[（(]?\d{4}[）)]?.+?民[初重终]?\d+号?", text)
    if m:
        meta["caseNumber"] = m.group(0).strip()

    # === 法院 ===
    m = re.search(r"\*\*受诉法院\*\*[：:]\s*(.+?)$", text, re.MULTILINE)
    if m:
        meta["court"] = m.group(1).strip()
    if not meta["court"]:
        meta["court"] = _table_val(text, "法院")
    if not meta["court"]:
        m = re.search(r"法院[：:]\s*(.+?)(?:\n|$)", text)
        if m: meta["court"] = m.group(1).strip()

    # === 原告九步法 ===
    meta["ourSide"] = plaintiff

    return meta


def parse_stages_from_stage_md(text: str) -> dict:
    """从 STAGE.md 解析阶段状态"""
    stages = {"currentStage": "", "items": []}

    # 解析阶段表格
    lines = text.split("\n")
    stage_rows = []
    in_table = False
    for line in lines:
        if re.match(r"\|\s*阶段ID", line):
            in_table = True
            continue
        if in_table and re.match(r"\|\s*[-─]+\s*\|", line):
            continue
        if in_table and re.match(r"\|\s*S\d", line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                stage_rows.append(parts)
        elif in_table and not re.match(r"\|\s*\S", line):
            in_table = False

    # 解析产物列
    stage_products = {}
    current_stage_id = None
    for line in lines:
        m = re.search(r"###\s+S\d[:：]\s+", line)
        if m:
            current_stage_id = re.search(r"S\d", line).group(0)
            stage_products[current_stage_id] = []
        elif current_stage_id and "产出路径" in line:
            m = re.search(r"`([^`]+)`", line)
            if m:
                stage_products[current_stage_id].append(m.group(1))

    # 映射状态
    current = ""
    first_in_progress = ""
    for row in stage_rows:
        if len(row) < 5:
            continue
        stage_id = row[1].strip()
        if not stage_id:
            continue
        name_raw = row[2].strip()
        status_raw = row[3].strip()
        start_raw = row[4].strip() if len(row) > 4 else ""
        end_raw = row[5].strip() if len(row) > 5 else ""

        # 解析状态
        status = "pending"
        for emoji, s in STATUS_MAP.items():
            if emoji in status_raw:
                status = s
                break

        # 解析时间
        start_time = None
        end_time = None
        if start_raw and start_raw != "-":
            try:
                dt = datetime.fromisoformat(start_raw)
                start_time = dt.isoformat()
            except Exception:
                pass
        if end_raw and end_raw != "-":
            try:
                dt = datetime.fromisoformat(end_raw)
                end_time = dt.isoformat()
            except Exception:
                pass

        # 提取阶段名称（去掉emoji）
        name = re.sub(r"[^一-龥a-zA-Z]", "", name_raw).strip()

        item = {
            "id": stage_id,
            "name": name,
            "emoji": STAGE_EMOJI.get(stage_id, "📋"),
            "status": status,
            "statusLabel": STATUS_LABEL_MAP.get(status, status),
            "startTime": start_time,
            "endTime": end_time,
            "products": stage_products.get(stage_id, []),
        }
        stages["items"].append(item)

        # 确定当前阶段
        if status == "in_progress" and not first_in_progress:
            first_in_progress = stage_id
        if status == "pending" and not current:
            pass  # 第一个 pending 可能是当前
        if status in ("completed", "in_progress", "blocked"):
            current = stage_id

    if first_in_progress:
        stages["currentStage"] = first_in_progress
    elif stages["items"]:
        # 找最后一个非 pending
        for s in reversed(stages["items"]):
            if s["status"] != "pending":
                stages["currentStage"] = s["id"]
                break
        if not stages["currentStage"]:
            stages["currentStage"] = stages["items"][0]["id"]

    return stages


def parse_changelog_from_log(text: str) -> list:
    """从 LOG.md 解析变更记录"""
    changelog = []
    current_date = None

    for line in text.split("\n"):
        # 日期行
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", line)
        if m:
            current_date = m.group(1)
            if not changelog or changelog[-1]["date"] != current_date:
                changelog.append({"date": current_date, "entries": []})
            continue

        # 时间条目
        m = re.match(r"^\[?(\d{2}:\d{2})\]?\s*[-*]\s*(.+)", line)
        if m and current_date:
            time_str = m.group(1)
            content = m.group(2).strip()

            # 提取操作和描述
            action = content
            detail = ""
            files = []

            # 提取文件引用
            file_patterns = re.findall(r"`([^`]+)`", content)
            files.extend(file_patterns)

            # 清理动作
            action = re.sub(r"`[^`]+`", "", action).strip()
            action = re.sub(r"[-*]\s*", "", action).strip()

            # 简化描述
            if "→" in content:
                parts = content.split("→")
                if len(parts) > 1:
                    detail = parts[-1].strip()
            elif ":" in content:
                parts = content.split(":", 1)
                if len(parts) > 1 and len(parts[0]) < 20:
                    detail = parts[1].strip()

            if changelog:
                changelog[-1]["entries"].append({
                    "time": time_str,
                    "action": action or "更新",
                    "detail": detail,
                    "filesChanged": files,
                })

    return changelog


def parse_keyinfo_from_case_brain(text: str) -> dict:
    """从 CLAUDE.md 解析关键信息（兼容 key:value、表格、嵌套三种格式）"""
    ki = {
        "parties": {"plaintiff": "", "defendant": ""},
        "amount": "",
        "court": "",
        "deadline": "",
        "disputes": [],
    }

    # 嵌套格式提取当事人
    plaintiff = _extract_name_from_nested(text, "委托人（我方）")
    if not plaintiff:
        plaintiff = _extract_name_from_nested(text, "委托人")
    defendant = _extract_name_from_nested(text, "对方当事人")
    if not defendant:
        defendant = _extract_name_from_nested(text, "被告一") or _extract_name_from_nested(text, "被告")

    # 表格格式兜底
    if not plaintiff:
        plaintiff = _table_val(text, "原告")
    if not defendant:
        defendant = (_table_val(text, "我方当事人") or
                     _table_val(text, "被告一（我方）") or
                     _table_val(text, "原告九步法当事人") or
                     _table_val(text, "被告一（原告九步法）") or
                     _table_val(text, "被告一") or
                     _table_val(text, "被告"))

    # key-value 兜底
    if not plaintiff:
        m = re.search(r"原告[：:]\s*(.+?)(?:\n|$)", text)
        if m: plaintiff = m.group(1).strip()
    if not defendant:
        m = re.search(r"被告[：:]\s*(.+?)(?:\n|$)", text)
        if m: defendant = m.group(1).strip()

    ki["parties"]["plaintiff"] = plaintiff
    ki["parties"]["defendant"] = defendant

    # 诉讼标的
    m = re.search(r"\*\*诉讼主张欠款\*\*\s*\|\s*\*?\*?([\d,，.]+)\*?\*?", text)
    if m:
        ki["amount"] = m.group(1).strip().replace(",", "") + "元"
    if not ki["amount"]:
        ki["amount"] = _table_val(text, "诉讼标的") or _table_val(text, "金额")
    if not ki["amount"]:
        m = re.search(r"诉讼标的[：:]\s*(.+?)(?:\n|$)", text)
        if m: ki["amount"] = m.group(1).strip()
    if not ki["amount"]:
        m = re.search(r"金额[：:]\s*([^\n，。]+)", text)
        if m: ki["amount"] = m.group(1).strip()

    # 法院
    m = re.search(r"\*\*受诉法院\*\*[：:]\s*(.+?)$", text, re.MULTILINE)
    if m:
        ki["court"] = m.group(1).strip()
    if not ki["court"]:
        ki["court"] = _table_val(text, "法院")
    if not ki["court"]:
        m = re.search(r"法院[：:]\s*(.+?)(?:\n|$)", text)
        if m: ki["court"] = m.group(1).strip()

    # 期限：下次开庭时间
    m = re.search(r"(\d{4}\.\d{1,2}\.\d{1,2})[^\n]*开庭", text)
    if m:
        ki["deadline"] = m.group(1).replace(".", "年", 1).replace(".", "月", 1) + "日"
    else:
        m = re.search(r"(?:提交|截止|期限|开庭)[^\d]*(\d{4}年\d{1,2}月\d{1,2}[日]?(?:前)?)", text)
        if m:
            ki["deadline"] = m.group(1).strip()

    # 争议焦点：提取"核心争议焦点"章节下的编号行（仅限纠纷相关描述）
    disputes = []
    in_dispute_section = False
    for line in text.split("\n"):
        s = line.strip()
        # 检测章节标题
        if "争议焦点" in s and ("###" in s or "⚔" in s):
            in_dispute_section = True
            continue
        if in_dispute_section and s.startswith("#"):
            break  # 进入下一章节则退出
        if in_dispute_section:
            m = re.match(r"^\d+[.．、]\s*(.+?)$", s)
            if m:
                raw = m.group(1).strip()
                # 剥离 ** 加粗标记
                raw = re.sub(r"\*{1,2}([^*]+?)\*{1,2}", r"\1", raw)
                # 跳过非争议项（不含纠纷关键词的行，如操作建议类）
                if any(kw in raw for kw in ("【", "材料分析", "立案", "搜索核实", "——", "---")):
                    continue
                disputes.append(raw)
    if not disputes:
        # 兜底：旧版兼容
        for dm in re.finditer(r"^\d+[.．、]\s*\*\*([^*\n]+)\*\*", text, re.MULTILINE):
            disputes.append(dm.group(1).strip())
    ki["disputes"] = disputes[:5]

    return ki


_INTERNAL_DIRS = {"_archive", ".git", ".codex", ".claude", ".vscode", "intermediate"}
_INTERNAL_FILES = {
    "CLAUDE.md", "LOG.md", "阶段追踪.md", "AGENTS.md", "dashboard-ops.json",
    "dashboard-ops.json.bak", ".gitignore", "案件仪表盘.html", "案件仪表盘-data.js",
}
_INTERNAL_EXTS = {"cfg", "bak", "log"}


def _get_legal_cat(parts: tuple) -> str:
    """从路径中的文件夹名推断法律归属（忽略 emoji 等符号，只匹配中文关键字）"""
    for part in parts[:-1]:  # 只看目录名，不看文件名
        if "原告" in part:
            return "plaintiff"
        if "被告" in part or "原告九步法" in part:
            return "defendant"
        if "法院" in part:
            return "court"
        if "分析" in part or "支持" in part or "案例" in part:
            return "analysis"
        if "证据" in part:
            return "evidence"
    # FINAL 目录
    if "FINAL" in parts or "final" in parts:
        return "final"
    # 根目录文件：通过文件名关键词推断（起诉状/证据清单/地址确认书→原告，答辩状→被告）
    fname = parts[-1] if parts else ""
    if any(k in fname for k in ("起诉状", "起诉", "证据清单", "证据目录", "地址确认", "原告")):
        return "plaintiff"
    if any(k in fname for k in ("答辩", "被告")):
        return "defendant"
    return ""


def parse_memo_md(case_root: Path) -> dict:
    """读取案件备忘录.md，按章节解析"""
    memo_path = case_root / "案件备忘录.md"
    if not memo_path.exists():
        return {"sections": [], "raw": ""}

    content = memo_path.read_text(encoding="utf-8")
    sections = []
    current = None

    for line in content.split("\n"):
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = {"title": line[3:].strip(), "content": ""}
        elif current:
            current["content"] += line + "\n"

    if current:
        sections.append(current)

    return {"sections": sections, "raw": content}


def scan_files(root: Path) -> dict:
    """扫描文件目录，生成文件清单"""
    categories = [
        {"id": "raw", "label": "原始材料", "icon": "📎", "items": []},
        {"id": "markdown", "label": "Markdown转换件", "icon": "📝", "items": []},
        {"id": "intermediate", "label": "中间产物", "icon": "🔧", "items": []},
        {"id": "final", "label": "最终交付", "icon": "✅", "items": []},
    ]

    # 分类规则
    raw_extensions = {"pdf", "docx", "doc", "jpg", "jpeg", "png", "mp4", "mp3", "xlsx", "xls"}
    intermediate_dirs = {"intermediate", "01-问题梳理", "02-检索", "03-撰写", "04-自检", "05-可视化", "ima-output", "ima-input"}
    final_dirs = {"final", "FINAL"}

    for path in root.rglob("*"):
        if path.is_file() and not path.name.startswith("."):
            rel = path.relative_to(root)
            parts = rel.parts
            fname = path.name
            ext = get_file_ext(fname)

            # 排除系统内部目录（.git/.codex/.claude/.vscode，但保留 intermediate/_archive）
            if any(d in {".git", ".codex", ".claude", ".vscode"} for d in parts):
                continue
            # 排除系统内部文件
            if fname in _INTERNAL_FILES or ext in _INTERNAL_EXTS:
                continue
            # 排除 _archive 内非 markdown 内容（data.js 等）
            if "_archive" in parts and "markdown" not in parts:
                continue

            legal_cat = _get_legal_cat(parts)

            # 判断是否为用户有用文件（有法律归属，或在 FINAL 目录）
            is_user_file = bool(legal_cat) or any(p in final_dirs for p in parts)

            # 获取文件信息
            try:
                stat = path.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                size = 0
                mtime = None

            item = {
                "name": fname,
                "path": str(rel).replace("\\", "/"),
                "type": ext,
                "sizeBytes": size,
                "lastModified": mtime,
                "legalCat": legal_cat,
                "userVisible": is_user_file,
            }

            # 判断技术分类
            if "_archive" in parts and "markdown" in parts:
                categories[1]["items"].append(item)
            elif "intermediate" in parts or any(d in parts for d in intermediate_dirs):
                for part in parts:
                    m = re.match(r"(\d{2})-", part)
                    if m:
                        item["stage"] = f"S{m.group(1)[0]}"
                        break
                if any(p in final_dirs for p in parts):
                    categories[3]["items"].append(item)
                else:
                    categories[2]["items"].append(item)
            elif ext in raw_extensions or "raw" in parts:
                categories[0]["items"].append(item)
            elif ext == "md":
                categories[1]["items"].append(item)
            else:
                categories[0]["items"].append(item)

    # 计算汇总：totalFiles 只算对用户有用的文件（排除 markdown 转换件和内部文件）
    user_files = [i for c in categories for i in c["items"] if i.get("userVisible")]
    summary = {
        "rawCount": len(categories[0]["items"]),
        "markdownCount": len(categories[1]["items"]),
        "intermediateCount": len(categories[2]["items"]),
        "finalCount": len(categories[3]["items"]),
        "totalFiles": len(user_files),
        "totalSizeBytes": sum(i["sizeBytes"] for i in user_files),
    }

    return {"categories": categories, "summary": summary}


OPS_ACTION_LABELS = {
    "新增备忘录": "📝 新增备忘录",
    "编辑备忘录": "✏️ 编辑备忘录",
    "删除备忘录": "🗑️ 删除备忘录",
    "新增缺口": "📌 新增缺口",
    "完成缺口": "✅ 完成缺口",
    "回退缺口": "↩️ 回退缺口",
    "确认终版": "✓ 确认终版",
    "取消确认": "↩️ 取消确认",
    "移动文件": "📁 移动文件",
}


def sync_dashboard_ops(case_root: Path) -> None:
    """读取 dashboard-ops.json，将操作记录追加到 LOG.md"""
    ops_path = case_root / "dashboard-ops.json"
    if not ops_path.exists():
        return

    try:
        with open(ops_path, encoding="utf-8") as f:
            ops_data = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取 dashboard-ops.json 失败: {e}")
        return

    operations = ops_data.get("operations", [])
    if not operations:
        print("✅ dashboard-ops.json 无新操作，跳过")
        return

    # 读取 LOG.md
    log_path = case_root / "LOG.md"
    if log_path.exists():
        log_content = log_path.read_text(encoding="utf-8")
    else:
        log_content = ""
        # 如果没有 LOG.md，建立基本结构
        today = datetime.now().strftime("%Y-%m-%d")
        log_content = f"# 案件变更日志\n\n## {today}\n\n"

    # 找出今天是否已有条目
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_section_found = today_str in log_content

    # 解析现有 LOG.md 的最后日期
    last_date = None
    date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})", re.MULTILINE)
    for m in date_pattern.finditer(log_content):
        last_date = m.group(1)

    # 生成新 LOG 条目
    new_entries = []
    for op in operations:
        ts = op.get("ts", "")
        time_str = op.get("time", "")
        action = op.get("action", "")
        detail = op.get("detail", "")
        label = OPS_ACTION_LABELS.get(action, "● " + action)
        entry = f"[{time_str}] - {label}" + (f" → {detail}" if detail else "")
        new_entries.append(entry)

    if not new_entries:
        return

    # 如果有今天的 section，在其下追加；否则新建
    if today_section_found:
        # 在今天的日期行之后追加
        lines = log_content.split("\n")
        output_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            output_lines.append(line)
            if line.strip() == today_str:
                # 跳过日期行后的分隔线或空行
                i += 1
                while i < len(lines) and (lines[i].strip() == "" or re.match(r"^[-─*]", lines[i].strip())):
                    output_lines.append(lines[i])
                    i += 1
                # 追加新条目
                for entry in new_entries:
                    output_lines.append(f"  - {entry}")
                output_lines.append("")
            i += 1
        log_content = "\n".join(output_lines)
    else:
        # 新建今天 section
        log_content = log_content.rstrip()
        if log_content:
            log_content += "\n\n"
        log_content += f"## {today_str}\n\n"
        for entry in new_entries:
            log_content += f"  - {entry}\n"
        log_content += "\n"

    log_path.write_text(log_content, encoding="utf-8")
    print(f"✅ 已同步 {len(new_entries)} 条操作到 LOG.md")

    # 同时更新 CLAUDE.md 的备忘录和缺口部分
    _sync_memos_and_gaps_to_case_brain(case_root, ops_data)


def _sync_memos_and_gaps_to_case_brain(case_root: Path, ops_data: dict) -> None:
    """将仪表盘的备忘录和缺口数据写入 CLAUDE.md"""
    case_brain_path = case_root / "CLAUDE.md"
    if not case_brain_path.exists():
        return

    memos = ops_data.get("memos", [])
    gaps = ops_data.get("gaps", [])
    done_gaps = ops_data.get("doneGaps", [])

    if not memos and not gaps and not done_gaps:
        return

    content = case_brain_path.read_text(encoding="utf-8")

    # 更新备忘录 section
    if memos:
        memo_section = "\n## 案件备忘录\n\n"
        for m in memos:
            memo_section += f"- [{m.get('date', '')}] {m.get('text', '')}\n"
        memo_section += "\n"

        # 如果已有备忘录 section，替换；否则追加
        if "## 案件备忘录" in content:
            # 找到现有 section 并替换
            pattern = re.compile(r"## 案件备忘录\n\n.*?(?=\n## |\Z)", re.DOTALL)
            content = pattern.sub(memo_section.strip() + "\n\n", content)
        else:
            content = content.rstrip() + "\n" + memo_section

    # 更新缺口 section（已完成缺口）
    if done_gaps:
        gap_section = "\n## 已完成缺口\n\n"
        for d in done_gaps:
            gap_info = d.get("gap", {})
            note = d.get("note", "")
            done_at = d.get("doneAt", "")
            gap_text = gap_info.get("text", d.get("id", "")) if isinstance(gap_info, dict) else str(gap_info)
            gap_section += f"- [{done_at}] {gap_text}"
            if note:
                gap_section += f" → {note}"
            gap_section += "\n"
        gap_section += "\n"

        if "## 已完成缺口" in content:
            pattern = re.compile(r"## 已完成缺口\n\n.*?(?=\n## |\Z)", re.DOTALL)
            content = pattern.sub(gap_section.strip() + "\n\n", content)
        else:
            content = content.rstrip() + "\n" + gap_section

    case_brain_path.write_text(content, encoding="utf-8")
    print(f"✅ 已同步备忘录和缺口到 CLAUDE.md")

    # 备份 dashboard-ops.json 为已同步版本
    bak_path = case_root / "dashboard-ops.json.bak"
    ops_path = case_root / "dashboard-ops.json"
    bak_path.write_bytes(ops_path.read_bytes())
    # 清空原文件（下次刷新不会再重复同步）
    ops_path.write_text(json.dumps({"synced": True, "syncedAt": datetime.now().isoformat()}, ensure_ascii=False), encoding="utf-8")


def extract_tasks_from_case_brain(text: str) -> list:
    """从 CLAUDE.md 提取待办事项"""
    tasks = []
    task_pattern = re.compile(r"^\s*[-*□]\s*\[([ xX])\]\s*(.+)", re.MULTILINE)
    for m in task_pattern.finditer(text):
        done = m.group(1).lower() == "x"
        label = m.group(2).strip()
        tasks.append({
            "status": "done" if done else "in_progress",
            "label": label,
        })
    return tasks


def parse_dispute_matrix(case_root: Path) -> dict:
    """从 S6-争点矩阵.md 解析争议对撞矩阵"""
    s6_path = case_root / "intermediate" / "原告九步法" / "S6-争点矩阵" / "S6-争点矩阵.md"
    if not s6_path.exists():
        s6_path = case_root / "intermediate" / "原告九步法" / "S6-争点矩阵.md"
        return {"disputes": []}

    try:
        content = s6_path.read_text(encoding="utf-8")
    except Exception:
        return {"disputes": []}

    disputes = []

    # 解析优先级映射（从 6.2 表格或 P0/P1/P2 标题区）
    priority_map = {}  # {争点名: P0/P1/P2}
    lines = content.split('\n')
    current_priority = "P1"
    for i, line in enumerate(lines):
        # P0/P1/P2 标题区域
        m = re.match(r'^###\s*P(\d)', line)
        if m:
            current_priority = f"P{m.group(1)}"
        # 表格行含争点名和优先级
        if line.strip().startswith('|') and 'Z' in line:
            cells = [c.strip() for c in line.split('|')]
            valid = [c for c in cells if c and not c.startswith(':') and not re.match(r'^[-─]+$', c)]
            if len(valid) >= 2 and re.match(r'Z\d+', valid[0]):
                zid = valid[0]
                zname = valid[1] if len(valid) > 1 else ""
                priority_map[zname] = current_priority

    # 方法1: 解析 6.1 争点对撞表
    in_z_table = False
    for line in lines:
        if '6.1' in line and '争点对撞' in line:
            in_z_table = True
            continue
        if in_z_table and line.strip().startswith('|') and '---' not in line:
            cells = [c.strip() for c in line.split('|')]
            valid = [c for c in cells if c and not c.startswith(':') and not re.match(r'^[-─]+$', c)]
            # 去 ** 加粗
            clean_valid = [re.sub(r'\*+', '', c).strip() for c in valid]
            if len(clean_valid) >= 5 and re.match(r'Z\d+', clean_valid[0]):
                zid = clean_valid[0]
                zname = clean_valid[1] if len(clean_valid) > 1 else ""
                z_plaintiff = clean_valid[2] if len(clean_valid) > 2 else ""
                z_defendant = clean_valid[3] if len(clean_valid) > 3 else ""
                z_strength = clean_valid[4] if len(clean_valid) > 4 else "🟡 中对撞"
                priority = priority_map.get(zname, "P1")
                disputes.append({
                    "id": zid,
                    "name": zname,
                    "level": priority,
                    "plaintiff": z_plaintiff[:80] if z_plaintiff else "—",
                    "defendant": z_defendant[:80] if z_defendant else "—",
                    "risk": z_strength,
                    "focus": "",
                })
        elif in_z_table and not line.strip().startswith('|') and line.strip() and not line.startswith('#'):
            in_z_table = False

    # 方法2: 如果表格解析为空，尝试 ### Z1：格式
    if not disputes:
        for m in re.finditer(r'^###\s*(Z\d+)[：:]\s*(.+?)$', content, re.MULTILINE):
            zid = m.group(1)
            zname = m.group(2).strip()
            priority = priority_map.get(zname, "P1")
            disputes.append({
                "id": zid,
                "name": zname,
                "level": priority,
                "plaintiff": "—",
                "defendant": "—",
                "risk": "🟡中",
                "focus": "",
            })

    return {"disputes": disputes}


def parse_nine_steps_from_index(case_root: Path) -> dict:
    """从 intermediate/_index.json 读取九步法双视图进度（v6.0）"""
    index_path = case_root / "intermediate" / "_index.json"
    if not index_path.exists():
        return {"steps": [], "currentStep": "S1", "summary": {}}
    try:
        with open(index_path, encoding="utf-8") as f:
            idx = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取 _index.json 失败: {e}")
        return {"steps": [], "currentStep": "S1", "summary": {}}
    if idx.get("schema") != "九步法双视图":
        return {"steps": [], "currentStep": "S1", "summary": {}}

    # 向后兼容旧版 _index.json（"我方"/"对方" → "原告九步法"/"被告九步法"）
    w_map = idx.get("原告九步法") or idx.get("我方", {})
    t_map = idx.get("被告九步法") or idx.get("对方", {})

    steps = []
    current = "S1"
    for sn in [f"S{i}" for i in range(1, 10)]:
        w = w_map.get(f"{sn}-", {})
        t = t_map.get(f"{sn}-", {})
        if not w:
            for k, v in w_map.items():
                if k.startswith(sn + "-"):
                    w = v; break
        if not t:
            for k, v in t_map.items():
                if k.startswith(sn + "-"):
                    t = v; break
        ws = w.get("status", "pending")
        ts = t.get("status", "pending")
        if ws not in ("pending",) or ts not in ("pending",):
            current = sn
        if ws in ("in_progress", "review_pending") or ts in ("in_progress", "review_pending"):
            current = sn
        steps.append({
            "step": sn,
            "emoji": STAGE_EMOJI.get(sn, "📋"),
            "name": f"{sn}",
            "原告九步法": ws,
            "被告九步法": ts if ts != "shared_with_原告九步法" else ws,
            "wStarted": w.get("started_at"),
            "wCompleted": w.get("completed_at"),
            "wProduct": w.get("产物"),
            "wPkulaw": w.get("北大法宝复验"),
            "tStarted": t.get("started_at"),
            "tCompleted": t.get("completed_at"),
            "tProduct": t.get("产物"),
        })

    summary = {
        "wCompleted": sum(1 for s in steps if s["原告九步法"] == "completed"),
        "tCompleted": sum(1 for s in steps if s["被告九步法"] == "completed"),
        "wReview": sum(1 for s in steps if s["原告九步法"] == "review_pending"),
        "tReview": sum(1 for s in steps if s["被告九步法"] == "review_pending"),
        "wInProgress": sum(1 for s in steps if s["原告九步法"] == "in_progress"),
        "tInProgress": sum(1 for s in steps if s["被告九步法"] == "in_progress"),
    }

    return {"steps": steps, "currentStep": current, "summary": summary}


def parse_s0_data(case_root: Path) -> dict:
    """从 intermediate/S0-证据卡片库.json 解析证据卡片数据"""
    s0_json_path = case_root / "intermediate" / "S0-证据卡片库.json"
    if not s0_json_path.exists():
        return {"status": "pending", "total_count": 0, "cards": [],
                "purpose_distribution": {}, "meta": {}}

    try:
        with open(s0_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取 S0 JSON 失败: {e}")
        return {"status": "parse_error", "total_count": 0, "cards": [], "meta": {}}

    # 检测状态
    cards = data.get("cards", data.get("snippets", []))
    meta = data.get("meta", {})
    purpose_dist = data.get("purpose_distribution", {})

    # 检查是否有未确认卡片
    unreviewed = sum(1 for s in cards if not s.get("confirmed", True))
    if unreviewed == 0 and cards:
        status = "completed"
    elif cards:
        status = "review_pending"
    else:
        status = "pending"

    return {
        "status": status,
        "total_count": meta.get("total_count", len(cards)),
        "high_confidence": meta.get("high_confidence", 0),
        "medium_confidence": meta.get("medium_confidence", 0),
        "low_confidence": meta.get("low_confidence", 0),
        "need_review": meta.get("need_review", 0),
        "cards": cards,
        "purpose_distribution": purpose_dist,
        "meta": meta,
    }


def _truncate_text(text: str, max_chars: int = 60) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars] + "…" if len(text) > max_chars else text


def generate_timeline_data(s0_data: dict, keyinfo: dict) -> list:
    """从 S0 证据卡片生成时间线数据"""
    cards = s0_data.get("cards", [])
    events = []
    for sp in cards:
        time_val = sp.get("time", "").strip()
        if time_val and time_val != "—":
            events.append({
                "date": time_val,
                "label": _truncate_text(sp.get("text", ""), 60),
                "source": sp.get("source", ""),
                "id": sp.get("id", ""),
                "parties": sp.get("parties", ""),
                "amount": sp.get("amount", ""),
                "purpose": sp.get("purpose_label", ""),
            })
    events.sort(key=lambda e: e["date"])
    return events


def generate_dispute_evidence_data(s0_data: dict, dispute_matrix: dict) -> list:
    """将 S0 证据卡片映射到 S6 争议点"""
    disputes = dispute_matrix.get("disputes", [])
    cards = s0_data.get("cards", [])
    if not disputes:
        return []

    result = []
    for d in disputes:
        dispute_name = d.get("name", "")
        keywords = re.sub(r"[^一-龥a-zA-Z0-9]", " ", dispute_name).split()
        matched = []
        for sp in cards:
            text = (sp.get("text", "") + " " + sp.get("purpose_label", "") + " " + sp.get("parties", ""))
            match_count = sum(1 for kw in keywords if len(kw) > 1 and kw in text)
            if match_count >= 1:
                matched.append({
                    "id": sp.get("id", ""),
                    "text": _truncate_text(sp.get("text", ""), 50),
                    "source": sp.get("source", ""),
                    "confidence": sp.get("confidence", ""),
                })
        result.append({
            "name": dispute_name,
            "level": d.get("level", "P1"),
            "risk": d.get("risk", "🟡中"),
            "evidence_count": len(matched),
            "evidence": matched[:10],
        })
    return result


def _short_company(name: str) -> str:
    """去除公司后缀"""
    for kw in ["有限公司", "责任公司", "集团", "股份"]:
        name = name.replace(kw, "")
    return name.strip()


# 个人称呼后缀：工/总（排除"工程""工厂""总监"等复合词首字）
_TITLE_RE = re.compile(r'(工|总)(?!程|程师|厂|业|地|期|作|具|艺|会|人|资|种|序|段|监)')


def generate_party_relation_data(keyinfo: dict, s0_data: dict) -> dict:
    """从 S0 证据卡片提取当事人关系图
    - 公司实体：原告/被告公司节点（蓝色/红色）
    - 个人实体：从 parties 字段提取的自然人（如 赵工、李工），按关联公司归类归属方
    - 排除纯公司名（不含个人后缀的）、方向描述词、历史注释
    """
    cards = s0_data.get("cards", [])
    plaintiff = keyinfo.get("parties", {}).get("plaintiff", "")
    defendant = keyinfo.get("parties", {}).get("defendant", "")

    nodes = []
    edges = []
    entity_seen = set()   # 已添加的实体名（用于去重）
    person_seen = set()   # 已添加的个人标识（用于去重，如 "赵工"）

    # ---- 1. 公司当事人节点 ----
    if plaintiff:
        short_p = _short_company(plaintiff)
        nodes.append({"id": "P1", "name": short_p, "type": "plaintiff"})
        entity_seen.add(plaintiff)
        entity_seen.add(short_p)
    if defendant:
        short_d = _short_company(defendant)
        nodes.append({"id": "D1", "name": short_d, "type": "defendant"})
        entity_seen.add(defendant)
        entity_seen.add(short_d)

    # 公司简称关键词（用于判断个人归属）
    p_kw = plaintiff[:4] if plaintiff else ""
    d_kw = defendant[:4] if defendant else ""

    # ---- 2. 从证据卡片提取自然人 ----
    for sp in cards:
        parties_str = sp.get("parties", "").strip()
        if not parties_str or parties_str == "—":
            continue

        # 按方向箭头拆分为左右两侧
        for seg in re.split(r"[→↔]", parties_str):
            seg = seg.strip()
            if not seg:
                continue
            # 跳过纯公司、纯方向描述
            if seg in ("双方", "原告", "被告", "我方", "对方"):
                continue
            if "原名" in seg:
                continue

            # 提取个人名：找 X工/X总 后缀，取其前1个汉字作为姓氏
            for m in _TITLE_RE.finditer(seg):
                suffix_pos = m.start()
                if suffix_pos < 1:
                    continue
                person_name = seg[suffix_pos - 1:suffix_pos + 1]  # "赵工"
                # 校验：须以汉字开头（排除"的工""人工"等非人名模式）
                if not re.match(r'[一-鿿]', person_name[0]):
                    continue
                if person_name in person_seen:
                    continue

                # 判断归属方：看这个人名出现在哪个公司一侧
                if p_kw and any(w in seg for w in (p_kw, "挚盛", "东方雨虹")):
                    side = "plaintiff"
                elif d_kw and any(w in seg for w in (d_kw, "浙南")):
                    side = "defendant"
                else:
                    # 无法判定时按通用关键词
                    if "原告" in parties_str or "原告九步法" in parties_str:
                        side = "plaintiff"
                    elif "被告" in parties_str:
                        side = "defendant"
                    else:
                        side = "unknown"

                person_seen.add(person_name)
                p_id = f"R{len(nodes) + 1}"
                node_type = f"{side}_person" if side != "unknown" else "other"
                nodes.append({"id": p_id, "name": person_name, "type": node_type})

                # 连接到所属公司
                target = "D1" if side == "defendant" else "P1"
                edges.append({"from": p_id, "to": target, "type": "related", "label": "所属"})

    # ---- 3. 原告-被告 纠纷连线 ----
    if plaintiff and defendant:
        edges.insert(0, {"from": "P1", "to": "D1", "type": "dispute", "label": "纠纷"})

    return {"nodes": nodes, "edges": edges}


def generate_money_flow_data(s0_data: dict) -> list:
    """从 S0 提取金额流向"""
    cards = s0_data.get("cards", [])
    flows = []
    for sp in cards:
        amount = sp.get("amount", "").strip()
        time_val = sp.get("time", "").strip()
        if amount and amount != "—":
            amount_num = None
            m = re.search(r"([\d,，.]+)", amount)
            if m:
                try:
                    amount_num = float(m.group(1).replace(",", "").replace("，", ""))
                except ValueError:
                    pass
            flows.append({
                "id": sp.get("id", ""),
                "parties": sp.get("parties", "—"),
                "amount": amount,
                "amount_num": amount_num,
                "date": time_val if time_val != "—" else "",
                "purpose": sp.get("purpose_label", ""),
                "text": _truncate_text(sp.get("text", ""), 40),
            })
    return flows


def generate_law_evidence_matrix(case_root: Path, s0_data: dict) -> dict:
    """从 S4 要件拆解和 S0 片段生成法条-证据对照矩阵"""
    s4_path = case_root / "intermediate" / "原告九步法" / "S4-要件拆解" / "S4-要件拆解.md"
    if not s4_path.exists():
        s4_path = case_root / "intermediate" / "原告九步法" / "S4-要件拆解.md"
    elements = []
    if s4_path.exists():
        try:
            content = s4_path.read_text(encoding="utf-8")
            seen_ids = set()
            for line in content.split("\n"):
                stripped = line.strip()
                if not stripped.startswith("|") or "---" in stripped:
                    continue
                # 匹配 | **E1** 合同关系 | ... |
                m = re.match(r'\|\s*\*{0,2}(E\d+)\*{0,2}\s+(.+?)\s*\|', stripped)
                if not m:
                    continue
                elem_id = m.group(1)
                rest_of_line = m.group(2)
                if elem_id in seen_ids:
                    continue
                seen_ids.add(elem_id)
                cells = [c.strip() for c in line.split("|")]
                valid = [c for c in cells if c and not c.startswith(":")]
                elements.append({
                    "id": elem_id,
                    "name": _truncate_text(valid[1] if len(valid) > 1 else rest_of_line, 30),
                    "standard": valid[2] if len(valid) > 2 else "",
                    "burden": valid[3] if len(valid) > 3 else "",
                })
        except Exception:
            pass

    cards = s0_data.get("cards", [])
    element_evidence = []
    for el in elements:
        matched = []
        el_name = el.get("name", "")
        if el_name:
            for sp in cards:
                text = sp.get("text", "") + sp.get("purpose_label", "")
                if any(kw in text for kw in el_name.split() if len(kw) > 1):
                    matched.append({
                        "id": sp.get("id", ""),
                        "text": _truncate_text(sp.get("text", ""), 40),
                    })
        element_evidence.append({
            "id": el["id"],
            "name": el["name"] or f"要件{el['id']}",
            "evidence_count": len(matched),
            "has_evidence": len(matched) > 0,
            "evidence": matched[:5],
        })

    return {
        "elements": element_evidence,
        "total_elements": len(elements),
        "covered": sum(1 for e in element_evidence if e["has_evidence"]),
    }


def _extract_step_summary(file_path: Path, max_chars: int = 200) -> str:
    """从步骤 md 文件中提取第一个有意义的段落作为摘要"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    current: list[str] = []
    paragraphs: list[str] = []
    for line in content.split("\n"):
        s = line.strip()
        if s.startswith("#") or s.startswith("---") or s.startswith("==="):
            if current:
                paragraphs.append(" ".join(current))
                current = []
        elif s:
            current.append(s)
        else:
            if current:
                paragraphs.append(" ".join(current))
                current = []
    if current:
        paragraphs.append(" ".join(current))
    for p in paragraphs:
        clean = re.sub(r"[*|`\-=>#\d\s年月日:/.\[\]()（）]", "", p)
        if len(clean) > 8:
            return p[:max_chars] + ("…" if len(p) > max_chars else "")
    return ""


def scan_step_summaries(case_root: Path) -> dict:
    """
    扫描 intermediate/原告九步法/ 和 被告九步法/ 目录，提取各步骤摘要和文件路径。
    S6 争点矩阵归入 shared，不重复出现在 plaintiff。
    返回: { "plaintiff": {S1:{summary,filePath},...}, "defendant":{...}, "shared":{S6:{...}} }
    """
    result: dict = {"plaintiff": {}, "defendant": {}, "shared": {}}
    configs = [
        ("plaintiff", "原告九步法", ["S1","S2","S3","S4","S5","S6","S7","S8","S9"]),
        ("defendant", "被告九步法", ["S1","S2","S3","S4","S5","S7","S8","S9"]),
    ]
    for role_key, dir_name, steps in configs:
        dir_path = case_root / "intermediate" / dir_name
        if not dir_path.exists():
            continue
        for step in steps:
            matches = sorted(dir_path.glob(f"{step}-*.md"))
            if not matches:
                continue
            fp = matches[0]
            summary = _extract_step_summary(fp)
            file_uri = fp.resolve().as_uri()
            entry = {"summary": summary, "filePath": file_uri}
            if step == "S6" and role_key == "plaintiff":
                result["shared"]["S6"] = entry
            else:
                result[role_key][step] = entry
    return result


def main():
    # 确定案件根目录
    if len(sys.argv) > 1:
        case_root = Path(sys.argv[1])
    else:
        case_root = Path.cwd()

    print(f"🔍 扫描案件目录: {case_root}")

    # 读取核心文件
    case_brain_md = ""
    stage_md = ""
    log_md = ""

    case_brain_path = case_root / "CLAUDE.md"
    if case_brain_path.exists():
        case_brain_md = case_brain_path.read_text(encoding="utf-8")
        print(f"✅ 读取 CLAUDE.md ({len(case_brain_md)} 字符)")

    stage_path = case_root / "阶段追踪.md"
    if stage_path.exists():
        stage_md = stage_path.read_text(encoding="utf-8")
        print(f"✅ 读取 STAGE.md ({len(stage_md)} 字符)")

    log_path = case_root / "LOG.md"
    if log_path.exists():
        log_md = log_path.read_text(encoding="utf-8")
        print(f"✅ 读取 LOG.md ({len(log_md)} 字符)")

    # 同步仪表盘操作记录到 LOG.md
    sync_dashboard_ops(case_root)

    # 读取 AI 争议焦点评估（由 Claude Code 分析案卷后写入）
    assessments = []
    assessment_path = case_root / "_archive" / "dispute-assessments.json"
    if assessment_path.exists():
        try:
            with open(assessment_path, encoding="utf-8") as f:
                adata = json.load(f)
                assessments = adata.get("assessments", [])
            print(f"✅ 读取争议焦点评估 ({len(assessments)} 项)")
        except Exception as e:
            print(f"⚠️  读取评估文件失败: {e}")

    # 解析数据
    meta = parse_meta_from_case_brain(case_brain_md)
    meta["caseName"] = case_root.name  # 始终使用文件夹名作为案件名称（非当事人全名）

    stages = parse_stages_from_stage_md(stage_md)
    keyinfo = parse_keyinfo_from_case_brain(case_brain_md)
    changelog = parse_changelog_from_log(log_md)
    files = scan_files(case_root)
    tasks = extract_tasks_from_case_brain(case_brain_md)
    nine_steps = parse_nine_steps_from_index(case_root)
    dispute_matrix = parse_dispute_matrix(case_root)
    step_summaries = scan_step_summaries(case_root)

    # 解析 S0 证据卡片数据
    s0_data = parse_s0_data(case_root)
    if s0_data.get("total_count", 0) > 0:
        print(f"✅ 读取 S0 证据卡片 ({s0_data['total_count']} 条)")

    # 生成图表数据
    timeline_data = generate_timeline_data(s0_data, keyinfo)
    dispute_evidence = generate_dispute_evidence_data(s0_data, dispute_matrix)
    party_relations = generate_party_relation_data(keyinfo, s0_data)
    money_flow = generate_money_flow_data(s0_data)
    law_matrix = generate_law_evidence_matrix(case_root, s0_data)
    if timeline_data:
        print(f"✅ 生成时间线 ({len(timeline_data)} 个事件)")
    if dispute_evidence:
        print(f"✅ 生成争议点-证据映射 ({len(dispute_evidence)} 个争点)")
    if party_relations.get("nodes"):
        print(f"✅ 生成当事人关系 ({len(party_relations['nodes'])} 个节点)")
    if money_flow:
        print(f"✅ 生成金额流向 ({len(money_flow)} 笔)")
    if law_matrix.get("elements"):
        print(f"✅ 生成法条-证据矩阵 ({len(law_matrix['elements'])} 个要件)")

    # 组装数据
    data = {
        "meta": meta,
        "stages": stages,
        "nineSteps": nine_steps,
        "disputeMatrix": dispute_matrix,
        "keyInfo": keyinfo,
        "files": files,
        "changelog": changelog,
        "tasks": tasks,
        "disputeAssessments": assessments,
        "stepSummaries": step_summaries,
        "s0Data": s0_data,
        "timelineData": timeline_data,
        "disputeEvidence": dispute_evidence,
        "partyRelations": party_relations,
        "moneyFlow": money_flow,
        "lawMatrix": law_matrix,
        "memo": parse_memo_md(case_root),
    }

    # 生成 JS 文件（放入 _archive/ 保持根目录清洁）
    archive_dir = case_root / "_archive"
    archive_dir.mkdir(exist_ok=True)
    output_path = archive_dir / "CaseDashboard-data.js"
    js_content = f"// 案件仪表盘数据\n// 生成时间: {datetime.now().isoformat()}\n// 案件: {meta['caseName']}\n\nwindow.CASE_DASHBOARD_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};"

    output_path.write_text(js_content, encoding="utf-8")
    print(f"✅ 生成 {output_path.name} ({len(js_content)} 字符)")
    print(f"📊 统计: {files['summary']['totalFiles']} 个文件, "
          f"{len(stages['items'])} 个阶段, "
          f"{len(nine_steps.get('steps', []))} 步九步法, "
          f"{len(changelog)} 天变更记录")


if __name__ == "__main__":
    main()
