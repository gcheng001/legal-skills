#!/bin/bash
# 测试get_agent_status函数

HOME_PATH="$HOME"

get_agent_status() {
    local agent_name=$1
    local plist_file="$HOME_PATH/Library/LaunchAgents/com.claude.caseos.${agent_name}.plist"
    local label=$(launchctl list | grep "com.claude.caseos.${agent_name}" | awk '{print $1}')

    echo "DEBUG: agent_name=$agent_name"
    echo "DEBUG: plist_file=$plist_file"
    echo "DEBUG: label=$label"
    echo "DEBUG: 文件存在测试: $( [ -f "$plist_file" ] && echo "存在" || echo "不存在" )"

    if [ ! -f "$plist_file" ]; then
        echo "未安装"
    elif [ -n "$label" ]; then
        echo "运行中"
    else
        echo "已安装但未运行"
    fi
}

echo "=== 测试 court-sms-monitor ==="
get_agent_status "court-sms-monitor"

echo ""
echo "=== 测试 weekly-scan ==="
get_agent_status "weekly-scan"
