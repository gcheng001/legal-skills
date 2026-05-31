#!/bin/bash
# 案件OS每周定期扫描 - launchd 调用入口
# 扫描所有案件文件夹，输出结果到文件，通过微信推送

SCAN_SCRIPT="$HOME/.claude/skills/case-os/scripts/scan_case_folders.py"
RESULT_FILE="$HOME/.claude/skills/case-os/data/last-scan-result.txt"
LOG_FILE="$HOME/.claude/skills/case-os/data/scan.log"

echo "=== 案件OS定期扫描 $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"

# 运行扫描脚本，输出到结果文件
python3 "$SCAN_SCRIPT" > "$RESULT_FILE" 2>&1
SCAN_EXIT=$?

if [ $SCAN_EXIT -eq 0 ]; then
    echo "扫描完成" >> "$LOG_FILE"
else
    echo "扫描失败 (exit code: $SCAN_EXIT)" >> "$LOG_FILE"
fi

# 读取结果内容
RESULT=$(cat "$RESULT_FILE")

# 通过微信 API 直接发送消息
if [ -n "$RESULT" ]; then
    python3 << 'PYTHON_SCRIPT' >> "$LOG_FILE" 2>&1
import json
import os
import time
import urllib.request
import urllib.error

# 读取扫描结果
result_file = os.path.expanduser('~/.claude/skills/case-os/data/last-scan-result.txt')
with open(result_file, 'r') as f:
    content = f.read().strip()

if not content:
    print('无扫描结果，跳过发送')
    exit(0)

# 读取微信配置：Claude Code 独立配置优先；若用户仍沿用旧桥接配置，则兼容读取。
candidate_files = [
    os.path.expanduser('~/.claude-to-im/data/weixin-accounts.json'),
    os.path.join(os.path.expanduser('~'), '.claude' + '-to-im', 'data', 'weixin-accounts.json'),
]
accounts_file = next((p for p in candidate_files if os.path.exists(p)), '')
if not accounts_file:
    print('未找到微信账号配置，已跳过发送')
    exit(0)

with open(accounts_file, 'r') as f:
    accounts = json.load(f)

if not accounts:
    print('未找到微信账号配置')
    exit(1)

# 使用第一个启用的账号
account = accounts[0]
bot_token = account.get('token', '')
base_url = account.get('baseUrl', 'https://ilinkai.weixin.qq.com')
user_id = account.get('userId', '')

if not bot_token or not user_id:
    print('微信配置不完整')
    exit(1)

# 构造消息
msg_text = f"📋 案件OS每周扫描报告\n\n{content}"

# 发送消息
import random
import string

def generate_client_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

client_id = generate_client_id()

payload = {
    "msg": {
        "from_user_id": "",
        "to_user_id": user_id,
        "client_id": client_id,
        "message_type": 2,
        "message_state": 2,
        "item_list": [
            {
                "type": 1,
                "text_item": {"text": msg_text}
            }
        ]
    },
    "base_info": {
        "channel_version": "claude-case-os-weekly-scan/1.0"
    }
}

url = f"{base_url.rstrip('/')}/ilink/bot/sendmessage"

headers = {
    'Content-Type': 'application/json',
    'AuthorizationType': 'ilink_bot_token',
    'Authorization': f'Bearer {bot_token}',
}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print(f'消息发送成功: client_id={client_id}')
except urllib.error.HTTPError as e:
    print(f'消息发送失败: HTTP {e.code} {e.reason}')
except Exception as e:
    print(f'消息发送异常: {e}')

PYTHON_SCRIPT
fi

echo "---" >> "$LOG_FILE"
