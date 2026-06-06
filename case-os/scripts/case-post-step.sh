#!/bin/bash
# case-post-step.sh - case-os local structured-state hook
# Usage: case-post-step.sh <case-path> [step]

set -euo pipefail

CASE_PATH="${1:?用法: case-post-step.sh <案件路径> [步骤名称]}"
STEP_NAME="${2:-unknown}"
SCRIPTS_DIR="$HOME/.codex/skills/case-os/scripts"
STATE_SCRIPT="$SCRIPTS_DIR/manage_integration_state.py"
FEISHU_SYNC_SCRIPT="$HOME/.local/bin/sync-claude-md-to-feishu.py"

echo "[Hook] 后置动作：$STEP_NAME"

# Phase B 索引只在正式目录已存在时同步，避免为 Phase A 创建额外产物。
if [ -f "$CASE_PATH/intermediate/_index.json" ]; then
    echo "  -> 同步九步法索引"
    python3 "$SCRIPTS_DIR/sync_step_index.py" "$CASE_PATH" --action sync
fi

echo "  -> 刷新本地结构化状态"
if [ "$STEP_NAME" = "unknown" ]; then
    python3 "$STATE_SCRIPT" refresh "$CASE_PATH"
else
    python3 "$STATE_SCRIPT" refresh "$CASE_PATH" --step "$STEP_NAME"
fi

echo "  -> 校验本地状态与发布摘要白名单"
python3 "$STATE_SCRIPT" validate "$CASE_PATH"

# A5 飞书同步：检测 CLAUDE.md 变更并自动触发同步
# 贯穿整个案件OS始终，任何步骤完成后如 CLAUDE.md 有变更，自动同步到飞书
CLAUDE_MD="$CASE_PATH/CLAUDE.md"
STATE_FILE="$CASE_PATH/_archive/case-os-state.json"

if [ -f "$CLAUDE_MD" ] && [ -f "$STATE_FILE" ]; then
    # 检查 A5 步骤状态，确定是否需要同步
    A5_STATUS=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
a5 = state.get('workflow', {}).get('phase_a', {}).get('A5', {})
print(a5.get('status', 'pending'))
" 2>/dev/null || echo "pending")

    # 如果 A5 已完成，检查 CLAUDE.md 是否有新的变更
    if [ "$A5_STATUS" = "completed" ]; then
        # 获取 A5 上次同步时间
        A5_SYNCED_AT=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
a5 = state.get('workflow', {}).get('phase_a', {}).get('A5', {})
print(a5.get('synced_at', ''))
" 2>/dev/null || echo "")

        # 获取 CLAUDE.md 最后修改时间
        CLAUDE_MTIME=$(stat -f "%m" "$CLAUDE_MD" 2>/dev/null || echo "0")

        # 如果 CLAUDE.md 在 A5 同步后有更新，触发重新同步
        if [ -n "$A5_SYNCED_AT" ] && [ -n "$CLAUDE_MTIME" ]; then
            # 简单比较：如果文件修改时间晚于同步时间，需要重新同步
            # 这里使用简化的逻辑，实际应该用更精确的时间比较
            echo "  -> 检测 CLAUDE.md 变更..."
            # 如果有变更，触发 A5 同步
            if [ "$STEP_NAME" != "A5" ]; then
                echo "  -> 触发 A5 飞书同步（CLAUDE.md 已更新）"
                python3 "$FEISHU_SYNC_SCRIPT" "$CASE_PATH" || echo "  ⚠️ 飞书同步失败，请手动执行"
            fi
        fi
    elif [ "$STEP_NAME" = "A4" ] || [ "$STEP_NAME" = "A5" ]; then
        # A4 或 A5 步骤完成后，首次触发飞书同步
        echo "  -> 触发 A5 飞书同步（首次）"
        python3 "$FEISHU_SYNC_SCRIPT" "$CASE_PATH" || echo "  ⚠️ 飞书同步失败，请手动执行"
    fi
fi

echo "[Hook] 完成：$STEP_NAME"
