#!/bin/bash
# 法院短信监控包装脚本 - 由LaunchAgent调用

SMS_DB_PATH="$HOME/Library/SMS/sms.db"
LOG_DIR="$HOME/.claude/skills/case-os/data"
MONITOR_SCRIPT="$HOME/.claude/skills/case-os/agents/court-sms-monitor/monitor.py"

echo "=== 法院短信监控Agent启动 ===" >> "$LOG_DIR/sms-monitor.log"
echo "启动时间：$(date)" >> "$LOG_DIR/sms-monitor.log"
echo "监控目标：$SMS_DB_PATH" >> "$LOG_DIR/sms-monitor.log"

# 监控短信数据库变化
fswatch -o "$SMS_DB_PATH" | while read event; do
    echo "=== 检测到短信数据库变化 ===" >> "$LOG_DIR/sms-monitor.log"
    echo "时间：$(date)" >> "$LOG_DIR/sms-monitor.log"

    # 调用监控脚本
    python3 "$MONITOR_SCRIPT" >> "$LOG_DIR/sms-monitor.log" 2>&1

    echo "=== 处理完成 ===" >> "$LOG_DIR/sms-monitor.log"
done
