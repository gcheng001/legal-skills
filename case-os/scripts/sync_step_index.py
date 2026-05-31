#!/usr/bin/env python3
"""
九步法双视图 — 目录初始化 + 镜像生成 + _index.json 同步 + 总览生成

功能:
  1. init   — 初始化案件 intermediate 目录（原告九步法/被告九步法 S1-S9 扁平文件 + _index.json）
  2. mirror — 从原告模板生成被告镜像文件（首次建案时调用）
  3. sync   — 扫描已有文件，回写 _index.json 状态 + 生成九步法总览.md
  4. all    — init + mirror + sync（默认）

用法:
    python3 sync_step_index.py [案件文件夹路径] [--action init|mirror|sync|all]
    python3 sync_step_index.py [案件文件夹路径] --action init --force

输出:
    intermediate/_index.json          (18 格进度索引)
    intermediate/原告九步法/S1-*.md   (9 个扁平文件)
    intermediate/被告九步法/S1-*.md   (8 个扁平文件，S6 共用)
    intermediate/原告九步法/九步法总览.md (统一审阅文件，自动生成)
"""

import os
import sys
import json
import re
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# ===== 常量 =====
SKILL_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates" / "intermediate"

# 九步法步骤定义
S0_STEP = {"id": "S0", "dir": "S0-证据卡片库", "file": "S0-证据卡片库.md",
           "name": "证据卡片库", "emoji": "🔍",
           "原告九步法_desc": "从原始材料中提取结构化的证据卡片",
           "被告九步法_desc": "预判被告可能使用的证据卡片"}

STEPS = [
    {"id": "S1", "dir": "S1-固定权利请求", "file": "S1-固定权利请求.md",
     "name": "固定权利请求", "emoji": "📋",
     "原告九步法_desc": "明确原告九步法诉讼请求/仲裁请求",
     "被告九步法_desc": "预判被告九步法诉讼请求/答辩请求"},
    {"id": "S2", "dir": "S2-请求权基础", "file": "S2-请求权基础.md",
     "name": "请求权基础", "emoji": "📜",
     "原告九步法_desc": "检索原告九步法请求权基础规范",
     "被告九步法_desc": "预判被告九步法请求权基础"},
    {"id": "S3", "dir": "S3-抗辩规范", "file": "S3-抗辩规范.md",
     "name": "抗辩规范", "emoji": "🛡",
     "原告九步法_desc": "检索抗辩规范（权利消灭/妨碍/阻止）",
     "被告九步法_desc": "预判被告九步法可能抗辩"},
    {"id": "S4", "dir": "S4-要件拆解", "file": "S4-要件拆解.md",
     "name": "要件拆解", "emoji": "🔬",
     "原告九步法_desc": "拆解请求权构成要件，逐一检索证据",
     "被告九步法_desc": "预判被告九步法要件拆解"},
    {"id": "S5", "dir": "S5-主张检索", "file": "S5-主张检索.md",
     "name": "主张检索", "emoji": "🔍",
     "原告九步法_desc": "检索支持各要件的主张和判例",
     "被告九步法_desc": "预判被告九步法主张检索"},
    {"id": "S6", "dir": "S6-争点矩阵", "file": "S6-争点矩阵.md",
     "name": "争点矩阵", "emoji": "⚖",
     "原告九步法_desc": "双方争点对撞，确定主次战场",
     "被告九步法_desc": "shared_with_原告九步法"},
    {"id": "S7", "dir": "S7-举证责任", "file": "S7-举证责任.md",
     "name": "举证责任", "emoji": "📊",
     "原告九步法_desc": "分配各要件举证责任，标红证据缺口",
     "被告九步法_desc": "预判被告九步法举证责任"},
    {"id": "S8", "dir": "S8-事实认定", "file": "S8-事实认定.md",
     "name": "事实认定", "emoji": "🧩",
     "原告九步法_desc": "逐要件认定事实，标记争议/无争议",
     "被告九步法_desc": "预判被告九步法事实认定"},
    {"id": "S9", "dir": "S9-要件归入与裁判预测", "file": "S9-要件归入与裁判预测.md",
     "name": "要件归入与裁判预测", "emoji": "🎯",
     "原告九步法_desc": "要件归入分析，裁判结果预测",
     "被告九步法_desc": "预判被告九步法要件归入与裁判预测"},
]

# AI 红线：这些步骤 AI 不得自主落定
AI_REDLINE_STEPS = {"S1", "S5", "S6", "S8", "S9"}

# 需北大法宝复验的步骤
PKULAW_VERIFY_STEPS = {"S2", "S4", "S7"}


def get_index_schema() -> dict:
    """生成 _index.json 的空模板"""
    now = datetime.now().isoformat()
    index = {
        "version": "6.0",
        "schema": "九步法双视图",
        "原告九步法": {},
        "被告九步法": {},
        "meta": {
            "case_name": None,
            "case_number": None,
            "created_at": now,
            "last_updated": now,
        }
    }
    for step in STEPS:
        sid = step["id"]
        dir_name = step["dir"]
        # 原告九步法
        w_entry = {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "产物": None,
        }
        if sid in PKULAW_VERIFY_STEPS:
            w_entry["北大法宝复验"] = "pending"
        else:
            w_entry["北大法宝复验"] = None
        index["原告九步法"][dir_name] = w_entry

    # S0 证据卡片库入口（单入口，不区分原被告）
    index["S0"] = {
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "产物": None,
    }

    for step in STEPS:
        sid = step["id"]
        dir_name = step["dir"]

        # 被告九步法
        if sid == "S6":
            index["被告九步法"][dir_name] = {
                "status": "shared_with_原告九步法",
                "note": "双方共用同一份",
            }
        else:
            t_entry = {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "产物": None,
            }
            index["被告九步法"][dir_name] = t_entry

    return index


def detect_status_from_content(content: str) -> str:
    """从文件内容推断状态

    保守策略：只有明确标记才改变状态，模板文件保持 pending。

    支持 JSON frontmatter：
    - status == "pending_review" → review_pending
    - status == "completed" → completed
    - status == "in_progress" → in_progress
    """
    # === JSON frontmatter 解析（优先） ===
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        try:
            frontmatter = json.loads(fm_match.group(1))
            fm_status = frontmatter.get("status", "")
            if fm_status == "pending_review":
                return "review_pending"
            if fm_status == "completed":
                return "completed"
            if fm_status == "in_progress":
                return "in_progress"
        except (json.JSONDecodeError, ValueError):
            pass  # JSON 解析失败，回退旧逻辑

    # === 旧 Markdown 标记兼容 ===
    if re.search(r'\*\*状态\*\*:\s*✅\s*(完成|已确认)', content):
        return "completed"
    if re.search(r'\*\*状态\*\*:\s*⚠️\s*待律师确认', content):
        return "review_pending"
    if re.search(r'\*\*状态\*\*:\s*🔄\s*进行中', content):
        return "in_progress"
    if re.search(r'\*\*状态\*\*:\s*❌\s*阻塞', content):
        return "blocked"

    # 检查是否有实际填写内容（排除模板占位符）
    # 模板特征：大量 [xxx] 占位符
    placeholder_count = len(re.findall(r'\[[一-鿿][^\]]*\]', content))
    # 模板特征：包含"待补充"/"待检索"/"待AI推导"等标记词
    template_markers = len(re.findall(r'待补充|待检索|待AI推导|待定|从材料提取|需根据', content))

    # 如果占位符或模板标记过多，说明仍是模板状态
    if placeholder_count > 3 or template_markers > 2:
        return "pending"

    # 无明确标记 + 无大量占位符 → 保守判定为 pending
    # （除非有明确的进行中标记，否则不自动升级）
    return "pending"


def detect_pkulaw_status(content: str) -> str | None:
    """从文件内容推断北大法宝复验状态"""
    if "北大法宝复验" not in content:
        return None
    if re.search(r'北大法宝复验[：:]\s*✅', content):
        return "verified"
    if re.search(r'北大法宝复验[：:]\s*⚠️', content):
        return "diff_found"
    return "pending"


def resolve_step_file(side_dir: Path, step: dict) -> Path | None:
    """解析步骤文件路径，优先扁平路径，回退旧目录路径（向后兼容）"""
    # 扁平路径：原告九步法/S1-固定权利请求.md
    flat = side_dir / step["file"]
    if flat.exists():
        return flat
    # 旧目录路径：原告九步法/S1-固定权利请求/S1-固定权利请求.md
    nested = side_dir / step["dir"] / f"{step['dir']}.md"
    if nested.exists():
        return nested
    return None


def init_dirs(case_root: Path, force: bool = False) -> None:
    """初始化 intermediate 目录结构（扁平化）"""
    inter = case_root / "intermediate"
    if inter.exists() and not force:
        print(f"⚠️ intermediate/ 已存在，跳过初始化（用 --force 强制覆盖）")
        return

    print("📁 初始化 intermediate 目录结构（扁平化）...")

    for side in ["原告九步法", "被告九步法"]:
        side_dir = inter / side
        side_dir.mkdir(parents=True, exist_ok=True)

    # FINAL 目录
    (inter / "FINAL").mkdir(exist_ok=True)

    # 复制模板文件（扁平化：直接放 md 文件到 side 目录下）
    for side in ["原告九步法", "被告九步法"]:
        tpl_side = TEMPLATES_DIR / side
        case_side = inter / side
        if not tpl_side.exists():
            continue
        for step in STEPS:
            if side == "被告九步法" and step["id"] == "S6":
                continue
            # 优先查扁平模板，回退旧目录模板
            tpl_flat = tpl_side / step["file"]
            tpl_nested = tpl_side / step["dir"] / f"{step['dir']}.md"
            tpl_file = tpl_flat if tpl_flat.exists() else tpl_nested
            case_file = case_side / step["file"]
            if tpl_file.exists() and not case_file.exists():
                shutil.copy2(tpl_file, case_file)

    # 生成 _index.json
    index = get_index_schema()
    index_path = inter / "_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"✅ 生成 {index_path.relative_to(case_root)}")


def mirror_templates(case_root: Path) -> None:
    """从原告九步法模板生成被告九步法镜像文件"""
    inter = case_root / "intermediate"
    w_dir = inter / "原告九步法"
    t_dir = inter / "被告九步法"

    if not w_dir.exists():
        print("❌ 原告九步法目录不存在，无法镜像")
        return

    print("🪞 生成被告九步法镜像文件...")
    count = 0
    for step in STEPS:
        if step["id"] == "S6":
            continue  # S6 共用，不镜像
        w_file = resolve_step_file(w_dir, step)
        t_file = t_dir / step["file"]

        if not w_file or not w_file.exists():
            continue
        if t_file.exists():
            continue  # 不覆盖已有文件
        content = w_file.read_text(encoding="utf-8")

        # 替换标题：原告九步法 → 被告九步法·预判
        content = content.replace("（原告九步法）", "（被告九步法·预判）")
        content = content.replace("原告九步法视角", "被告九步法视角")
        content = content.replace("原告九步法当事人", "被告九步法当事人")
        content = content.replace("原告九步法请求", "被告九步法请求预判")

        # 添加镜像标记
        header_end = content.find("---", content.find("---") + 3)
        if header_end > 0:
            mirror_note = (
                f"> **镜像来源**: 原告九步法 {step['dir']}\n"
                f"> **语义**: 预判（predict）— 基于原告九步法分析推演被告九步法可能的行动\n"
            )
            content = content[:header_end] + mirror_note + content[header_end:]

        t_file.write_text(content, encoding="utf-8")
        count += 1

    print(f"✅ 镜像生成完成: {count} 个文件")


def sync_index(case_root: Path) -> None:
    """扫描已有文件，回写 _index.json"""
    inter = case_root / "intermediate"
    index_path = inter / "_index.json"

    # 读取或创建 index
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = get_index_schema()

    print("🔄 同步 _index.json...")

    w_dir = inter / "原告九步法"
    t_dir = inter / "被告九步法"

    for step in STEPS:
        sid = step["id"]
        dir_name = step["dir"]

        # 原告九步法（优先扁平路径，回退旧目录路径）
        w_file = resolve_step_file(w_dir, step)
        if w_file and w_file.exists():
            content = w_file.read_text(encoding="utf-8")
            status = detect_status_from_content(content)
            w_entry = index["原告九步法"].get(dir_name, {})
            old_status = w_entry.get("status", "pending")

            # === 状态降级保护 ===
            # 如果旧状态是 completed/review_pending，新状态是 pending，且文件仍存在，则保留旧状态
            if old_status in ("completed", "review_pending") and status == "pending":
                status = old_status

            w_entry["status"] = status
            if status != "pending" and not w_entry.get("started_at"):
                w_entry["started_at"] = datetime.now().isoformat()
            if status == "completed":
                w_entry["completed_at"] = datetime.now().isoformat()
                # 检查产物
                final_dir = inter / "FINAL"
                if final_dir.exists():
                    products = [f.name for f in final_dir.iterdir()
                                if f.is_file() and sid in f.name]
                    if products:
                        w_entry["产物"] = products[0]

            # 北大法宝复验
            if sid in PKULAW_VERIFY_STEPS:
                pkulaw = detect_pkulaw_status(content)
                if pkulaw:
                    w_entry["北大法宝复验"] = pkulaw

            index["原告九步法"][dir_name] = w_entry
            if old_status != status:
                print(f"  原告九步法 {dir_name}: {old_status} → {status}")

        # 被告九步法（优先扁平路径，回退旧目录路径）
        if sid == "S6":
            continue  # S6 共用
        t_file = resolve_step_file(t_dir, step)
        if t_file and t_file.exists():
            content = t_file.read_text(encoding="utf-8")
            status = detect_status_from_content(content)
            t_entry = index["被告九步法"].get(dir_name, {})
            old_status = t_entry.get("status", "pending")

            # === 状态降级保护 ===
            # 如果旧状态是 completed/review_pending，新状态是 pending，且文件仍存在，则保留旧状态
            if old_status in ("completed", "review_pending") and status == "pending":
                status = old_status

            t_entry["status"] = status
            if status != "pending" and not t_entry.get("started_at"):
                t_entry["started_at"] = datetime.now().isoformat()
            if status == "completed":
                t_entry["completed_at"] = datetime.now().isoformat()

            index["被告九步法"][dir_name] = t_entry
            if old_status != status:
                print(f"  被告九步法 {dir_name}: {old_status} → {status}")

    # S0 证据卡片库状态检测
    s0_file = inter / "S0-证据卡片库.md"
    s0_entry = index.get("S0", {"status": "pending"})
    old_s0 = s0_entry.get("status", "pending")
    if s0_file.exists():
        content = s0_file.read_text(encoding="utf-8")
        s0_status = detect_status_from_content(content)
        s0_entry["status"] = s0_status
        if s0_status != "pending" and not s0_entry.get("started_at"):
            s0_entry["started_at"] = datetime.now().isoformat()
        if s0_status in ("completed", "approved"):
            s0_entry["completed_at"] = datetime.now().isoformat()
        # 检查是否已有 JSON 解析产物
        s0_json = inter / "S0-证据卡片库.json"
        if s0_json.exists():
            s0_entry["产物"] = "S0-证据卡片库.json"
    index["S0"] = s0_entry
    if old_s0 != s0_entry["status"]:
        print(f"  S0: {old_s0} → {s0_entry['status']}")

    # 更新 meta
    index["meta"]["last_updated"] = datetime.now().isoformat()

    # 写入
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # 打印摘要
    s0_status = index.get("S0", {}).get("status", "pending")
    w_done = sum(1 for s in STEPS
                 if index["原告九步法"].get(s["dir"], {}).get("status") == "completed")
    t_done = sum(1 for s in STEPS if s["id"] != "S6"
                 and index["被告九步法"].get(s["dir"], {}).get("status") == "completed")
    print(f"\n📊 进度摘要: S0 [{s0_status}] | 原告九步法 {w_done}/9 完成 | 被告九步法 {t_done}/8 完成（S6 共用）")
    print(f"✅ _index.json 已更新")

    # 自动生成九步法总览
    generate_overview(case_root, index)


def generate_overview(case_root: Path, index: dict = None) -> None:
    """生成九步法总览.md — 统一审阅文件"""
    inter = case_root / "intermediate"
    overview_path = inter / "原告九步法" / "九步法总览.md"

    # 读取 index
    if index is None:
        index_path = inter / "_index.json"
        if not index_path.exists():
            return
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)

    # 提取案件名称
    case_name = index.get("meta", {}).get("case_name") or case_root.name
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 计算进度
    s0_entry = index.get("S0", {})
    s0_status = s0_entry.get("status", "pending")
    s0_label = {"pending": "待启动", "in_progress": "进行中",
                 "completed": "完成", "review_pending": "待确认",
                 "blocked": "阻塞"}.get(s0_status, s0_status)
    w_done = sum(1 for s in STEPS
                 if index.get("原告九步法", {}).get(s["dir"], {}).get("status") == "completed")
    t_done = sum(1 for s in STEPS if s["id"] != "S6"
                 and index.get("被告九步法", {}).get(s["dir"], {}).get("status") == "completed")

    lines = [
        f"# 九步法总览 — {case_name}",
        f"",
        f"> 自动生成于 {now} | S0: [{s0_label}] | 原告九步法进度: {w_done}/9 | 被告九步法进度: {t_done}/8",
        f"> 本文件由 sync_step_index.py 自动生成，勿手动编辑",
        f"",
        f"---",
    ]

    w_dir = inter / "原告九步法"

    # S0 证据卡片库
    lines.append(f"")
    lines.append(f"## S0 🔍 证据卡片库 [{s0_label}]")
    s0_path = inter / "S0-证据卡片库.md"
    s0_json = inter / "S0-证据卡片库.json"
    if s0_json.exists():
        try:
            import json as _json
            s0_data = _json.loads(s0_json.read_text(encoding="utf-8"))
            total = s0_data.get("meta", {}).get("total_count", 0)
            need_review = s0_data.get("meta", {}).get("need_review", 0)
            lines.append(f"")
            lines.append(f"**摘要**: {total} 条证据卡片, {need_review} 条待确认")
        except Exception:
            pass
    elif s0_path.exists():
        lines.append(f"")
        lines.append(f"（文件已生成，待 AI 填写标签）")
    else:
        lines.append(f"")
        lines.append(f"（尚未启动）")
    lines.append(f"")

    for step in STEPS:
        sid = step["id"]
        dir_name = step["dir"]
        w_entry = index.get("原告九步法", {}).get(dir_name, {})
        status = w_entry.get("status", "pending")
        status_map = {
            "pending": "待启动", "in_progress": "进行中",
            "completed": "完成", "review_pending": "待确认",
            "blocked": "阻塞",
        }
        status_label = status_map.get(status, status)

        lines.append(f"")
        lines.append(f"## {step['id']} {step['emoji']} {step['name']} [{status_label}]")

        # 读取文件内容，提取摘要
        w_file = resolve_step_file(w_dir, step)
        if w_file and w_file.exists():
            content = w_file.read_text(encoding="utf-8")

            # 提取核心结论
            conclusion = _extract_section(content, ["核心结论", "结论", "总结"])
            if conclusion:
                lines.append(f"")
                lines.append(f"**核心结论**: {conclusion}")

            # 提取关键要点
            points = _extract_list_items(content, ["关键要点", "要点", "关键", "分析"])
            if points:
                lines.append(f"")
                lines.append(f"**关键要点**:")
                for p in points[:5]:
                    lines.append(f"- {p}")

            # 提取待确认项
            checkboxes = _extract_checkboxes(content)
            if checkboxes:
                lines.append(f"")
                lines.append(f"**待确认项**:")
                for cb in checkboxes:
                    lines.append(f"- [ ] {cb}")
            elif status == "completed":
                lines.append(f"")
                lines.append(f"**待确认项**: 无")

            # 北大法宝复验状态
            if sid in PKULAW_VERIFY_STEPS:
                pkulaw = w_entry.get("北大法宝复验", "pending")
                pkulaw_map = {
                    "pending": "待复验", "verified": "已复验",
                    "diff_found": "有差异",
                }
                pkulaw_label = pkulaw_map.get(pkulaw, "待复验")
                lines.append(f"")
                lines.append(f"**北大法宝复验**: {pkulaw_label}")
        else:
            lines.append(f"")
            lines.append(f"（文件尚未创建）")

        lines.append(f"")

    # 进度摘要表
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 进度摘要")
    lines.append(f"")
    lines.append(f"| 步骤 | 原告九步法 | 被告九步法 | 北大法宝 |")
    lines.append(f"|------|------|------|---------|")
    lines.append(f"| S0 🔍 证据卡片库 | {s0_label} | — | — |")
    for step in STEPS:
        dir_name = step["dir"]
        w_status = index.get("原告九步法", {}).get(dir_name, {}).get("status", "pending")
        if step["id"] == "S6":
            t_status = "shared"
        else:
            t_status = index.get("被告九步法", {}).get(dir_name, {}).get("status", "pending")
        status_short = {
            "pending": "待启动", "in_progress": "进行中",
            "completed": "完成", "review_pending": "待确认",
            "blocked": "阻塞", "shared_with_原告九步法": "共用", "shared": "共用",
        }
        w_s = status_short.get(w_status, w_status)
        t_s = status_short.get(t_status, t_status)
        pkulaw = ""
        if step["id"] in PKULAW_VERIFY_STEPS:
            pk = index.get("原告九步法", {}).get(dir_name, {}).get("北大法宝复验", "pending")
            pkulaw = {"pending": "待复验", "verified": "已复验", "diff_found": "有差异"}.get(pk, "待复验")
        else:
            pkulaw = "—"
        lines.append(f"| {step['id']} {step['name']} | {w_s} | {t_s} | {pkulaw} |")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*此文件由案件OS自动生成，每次运行 sync 后自动更新*")

    # 写入
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 生成 {overview_path.relative_to(case_root)}")


def _extract_section(content: str, headers: list[str]) -> str | None:
    """从 markdown 中提取指定标题下的第一个段落"""
    for header in headers:
        pattern = rf'##\s*{re.escape(header)}[^\n]*\n+(.+?)(?:\n##|\n---|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # 取第一段（到第一个空行或列表）
            first_para = text.split('\n\n')[0].split('\n-')[0].strip()
            # 去掉 markdown 标记
            first_para = re.sub(r'\*\*([^*]+)\*\*', r'\1', first_para)
            if first_para and len(first_para) > 5:
                return first_para[:200]
    return None


def _extract_list_items(content: str, headers: list[str]) -> list[str]:
    """从 markdown 中提取指定标题下的列表项"""
    for header in headers:
        pattern = rf'##\s*{re.escape(header)}[^\n]*\n+((?:[-*] .+\n?)+)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            items = []
            for line in match.group(1).strip().split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    item = line[2:].strip()
                    item = re.sub(r'\*\*([^*]+)\*\*', r'\1', item)
                    if item:
                        items.append(item)
            if items:
                return items
    return []


def _extract_checkboxes(content: str) -> list[str]:
    """提取所有未完成的 checkbox 项"""
    return re.findall(r'\[ \]\s*(.+)', content)


def main():
    parser = argparse.ArgumentParser(
        description="九步法双视图 — 目录初始化 + 镜像生成 + _index.json 同步"
    )
    parser.add_argument("case_root", nargs="?", default=".",
                        help="案件文件夹路径")
    parser.add_argument("--action", default="all",
                        choices=["init", "mirror", "sync", "all"],
                        help="执行动作（默认 all）")
    parser.add_argument("--force", action="store_true",
                        help="强制覆盖已有目录")
    args = parser.parse_args()

    case_root = Path(args.case_root).resolve()
    print(f"🔍 案件目录: {case_root}")

    action = args.action

    if action in ("init", "all"):
        init_dirs(case_root, force=args.force)

    if action in ("mirror", "all"):
        mirror_templates(case_root)

    if action in ("sync", "all"):
        sync_index(case_root)

    print("\n✅ 完成")


if __name__ == "__main__":
    main()
