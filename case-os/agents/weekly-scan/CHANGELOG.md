# 案件周度扫描Agent - 设计文档

## 设计目标

基于Anthropic claude-for-legal的Agent设计理念，为案件OS添加**第一层自动化**——定时监控Agent。

## 核心设计原则

### 1. 安全隔离（Reader层）

```python
# ✅ 只读权限
permissions:
  read: true
  write: false
  network: false
```

**设计依据**：文章强调的"三层架构"
- Reader层：只读原始文档，无网络访问
- 防止Prompt Injection：合同中的指令无法被执行
- 数据泄露防护：无法访问攻击者控制的URL

### 2. "等待确认"机制

```python
print("⏸️  扫描完成，等待用户确认...")
```

**设计依据**：文章第3节核心观点
> "呈现，等待确认不是一个技术细节，而是一个设计选择"

Agent在关键点主动停下来，等人类补充上下文。这符合案件OS的"确认点"设计哲学。

### 3. 固定模板防御

```python
def format_urgent_item(item: Dict) -> List[str]:
    """格式化紧急项"""
    if item["type"] == "court_reminder":
        return [
            f"### {item['case']} - 开庭提醒",
            # ... 固定格式
        ]
```

**设计依据**：文章第5节的移交请求验证
> "发给下一个Agent的指令怎么生成：不是从Agent的输出里拼接出来的，而是用固定模板渲染的"

报告格式完全固定，防止数据注入攻击。

### 4. 白名单枚举

```python
# 扫描维度固定枚举
SCAN_DIMENSIONS = [
    "court_reminder",   # 开庭提醒
    "evidence_gap",     # 证据缺口
    "pending_task",     # 待办事项
    "stale",            # 久未更新
    "new_files",        # 新增文件
]
```

**设计依据**：文章第8节五层防线第1层
> "意图必须是固定枚举列表里的值。不在列表里的直接拒绝。"

## 与案件OS的关系

```
案件OS架构：
┌─────────────────────────────────────┐
│  定时监控Agent（新增）               │
│  - weekly-scan: 周度扫描            │
│  - future: 实时提醒                 │
└─────────────────────────────────────┘
           ↓ 提醒
┌─────────────────────────────────────┐
│  手动Skill（现有）                  │
│  - A1-A6: Phase A                  │
│  - S1-S10: Phase B                 │
│  - 其他工具Skill                   │
└─────────────────────────────────────┘
```

**定位**：
- Agent是**监控层**，发现问题
- Skill是**执行层**，解决问题
- Agent不替代Skill，而是指导何时调用哪个Skill

## 技术实现

### 调度方式

使用macOS的LaunchAgent（类似Linux的cron）：

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key>
    <integer>1</integer>   <!-- 周一 -->
    <key>Hour</key>
    <integer>8</integer>   <!-- 8点 -->
</dict>
```

### 文件结构

```
agents/weekly-scan/
├── AGENT.md          # Agent配置文件
├── scan.py           # 扫描实现
├── install.sh        # 安装脚本
├── README.md         # 使用说明
└── CHANGELOG.md      # 设计文档（本文件）
```

### 数据流

```
案件文件夹
    ↓ (读取)
scan.py (Reader + Analyzer)
    ↓ (生成)
Markdown报告
    ↓ (保存)
桌面报告文件
```

## 扫描逻辑详解

### 1. 发现案件

遍历扫描根目录，查找包含`CLAUDE.md`的文件夹：
```python
for item in root.rglob("CLAUDE.md"):
    case_dir = item.parent
    cases.append(CaseItem(case_dir.name, case_dir))
```

### 2. 检查开庭提醒

从`_archive/court-sms.json`读取开庭信息，筛选7天内的：
```python
if 0 <= days_until <= 7:
    upcoming.append({...})
```

### 3. 检查证据缺口

扫描证据卡片库，查找标记为"待补充"的：
```python
if re.search(r'\[待补充\]|\[缺失\]|\[待提供\]', content):
    gaps.append(file.stem)
```

### 4. 检查待办事项

从`阶段追踪.md`提取未完成的checkbox：
```python
if re.match(r'^- \[ \]', line):
    pending.append(line.strip()[6:])
```

### 5. 检查久未更新

对比CLAUDE.md的修改时间：
```python
days_since = (datetime.now() - last_update).days
if days_since >= 7:
    results.warning.append(...)
```

## 报告格式

```markdown
# 案件周度扫描报告

**扫描时间**：2026-05-16 08:00
**扫描范围**：X个案件

## 🚨 紧急待办（需要立即处理）
### [案件名称] - 开庭提醒
- 开庭时间：2026-05-20 14:00
- 法院：XX法院
- 距离：3天

## ⚠️ 本周待办（建议本周处理）
### [案件名称] - 证据缺口
- 缺失证据：XX合同

## 📄 新增材料（本周）
### [案件名称]
- 新增：XX证据.pdf

---
**下次扫描时间**：2026-05-23 08:00
```

## 扩展方向

### 短期（v1.1）
- [ ] 添加命令行参数（手动指定扫描路径）
- [ ] 支持多个扫描根目录配置
- [ ] 添加飞书/邮件通知

### 中期（v2.0）
- [ ] 实时监控（fswatch监控文件变化）
- [ ] 裁判文书网监控（新判决提醒）
- [ ] 工商信息变更监控

### 长期（v3.0）
- [ ] Agent协作编排器（类似orchestrate.py）
- [ ] 多层Agent架构（Reader → Analyzer → Writer分离）
- [ ] 审计日志系统

## 版本历史

- v1.0 - 初始版本（2026-05-16）
  - 周度定时扫描
  - 5个扫描维度
  - LaunchAgent调度
  - Markdown报告生成

## 参考资料

- Anthropic claude-for-legal Agent设计
- 《Anthropic设计了什么样的法律AI机器人？》
- 案件OS v10.0架构文档
