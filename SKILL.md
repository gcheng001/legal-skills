---
name: court-sms
homepage: https://github.com/goacheng001/legal-skills
author: 高澄（微信cheng715)
version: "2.0.0"
license: MIT
description: 本技能应在用户收到法院短信（文书送达、立案通知、开庭提醒等）时使用。TRIGGER: 短信含法院名称 + 案号 + zxfw.court.gov.cn/sd.gdems.com/jysd.10102368.com 任一送达平台链接 → 立即调用此 skill，不先尝试 WebFetch/pkulaw/其他工具。下载到 ~/Desktop/文书下载/，原样保存不删不改，仅对传票/开庭通知提取关键信息写飞书。
---

# 法院短信识别与文书下载

## 核心原则（强制执行）

1. **触发即调用**：消息含法院名称 + 案号 + 送达平台链接（zxfw.court.gov.cn / sd.gdems.com / jysd.10102368.com）→ 立即调用本 skill，不绕路
2. **下载到桌面**：所有文件下载到 `~/Desktop/文书下载/{案号}/`，不放到案件目录
3. **原样保存，同名去重**：保留 API 返回的原始文件名，不删除、不整理、不合并。如同名文件已存在，追加 `_2`、`_3` 后缀防止覆盖
4. **只提取关键文书**：仅对传票和开庭/出庭通知书提取关键信息写飞书，其他文书不读不总结

## 功能概述

处理法院短信的完整流程：**粘贴短信 → 解析内容 → 下载文书 → 原样保存到桌面 → 仅提取传票/开庭通知关键日期 → 写入飞书**。

支持两种触发方式：

**方式一：粘贴短信原文**

```text
收到法院短信，内容如下：
【xx市人民法院】张三，您好！您有（2025）苏0981民初1234号案件文书送达，请点击链接查收：https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=DEMO1&sdbh=DEMO2&sdsin=DEMO3
```

**方式二：直接发送送达链接**

用户可能直接粘贴送达链接（非完整短信文本），此时跳过短信文本解析，直接从 URL 中提取 `qdbh`、`sdbh`、`sdsin` 参数，进入第三步下载流程。

```text
https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=xxx&sdbh=xxx&sdsin=xxx
```

## 短信类型分类

| 类型 | 特征 | 含下载链接 | 处理方式 |
| --- | --- | --- | --- |
| 文书送达 | 含送达平台链接 + 案号 | 是 | 下载文书并归档到案件目录 |
| 立案通知 | 含"已立案"等关键词 | 可能有 | 展示解析结果 |
| 信息通知 | 无链接，纯信息 | 否 | 展示解析结果 |

**支持的送达平台**：`zxfw.court.gov.cn`（全国）、`sd.gdems.com`（广东）、`jysd.10102368.com`（集约送达）。详见 `references/sms-patterns.json`。

---

## 工作流（五步）

### 第一步：输入解析

1. 读取 `references/sms-patterns.json` 作为解析参考
2. **判断输入类型**：
   - **完整短信**：包含法院签名（如 `【xx法院】`）+ 正文 + 链接 → 完整解析流程
   - **纯链接**：用户直接发送送达 URL（如 `https://zxfw.court.gov.cn/...?qdbh=xxx&sdbh=xxx&sdsin=xxx`）→ 跳过短信文本解析，直接从 URL 提取参数，进入第三步下载。案号、当事人等信息在下载文书后从文书内容中提取。
3. 对用户粘贴的短信文本进行分析（纯链接输入跳过此步）：

**a) 短信分类**：根据关键词判断类型
- 文书送达：包含 zxfw.court.gov.cn 链接
- 立案通知：包含"已立案"、"立案通知"等
- 信息通知：其他

**b) 案号提取**：使用正则 `[（(〔[]\d{4}[）)〕]]` 匹配标准案号格式

标准案号格式示例：
- `（2025）苏0981民初1234号`
- `(2024)粤0604执保5678号`
- `〔2025〕京0105民初901号`

**c) 当事人提取**：从短信文本初步识别，最终以文书内容为准
- **注意**：短信中的称呼（如"张三，您好"）仅为短信接收人，不作为案件当事人
- 公司名称：`xx有限责任公司`、`xx有限公司`、`xx股份有限公司`
- 诉讼对峙：`A与B`、`A诉B`、`原告A 被告B`
- 角色前缀：`原告：xxx`、`被告：xxx` 等
- 下载文书后，以起诉状、传票中的当事人信息为准，覆盖短信阶段的初步判断

**d) 下载链接提取**：识别短信中的送达平台链接并提取参数

| 平台 | 域名 | 下载方式 | 提取参数 |
|------|------|----------|----------|
| 全国法院统一送达平台 | `zxfw.court.gov.cn` | curl API 直连 | qdbh, sdbh, sdsin |
| 广东法院电子送达 | `sd.gdems.com` | 浏览器自动化 | 路径中的送达标识码 |
| 集约送达平台 | `jysd.10102368.com` | 浏览器自动化 | key |

> **排除列表**：法院名称、法官姓名、地名、法律术语等不应作为当事人提取。详见 `sms-patterns.json` → `party_extraction.exclude_keywords`。

**输出格式**（向用户展示）：

```text
📋 短信解析结果：
- 类型：文书送达
- 案号：（2025）苏0981民初1234号
- 当事人：张三、xx有限公司
- 下载链接：已提取（zxfw.court.gov.cn）
```

### 第二步：确定下载目录

固定下载到桌面：`~/Desktop/文书下载/{案号}/`

- `{案号}` 使用短信中提取的案号，示例：`（2026）苏0692民初552号`
- 目录不存在则自动创建
- **不扫描案件目录，不询问用户，直接使用此固定路径**

### 第三步：文书下载

> **平台判断**：根据第一步识别的链接域名，选择下载策略。
> - `zxfw.court.gov.cn` → 方案一（API 直连）→ 方案二 → 方案三
> - `sd.gdems.com` 或 `jysd.10102368.com` → 跳过方案一，直接方案二 → 方案三
> - 未知域名 → 提示用户提供链接信息
>
> **⛔ 降级铁律**：严格串行，禁止并行。当前方案成功即停止，绝不降级。禁止"双保险"并行尝试多个方案。

#### 依赖

| 依赖 | 用途 | 适用方案 | 安装方式 |
|------|------|----------|----------|
| `curl` | API 下载 | 方案一 | macOS/Linux 预装 |
| `jq` | JSON 解析（可选） | 方案一 | `brew install jq` |
| Playwright | 浏览器自动化 | 方案二/三 | 见下方 |

**Playwright 安装指引**（仅方案二/三需要）：

```bash
# 方案二: Playwright CLI
npm install -g playwright
npx playwright install chromium

# 方案三: Playwright MCP（需在 Claude Code 设置中配置）
# 在 settings.json 的 mcpServers 中添加：
# "playwright": { "command": "npx", "args": ["@anthropic-ai/mcp-playwright"] }
```

> **⛔ 大多数情况下不需要 Playwright**：zxfw 平台方案一直接 curl 调用 API，无需浏览器。仅 gdems/jysd 平台或**方案一失败后**才需要方案二/三。禁止在方案一执行期间同时打开浏览器。

#### 方案一 — API 直连（优先）

完全无头，无需浏览器。直接调用 zxfw 后端 API 获取文书下载链接，再用 curl 下载 PDF。

**API 信息**：

- 端点：`POST https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew`
- Content-Type：`application/json`
- 请求体：`{ "qdbh": "xxx", "sdbh": "xxx", "sdsin": "xxx" }`（从短信 URL 提取）
- 响应字段：`data[].c_wsmc`（文书名称）、`data[].wjlj`（OSS 签名下载链接）、`data[].c_fymc`（法院名称）
- 无需认证、无需浏览器

```bash
# 1. 从短信 URL 提取参数（示例）
qdbh="DEMO_qdbh_value"
sdbh="DEMO_sdbh_value"
sdsin="DEMO_sdsin_value"

# 2. 调用 API 获取文书列表
mkdir -p /tmp/court-sms-staging/
resp=$(curl -s -X POST "https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew" \
  -H "Content-Type: application/json" \
  -d "{\"qdbh\":\"$qdbh\",\"sdbh\":\"$sdbh\",\"sdsin\":\"$sdsin\"}")

# 3. 解析文书列表，逐个下载 PDF
echo "$resp" | jq -r '.data[] | "\(.c_wsmc)\t\(.wjlj)"' | while IFS=$'\t' read -r name url; do
  curl -sL -o "/tmp/court-sms-staging/${name}.pdf" "$url"
done

# 4. 验证下载结果
ls -lh /tmp/court-sms-staging/*.pdf
```

#### 方案二 — 无头浏览器（Playwright CLI）

当方案一 API 不可用或链接过期时，用 Playwright CLI 无头模式打开页面，拦截网络请求获取下载链接。

```bash
# 需要先安装 playwright
npx playwright install chromium 2>/dev/null

# 无头模式运行（脚本需自行编写，拦截 getWsListBySdbhNew API 响应）
node scripts/download_court_docs.mjs --url "{短信链接}" --output /tmp/court-sms-staging/
```

#### 方案三 — 交互式浏览器（Playwright MCP）

当方案二不可用时（需要已配置 Playwright MCP）：

```text
1. browser_navigate → 打开短信中的 zxfw URL
2. 等待页面加载
3. browser_evaluate → 直接调用 fetch API 获取文书列表
4. browser_run_code → 下载 PDF 文件到 /tmp/court-sms-staging/
```

如 API 调用未成功，改用页面交互：

```text
1. browser_snapshot → 查看当前页面结构
2. 找到文书列表或 PDF 预览区域
3. 定位下载按钮（可能在 iframe 内）
4. browser_click → 点击下载
5. 等待下载完成，保存到临时目录
```

#### 失败兜底

当三级均失败时：

```text
⚠️ 自动下载失败，请手动访问以下链接下载：
{原始链接}

下载后请将文件放到对应案件目录中。

我将为您创建待处理记录。
```

### 第四步：保存到桌面

1. **确定目标目录**：`~/Desktop/文书下载/{案号}/`
2. **保存文件**：将临时目录中的所有文件（PDF + MP4 等）复制到目标目录
3. **同名处理**：保留 API 返回的原始文件名；如同名文件已存在，追加 `_2`、`_3` 后缀（检测文件大小，大小相同则为真重复跳过，大小不同则为同名异内容保留）
4. **不做任何删减**：不删除文件、不重命名、不整理子目录、不合并 PDF。API 返回多少就保留多少
5. **写入内部记录**：保存本次处理的元信息到 `archive/` 目录

### 第五步：关键文书提取与飞书写入

> **仅提取传票和开庭/出庭通知书**，其他文书（举证通知、判决书、裁定书等）不读取、不总结。

#### 依赖

| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| `pdftotext` | PDF 文本提取 | `brew install poppler` |
| `lark-cli` | 飞书 API 调用 | `npm install -g @larksuiteoapi/lark-cli` |

#### 配置

在 `config/feishu-config.json` 中配置飞书多维表格信息（不存在则创建）：

```json
{
  "app_token": "LLyLbvBSMaN3VJslA4Dcd9dCnSb",
  "table_name": "日程任务中枢",
  "table_id": "tblVEFh7rLdakiSS"
}
```

> **实测经验（2026-05-19）**：
> - ✅ 使用字段名（中文）写入：`{"fields": {"事项": "xxx", "优先级": "高"}}`
> - ❌ 使用 field_id 写入会报错 FieldNameNotFound
> - 单选字段直接用选项名"高"/"中"/"低"
> - 日期时间字段传毫秒时间戳

#### 文书类型识别（仅两种）

| 文书类型 | 识别关键词 | 必须提取的信息 |
|---------|-----------|---------------|
| **传票** | 标题含"传票" | 开庭时间、地点、法庭、案号、案由 |
| **开庭通知书/出庭通知书** | 标题含"开庭通知"或"出庭通知" | 开庭/宣判时间、地点、法庭、案号 |

> 其他文书类型（举证通知、缴费通知、判决书、裁定书、调解书、执行通知等）一概跳过，不读取 PDF 内容。

#### 提取方式

1. 扫描目标目录文件名，找到标题含"传票"或"开庭通知"或"出庭通知"的 PDF
2. 用 `pdftotext` 提取文本（前 500 字符即可）
3. 正则匹配日期时间、地点、案号等信息
4. 写入飞书

#### 写入飞书多维表格

```bash
APP_TOKEN="LLyLbvBSMaN3VJslA4Dcd9dCnSb"
TABLE_ID="tblVEFh7rLdakiSS"

timestamp=$(date -j -f "%Y-%m-%d %H:%M" "2026-06-04 14:00" "+%s")000

lark-cli api POST "/open-apis/bitable/v1/apps/${APP_TOKEN}/tables/${TABLE_ID}/records" \
  --as user \
  --data '{
    "fields": {
      "事项": "开庭审理（2026）苏0692民初552号",
      "任务内容": "南通通州湾江海联动开发示范区人民法院 - 万邦-季军劳务合同纠纷",
      "开始时间": '"$timestamp"',
      "地点": "第四法庭",
      "来源": "法院短信",
      "优先级": "高"
    }
  }'
```

#### 写入飞书多维表格

使用 `lark-cli` 写入记录：

```bash
# 读取配置（实际项目中从 config/feishu-config.json 读取）
APP_TOKEN="LLyLbvBSMaN3VJslA4Dcd9dCnSb"
TABLE_ID="tblVEFh7rLdakiSS"

# 将日期时间转换为毫秒时间戳（macOS date 命令）
timestamp=$(date -j -f "%Y-%m-%d %H:%M" "2026-05-22 14:40" "+%s")000

# 写入飞书多维表格
# ⚠️ 重要：使用【字段名】而非 field_id，单选字段用选项名而非 option ID
lark-cli api POST "/open-apis/bitable/v1/apps/${APP_TOKEN}/tables/${TABLE_ID}/records" \
  --as user \
  --data '{
    "fields": {
      "事项": "公开宣判（2026）浙0304刑初347号",
      "任务内容": "温州市瓯海区人民法院 - 尚家进、张紫源开设赌场罪",
      "开始时间": '"$timestamp"',
      "地点": "第四审判庭",
      "来源": "法院短信",
      "优先级": "高"
    }
  }'
```

**字段映射参考（日程任务中枢）**：

| 字段名 | 字段ID | 类型 | 说明 |
|--------|--------|------|------|
| 事项 | fldSAKBW7G | Text | 主要标题 |
| 任务内容 | fldXQrmu9c | Text | 详细描述 |
| 开始时间 | fld08Jn28a | DateTime | 开始时间（含时分） |
| 截止时间 | fld9Oy0o4k | DateTime | 截止日期（仅日期） |
| 地点 | fldBZxRkOG | Text | 地点/法庭 |
| 备注 | fldrPV4xbx | Text | 备注信息 |
| 来源 | fldlcmmODX | Text | 来源标识 |
| 优先级 | fldp66GC1l | SingleSelect | 选项：高/中/低 |

> **实测经验（2026-05-19）**：
> - ✅ 使用字段名（中文）写入成功
> - ✅ 单选字段直接用"高"/"中"/"低"
> - ✅ 日期时间毫秒时间戳格式正确
> - `lark-cli` 认证通过 Keychain 持久化

#### 向用户汇报

提取完成后，向用户展示结构化报告：

```text
📅 关键日期信息已提取并写入飞书：

┌─────────────────────────────────────────────────────────────┐
│ 案号：（2026）浙0304刑初347号                                │
│ 法院：温州市瓯海区人民法院                                    │
│ 当事人：尚家进、张紫源                                        │
├─────────────────────────────────────────────────────────────┤
│ ⚠️  2026-05-22 14:40  —  开庭审理  —  第四审判庭            │
└─────────────────────────────────────────────────────────────┘

✅ 已写入飞书多维表格（表格：日程任务中枢）
```

#### 向用户汇报（归档）

按 [`references/report-format.md`](references/report-format.md) 输出结构化报告
- 先确认归档完成（案号、法院、当事人、案由、文件数、位置）
- 列出所有已归档的文书清单
- **展示关键日期信息汇总**（如有）
- 如含传票/开庭通知，⚠️ 高亮提醒时间、地点
- 如部分失败，列出失败文书和原始链接

---

## 内部归档格式

每次处理完成后在 `archive/` 下创建 JSON 记录，格式详见 [`references/archive-format.md`](references/archive-format.md)。

---

## 常见法院短信格式参考

### 文书送达短信

```text
【xx市人民法院】张三，您好！您有（2025）苏0981民初1234号案件文书送达，
请点击链接查收：
https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=DEMO1&sdbh=DEMO2&sdsin=DEMO3
如非本人操作请联系法院。
```

### 立案通知短信

```text
【xx市xx区人民法院】您好，您提交的立案材料已审核通过。
案号：（2025）京0105民初54321号
请及时缴纳诉讼费用。
```

### 开庭提醒短信

```text
【xx市xx区人民法院】提醒：您有（2025）苏0508民初567号案件，
定于2025年3月15日上午9:30在第3法庭开庭，请准时到庭。
```

---

## 故障排除

| 问题 | 解决方案 |
| --- | --- |
| 短信无法识别类型 | 展示原文，请用户确认类型后继续 |
| 案号提取失败 | 手动输入案号 |
| 当事人识别不准 | 提示用户确认/修正当事人列表 |
| Playwright 下载超时 | 检查网络连接，尝试刷新页面重试 |
| 页面需要验证码 | 通知用户，暂停等待手动处理 |
| 下载文件损坏 | 清理临时目录，重新尝试下载 |
| 桌面目录创建失败 | 检查磁盘空间和权限 |
| 飞书写入失败 FieldNameNotFound | 使用字段名（中文）而非 field_id |
| 飞书认证失败 | 首次使用需登录，lark-cli 通过 Keychain 持久化 |

---

## 配置

无额外配置需求。解析规则参考 `references/sms-patterns.json`。

如需修改解析规则（添加新文书标题、调整正则等），编辑该 JSON 文件即可。

飞书配置见 `config/feishu-config.json`。

---

## 🔄 变更历史

完整变更日志见 [CHANGELOG.md](CHANGELOG.md)。归属声明见 [references/ATTRIBUTION.md](references/ATTRIBUTION.md)。
