# Claude Code agents safety note

This `agents/` subtree was synced from `goacheng001/case-os` main on 2026-05-19 and path-adapted from Claude Code to Claude Code.

The files are installed as opt-in source files only. Do not run `install.sh`, `agent_manager.sh start`, or load any LaunchAgent unless the user explicitly asks to enable that specific agent.

Sensitive boundaries:

- `court-sms-monitor` reads `~/Library/SMS/sms.db`.
- `court-sms-monitor` can send data to Feishu when `FEISHU_BOT_WEBHOOK` or Feishu table credentials are configured.
- `weekly-scan` can create a scheduled LaunchAgent.
- Feishu tokens must come from environment variables; no default app token should be kept in source.
