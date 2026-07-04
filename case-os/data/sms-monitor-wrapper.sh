#!/bin/bash
# 法院短信监控包装脚本 - 由LaunchAgent调用
# 独立脚本，必须自己自定位，不依赖调用方环境变量

_SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# wrapper 在 case-os/data/ 下，回到 case-os 根只需一层 ..（不是 ../..）
CASE_OS_ROOT="$(cd -P "$_SCRIPT_DIR/.." && pwd -P)"

# launchd 默认 PATH 不带 /opt/homebrew/bin，fswatch 找不到；显式扩展
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
SMS_DB_PATH="~/Library/SMS/sms.db"
LOG_DIR="$CASE_OS_ROOT/data"
MONITOR_SCRIPT="$CASE_OS_ROOT/agents/court-sms-monitor/monitor.py"

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
