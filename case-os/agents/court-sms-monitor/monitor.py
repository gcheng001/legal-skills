#!/usr/bin/env python3
"""
法院短信实时监控Agent - 实现脚本
监控iOS短信数据库，发现法院相关短信后实时提醒并同步到飞书
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# 导入飞书通知器
try:
    from feishu_notifier import CourtSMSFeishuNotifier
except ImportError:
    print("⚠️  警告：未找到飞书通知器，飞书功能将不可用")
    CourtSMSFeishuNotifier = None

# ==================== 配置 ====================
SMS_DB_PATH = Path.home() / "Library" / "SMS" / "sms.db"
SCAN_ROOTS = [
    Path.home() / "Documents" / "Documents" / "cases",
]
ARCHIVE_DIR = "_archive"
COURT_SMS_FILE = "court-sms.json"
STATE_FILE = Path.home() / ".claude" / "skills" / "case-os" / "data" / "sms-monitor-state.json"

# 飞书配置（从环境变量读取）
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN", "")

# 关键词配置
KEYWORDS = {
    "hearing": ["开庭", "庭审", "传票", "出庭", "听证"],
    "evidence": ["举证", "证据交换", "证据材料", "提交证据"],
    "payment": ["缴费", "诉讼费", "受理费", "预交"],
    "judgment": ["判决", "裁定", "送达", "裁判文书"],
}

IGNORE_KEYWORDS = ["验证码", "优惠", "促销", "活动", "中奖"]

# ==================== 短信解析 ====================
class SMSParser:
    """短信解析器"""

    @staticmethod
    def extract_case_number(text: str) -> Optional[str]:
        """提取案号"""
        patterns = [
            r'[(\（]?\d{4}[)\）]?[^\d]+民[一-龥]{1,3}?\d+号',
            r'\(\d{4}\)[^\d]+民[一-龥]{1,3}?\d+号',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def extract_date(text: str) -> Optional[str]:
        """提取日期"""
        patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                match = matches[0]
                if len(match) == 3:
                    year, month, day = match
                    if len(year) == 4:
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        current_year = datetime.now().year
                        return f"{current_year}-{month.zfill(2)}-{day.zfill(2)}"
        return None

    @staticmethod
    def extract_time(text: str) -> Optional[str]:
        """提取时间"""
        patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})点(\d{1,2})分',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                hour, minute = match.groups()
                return f"{hour.zfill(2)}:{minute.zfill(2)}"
        return None

    @staticmethod
    def extract_court(text: str) -> Optional[str]:
        """提取法院名称"""
        court_patterns = [
            r'[^，。]+?法院',
            r'[^，。]+?法庭',
        ]
        for pattern in court_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def classify_sms(text: str) -> Optional[str]:
        """分类短信类型"""
        for msg_type, keywords in KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return msg_type
        return None


class CourtSMSMonitor:
    """法院短信监控器"""

    def __init__(self):
        self.parser = SMSParser()
        self.state = self.load_state()
        self.feishu_notifier = CourtSMSFeishuNotifier() if CourtSMSFeishuNotifier else None

    def load_state(self) -> Dict:
        """加载监控状态"""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return {"last_sms_id": 0, "processed_ids": []}

    def save_state(self):
        """保存监控状态"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_new_messages(self) -> List[Dict]:
        """获取新短信"""
        if not SMS_DB_PATH.exists():
            print(f"⚠️  短信数据库不存在：{SMS_DB_PATH}")
            return []

        try:
            conn = sqlite3.connect(str(SMS_DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询新短信
            query = """
                SELECT rowid, date, address, text
                FROM message
                WHERE rowid > ?
                ORDER BY date DESC
                LIMIT 50
            """
            cursor.execute(query, (self.state["last_sms_id"],))
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return messages
        except sqlite3.Error as e:
            print(f"❌ 数据库错误：{e}")
            return []

    def is_court_sms(self, text: str) -> bool:
        """判断是否为法院短信"""
        # 检查忽略关键词
        if any(keyword in text for keyword in IGNORE_KEYWORDS):
            return False

        # 检查法院关键词
        msg_type = self.parser.classify_sms(text)
        return msg_type is not None

    def parse_court_sms(self, sms: Dict) -> Optional[Dict]:
        """解析法院短信"""
        text = sms.get("text", "")
        if not self.is_court_sms(text):
            return None

        msg_type = self.parser.classify_sms(text)

        parsed = {
            "id": f"msg_{sms['rowid']}",
            "type": msg_type,
            "content": text,
            "sender": sms.get("address", "未知"),
            "received_at": datetime.fromtimestamp(sms["date"] / 1000000000).isoformat(),
            "extracted": {},
        }

        # 提取关键信息
        case_number = self.parser.extract_case_number(text)
        if case_number:
            parsed["extracted"]["case_number"] = case_number

        court = self.parser.extract_court(text)
        if court:
            parsed["extracted"]["court"] = court

        date_str = self.parser.extract_date(text)
        time_str = self.parser.extract_time(text)

        if date_str:
            if time_str:
                parsed["extracted"]["datetime"] = f"{date_str} {time_str}"
            else:
                parsed["extracted"]["date"] = date_str

            # 计算截止时间
            try:
                if msg_type == "judgment":
                    # 判决书：上诉期15天
                    delivery_date = datetime.strptime(date_str, "%Y-%m-%d")
                    deadline = delivery_date + timedelta(days=15)
                    parsed["extracted"]["appeal_deadline"] = deadline.strftime("%Y-%m-%d")
                    parsed["deadline"] = deadline.strftime("%Y-%m-%d")
                else:
                    # 其他：使用提取的日期
                    parsed["deadline"] = date_str
            except ValueError:
                pass

        return parsed

    def identify_case(self, sms_info: Dict) -> Optional[Path]:
        """识别短信属于哪个案件"""
        extracted = sms_info.get("extracted", {})
        case_number = extracted.get("case_number")
        court = extracted.get("court")

        # 遍历案件文件夹
        for root in SCAN_ROOTS:
            if not root.exists():
                continue
            for case_dir in root.rglob("CLAUDE.md"):
                case_path = case_dir.parent

                # 读取案件信息
                claude_md = case_path / "CLAUDE.md"
                if claude_md.exists():
                    content = claude_md.read_text(encoding="utf-8")

                    # 匹配案号
                    if case_number and case_number in content:
                        return case_path

                    # 匹配法院
                    if court and court in content:
                        return case_path

        return None

    def save_to_archive(self, case_path: Path, sms_info: Dict):
        """保存到案件档案"""
        archive_dir = case_path / ARCHIVE_DIR
        archive_dir.mkdir(parents=True, exist_ok=True)

        court_sms_file = archive_dir / COURT_SMS_FILE

        # 读取现有数据
        if court_sms_file.exists():
            try:
                data = json.loads(court_sms_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                data = {"messages": []}
        else:
            data = {"messages": []}

        # 添加新短信
        data["messages"].append(sms_info)

        # 保存
        court_sms_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def sync_to_feishu(self, sms_info: Dict, case_name: str):
        """同步到飞书（机器人消息 + 多维表格）"""
        if not self.feishu_notifier:
            print("⚠️  飞书通知器未配置，跳过同步")
            return

        try:
            # 发送飞书机器人消息（卡片形式）
            # 并写入多维表格
            self.feishu_notifier.send_court_sms(sms_info, case_name)
        except Exception as e:
            print(f"❌ 飞书同步失败：{e}")

    def get_type_label(self, msg_type: str) -> str:
        """获取类型标签"""
        labels = {
            "hearing": "开庭通知",
            "evidence": "举证期限",
            "payment": "缴费通知",
            "judgment": "判决送达",
        }
        return labels.get(msg_type, "其他")

    def send_notification(self, sms_info: Dict, case_name: str):
        """发送通知"""
        msg_type = self.get_type_label(sms_info["type"])
        extracted = sms_info.get("extracted", {})

        # 构建通知内容
        title = f"🔔 法院短信提醒：{msg_type}"
        message_parts = [
            f"案件：{case_name}",
        ]

        if extracted.get("court"):
            message_parts.append(f"法院：{extracted['court']}")

        if extracted.get("date"):
            deadline_str = extracted["date"]
            if extracted.get("appeal_deadline"):
                deadline_str = f"上诉期截止：{extracted['appeal_deadline']}"
            message_parts.append(f"时间：{deadline_str}")

        if extracted.get("case_number"):
            message_parts.append(f"案号：{extracted['case_number']}")

        message = "\n".join(message_parts)

        # 发送macOS桌面通知
        os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')

        print(f"\n🔔 {title}")
        print(message)
        print()

    def process(self):
        """处理新短信"""
        messages = self.get_new_messages()

        if not messages:
            print("✅ 无新短信")
            return

        print(f"📱 发现 {len(messages)} 条新短信")

        court_sms_count = 0
        for sms in messages:
            sms_info = self.parse_court_sms(sms)
            if not sms_info:
                continue

            court_sms_count += 1
            print(f"\n{'='*50}")
            print(f"🏛️  发现法院短信：{self.get_type_label(sms_info['type'])}")
            print(f"内容：{sms_info['content'][:100]}...")
            print(f"{'='*50}")

            # 识别案件
            case_path = self.identify_case(sms_info)
            if case_path:
                case_name = case_path.name
                print(f"✅ 匹配案件：{case_name}")

                # 保存到档案
                self.save_to_archive(case_path, sms_info)

                # 同步到飞书
                self.sync_to_feishu(sms_info, case_name)

                # 发送通知
                self.send_notification(sms_info, case_name)
            else:
                print(f"⚠️  未找到匹配案件")
                # TODO: 保存到未分类记录

            # 标记为已处理
            self.state["processed_ids"].append(sms["rowid"])

        # 更新状态
        if messages:
            self.state["last_sms_id"] = max(msg["rowid"] for msg in messages)
            self.save_state()

        if court_sms_count > 0:
            print(f"\n✅ 处理完成：发现 {court_sms_count} 条法院短信")
        else:
            print(f"\n✅ 处理完成：无法院短信")


def main():
    """主函数"""
    print("🔍 法院短信监控Agent启动...")
    print(f"📂 监控数据库：{SMS_DB_PATH}")
    print(f"📂 扫描案件根目录：{SCAN_ROOTS}")
    print()

    monitor = CourtSMSMonitor()
    monitor.process()


if __name__ == "__main__":
    sys.exit(main())
