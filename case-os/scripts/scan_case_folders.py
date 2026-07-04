#!/usr/bin/env python3
"""定期扫描案件文件夹，检测新增文件，维护待处理队列"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# case-os 物理根 = 脚本所在 scripts/ 的上级。
# 不依赖 ~/.codex 或 ~/.claude 软链存在（两者都可能被清理）。
_SKILL_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _SKILL_ROOT / "data"

# 扫描根从配置文件读取，路径迁移后只改一处。
# 配置每行一个绝对路径（# 注释、空行忽略）。
SCAN_ROOTS_FILE = _DATA_DIR / "scan-roots.txt"

def _load_scan_roots():
    if not SCAN_ROOTS_FILE.exists():
        print(f"⚠️  case-os：扫描根配置缺失 → {SCAN_ROOTS_FILE}", file=sys.stderr)
        return []
    roots = []
    for line in SCAN_ROOTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        roots.append(Path(line))
    return roots

SCAN_ROOTS = _load_scan_roots()

QUEUE_FILE = _DATA_DIR / "pending-files.json"

def find_case_folders():
    """扫描所有有CLAUDE.md的案件文件夹"""
    if not SCAN_ROOTS:
        print(f"⚠️  case-os：未配置扫描根，请检查 {SCAN_ROOTS_FILE}", file=sys.stderr)
    cases = []
    for root in SCAN_ROOTS:
        if not root.exists():
            print(f"⚠️  扫描根不可访问（跳过）：{root}", file=sys.stderr)
            continue
        for item in root.rglob("CLAUDE.md"):
            case_dir = item.parent
            cases.append(case_dir)
    return cases

def scan_new_files(case_dir, known_files):
    """检测案件文件夹中的新增文件"""
    new_files = []
    for f in case_dir.iterdir():
        if f.is_file() and f.name not in known_files and not f.name.startswith("."):
            new_files.append({
                "file": f.name,
                "path": str(f),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    return new_files

def load_queue():
    """加载待处理队列"""
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    return {"pending": [], "skipped_permanently": []}

def save_queue(queue):
    """保存待处理队列"""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    """主扫描流程"""
    queue = load_queue()
    known_files = {item["file"] + "|" + item["case"] for item in queue["pending"]}
    known_files.update(item["file"] + "|" + item["case"] for item in queue["skipped_permanently"])

    cases = find_case_folders()

    # 所有扫描根都不可访问（典型：移动硬盘未连接）→ 醒目提示，避免伪装成"无新文件"
    if SCAN_ROOTS and not any(r.exists() for r in SCAN_ROOTS):
        print("⚠️  所有扫描根不可访问——移动硬盘是否未连接？本次扫描视为未执行。")
        return

    new_items = []

    for case_dir in cases:
        case_name = case_dir.name
        for f in case_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                key = f.name + "|" + case_name
                if key not in known_files:
                    is_judgment = "判决" in f.name or "裁定" in f.name
                    new_items.append({
                        "case": case_name,
                        "case_path": str(case_dir),
                        "file": f.name,
                        "file_path": str(f),
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        "is_judgment": is_judgment,
                        "status": "pending",
                    })

    queue["pending"].extend(new_items)
    save_queue(queue)

    if new_items:
        print(f"发现 {len(new_items)} 个新增文件：")
        for item in new_items:
            marker = " [判决书]" if item["is_judgment"] else ""
            print(f"  {item['case']} — {item['file']}{marker}")
    else:
        print("未发现新增文件。")

    total_pending = len([i for i in queue["pending"] if i["status"] == "pending"])
    if total_pending > 0:
        print(f"\n待处理队列中共有 {total_pending} 个文件。")

if __name__ == "__main__":
    main()
