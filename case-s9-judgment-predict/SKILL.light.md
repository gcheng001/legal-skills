# 轻量路说明（ADR-0005）

默认 `light` 档：S9 生成并落盘后进 S10，等九步整包一起确认；须带 `predict_marker`，状态记 `pending_review`。预测结论变更时只重跑 S9 及 S10 复验。

full 档：S9 须律师确认后才进 S10。
