#!/bin/bash
# 案件周度扫描Agent - 安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR"
SCAN_SCRIPT="$AGENT_DIR/scan.py"
PLIST_FILE="$HOME/Library/LaunchAgents/com.claude.caseos.weekly-scan.plist"

echo "🔧 安装案件周度扫描Agent..."

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到python3"
    exit 1
fi

# 确保脚本可执行
chmod +x "$SCAN_SCRIPT"

# 创建LaunchAgent配置文件
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.caseos.weekly-scan</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SCAN_SCRIPT</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$HOME/.claude/skills/case-os/data/launchd-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/.claude/skills/case-os/data/launchd-stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>
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
echo "   - 运行时间：每周一早上8点"
echo "   - 日志路径：~/.claude/skills/case-os/data/launchd-*.log"
echo ""
echo "🧪 手动测试："
echo "   python3 $SCAN_SCRIPT"
echo ""
echo "📝 卸载命令："
echo "   launchctl unload $PLIST_FILE"
echo "   rm $PLIST_FILE"
