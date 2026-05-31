# 案件周度扫描Agent

> 安全设计：只读扫描，无写入权限，无网络访问

## 功能概述

每周一早上8点自动扫描所有案件，生成待办提醒报告。

### 扫描维度

1. **🚨 紧急待办**（需要立即处理）
   - 开庭提醒（7天内）

2. **⚠️ 本周待办**（建议本周处理）
   - 证据缺口（标记为"待补充"的证据）
   - 待办事项（阶段追踪.md中的未完成项）
   - 久未更新（7天以上未更新的案件）

3. **📄 新增材料**（信息记录）
   - 本周新增的案件材料

## 安装步骤

```bash
cd ~/.claude/skills/case-os/agents/weekly-scan
bash install.sh
```

## 手动测试

```bash
python3 scan.py
```

## 查看日志

```bash
# 标准输出
tail -f ~/.claude/skills/case-os/data/launchd-stdout.log

# 错误输出
tail -f ~/.claude/skills/case-os/data/launchd-stderr.log
```

## 卸载

```bash
launchctl unload ~/Library/LaunchAgents/com.claude.caseos.weekly-scan.plist
rm ~/Library/LaunchAgents/com.claude.caseos.weekly-scan.plist
```

## 报告位置

每次扫描后，报告会保存到桌面：
```
~/Desktop/案件周度扫描报告-2026-05-16.md
```

## 安全设计

基于Anthropic claude-for-legal的三层架构：

| 层级 | 职责 | 权限 |
|------|------|------|
| Reader | 读取案件文件 | ✅ 只读 |
| Analyzer | 分析状态、生成报告 | ✅ 只读 |
| Writer | 保存报告到桌面 | ✅ 只写（固定路径） |

**禁止**：
- ❌ 修改原始案件文件
- ❌ 连接外部网络
- ❌ 执行任意操作指令

## 设计启发

来自Anthropic claude-for-legal的Agent设计：

1. **"等待确认"机制**：扫描完成后停止，等待用户查看报告
2. **只读隔离**：Reader层不接触写入，防止Prompt Injection
3. **固定模板**：报告格式固定，防止数据注入攻击
4. **审计日志**：所有扫描操作记录在日志文件中

## 与案件OS集成

该Agent是案件OS的**第一层自动化**：
- 不替代手动触发的Skill（如case-ocr、case-dashboard）
- 作为**监控层**，提醒需要跟进的工作
- 扫描结果可以指导用户调用哪个Skill

## 后续扩展

可以添加的扫描维度：
- 法院短信监控（实时）
- 裁判文书网监控（新判决）
- 工商信息变更监控（当事人）
- 法律法规更新监控

## 版本历史

- v1.0 - 初始版本（2026-05-16）
