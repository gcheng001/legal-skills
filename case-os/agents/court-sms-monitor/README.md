# 法院短信实时监控Agent

> 实时监控iOS短信数据库，发现法院相关短信后立即提醒并同步到飞书多维表格

## 功能概述

### 监控内容

| 类型 | 关键词 | 提取信息 | 紧急度 |
|------|--------|----------|--------|
| 开庭通知 | 开庭、庭审、传票 | 开庭时间、法院、案号 | 🚨 最高 |
| 举证期限 | 举证、证据交换 | 举证截止日期 | ⚠️ 高 |
| 缴费通知 | 缴费、诉讼费 | 缴费截止日期、金额 | ⚠️ 高 |
| 判决送达 | 判决、裁定、送达 | 送达日期、上诉期（15天） | ⚠️ 高 |

### 工作流程

```
收到新短信
    ↓
识别法院短信（关键词匹配）
    ↓
提取关键信息（案号、日期、法院）
    ↓
匹配案件（自动识别属于哪个案件）
    ↓
保存到案件档案（_archive/court-sms.json）
    ↓
同步到飞书多维表格
    ↓
发送桌面通知
```

## 安装步骤

### 前置要求

1. **Python 3**
2. **fswatch**（文件监控工具）
3. **Homebrew**（用于安装fswatch）

### 安装命令

```bash
cd ~/.claude/skills/case-os/agents/court-sms-monitor
bash install.sh
```

安装脚本会自动：
1. 检查并安装fswatch
2. 创建LaunchAgent配置
3. 启动实时监控

## 使用方法

### 自动运行（推荐）

LaunchAgent会在后台自动运行：
- 实时监控`~/Library/SMS/sms.db`
- 发现新短信立即处理
- 无需手动操作

### 手动测试

```bash
python3 monitor.py
```

### 查看日志

```bash
# 查看完整日志
tail -f ~/.claude/skills/case-os/data/sms-monitor.log

# 查看标准输出
tail -f ~/.claude/skills/case-os/data/sms-monitor-stdout.log

# 查看错误输出
tail -f ~/.claude/skills/case-os/data/sms-monitor-stderr.log
```

## 飞书同步

### 配置

创建环境变量：
```bash
export FEISHU_APP_TOKEN="<FEISHU_APP_TOKEN>"
```

或写入`~/.bashrc`/`~/.zshrc`：
```bash
echo 'export FEISHU_APP_TOKEN="<FEISHU_APP_TOKEN>"' >> ~/.zshrc
source ~/.zshrc
```

### 写入字段

| 字段 | 说明 |
|------|------|
| 案件名称 | 自动匹配的案件名称 |
| 提醒类型 | 开庭通知/举证期限/缴费通知/判决送达 |
| 截止时间 | 提取的日期时间 |
| 法院 | 提取的法院名称 |
| 案号 | 提取的案号 |
| 详情 | 短信内容摘要 |
| 状态 | 默认"待处理" |

## 卸载

```bash
# 停止LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.claude.caseos.sms-monitor.plist

# 删除配置文件
rm ~/Library/LaunchAgents/com.claude.caseos.sms-monitor.plist

# 删除监控脚本
rm ~/.claude/skills/case-os/data/sms-monitor-wrapper.sh
```

## 案件匹配逻辑

### 匹配顺序

1. **通过案号匹配**：最准确
2. **通过法院名称匹配**：次选
3. **通过当事人名称匹配**：备选

### 未匹配处理

如果无法识别案件，会：
1. 在日志中记录
2. 显示"未找到匹配案件"警告
3. TODO：保存到未分类记录供人工确认

## 提醒规则

### 开庭通知

- 提前3天：第一次提醒
- 提前1天：第二次提醒
- 当天早上：第三次提醒

### 举证期限

- 提前3天：第一次提醒
- 提前1天：第二次提醒
- 截止当天：第三次提醒

### 判决送达（上诉期）

- 收到当天：立即提醒
- 第10天：提醒上诉期过半
- 第13天：最后提醒（还剩2天）

## 技术实现

### 文件监控

使用`fswatch`监控短信数据库变化：
```bash
fswatch -o ~/Library/SMS/sms.db | xargs -n1 python3 monitor.py
```

### 短信解析

- 正则表达式提取案号、日期、时间、法院
- 关键词匹配识别短信类型
- 自动计算上诉期（判决+15天）

### 数据存储

- 监控状态：`~/.claude/skills/case-os/data/sms-monitor-state.json`
- 案件档案：`<案件路径>/_archive/court-sms.json`

## 安全设计

### 只读访问

- 只读取短信数据库，不修改
- 不访问短信内容之外的敏感数据

### 本地处理

- 所有处理在本地完成
- 短信内容不会上传到外部服务器

### 权限控制

- macOS需要授权访问短信数据库
- 首次运行时系统会提示授权

## 故障排除

### 问题：无法读取短信数据库

**原因**：没有授权访问短信

**解决**：
1. 系统偏好设置 → 隐私与安全性 → 完全磁盘访问权限
2. 添加Terminal或允许Python访问

### 问题：fswatch未安装

**解决**：
```bash
brew install fswatch
```

### 问题：飞书同步失败

**检查**：
1. 环境变量是否设置：`echo $FEISHU_APP_TOKEN`
2. 网络连接是否正常
3. 飞书API权限是否正确

## 版本历史

- v1.0 - 初始版本（2026-05-16）
  - 实时监控短信数据库
  - 4种短信类型识别
  - 自动案件匹配
  - 飞书多维表格同步
  - macOS桌面通知
