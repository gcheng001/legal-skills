#!/bin/bash
# 法院短信实时监控Agent - 安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR"
MONITOR_SCRIPT="$AGENT_DIR/monitor.py"
PLIST_FILE="$HOME/Library/LaunchAgents/com.claude.caseos.sms-monitor.log"

echo "🔧 安装法院短信实时监控Agent..."

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到python3"
    exit 1
fi

# 检查fswatch
if ! command -v fswatch &> /dev/null; then
    echo "📦 正在安装fswatch..."
    if command -v brew &> /dev/null; then
        brew install fswatch
    else
        echo "❌ 错误：未找到Homebrew，请手动安装fswatch"
        echo "   安装命令：brew install fswatch"
        exit 1
    fi
fi

# 确保脚本可执行
chmod +x "$MONITOR_SCRIPT"

# 创建日志目录
LOG_DIR="$HOME/.claude/skills/case-os/data"
mkdir -p "$LOG_DIR"

# 创建监控脚本（使用fswatch）
WATCH_SCRIPT="$LOG_DIR/sms-monitor-wrapper.sh"
cat > "$WATCH_SCRIPT" << 'EOFSCRIPT'
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
EOFSCRIPT

chmod +x "$WATCH_SCRIPT"

# 创建LaunchAgent配置文件
PLIST_FILE="$HOME/Library/LaunchAgents/com.claude.caseos.sms-monitor.plist"
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.caseos.sms-monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>$WATCH_SCRIPT</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/sms-monitor-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$LOG_DIR/sms-monitor-stderr.log</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent配置文件已创建：$PLIST_FILE"

# 加载LaunchAgent
echo "📝 正在加载LaunchAgent..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "✅ LaunchAgent已加载"
echo ""
echo "📋 调度信息："
echo "   - 运行模式：实时监控（fswatch）"
echo "   - 监控目标：~/Library/SMS/sms.db"
echo "   - 日志路径：~/.claude/skills/case-os/data/sms-monitor*.log"
echo ""
echo "🧪 手动测试："
echo "   python3 $MONITOR_SCRIPT"
echo ""
echo "📝 卸载命令："
echo "   launchctl unload $PLIST_FILE"
echo "   rm $PLIST_FILE"
echo "   rm $WATCH_SCRIPT"
