#!/usr/bin/env python3
"""
飞书通知模块 - 通过飞书机器人发送消息和写入多维表格
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional

# 飞书配置（从环境变量读取）
FEISHU_BOT_WEBHOOK = os.getenv("FEISHU_BOT_WEBHOOK", "")  # 飞书机器人Webhook
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN", "")  # 飞书多维表格App Token
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "")  # 表格ID（可选，默认使用第一个表格）


class FeishuNotifier:
    """飞书通知器"""

    def __init__(self):
        self.webhook = FEISHU_BOT_WEBHOOK
        self.app_token = FEISHU_APP_TOKEN
        self.table_id = FEISHU_TABLE_ID

    def send_card(self, title: str, content: Dict, urgent: bool = False):
        """发送飞书卡片消息

        Args:
            title: 卡片标题
            content: 卡片内容
            urgent: 是否紧急（红色标签）
        """
        if not self.webhook:
            print("⚠️  飞书机器人Webhook未配置，跳过发送")
            return

        # 构建卡片内容
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title,
                    },
                    "template": urgent and "red" or "yellow",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": self._format_content(content),
                        }
                    }
                ],
            }
        }

        # 发送
        try:
            response = requests.post(
                self.webhook,
                json=card,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            print(f"✅ 飞书消息已发送：{title}")
        except Exception as e:
            print(f"❌ 飞书消息发送失败：{e}")

    def _format_content(self, content: Dict) -> str:
        """格式化卡片内容为Markdown"""
        lines = []
        for key, value in content.items():
            if isinstance(value, list):
                lines.append(f"**{key}**")
                for item in value:
                    lines.append(f"  • {item}")
            else:
                lines.append(f"**{key}**：{value}")
        return "\n\n".join(lines)

    def write_to_table(self, record: Dict) -> bool:
        """写入飞书多维表格

        Args:
            record: 记录数据

        Returns:
            是否成功
        """
        if not self.app_token:
            print("⚠️  飞书多维表格App Token未配置，跳过写入")
            return False

        # TODO: 实现飞书多维表格写入
        # 需要使用飞书开放平台API
        print(f"📝 写入飞书多维表格：{record.get('案件名称', '未知案件')}")
        return True


class CourtSMSFeishuNotifier(FeishuNotifier):
    """法院短信飞书通知器"""

    def send_court_sms(self, sms_info: Dict, case_name: str):
        """发送法院短信通知

        Args:
            sms_info: 短信信息
            case_name: 案件名称
        """
        extracted = sms_info.get("extracted", {})
        msg_type = self._get_type_label(sms_info["type"])

        # 判断紧急程度
        urgent = sms_info["type"] in ["hearing", "payment"]

        # 构建卡片内容
        content = {
            "案件": case_name,
        }

        if extracted.get("court"):
            content["法院"] = extracted["court"]

        if extracted.get("case_number"):
            content["案号"] = extracted["case_number"]

        if extracted.get("date"):
            date_text = extracted["date"]
            if extracted.get("appeal_deadline"):
                date_text = f"上诉期截止：{extracted['appeal_deadline']}"
            content["时间"] = date_text

        if extracted.get("datetime"):
            content["具体时间"] = extracted["datetime"]

        # 短信原文摘要
        content["短信摘要"] = sms_info["content"][:100] + "..."

        # 发送卡片
        title = f"🏛️  法院短信提醒：{msg_type}"
        self.send_card(title, content, urgent=urgent)

        # 写入多维表格
        self._write_court_sms_to_table(sms_info, case_name)

    def _write_court_sms_to_table(self, sms_info: Dict, case_name: str):
        """写入法院短信到多维表格"""
        extracted = sms_info.get("extracted", {})

        record = {
            "案件名称": case_name,
            "提醒类型": self._get_type_label(sms_info["type"]),
            "短信类型": sms_info["type"],
            "截止时间": extracted.get("deadline") or extracted.get("datetime") or "",
            "日期": extracted.get("date") or "",
            "法院": extracted.get("court") or "",
            "案号": extracted.get("case_number") or "",
            "短信内容": sms_info["content"],
            "收到时间": sms_info["received_at"],
            "状态": "待处理",
            "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 如果有上诉期，单独记录
        if extracted.get("appeal_deadline"):
            record["上诉期截止"] = extracted["appeal_deadline"]

        self.write_to_table(record)

    def _get_type_label(self, msg_type: str) -> str:
        """获取类型标签"""
        labels = {
            "hearing": "开庭通知",
            "evidence": "举证期限",
            "payment": "缴费通知",
            "judgment": "判决送达",
        }
        return labels.get(msg_type, "其他")
