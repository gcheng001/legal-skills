# OMC 命令速查

> 民事案件OS使用的OMC多Agent调度命令参考。

---

## 快速指南

| 场景                     | OMC命令                         | 说明                                         |
| ------------------------ | ------------------------------- | -------------------------------------------- |
| 复杂任务/多步骤          | `/team 5:executor "任务描述"`   | 多Agent并行流水线（plan→exec→verify→fix） |
| 自主端到端               | `/autopilot "任务描述"`         | 单Lead Agent从规划到验证                     |
| 持久验证                 | `/ralph "任务描述"`             | 带verify/fix循环，确保完全完成               |
| 最大并行                 | `/ultrawork "任务描述"`         | 批量并行修复/重构                            |
| 规划共识                 | `/ralplan "任务描述"`           | 迭代规划，多轮确认                           |
| 深度面试                 | `/deep-interview "需求"`        | Socratic提问式需求澄清                       |
| Provider顾问             | `/ask codex "问题"`             | 调用本地Provider顾问                         |

## 配置说明

- **Codex适配说明**：本文件仅作 OMC 旧命令速查；在 Codex 中优先使用当前会话可用的 Codex 工具、内置图像生成、前端预览和本地脚本能力。
- **模型路由**（OMC自动）：简单→Haiku / 标准→Sonnet / 复杂→Opus
