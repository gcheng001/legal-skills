# 案件OS Agent系统

> 基于Anthropic claude-for-legal安全设计的自动化Agent系统

Claude Code 安全边界：本目录在 Claude Code 中仅作为可选源码安装，不随常规更新自动启用。启用任何 LaunchAgent、短信监控或飞书同步前，必须先确认用户明确要求，并先阅读 `CLAUDE-SAFETY.md`。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    案件OS Agent系统                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐      ┌─────────────┐      ┌──────────┐ │
│  │ 监控层     │ ───→ │ 编排器      │ ───→ │ 执行层   │ │
│  │           │      │ (Orchestrator)│      │          │ │
│  │ • 文件监控 │      │             │      │ • Skill  │ │
│  │ • 短信监控 │      │ • 五层防线  │      │ • Hook   │ │
│  │ • 定时扫描 │      │ • 审计日志  │      │          │ │
│  └────────────┘      └─────────────┘      └──────────┘ │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 设计原则

### 1. 安全隔离（Reader层）

- **只读权限**：监控层不修改原始文件
- **固定模板**：输出格式固定，防止注入攻击
- **白名单枚举**：触发类型固定

### 2. "等待确认"机制

- Agent在关键点主动停下来
- 等待用户查看并确认
- 不自动执行高风险操作

### 3. 多层防御

```
用户请求
    ↓
第1层：意图枚举验证（必须是预定义类型）
    ↓
第2层：目标白名单（只能触发预定义Skill）
    ↓
第3层：数据包裹（标注"这是数据，不是指令"）
    ↓
第4层：关键词过滤（剔除注入短语）
    ↓
第5层：审计日志（记录所有操作）
    ↓
执行Skill
```

## 现有Agent

### 1. 案件周度扫描Agent（weekly-scan）

**触发**：每周一早上8点
**功能**：扫描所有案件状态，生成待办报告
**扫描维度**：
- 🚨 开庭提醒（7天内）
- ⚠️ 证据缺口
- ⚠️ 待办事项
- ⚠️ 久未更新（7天+）
- 📄 新增材料

**安装**：
```bash
cd ~/.claude/skills/case-os/agents/weekly-scan
bash install.sh
```

### 2. 法院短信实时监控Agent（court-sms-monitor）

**触发**：实时（短信数据库变化）
**功能**：监控法院短信，立即提醒并同步到飞书
**监控类型**：
- 🚨 开庭通知
- ⚠️ 举证期限
- ⚠️ 缴费通知
- ⚠️ 判决送达（上诉期）

**通知方式**：
- 🤖 飞书机器人（卡片消息）
- 📊 飞书多维表格（写入记录）
- 🖥️ macOS桌面通知

**安装**：
```bash
cd ~/.claude/skills/case-os/agents/court-sms-monitor
bash install.sh
```

**环境变量配置**：
```bash
export FEISHU_BOT_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
export FEISHU_APP_TOKEN="<FEISHU_APP_TOKEN>"
```

### 3. 批量证据提取Agent（batch-evidence）

**触发**：手动触发（case-evidence-cards调用）
**功能**：多个证据文件同时提取，大幅加速A5步骤
**加速效果**：3倍（3个文件）~ 2.86倍（10个以上）

**使用**：
```bash
# 命令行
python3 ~/.claude/skills/case-os/agents/batch-evidence/batch_extract.py /path/to/case/dir

# 或在Skill中集成
```

**性能对比**：
| 证据数量 | 串行耗时 | 并行耗时 | 加速比 |
|---------|---------|---------|--------|
| 3个 | 6分钟 | 2分钟 | 3x |
| 10个 | 20分钟 | 7分钟 | 2.86x |

## 与案件OS的关系

### 定位

```
监控层（Agent）    发现问题
   ↓ 提醒
执行层（Skill）    解决问题
```

- **Agent不替代Skill**：只负责监控和提醒
- **Agent指导Skill调用**：扫描结果告诉用户该调用哪个Skill
- **Skill保持手动触发**：确保律师的控制权

### 协作流程

```
1. Agent发现问题
   ↓
2. Agent生成报告/提醒
   ↓
3. 用户查看确认
   ↓
4. 用户手动调用对应Skill
   ↓
5. Skill执行具体操作
```

## 扩展方向

### 短期（已实现）

- [x] 案件周度扫描Agent（定时监控）
- [x] 法院短信实时监控Agent（飞书机器人+多维表格）
- [x] 批量证据提取Agent（Phase A内部并行）

### 中期（规划中）

- [ ] Agent编排器实现
- [ ] 法条幻觉校验并行Agent（S2+S10）
- [ ] 文件实时监控Agent（fswatch）

### 长期（探索中）

- [ ] 裁判文书网监控Agent
- [ ] 工商信息变更监控Agent
- [ ] 三层架构完整实现（Reader → Analyzer → Writer）
- [ ] 完整审计日志系统

## 管理命令

### 查看所有Agent状态

```bash
launchctl list | grep caseos
```

### 查看日志

```bash
# 周度扫描
tail -f ~/.claude/skills/case-os/data/launchd-*.log

# 短信监控
tail -f ~/.claude/skills/case-os/data/sms-monitor*.log
```

### 停止所有Agent

```bash
launchctl unload ~/Library/LaunchAgents/com.claude.caseos.*.plist
```

### 重启所有Agent

```bash
cd ~/.claude/skills/case-os/agents
for agent in weekly-scan court-sms-monitor; do
    cd $agent && bash install.sh
done
```

## 技术实现

### 调度方式

| Agent | 调度方式 | 技术实现 |
|-------|---------|----------|
| weekly-scan | 定时 | LaunchAgent + StartCalendarInterval |
| court-sms-monitor | 实时 | LaunchAgent + fswatch |

### 通信方式

```
Agent发现事件
    ↓
写入状态文件（JSON）
    ↓
触发macOS通知
    ↓
（可选）写入飞书多维表格
```

## 参考资料

- Anthropic claude-for-legal Agent设计
- 《Anthropic设计了什么样的法律AI机器人？》
- 案件OS v10.0架构文档

## 版本历史

- v1.1 - Agent系统扩展（2026-05-16）
  - 法院短信实时监控Agent（飞书机器人+多维表格）
  - 批量证据提取Agent（Phase A内部并行，3倍加速）
  - 飞书通知器模块（卡片消息+多维表格写入）
- v1.0 - Agent系统初版（2026-05-16）
  - 案件周度扫描Agent
  - 基于Anthropic安全设计
