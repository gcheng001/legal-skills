#!/bin/bash
# 法院短信实时监控Agent - 安装脚本

set -e

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
AGENT_DIR="$SCRIPT_DIR"
MONITOR_SCRIPT="$AGENT_DIR/monitor.py"
# 自定位 case-os 物理根（不依赖 ~/.codex 或 ~/.claude 软链）
CASE_OS_ROOT="$(cd -P "$SCRIPT_DIR/../.." && pwd -P)"
DATA_DIR="$CASE_OS_ROOT/data"
# 用绝对 HOME，避免 sandbox $HOME=/var/folders/... 错位
PLIST_FILE="~/Library/LaunchAgents/com.claude.caseos.sms-monitor.plist"

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
LOG_DIR="$DATA_DIR"
mkdir -p "$LOG_DIR"

# 创建监控脚本（使用fswatch）
# 注意：heredoc 不能加单引号，否则内部变量不展开
WATCH_SCRIPT="$LOG_DIR/sms-monitor-wrapper.sh"
cat > "$WATCH_SCRIPT" << WATCHEOF
#!/bin/bash
# 法院短信监控包装脚本 - 由LaunchAgent调用
# 独立脚本，必须自己自定位，不依赖调用方环境变量

_SCRIPT_DIR="\$(cd -P "\$(dirname "\${BASH_SOURCE[0]}")" && pwd -P)"
# wrapper 在 case-os/data/ 下，回到 case-os 根只需一层 ..（不是 ../..）
CASE_OS_ROOT="\$(cd -P "\$_SCRIPT_DIR/.." && pwd -P)"

# launchd 默认 PATH 不带 /opt/homebrew/bin，fswatch 找不到；显式扩展
export PATH="/opt/homebrew/bin:/usr/local/bin:\$PATH"
SMS_DB_PATH="~/Library/SMS/sms.db"
LOG_DIR="\$CASE_OS_ROOT/data"
MONITOR_SCRIPT="\$CASE_OS_ROOT/agents/court-sms-monitor/monitor.py"

echo "=== 法院短信监控Agent启动 ===" >> "\$LOG_DIR/sms-monitor.log"
echo "启动时间：\$(date)" >> "\$LOG_DIR/sms-monitor.log"
echo "监控目标：\$SMS_DB_PATH" >> "\$LOG_DIR/sms-monitor.log"

# 监控短信数据库变化
fswatch -o "\$SMS_DB_PATH" | while read event; do
    echo "=== 检测到短信数据库变化 ===" >> "\$LOG_DIR/sms-monitor.log"
    echo "时间：\$(date)" >> "\$LOG_DIR/sms-monitor.log"

    # 调用监控脚本
    python3 "\$MONITOR_SCRIPT" >> "\$LOG_DIR/sms-monitor.log" 2>&1

    echo "=== 处理完成 ===" >> "\$LOG_DIR/sms-monitor.log"
done
WATCHEOF

chmod +x "$WATCH_SCRIPT"

# 创建LaunchAgent配置文件
PLIST_FILE="~/Library/LaunchAgents/com.claude.caseos.sms-monitor.plist"
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
echo "   - 日志路径：$DATA_DIR/sms-monitor*.log"
echo ""
echo "🧪 手动测试："
echo "   python3 $MONITOR_SCRIPT"
echo ""
echo "📝 卸载命令："
echo "   launchctl unload $PLIST_FILE"
echo "   rm $PLIST_FILE"
echo "   rm $WATCH_SCRIPT"
