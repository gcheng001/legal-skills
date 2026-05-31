#!/usr/bin/env python3
"""
案件周度扫描Agent - 实现脚本
安全设计：只读扫描，无写入权限，无网络访问
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


# ==================== 配置 ====================
SCAN_ROOTS = [
    Path.home() / "Documents" / Documents / cases / "案件",
]

STATE_DIR = Path.home() / ".claude" / "skills" / "case-os" / "data"
LAST_SCAN_FILE = STATE_DIR / "last-scan-result.txt"
PENDING_QUEUE_FILE = STATE_DIR / "pending-files.json"
OUTPUT_DIR = Path.home() / "Desktop"

# 忽略的文件/目录
IGNORE_PATTERNS = [
    r"^\.",           # 以.开头的隐藏文件
    r"^\.DS_Store$",
    r"^~.*",          # ~开头的临时文件
    r"^_archive",     # 归档目录
]

# ==================== 数据结构 ====================
class ScanResult:
    def __init__(self):
        self.urgent = []      # 紧急待办
        self.warning = []     # 警告
        self.info = []        # 信息
        self.errors = []      # 错误
        self.scan_time = datetime.now()


class CaseItem:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.claude_md = path / "CLAUDE.md"
        self.tracking_md = path / "阶段追踪.md"
        self.memo_md = path / "案件备忘录.md"
        self.court_sms = path / "_archive" / "court-sms.json"


# ==================== 核心扫描函数 ====================
def find_case_folders() -> List[CaseItem]:
    """扫描所有案件文件夹（查找CLAUDE.md）"""
    cases = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for item in root.rglob("CLAUDE.md"):
            case_dir = item.parent
            # 跳归档目录
            if "_archive" in str(case_dir):
                continue
            cases.append(CaseItem(case_dir.name, case_dir))
    return cases


def check_court_reminder(case: CaseItem) -> Dict[str, Any]:
    """检查开庭提醒（从court-sms.json）"""
    if not case.court_sms.exists():
        return None

    try:
        data = json.loads(case.court_sms.read_text(encoding="utf-8"))
        if not data.get("messages"):
            return None

        # 找7天内的开庭
        upcoming = []
        now = datetime.now()
        for msg in data["messages"]:
            if msg.get("type") == "开庭通知":
                try:
                    court_date = datetime.strptime(msg.get("date", ""), "%Y-%m-%d")
                    days_until = (court_date - now).days
                    if 0 <= days_until <= 7:
                        upcoming.append({
                            "case": case.name,
                            "date": msg.get("date"),
                            "court": msg.get("court", "未知法院"),
                            "days_until": days_until,
                        })
                except ValueError:
                    pass

        return upcoming[0] if upcoming else None
    except (json.JSONDecodeError, KeyError):
        return None


def check_evidence_gaps(case: CaseItem) -> List[str]:
    """检查证据缺口（从证据卡片库）"""
    evidence_dir = case.path / "_intermediate" / "证据卡片库"
    if not evidence_dir.exists():
        return []

    gaps = []
    for file in evidence_dir.rglob("*.md"):
        content = file.read_text(encoding="utf-8")
        # 检查是否标记为待补充
        if re.search(r'\[待补充\]|\[缺失\]|\[待提供\]', content):
            gaps.append(file.stem)

    return gaps


def check_pending_tasks(case: CaseItem) -> List[str]:
    """检查待办事项（从阶段追踪.md）"""
    if not case.tracking_md.exists():
        return []

    content = case.tracking_md.read_text(encoding="utf-8")
    pending = []

    # 查找未完成的checkbox
    for line in content.split('\n'):
        if re.match(r'^- \[ \]', line):
            pending.append(line.strip()[6:])  # 去掉"- [ ] "

    return pending


def check_last_update(case: CaseItem) -> int:
    """检查最后更新时间（CLAUDE.md修改时间）"""
    if not case.claude_md.exists():
        return None

    mtime = case.claude_md.stat().st_mtime
    last_update = datetime.fromtimestamp(mtime)
    days_since = (datetime.now() - last_update).days
    return days_since


def detect_new_files(case: CaseItem, known_files: set) -> List[str]:
    """检测新增文件"""
    new_files = []
    for file in case.path.iterdir():
        if should_ignore_file(file.name):
            continue
        if file.is_file():
            key = f"{case.name}/{file.name}"
            if key not in known_files:
                new_files.append(file.name)
    return new_files


def should_ignore_file(name: str) -> bool:
    """判断是否应忽略该文件"""
    for pattern in IGNORE_PATTERNS:
        if re.match(pattern, name):
            return True
    return False


# ==================== 报告生成 ====================
def generate_report(results: ScanResult, case_count: int) -> str:
    """生成Markdown报告"""
    lines = [
        "# 案件周度扫描报告",
        "",
        f"**扫描时间**：{results.scan_time.strftime('%Y-%m-%d %H:%M')}",
        f"**扫描范围**：{case_count}个案件",
        "",
    ]

    # 紧急待办
    if results.urgent:
        lines.extend([
            "## 🚨 紧急待办（需要立即处理）",
            "",
        ])
        for item in results.urgent:
            lines.extend(format_urgent_item(item))
            lines.append("")

    # 警告
    if results.warning:
        lines.extend([
            "## ⚠️ 本周待办（建议本周处理）",
            "",
        ])
        for item in results.warning:
            lines.extend(format_warning_item(item))
            lines.append("")

    # 新增材料
    if results.info:
        lines.extend([
            "## 📄 新增材料（本周）",
            "",
        ])
        for item in results.info:
            lines.extend(format_info_item(item))
            lines.append("")

    # 错误
    if results.errors:
        lines.extend([
            "## ⚠️ 扫描错误",
            "",
        ])
        for error in results.errors:
            lines.append(f"- {error}")
        lines.append("")

    # 下次扫描时间
    next_scan = results.scan_time + timedelta(days=7)
    lines.extend([
        "---",
        "",
        f"**下次扫描时间**：{next_scan.strftime('%Y-%m-%d %H:%M')}",
    ])

    return "\n".join(lines)


def format_urgent_item(item: Dict) -> List[str]:
    """格式化紧急项"""
    if item["type"] == "court_reminder":
        return [
            f"### {item['case']} - 开庭提醒",
            f"- 开庭时间：{item['date']}",
            f"- 法院：{item['court']}",
            f"- 距离：{item['days_until']}天",
        ]
    return []


def format_warning_item(item: Dict) -> List[str]:
    """格式化警告项"""
    if item["type"] == "evidence_gap":
        lines = [f"### {item['case']} - 证据缺口"]
        for gap in item["gaps"]:
            lines.append(f"- 缺失证据：{gap}")
        return lines
    elif item["type"] == "stale":
        return [
            f"### {item['case']} - 久未更新",
            f"- 最后更新：{item['last_update']}（{item['days_since']}天前）",
            "- 建议：检查是否有新进展",
        ]
    elif item["type"] == "pending_task":
        lines = [f"### {item['case']} - 待办事项"]
        for task in item["tasks"][:3]:  # 最多显示3条
            lines.append(f"- {task}")
        if len(item["tasks"]) > 3:
            lines.append(f"- ...还有{len(item['tasks'])-3}项待办")
        return lines
    return []


def format_info_item(item: Dict) -> List[str]:
    """格式化信息项"""
    if item["type"] == "new_files":
        lines = [f"### {item['case']}"]
        for file in item["files"][:5]:  # 最多显示5个
            lines.append(f"- 新增：{file}")
        if len(item["files"]) > 5:
            lines.append(f"- ...还有{len(item['files'])-5}个文件")
        return lines
    return []


# ==================== 主流程 ====================
def load_known_files() -> set:
    """加载已知文件列表"""
    if PENDING_QUEUE_FILE.exists():
        try:
            data = json.loads(PENDING_QUEUE_FILE.read_text(encoding="utf-8"))
            return {f"{item['case']}/{item['file']}" for item in data.get("pending", [])}
        except (json.JSONDecodeError, KeyError):
            pass
    return set()


def save_scan_result(report: str):
    """保存扫描结果"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_SCAN_FILE.write_text(report, encoding="utf-8")


def save_report_to_desktop(report: str):
    """保存报告到桌面"""
    filename = f"案件周度扫描报告-{datetime.now().strftime('%Y-%m-%d')}.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main():
    """主扫描流程"""
    print("🔍 开始扫描案件...")
    results = ScanResult()
    known_files = load_known_files()

    # 扫描所有案件
    cases = find_case_folders()
    print(f"发现 {len(cases)} 个案件文件夹")

    for case in cases:
        print(f"  扫描：{case.name}")

        # 检查开庭提醒（紧急）
        court_info = check_court_reminder(case)
        if court_info:
            results.urgent.append({
                "type": "court_reminder",
                **court_info,
            })

        # 检查证据缺口（警告）
        gaps = check_evidence_gaps(case)
        if gaps:
            results.warning.append({
                "type": "evidence_gap",
                "case": case.name,
                "gaps": gaps,
            })

        # 检查待办事项（警告）
        pending = check_pending_tasks(case)
        if pending:
            results.warning.append({
                "type": "pending_task",
                "case": case.name,
                "tasks": pending,
            })

        # 检查久未更新（警告）
        days_since = check_last_update(case)
        if days_since and days_since >= 7:
            mtime = datetime.fromtimestamp(case.claude_md.stat().st_mtime)
            results.warning.append({
                "type": "stale",
                "case": case.name,
                "days_since": days_since,
                "last_update": mtime.strftime("%Y-%m-%d"),
            })

        # 检测新增文件（信息）
        new_files = detect_new_files(case, known_files)
        if new_files:
            results.info.append({
                "type": "new_files",
                "case": case.name,
                "files": new_files,
            })

    # 生成报告
    report = generate_report(results, len(cases))

    # 保存报告
    save_scan_result(report)
    output_path = save_report_to_desktop(report)

    # 输出摘要
    print("\n" + "="*50)
    print(f"✅ 扫描完成")
    print(f"📊 紧急待办：{len(results.urgent)}项")
    print(f"⚠️  本周待办：{len(results.warning)}项")
    print(f"📄 新增材料：{sum(len(i.get('files', [])) for i in results.info)}个文件")
    print(f"💾 报告已保存：{output_path}")
    print("="*50)

    # 如果有紧急待办，单独提醒
    if results.urgent:
        print("\n🚨 紧急待办提醒：")
        for item in results.urgent:
            print(f"  - {item['case']}: {item['date']} 开庭")

    print("\n⏸️  扫描完成，等待用户确认...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
