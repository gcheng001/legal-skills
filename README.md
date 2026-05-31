# Legal Skills for Claude Code

一套为律师和法律从业者设计的 Claude Code 技能集合，帮助自动化法律文书处理工作流。

## 技能列表

### 📋 court-sms — 法院短信识别与文书下载

收到法院送达短信时自动完成：**解析短信 → 下载文书 → 保存到桌面 → 提取关键日期 → 写入飞书**。

**触发条件**：消息包含法院名称 + 案号 + 送达平台链接（如 `zxfw.court.gov.cn`）

**功能**：
- 解析法院短信（文书送达 / 立案通知 / 开庭提醒）
- 从全国法院统一送达平台、广东电子送达、集约送达平台自动下载文书
- 文书原样保存到桌面，保留原始文件名
- 自动提取传票/开庭通知书中的关键日期
- 将开庭信息写入飞书多维表格

## 安装

### 前置依赖

| 依赖 | 说明 | 安装 |
|------|------|------|
| Python 3.9+ | 运行下载脚本 | 系统自带 |
| poppler | PDF 文本提取 | `brew install poppler` |
| lark-cli | 飞书 API 调用 | `npm install -g @larksuiteoapi/lark-cli` |

### 安装步骤

1. 克隆仓库：

```bash
git clone https://github.com/goacheng001/legal-skills.git
```

2. 复制配置文件：

```bash
cp config/feishu-config.example.json config/feishu-config.json
```

3. 编辑 `config/feishu-config.json`，填入你的飞书多维表格信息：

```json
{
  "app_token": "<你的飞书多维表格 App Token>",
  "table_name": "日程任务中枢",
  "table_id": "<你的表格 ID>"
}
```

4. 在 Claude Code 中配置技能路径（添加到项目的 CLAUDE.md 或全局配置）。

## 使用方法

### court-sms

收到法院短信后，直接将短信内容粘贴到 Claude Code 对话中：

```
【xx市人民法院】张三，您好！您有（2025）苏0981民初1234号案件文书送达，
请点击链接查收：https://zxfw.court.gov.cn/zxfw/...
```

技能会自动：
1. 解析短信，提取案号、法院、当事人
2. 从送达平台下载所有文书
3. 保存到 `~/Desktop/文书下载/{案号}/`
4. 提取传票/开庭通知的关键日期信息
5. 写入飞书多维表格

### 仅粘贴送达链接

也可以直接发送送达平台链接（无需完整短信），技能会从链接参数获取信息并下载文书。

## 项目结构

```
legal-skills/
├── SKILL.md                    # 技能主文件
├── config/
│   ├── feishu-config.example.json  # 飞书配置模板
│   └── config.json                 # 表格结构配置（需自建）
├── scripts/
│   └── download_sms_docs.py    # 文书下载脚本
├── references/                 # 解析规则和格式参考
├── archive/                    # 处理记录归档
├── CHANGELOG.md               # 变更日志
├── LICENSE.txt                # MIT 许可证
└── README.md                  # 本文件
```

## 飞书多维表格配置

技能将开庭信息写入飞书多维表格。需要创建一个包含以下字段的表格：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 事项 | Text | 主要标题（如"开庭审理"） |
| 任务内容 | Text | 法院名称 + 案由详情 |
| 开始时间 | DateTime | 开庭/宣判时间 |
| 截止时间 | DateTime | 截止日期 |
| 地点 | Text | 法庭/地点 |
| 备注 | Text | 备注信息 |
| 来源 | Text | 来源标识 |
| 优先级 | SingleSelect | 高 / 中 / 低 |

飞书 CLI 首次使用需登录认证（通过 Keychain 持久化）。

## 支持的送达平台

| 平台 | 域名 | 下载方式 |
|------|------|----------|
| 全国法院统一送达平台 | `zxfw.court.gov.cn` | API 直连 |
| 广东法院电子送达 | `sd.gdems.com` | 浏览器自动化 |
| 集约送达平台 | `jysd.10102368.com` | 浏览器自动化 |

## 贡献

欢迎提交 Issue 和 Pull Request，添加新的法律相关技能或改进现有功能。

## 许可证

MIT License — 详见 [LICENSE.txt](LICENSE.txt)
