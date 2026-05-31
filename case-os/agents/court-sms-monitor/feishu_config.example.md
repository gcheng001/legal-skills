# 飞书配置说明

## 飞书机器人Webhook获取

### 1. 创建飞书机器人

1. 打开飞书
2. 进入群聊（或创建新群）
3. 点击群设置 → 群机器人 → 添加机器人
4. 选择"自定义机器人"
5. 设置机器人名称和头像
6. 获取Webhook URL

### 2. 配置Webhook

将Webhook URL添加到环境变量：

```bash
# 方式1：临时设置（当前会话）
export FEISHU_BOT_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# 方式2：永久设置（写入shell配置）
echo 'export FEISHU_BOT_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"' >> ~/.zshrc
source ~/.zshrc
```

## 飞书多维表格配置

### 1. 获取App Token

1. 打开飞书多维表格
2. 点击表格右上角"..."
3. 选择"获取表格链接"
4. 从链接中提取App Token：
   ```
   https://example.feishu.cn/base/APP_TOKEN/...
   ```

### 2. 配置App Token

```bash
export FEISHU_APP_TOKEN="<FEISHU_APP_TOKEN>"
```

### 3. 创建表格字段（可选）

在多维表格中创建以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 案件名称 | 文本 | 案件名称 |
| 提醒类型 | 单选 | 开庭通知/举证期限/缴费通知/判决送达 |
| 截止时间 | 日期 | 截止日期时间 |
| 法院 | 文本 | 法院名称 |
| 案号 | 文本 | 案件编号 |
| 短信内容 | 文本 | 短信原文 |
| 收到时间 | 日期 | 收到短信的时间 |
| 状态 | 单选 | 待处理/已处理/已忽略 |
| 创建时间 | 日期 | 记录创建时间 |

## 测试配置

### 测试机器人消息

```bash
# 发送测试消息
curl -X POST "$FEISHU_BOT_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{
    "msg_type": "text",
    "content": {"text": "测试消息：法院短信监控Agent已配置"}
  }'
```

### 测试短信监控

```bash
# 手动运行短信监控
python3 ~/.claude/skills/case-os/agents/court-sms-monitor/monitor.py
```

## 故障排除

### 问题：机器人消息发送失败

**检查**：
1. Webhook URL是否正确
2. 网络连接是否正常
3. 飞书群是否存在

**解决**：
```bash
# 测试Webhook
curl -v -X POST "$FEISHU_BOT_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试"}}'
```

### 问题：多维表格写入失败

**原因**：多维表格写入需要飞书开放平台API权限

**当前状态**：基础版本中，多维表格写入功能为预留接口

**后续实现**：
- 飞书开放平台应用认证
- OAuth授权流程
- API调用实现

### 临时解决方案

如果不配置飞书，Agent仍然可以：
- ✅ 保存到案件档案（`_archive/court-sms.json`）
- ✅ 发送macOS桌面通知
- ❌ 不发送飞书消息（跳过）
