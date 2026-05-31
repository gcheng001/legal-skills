#!/bin/bash
# case-post-step.sh - case-os local structured-state hook
# Usage: case-post-step.sh <case-path> [step]

set -euo pipefail

CASE_PATH="${1:?用法: case-post-step.sh <案件路径> [步骤名称]}"
STEP_NAME="${2:-unknown}"
SCRIPTS_DIR="$HOME/.claude/skills/case-os/scripts"
STATE_SCRIPT="$SCRIPTS_DIR/manage_integration_state.py"

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

echo "[Hook] 完成：$STEP_NAME"
