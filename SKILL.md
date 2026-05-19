---
name: court-sms
homepage: https://github.com/goacheng001/legal-skills
author: 高澄（微信cheng715)
version: "1.5.0"
license: MIT
description: 本技能应在用户收到法院短信（文书送达、立案通知、开庭提醒等）时使用，自动提取案号、当事人、下载链接，下载文书并归档到对应案件目录，**自动总结文件内容、提取关键日期信息并写入飞书多维表格**。**唯一版本，已整合 case-court-sms 功能**。
---

# 法院短信识别与文书下载

## 功能概述

处理法院短信的完整流程：**粘贴短信 → 解析内容 → 匹配案件 → 下载文书 → 总结内容 → 归档保存 → 提取关键日期 → 写入飞书多维表格**。

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

## 工作流（七步）

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

### 第二步：确定归档目录

1. **扫描当前工作目录**：识别目录结构，找到与短信案号或当事人匹配的案件目录
2. **查找归档子目录**：在匹配到的案件目录下，查找法院文书相关的子目录（如 `08*`、`法院送达`、`court` 等）
3. 如未找到匹配案件，询问用户选择归档位置或暂存

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

### 第四步：文件内容总结

> **核心功能**：下载完成后，自动读取每份文书的内容，生成结构化总结报告，让用户快速了解文书要点。

#### 依赖

| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| `pdftotext` | PDF 文本提取 | `brew install poppler` |

#### 总结规则

根据文书类型，提取不同维度的信息：

**1. 传票/开庭传票/出庭通知书**
```
📋 文书：传票
├─ 案号：（2026）浙0304刑初347号
├─ 法院：温州市瓯海区人民法院
├─ 当事人：尚家进、张紫源（被告人）
├─ 案由：开设赌场罪
├─ 事项：公开宣判
├─ 时间：2026年05月22日 14:40
└─ 地点：第四审判庭
```

**2. 起诉状/公诉书**
```
📋 文书：起诉状
├─ 案号：（2026）浙0304民初123号
├─ 原告：张三
├─ 被告：李四有限公司
├─ 案由：买卖合同纠纷
├─ 诉讼请求：
│  1. 判令被告支付货款人民币100,000元
│  2. 判令被告支付逾期付款违约金
│  3. 诉讼费用由被告承担
└─ 事实与理由：
   简要概括原告主张的核心事实（不超过100字）
```

**3. 判决书/裁定书**
```
📋 文书：民事判决书
├─ 案号：（2026）浙0304民初123号
├─ 法院：温州市瓯海区人民法院
├─ 当事人：原告张三 vs 被告李四
├─ 案由：买卖合同纠纷
├─ 判决结果：
│  ✅ 驳回原告全部诉讼请求
│  或 ✅ 支持原告第1、2项诉讼请求
├─ 上诉期限：判决书送达之日起15日内
└─ 履行期限：判决生效后10日内
```

**4. 通知书类（举证/缴费/应诉等）**
```
📋 文书：举证通知书
├─ 案号：（2026）浙0304民初123号
├─ 法院：温州市瓯海区人民法院
├─ 核心内容：
│  ⚠️ 举证期限：收到本通知书之日起15日内
│  ⚠️ 逾期举证的法律后果：可能承担不利后果
└─ 特别提醒：如有困难可申请延期举证
```

**5. 其他文书**
```
📋 文书：[文书标题]
├─ 法院：[法院名称]
├─ 案号：[案号]
└─ 内容摘要：[提取核心信息，不超过200字]
```

#### 输出格式

向用户展示结构化的文书总结报告：

```text
📦 已下载 2 份文书，内容总结如下：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 1. 出庭通知书（82KB）
┌──────────────────────────────────────────────┐
│ 案号：（2026）浙0304刑初347号                  │
│ 法院：温州市瓯海区人民法院                      │
│ 当事人：尚家进、张紫源（被告人）                │
│ 案由：开设赌场罪                               │
│ 事项：公开宣判                                 │
│ ⚠️  时间：2026-05-22 14:40                    │
│ 地点：第四审判庭                               │
└──────────────────────────────────────────────┘

📄 2. 应诉通知书（45KB）
┌──────────────────────────────────────────────┐
│ 案号：（2026）浙0304刑初347号                  │
│ 法院：温州市瓯海区人民法院                      │
│ ⚠️  举证期限：收到本通知书之日起15日内          │
│ ⚠️  应诉期限：收到起诉状副本之日起15日内提交答辩状 │
└──────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 实现方式

使用 `pdftotext` 提取 PDF 文本，然后用正则匹配和关键词识别提取信息：

```bash
# 提取 PDF 文本（前500字符通常包含关键信息）
pdftotext "/path/to/file.pdf" - | head -c 500

# 根据文书标题和内容特征，识别类型并提取对应字段
```

### 第五步：归档保存

1. **确定目标目录**：根据当前项目环境自动判断，不询问用户
   - 扫描当前项目目录，匹配与案号或当事人相关的案件目录
   - 如找到匹配案件目录，优先查找法院文书子目录（如 `08*`、`法院送达`、`court` 等）；如无子目录则直接归档到案件根目录
   - **如未找到匹配案件，自动在当前项目下新建**：`{案号} {当事人与案由}/`
   - 如目标目录不存在，自动创建
2. **获取当前日期**：`date "+%Y%m%d"`
3. **确定文书标题**：
   - 优先使用 API 返回的标题
   - 否则根据 `sms-patterns.json` 中的 `document_titles` 映射推断
   - 最后回退到 `未知文书`
4. **构建文件名**：`{title}（{case_name}）_{YYYYMMDD}收.pdf`
   - 示例：`受理通知书（张三与李四合同纠纷）_20260404收.pdf`
   - 清理非法字符：`< > : " | ? * \ /`
   - 如同名文件已存在，追加 `_2` 后缀
5. **移入目标目录**
6. **写入内部记录**：保存本次处理的完整信息到 `archive/` 目录（格式详见 [`references/archive-format.md`](references/archive-format.md)）

### 第六步：关键信息提取与飞书写入

> **核心功能**：自动提取文书中的关键日期信息，写入飞书多维表格，防止遗漏重要期限。

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
  "table_id": "tblVEFh7rLdakiSS",
  "field_mappings": {
    "事项": "fldSAKBW7G",
    "任务内容": "fldXQrmu9c",
    "开始时间": "fld08Jn28a",
    "截止时间": "fld9Oy0o4k",
    "地点": "fldBZxRkOG",
    "备注": "fldrPV4xbx",
    "来源": "fldlcmmODX",
    "优先级": "fldp66GC1l"
  },
  "select_options": {
    "优先级": {
      "高": "opt8trQ9rG",
      "中": "optgGaMdRq",
      "低": "opt0jS1OE7"
    }
  },
  "notes": [
    "⚠️ 重要经验（2026-05-19实测）",
    "1. lark-cli 写入时使用【字段名】而非 field_id",
    "2. 单选字段（如优先级）直接用选项名称（\"高\"），不用 option ID",
    "3. 日期时间字段需传毫秒时间戳，格式：$(date -j -f \"%Y-%m-%d %H:%M\" \"2026-05-22 14:40\" \"+%s\")000",
    "4. 飞书 CLI 认证通过 Keychain 持久化，首次使用需登录",
    "5. 查询表格列表：lark-cli api GET \"/open-apis/bitable/v1/apps/{app_token}/tables\" --as user",
    "6. 查询字段信息：lark-cli api GET \"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields\" --as user"
  ]
}
```

> **实测经验（2026-05-19）**：
> - ✅ 使用字段名（中文）写入成功：`{"fields": {"事项": "xxx", "优先级": "高"}}`
> - ❌ 使用 field_id 写入失败：`{"fields": {"fldSAKBW7G": "xxx"}}` 报错 FieldNameNotFound
> - 单选字段直接用选项名"高"，不用 option ID "opt8trQ9rG"

#### 文书类型识别与信息提取规则

提取 PDF 首页文本，根据文书标题识别类型并提取对应信息：

| 文书类型 | 识别关键词 | 必须提取的信息 | 提取规则 |
|---------|-----------|---------------|---------|
| **传票/开庭传票** | 标题含"传票"，正文含"开庭" | 开庭时间、地点、法庭、案号、审理程序 | 正则匹配日期时间格式 |
| **开庭通知书/出庭通知书** | 标题含"开庭通知"或"出庭通知" | 开庭/宣判时间、地点、法庭、案号 | 正则匹配日期时间格式 |
| **举证通知书** | 标题含"举证通知" | 举证期限截止日期 | 查找"举证期限"、"×日内提交"等关键词 |
| **缴费通知书** | 标题含"缴费通知"或"诉讼费" | 缴费期限截止日期 | 查找"×日内缴纳"、"截止日期"等关键词 |
| **取证通知书** | 标题含"取证通知" | 取证时间、地点 | 提取具体日期时间和地点 |
| **判决书/裁定书** | 标题含"判决书"或"裁定书" | **上诉期**、履行期 | 查找"如不服本判决"、"×日内上诉"、"×日内履行"等 |
| **调解书** | 标题含"调解书" | 生效时间、履行期限 | 查找"本调解书经双方签收后生效"、"×日内履行" |
| **执行通知书** | 标题含"执行通知" | 履行期限、报告财产期限 | 查找"×日内履行"、"×日内报告财产状况" |

#### 提取示例

**传票**：
```
extracted = {
  "案号": "（2026）浙0304刑初347号",
  "时间": "2026-05-22 14:40",
  "事项": "开庭审理",
  "地点": "第四审判庭",
  "法院": "温州市瓯海区人民法院",
  "备注": "传票"
}
```

**判决书**：
```
extracted = {
  "案号": "（2026）浙0304民初123号",
  "时间": "上诉期15日（从收到判决书之日起算）",
  "事项": "上诉期限",
  "法院": "温州市瓯海区人民法院",
  "备注": "判决书，履行期：判决生效后10日内"
}
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

### 第七步：PDF 后处理（可选）

> **不默认启用**。仅在检测到文件拆分时主动提示用户。

归档完成后，扫描目标目录中的 PDF 文件，检测是否有同一文书被拆分为多个文件的情况。

#### 读取用户偏好

读取 `config/user-preferences.json` 获取用户的合并和重命名偏好。如文件不存在，使用默认值（参考 `config/user-preferences.example.json`）。

关键偏好项：

| 偏好 | 默认值 | 说明 |
|------|--------|------|
| `merge_strategy` | `per_evidence` | 合并策略：`per_evidence`（按编号分别合并）或 `unified`（统一合并） |
| `merge_options.unified.bookmarks.enabled` | `true` | 统一合并时是否添加 PDF 书签 |
| `rename.enabled` | `true` | 是否精简文件名 |

#### 触发检测

读取 `references/sms-patterns.json` → `post_processing.trigger` 配置，按以下规则分组：

```text
分组规则：
1. 证据类：文件名以"证据"开头 → 按编号分组（证据1、证据2、证据3…）
2. 其他文书：按文书类型分组（传票、起诉状、应诉通知书…）
3. 如任一组内文件数 > 3（threshold），触发提示
```

**示例**：证据3 下有 10 个 PDF → 触发。

#### 用户确认

使用 AskUserQuestion 提示用户，列出检测到的拆分情况：

```text
检测到以下文书被拆分为多个 PDF：
- 证据3：10 个文件
- 证据5：4 个文件

是否执行 PDF 后处理（合并 + 重命名）？
  → 是，合并所有
  → 让我选择（逐个确认）
  → 跳过
```

#### 执行后处理

用户确认后，根据 `user-preferences.json` 中的 `merge_strategy` 执行：

**策略一：per_evidence（默认）**

按单个证据编号分别合并，每个证据独立保留：

```text
- 证据3 有 10 个拆分文件 → 合并为「证据3：打印截图.pdf」
- 证据5 有 4 个拆分文件 → 合并为「证据5：电脑截图.pdf」
- 未被拆分的证据（如证据1 只有 1 个文件）保持不动
```

**策略二：unified**

将证据目录 + 所有证据合并为一个「原告证据.pdf」，并添加 PDF 书签：

```text
合并顺序：证据目录 → 证据1 → 证据2 → … → 证据N
书签格式：
  📑 证据目录
  📑 证据1：仲裁申请书、不予受理通知书
  📑 证据2：劳动合同、保密协议
  📑 证据3：被告工资表
  📑 证据4：泄露账号密码的电脑截图
  📑 证据5：打印及拷贝资料的电脑截图
  📑 证据6：删除电脑操作痕迹的截图
```

书签名称使用简洁版：证据编号 + 冒号 + 证据标题（去除当事人和日期后缀）。使用 pypdf 的 `add_outline_item` 添加书签。

> 用户可随时修改 `user-preferences.json` 切换策略，无需改动 skill 本身。

#### 页面尺寸标准化

合并过程中同时标准化页面尺寸为 A4（210×297mm）。使用 pypdf 逐页处理：

```python
from pypdf import PdfReader, PdfWriter, Transformation

A4_W = 595.27  # 210mm in points
A4_H = 841.89  # 297mm in points

for page in reader.pages:
    pw, ph = float(page.mediabox.width), float(page.mediabox.height)
    is_landscape = pw > ph

    # 保持原始方向：纵向→A4纵向，横向→A4横向
    target_w = A4_H if is_landscape else A4_W
    target_h = A4_W if is_landscape else A4_H

    # 等比缩放并居中
    scale = min(target_w / pw, target_h / ph)
    offset_x = (target_w - pw * scale) / 2
    offset_y = (target_h - ph * scale) / 2

    new_page = writer.add_blank_page(width=target_w, height=target_h)
    page.add_transformation(Transformation().scale(scale).translate(offset_x, offset_y))
    new_page.merge_page(page)
```

**规则**：
- 纵向页面 → A4 纵向（210×297mm）
- 横向页面 → A4 横向（297×210mm），不强制旋转为纵向
- 等比缩放、居中放置，不裁剪、不拉伸

#### 精简文件名

根据 `user-preferences.json` → `rename` 配置对所有文件统一重命名：

```text
去除规则（strip_patterns）：
- 去掉括号内的当事人信息：（张三与李四合同纠纷）
- 去掉日期后缀：_20260405收
- 去掉平台标记：（合并）、（自贸法庭）、（素）-

特殊映射（special_mappings）：
- 起诉状（素）… → 起诉状（要素式）.pdf
- 开庭传票 → 传票.pdf
```

**重命名示例**：

| 原始 | 重命名后 |
|------|----------|
| `传票（张三与李四合同纠纷）_20260405收.pdf` | `传票.pdf` |
| `起诉状（合并）.pdf` | `起诉状.pdf` |
| `起诉状（素）-要素式起诉状（合并）.pdf` | `起诉状（要素式）.pdf` |
| `应诉通知书（自贸法庭）.pdf` | `应诉通知书.pdf` |
| `E法桥平台使用告知书（xxx）_20260405收.pdf` | `E法桥平台使用告知书.pdf` |

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
| 无匹配案件 | 提供三个选项：选已有/新建/暂存 |
| Playwright 下载超时 | 检查网络连接，尝试刷新页面重试 |
| 页面需要验证码 | 通知用户，暂停等待手动处理 |
| 下载文件损坏 | 清理临时目录，重新尝试下载 |
| 目标目录不存在 | 自动创建对应目录 |
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
