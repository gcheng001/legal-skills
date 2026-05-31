# 案件OS多Agent并行运行报告

## 🎯 当前运行的Agent

| Agent名称 | 类型 | 调度方式 | 状态 |
|-----------|------|---------|------|
| weekly-scan | 案件周度扫描Agent | 每周一早上8点 | ✅ 运行中 |
| court-sms-monitor | 法院短信实时监控Agent | 实时监控（fswatch） | ✅ 运行中 |
| batch-evidence | 批量证据提取Agent | 手动触发 | 🔄 待命 |

## 🚀 并行运行架构

```
┌──────────────────────────────────────────────────────────┐
│                   案件OS多Agent系统                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📅 定时监控层                              │
│  ├─ weekly-scan: 每周一8点扫描所有案件                    │
│  │  └─ 生成待办报告 → 桌面通知                            │
│  │                                                         │
│  📡 实时监控层                              │
│  └─ court-sms-monitor: 实时监控短信数据库                  │
│     └─ 发现法院短信 → 飞书机器人 + 多维表格 + 桌面通知     │
│                                                          │
│  ⚡ 执行层（手动触发）                      │
│  └─ batch-evidence: 批量证据提取（3倍加速）                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 📋 Agent详细说明

### 1. 案件周度扫描Agent (weekly-scan)

**功能**：每周一早上8点自动扫描所有案件，生成待办报告

**扫描维度**：
- 🚨 开庭提醒（7天内）
- ⚠️ 证据缺口
- ⚠️ 待办事项
- ⚠️ 久未更新（7天+）
- 📄 新增材料

**输出**：
- 报告文件：`~/Desktop/案件周度扫描报告-YYYY-MM-DD.md`
- 日志：`~/.claude/skills/case-os/data/launchd-*.log`

### 2. 法院短信实时监控Agent (court-sms-monitor)

**功能**：实时监控iOS短信数据库，发现法院相关短信后立即提醒

**监控类型**：
- 🚨 开庭通知（开庭时间、法院、案号）
- ⚠️ 举证期限（举证截止日期）
- ⚠️ 缴费通知（缴费截止日期、金额）
- ⚠️ 判决送达（送达日期、上诉期15天）

**输出**：
- 🤖 飞书机器人卡片消息
- 📊 飞书多维表格记录
- 🖥️ macOS桌面通知
- 📁 案件档案：`<案件路径>/_archive/court-sms.json`

### 3. 批量证据提取Agent (batch-evidence)

**功能**：多个证据文件同时提取，大幅加速A5步骤

**性能**：
- 3个文件：6分钟 → 2分钟（**3倍加速**）
- 10个文件：20分钟 → 7分钟（**2.86倍加速**）

**使用**：
```bash
python3 ~/.claude/skills/case-os/agents/batch-evidence/batch_extract.py /path/to/case/dir
```

## 🔧 管理命令

### 查看状态

```bash
# 使用Agent管理器
bash ~/.claude/skills/case-os/agents/agent_manager.sh status

# 使用别名（需要先 source ~/.zshrc）
caseos-status
```

### 启动/停止/重启

```bash
# 启动所有Agent
caseos-start

# 停止所有Agent
caseos-stop

# 重启所有Agent
caseos-restart
```

### 查看日志

```bash
# 周度扫描日志
tail -f ~/.claude/skills/case-os/data/launchd-stdout.log

# 短信监控日志
tail -f ~/.claude/skills/case-os/data/sms-monitor.log
```

### 测试Agent

```bash
# 测试周度扫描
python3 ~/.claude/skills/case-os/agents/weekly-scan/scan.py

# 测试短信监控
python3 ~/.claude/skills/case-os/agents/court-sms-monitor/monitor.py
```

## 🚨 监控覆盖

### 时间敏感事项

| 事项 | 监控方式 | 提前提醒 |
|------|---------|---------|
| 开庭通知 | 实时短信监控 | 3天、1天、当天 |
| 举证期限 | 实时短信监控 | 3天、1天、当天 |
| 缴费通知 | 实时短信监控 | 3天、1天、当天 |
| 上诉期 | 实时短信监控 | 收到当天、第10天、第13天 |

### 定期扫描事项

| 事项 | 扫描频率 | 发现方式 |
|------|---------|---------|
| 证据缺口 | 每周 | 证据卡片库扫描 |
| 久未更新 | 每周 | CLAUDE.md修改时间 |
| 待办事项 | 每周 | 阶段追踪.md检查 |
| 新增材料 | 每周 | 文件系统扫描 |

## 📊 工作流程

### 典型工作流

```
1. 收到法院短信
   ↓
2. court-sms-monitor实时发现
   ↓
3. 立即发送飞书机器人消息
   ↓
4. 写入飞书多维表格
   ↓
5. 发送macOS桌面通知
   ↓
6. 保存到案件档案
```

```
1. 每周一早上8点
   ↓
2. weekly-scan自动运行
   ↓
3. 扫描所有案件状态
   ↓
4. 生成待办报告
   ↓
5. 保存到桌面
```

```
1. 需要提取证据时
   ↓
2. 手动调用batch-evidence
   ↓
3. 并行处理多个证据
   ↓
4. 生成证据卡片
   ↓
5. 完成时间缩短3倍
```

## 🔮 后续扩展

### 计划中的Agent

- [ ] 法条幻觉校验并行Agent（S2+S10）
- [ ] 文件实时监控Agent（fswatch）
- [ ] 裁判文书网监控Agent
- [ ] Agent编排器（统一管理）

---

**报告生成时间**：2026-05-16 20:30
**Agent版本**：v1.1
**系统状态**：🟢 正常运行
