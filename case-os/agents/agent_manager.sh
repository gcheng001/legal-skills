#!/bin/bash
# 案件OS Agent管理器 - 统一管理所有Agent

set -e

AGENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_PATH="$HOME"  # 使用绝对路径
AGENT_LIST=(
    "weekly-scan:case-os.weekly-scan:案件周度扫描Agent:每周一早上8点"
    "court-sms-monitor:caseos.sms-monitor:法院短信实时监控Agent:实时监控"
    "batch-evidence::批量证据提取Agent:手动触发"
)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 获取Agent状态
get_agent_status() {
    local agent_name=$1
    local label_prefix=$2
    local plist_file="$HOME_PATH/Library/LaunchAgents/com.${label_prefix}.plist"
    local label=$(launchctl list | grep "com.${label_prefix}" | awk '{print $1}')

    if [ ! -f "$plist_file" ]; then
        echo "未安装"
    elif [ -n "$label" ]; then
        echo "运行中"
    else
        echo "已安装但未运行"
    fi
}

# 列出所有Agent
list_agents() {
    print_header "案件OS Agent状态"

    printf "%-25s %-30s %-15s\n" "Agent名称" "说明" "状态"
    printf "%-25s %-30s %-15s\n" "---------" "----" "----"

    for agent_info in "${AGENT_LIST[@]}"; do
        IFS=':' read -r agent_name label_prefix desc schedule <<< "$agent_info"

        status=$(get_agent_status "$agent_name" "$label_prefix")
        printf "%-25s %-30s %-15s\n" "$agent_name" "$desc" "$status"
    done

    echo ""
}

# 启动所有Agent
start_all_agents() {
    print_header "启动所有Agent"

    for agent_info in "${AGENT_LIST[@]}"; do
        IFS=':' read -r agent_name desc schedule <<< "$agent_info"

        # 跳过手动触发的Agent
        if [ "$agent_name" = "batch-evidence" ]; then
            print_info "$agent_name: 手动触发，跳过自动启动"
            continue
        fi

        print_info "启动 $agent_name..."

        install_script="$AGENTS_DIR/$agent_name/install.sh"
        if [ -f "$install_script" ]; then
            bash "$install_script"
        else
            print_warning "$agent_name: 未找到安装脚本"
        fi
    done

    print_success "所有Agent已启动"
}

# 停止所有Agent
stop_all_agents() {
    print_header "停止所有Agent"

    for agent_info in "${AGENT_LIST[@]}"; do
        IFS=':' read -r agent_name desc schedule <<< "$agent_info"

        # 跳过手动触发的Agent
        if [ "$agent_name" = "batch-evidence" ]; then
            continue
        fi

        plist_file="$HOME/Library/LaunchAgents/com.claude.caseos.${agent_name}.plist"

        if [ -f "$plist_file" ]; then
            print_info "停止 $agent_name..."
            launchctl unload "$plist_file" 2>/dev/null || true
            print_success "$agent_name 已停止"
        else
            print_warning "$agent_name: 未安装"
        fi
    done

    print_success "所有Agent已停止"
}

# 重启所有Agent
restart_all_agents() {
    print_header "重启所有Agent"
    stop_all_agents
    sleep 1
    start_all_agents
}

# 查看日志
view_logs() {
    local agent_name=$1

    if [ -z "$agent_name" ]; then
        print_error "请指定Agent名称"
        echo "用法: $0 logs <agent_name>"
        echo ""
        echo "可用的Agent:"
        for agent_info in "${AGENT_LIST[@]}"; do
            IFS=':' read -r agent_name desc schedule <<< "$agent_info"
            echo "  - $agent_name"
        done
        return 1
    fi

    log_file="$HOME/.claude/skills/case-os/data/${agent_name}.log"

    if [ ! -f "$log_file" ]; then
        log_file="$HOME/.claude/skills/case-os/data/${agent_name}-stdout.log"
    fi

    if [ ! -f "$log_file" ]; then
        print_error "未找到日志文件: $log_file"
        return 1
    fi

    print_header "查看 $agent_name 日志"
    tail -f "$log_file"
}

# 测试Agent
test_agent() {
    local agent_name=$1

    if [ -z "$agent_name" ]; then
        print_error "请指定Agent名称"
        echo "用法: $0 test <agent_name>"
        return 1
    fi

    print_header "测试 $agent_name"

    case "$agent_name" in
        weekly-scan)
            python3 "$AGENTS_DIR/weekly-scan/scan.py"
            ;;
        court-sms-monitor)
            python3 "$AGENTS_DIR/court-sms-monitor/monitor.py"
            ;;
        batch-evidence)
            print_error "batch-evidence需要指定案件目录"
            echo "用法: python3 $AGENTS_DIR/batch-evidence/batch_extract.py /path/to/case/dir"
            ;;
        *)
            print_error "未知的Agent: $agent_name"
            return 1
            ;;
    esac
}

# 显示帮助
show_help() {
    cat << EOF
案件OS Agent管理器

用法: $0 <command> [options]

命令:
  status              查看所有Agent状态
  start               启动所有Agent
  stop                停止所有Agent
  restart             重启所有Agent
  logs <agent_name>   查看指定Agent的日志
  test <agent_name>   测试指定Agent
  help                显示此帮助信息

可用的Agent:
  - weekly-scan        案件周度扫描Agent
  - court-sms-monitor  法院短信实时监控Agent
  - batch-evidence     批量证据提取Agent（手动触发）

示例:
  $0 status           # 查看状态
  $0 start            # 启动所有
  $0 logs weekly-scan # 查看周度扫描日志
  $0 test weekly-scan # 测试周度扫描

EOF
}

# 主函数
main() {
    local command=$1
    shift || true

    case "$command" in
        status)
            list_agents
            ;;
        start)
            start_all_agents
            ;;
        stop)
            stop_all_agents
            ;;
        restart)
            restart_all_agents
            ;;
        logs)
            view_logs "$@"
            ;;
        test)
            test_agent "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知的命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
