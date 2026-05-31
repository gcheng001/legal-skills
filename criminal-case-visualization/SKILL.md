---
name: criminal-case-visualization
description: 刑事案件可视化图表生成技能。用户明确提出”刑事可视化””刑事图表””刑事案件图表””刑事辩护图表”，或在刑事案件上下文中要求画图、做图表、做庭审展示图时使用；必须基于阅卷笔录或卷宗材料生成，不得用生成图替代证据原图。
metadata:
  author: Legal Skills Project
---

# 刑事案件可视化图表生成器

## 概述

基于诉讼可视化方法论，专门为刑事案件生成全套可视化图表。继承自 `litigation-chart` skill，但针对刑事案件的特殊需求（共同犯罪、量刑预测、证据矩阵、资金流向、程序流程等）做了定制化。

**父级**：`criminal-case-os`（刑事案件OS总控）
**依赖**：`litigation-chart`（通用可视化方法论）、`html2png`（渲染引擎）
**数据源**：`criminal-case-review`（刑事阅卷笔录）的输出产物

不得在通用 skill 中固化真实案件姓名、案号、当事人身份信息或联系方式；所有示例文件名必须使用占位符。

---

## 触发词

- `刑事可视化`、`刑事图表`、`刑事案件图表`
- `刑事辩护图表`、`辩护可视化`
- `criminal-case-visualization`

TRIGGER when: 用户在刑事案件上下文中说"可视化""画图表""画图""图表"且与刑事案件相关

---

## 🎯 输出契约（最高纪律：任何案件都产出同一效果）

本 skill 的目标是**确定性**——换任何案件、任何当事人，输出风格、结构、清晰度、目录形态必须完全一致。下面是不可商量的契约，每次执行逐条照做，不得即兴发挥、不得改配色、不得换布局方式。

### 不可变参数表（照抄，禁止临时改动）

| 项目 | 固定值 | 理由/出处 |
|------|--------|-----------|
| 风格 | Claude 橙白 · 方案A 极简克制 | 用户 2026-05-30 确认；受援人陶土橙是唯一焦点色 |
| 页面底色 | 暖白 `#FAFAF9`（**禁止冷灰 `#F9F9F9`**） | 规则6 |
| 受援人/己方 | 边框 `#D97757`／底 `#FBEEE8` | 规则6 |
| 主犯 | 深暖灰边 `#78716C`／白底（**禁止用红**，退后不抢焦点） | 规则6 |
| 同案犯 | 中暖灰 `#A8A29E`／白底 | 规则6 |
| 无关方/其他被害人 | 浅暖灰 `#D6D3D1`／暖白底 | 规则6 |
| 功能色（仅证据/量刑） | 绿`#10B981` 黄`#F59E0B` 红`#DC2626` | 规则6 |
| HTML 渲染宽度 | `--width=1467` | 设计规格 |
| Mermaid 渲染清晰度 | **`mmdc -s 4`**（禁止 `-s 2`，会糊） | 规则7+模板铁律 |
| Mermaid subgraph 底 | init 里 `clusterBkg:#FAFAF9`（禁止默认鹅黄） | 模板铁律 |
| 验收 | 双门禁全 PASS + 肉眼复核，缺一不可 | 门禁段 |

### 标准作业流程（SOP，按序执行，不跳步）

1. **取数**：从 `criminal-case-review` 阅卷笔录提取结构化数据（当事人/犯罪事实/证据/程序/金额）。法律事实**只许原样引用，禁止编造**任何姓名、金额、日期、法条、供述。
2. **分路**：按"渲染路线决策"表给 8 张图分派路线——文字密集图(2/3/4/5/6)走 `templates/light-card-table.html`；节点连线图(1/7/8)走 `templates/mermaid-graphs.md`。
3. **出图**：
   - HTML 图：复制 `light-card-table.html`，替换 `{{占位符}}`，删除用不到的 section。配色变量已是方案A，**不要改 `:root`**。
   - Mermaid 图：复制 `mermaid-graphs.md` 对应模板，填数据，存 `chart1.mmd/chart7.mmd/chart8.mmd`，用 `mmdc -i x.mmd -o x.png -b "#FFFFFF" -s 4` 渲染。
   - HTML 通过相对路径 `<img src="chart1.png">` 引用 Mermaid PNG。
4. **验收**：两个门禁脚本都必须 PASS，再肉眼复核 PNG（文字清晰、无黑块、无重叠、无压字）。任一不过则修到过，不得交付。
5. **落盘**（固定目录形态，保证每个案件长一样）：
   - 输出目录：`<案件目录>/可视化-YYYYMMDD/`
   - 主文件：`<案件名>-全套可视化图表.html`
   - 配图：`chart1.png chart7.png chart8.png`（与 HTML 同目录，否则图裂）
   - 预览：`<案件名>-全套可视化图表-预览.png`
   - **只保留这一套终版**；中间版、旧版生成完即删，不与终版并存（避免混淆）。
   - 文件名禁用冒号等非法字符，日期用 `YYYYMMDD` 短横线格式。

> 偏离本契约任何一条 = 输出不合格。若某案件数据缺失导致某张图无法生成，宁可**省略该图并说明**，也不得改风格凑数或编造数据。

---

## ⛔ 第一原则：渲染路线决策（动手前必读）

历史教训：本 skill 曾输出黑底卡片、时间轴文字重叠截断、连线压字。**根因不是坐标算错，而是该用 HTML/Mermaid 自动布局的图被手写成了 SVG。** 因此每张图开工前，先按下表定路线，**默认不手写 SVG**。

| 图表 | 内容性质 | 强制渲染路线 | 模板 |
|------|----------|--------------|------|
| 时间轴、量刑预测、共同犯罪对比、受援人参与、证据矩阵 | 文字密集 | **HTML 表格/卡片** | `templates/light-card-table.html` |
| 人物关系、资金流向、程序流程 | 节点连线 | **Mermaid（mmdc 自动布局）** | `templates/mermaid-graphs.md` |
| 需庭审反复精修的连线图 | — | 先出 Mermaid，再按需人工导入 draw.io 微调（draw.io 本机未装，需要时再装；它只精修，不自动布局） | — |
| 节点≤12、每框≤4行、文字短的极简图 | 极少 | 才允许手写 SVG | 见附录 |

> draw.io 定位：**最终庭审展示的可选人工精修出口**，不参与自动生成。当前以 HTML 表格 + Mermaid 为自动出图主力。

## 黑底卡片的真实根因（务必记住）

图表4/5 整张变黑，**不是有人填了黑色**，而是：
```css
.node rect { fill:#FFFFFF; filter: url(#shadow); }   /* 对所有 svg 的 .node rect 生效 */
```
但 `<filter id="shadow">` **只定义在第一个 `<svg>` 里**。其余 SVG 的 rect 引用了一个本节点内不存在的滤镜 → **headless Chrome 把整个 rect 渲成黑色**。

**铁律**：`filter: url(#X)`（无论写在 CSS 还是元素上）引用的滤镜，**必须在用到它的每一个 `<svg>` 内部各自定义一份**；跨 SVG 共享 defs 不生效。能不用 filter 阴影就别用（改用 CSS `box-shadow` 作用于 HTML 卡片）。此坑由 `gate_dangling_filter_refs` 自动拦截。

## ✅ 验收门禁（生成后必须全绿，否则不得交付）

```bash
# 门禁1：静态结构检查（黑底/裸rect/悬空filter/时间轴误用SVG/中文小字加粗 → ERROR）
python3 ~/.claude/skills/criminal-case-visualization/scripts/visual_layout_lint.py <file.html>

# 门禁2：渲染后像素采样（任何大面积黑带 → FAIL，覆盖一切未知机理）
python3 ~/.claude/skills/criminal-case-visualization/scripts/render_pixel_check.py <file.html>
```

两个脚本都必须 **PASS / 退出码0**。出现 ERROR 必须修到通过，不得"批量忽略 WARN"或直接交付。门禁通过后仍需肉眼看一遍 PNG。

---

## 标准图表套装（刑事案件8张图）

刑事案件可视化标准套装包含以下8张图表，每张图有特定的用途和设计要点：

| 序号 | 图表名称 | 图表类型 | 核心用途 | 目标读者 |
|------|----------|----------|----------|----------|
| 1 | 人物关系图谱 | 关系图 | 梳理全部涉案人员、层级关系 | 内部+法官 |
| 2 | 案件事实时间轴 | 时间图 | 时间-事件-证据三栏对照 | 法官 |
| 3 | 受援人/当事人参与分析图 | 数据图 | 逐起分析参与程度、获利、同案犯对比 | 法官+内部 |
| 4 | 量刑预测对比图 | 数据图 | 多情景量刑计算、法律依据 | 内部+当事人 |
| 5 | 共同犯罪地位对比图 | 关系图+数据图 | 多维度对比各被告地位作用 | 法官 |
| 6 | 证据印证关系矩阵图 | 数据图 | 双轴矩阵展示证据印证/矛盾 | 法官 |
| 7 | 资金/财物流向图 | 流程图 | 完整资金闭环、矛盾点标注 | 法官+内部 |
| 8 | 案件程序流程图 | 流程图 | 诉讼阶段、期限审查、程序合法性 | 内部 |

---

## 核心工作流

```
输入：阅卷笔录（criminal-case-review 输出）
  ↓
Step 1：数据提取
  ├── 当事人信息（姓名、角色、持股、年龄等）
  ├── 犯罪事实（每起的时间、地点、参与人、金额）
  ├── 证据清单（供述、陈述、转账记录、文书）
  ├── 程序节点（受案、立案、抓获、取保、起诉、开庭）
  └── 金额明细（分赃、转账、供述金额对比）
  ↓
Step 2：按"渲染路线决策"表选模板生成
  ├── 文字密集图 → 套 templates/light-card-table.html（浅色表格/卡片）
  ├── 节点连线图 → 套 templates/mermaid-graphs.md（mmdc 自动布局）
  └── 统一浅色调色板、统一页脚（案号、日期）
  ↓
Step 3：双门禁验收（铁律）
  ├── visual_layout_lint.py  → 必须 PASS
  └── render_pixel_check.py  → 必须 PASS（无黑带）
  ↓
Step 4：肉眼复核 PNG → 输出到案件目录
```

## 文字密集内容的排版原则（通用）

- 刑事案件事实、证据、程序日期、法条依据属于文字密集内容，**优先用 HTML 表格或卡片**，不要塞进 SVG 方框。
- 长事实句必须先摘要成短标签，完整说明放到表格备注或图下说明中。
- 一个图只表达一个论点：人物关系、事实时间、证据矛盾、量刑计算不要混在同一张图。
- 需要全套 8 张图时，拆成多个 HTML section；不要为了"一屏展示"压缩字号或减少留白。

### 手写 SVG 的强制门槛（落到附录A前先过这关）

只有**同时**满足以下条件，才允许手写 SVG，否则一律走模板：
- 单张图节点 ≤ 12 个；每框正文 ≤ 4 行；每行中文不超过行宽公式上限；
- 图例放入 SVG 内部，不得用 `position:absolute` 浮在图上；
- 若用阴影 `filter`，必须在**本 `<svg>` 内**定义 `<filter>`（见"黑底根因"）；
- 生成后必须过双门禁并肉眼复核。

---

## 附录A：手写 SVG 避坑清单（仅"极简图"路线适用）

> ⚠️ 仅当你按"渲染路线决策"表确认走**手写 SVG**（节点≤12、文字短）时，才需要逐条对照本清单。文字密集图和节点连线图请直接用模板，不要落到这里。这些规则是历史血泪教训，但**绝大多数已被双门禁脚本自动检查**——本清单仅作人工理解参考。

### 规则1：SVG text 必须显式设置 text-anchor

**坑因**：SVG `<text>` 默认 `text-anchor="start"`（左对齐）。如果 x 坐标设为方框中心，文字会从中心点向右延伸，导致溢出。

**规则**：
- 方框内居中文字：必须设置 `text-anchor="middle"`
- 标签类文字（靠左排列）：使用 `text-anchor="start"`，但 x 从方框左边界+padding 开始
- CSS中 `.node text { text-anchor: middle; }` **不会继承**到 `.flow-node text` 或 `.process-box text`，必须为每个容器类单独定义

**检查方法**：
```
grep -n 'class="flow-node' *.html  → 确认 CSS 中有 .flow-node text { text-anchor: middle; }
grep -n 'class="process-box' *.html → 确认 CSS 中有 .process-box text { text-anchor: middle; }
```

### 规则2：中文文字禁止 font-weight > 400

**坑因**：中文字体（如 PingFang SC）在 font-weight: 600 时笔画粘连，小字号下完全无法辨识。这与英文字体的"半粗体"效果完全不同。

**规则**：
- 所有中文字体：`font-weight: 400`（normal）或 不设置
- 标题可用 `font-weight: 600`，但字号必须 >= 16px
- SVG 中的 `font-weight="600"` 属性优先级高于 CSS，必须同时在 HTML 中清除
- **特别注意**：检查 CSS class 定义（如 `.process-title`）中是否内置了 `font-weight: 600`

**检查方法**：
```
grep -n 'font-weight="600"' *.html → 逐条确认字号 >= 16px 或删除
grep -n 'font-weight: 600' style → 检查 CSS class 定义
```

### 规则3：每行文字长度必须可控

**坑因**：SVG `<text>` 不支持自动换行。一行文字如果超出方框宽度，不会被截断而是直接溢出。

**规则**：
- 每行中文字符数 ≤ 方框宽度(px) ÷ 字号(px) × 0.9（留10%安全边距）
- 经验值：font-size:11px → 每行约22字；font-size:12px → 每行约20字
- 长文字必须拆分为多行 `<text>` 元素
- 宁可多占垂直空间，也不要让文字溢出

**公式**：`最大字符数 = (方框宽度 - 左右padding×2) ÷ (字号 × 1.1)`

### 规则4：方框尺寸必须留足余量

**坑因**：方框太小会导致：文字被盖住、行间距不够、底部文字截断。

**规则**：
- 方框高度 = 标题行(25px) + 内容行数 × 行高(17px) + 上下padding(各15px)
- 方框宽度 = 最长文字行宽 × 1.15（留15%安全边距）
- 文字底部 y 坐标必须比方框底边 y 坐标小至少 5px
- 如果方框内文字较多，宁可增大方框或减小字号

### 规则5：position:absolute 元素可能盖住 SVG 内容

**坑因**：`.legend` 使用 `position: absolute; bottom: 20px; right: 20px;`，会浮在 SVG 上方，可能盖住右下角的内容。

**规则**：
- SVG 内最后一个元素的 y 坐标必须比 `viewBox高度 - legend高度(约80px)` 小
- 或者将 legend 改为 SVG 内部元素（推荐）
- 或者给 `.chart-body` 添加 `padding-bottom: 80px`

### 规则6：颜色方案规范（Claude 橙白 · 方案A，2026-05-30 用户确认为默认）

**设计原则**：暖白底上浮白框，**受援人陶土橙是唯一焦点色**，主犯/同案用暖灰退后——不要让主犯的颜色与受援人争夺注意力。色值权威来源：`templates/light-card-table.html` 的 `:root` 与 `templates/mermaid-graphs.md` 的 classDef。

| 角色 | 边框色 | 底色 |
|------|--------|------|
| 己方/受援人（焦点） | 陶土橙 `#D97757` | 浅橙 `#FBEEE8` |
| 主犯/组织者 | 深暖灰 `#78716C`（**不用红**，退后） | 白 `#FFFFFF` |
| 同案犯 | 中暖灰 `#A8A29E` | 白 `#FFFFFF` |
| 被害人/第三方/未参与 | 浅暖灰 `#D6D3D1`/`#E7E5E4` | 暖白 `#FAFAF9` |
| 页面背景 | — | 暖白 `#FAFAF9` |

- 功能色（仅用于证据印证/量刑情景）：有利绿 `#10B981`、存疑黄 `#F59E0B`、矛盾红 `#DC2626`。
- **禁止深色/黑色方框**（已确认用户不喜欢）。**禁止冷灰底 `#F9F9F9`**，统一用暖白 `#FAFAF9`。
- Mermaid 必须在 init 覆盖 `clusterBkg:#FAFAF9`，否则 subgraph 会变默认鹅黄脏底。

### 规则7：必须执行双门禁验收

验收命令见上文"✅ 验收门禁"段。两个脚本(`visual_layout_lint.py` + `render_pixel_check.py`)都必须 PASS，再肉眼复核 PNG。对庭审展示图，宁可拆图，也不要缩小字号解决拥挤。

---

## 设计规格

### 标准尺寸

| 用途 | viewBox 尺寸 | 说明 |
|------|-------------|------|
| 关系图/数据图 | 1467 × 900 | 默认尺寸 |
| 时间轴 | HTML table | 不使用SVG，用HTML表格 |
| 矩阵图 | HTML table | 不使用SVG，用HTML表格 |
| 流程图 | 1467 × 650 | 横向流程 |

### 字号规范

| 用途 | 字号 | font-weight |
|------|------|-------------|
| 图表标题 | 16-20px | 600-700 |
| 模块标题 | 14-15px | 400 |
| 正文 | 11-12px | 400 |
| 标注/备注 | 10-11px | 400 |
| 标签 | 9-10px | 400 |

### 行高规范

- 同字号行间距：17px（font-size 11-12px 时）
- 不同区域间距：20-25px
- 方框内padding：15-20px

---

## 模板结构

生成的HTML文件采用以下结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>[案件名] - 全套可视化图表</title>
  <style>
    /* 通用样式：导航、容器、页脚 */
    /* SVG节点样式：.node, .flow-node, .process-box */
    /* 表格样式：.timeline-table, .matrix-table */
    /* 标签样式：.evidence-tag */
    /* 颜色变量 */
    /* 打印样式 @media print */
  </style>
</head>
<body>
  <nav><!-- 图表导航目录 --></nav>
  <section id="chart1"><!-- 人物关系图谱 --></section>
  <section id="chart2"><!-- 案件事实时间轴 --></section>
  <section id="chart3"><!-- 受援人参与分析图 --></section>
  <section id="chart4"><!-- 量刑预测对比图 --></section>
  <section id="chart5"><!-- 共同犯罪地位对比图 --></section>
  <section id="chart6"><!-- 证据印证关系矩阵 --></section>
  <section id="chart7"><!-- 资金流向图 --></section>
  <section id="chart8"><!-- 案件程序流程图 --></section>
  <footer><!-- 文档页脚 --></footer>
</body>
</html>
```

---

## 修改机制

### 最小化原则

| 修改类型 | 处理方式 |
|----------|----------|
| 文字内容调整 | 只改目标文字，不动布局 |
| 文字溢出修复 | 优先缩短文字，其次增大方框 |
| 颜色调整 | 修改CSS变量或style属性 |
| 全局重做 | 从头执行工作流 |

### 修改后必须重新检查

每次修改后，重新执行"✅ 验收门禁"中的两个脚本，必须全部 PASS。

---

## 与刑事案件OS的集成

### 触发时机

1. **阅卷完成后**：`criminal-case-review` 输出阅卷笔录后，可触发生成可视化图表
2. **会见准备前**：生成图表辅助会见准备
3. **庭审准备阶段**：生成/更新图表用于庭审展示
4. **用户手动触发**：说"画图表""可视化"即触发

### 数据流向

```
criminal-case-review（阅卷笔录）
  ↓ 提取结构化数据
criminal-case-visualization（可视化图表，按"输出契约"SOP执行）
  ↓ 输出固定目录形态
案件目录/可视化-YYYYMMDD/
  ├── [案件名]-全套可视化图表.html
  ├── chart1.png / chart7.png / chart8.png
  └── [案件名]-全套可视化图表-预览.png
```

### 调度方式

从 `criminal-case-os` 总控菜单中选择"可视化图表"选项，或直接说"刑事可视化"触发。

---

## 参考文档与模板

| 文件 | 用途 |
|------|------|
| `templates/light-card-table.html` | **首选**：文字密集图浅色 HTML 表格/卡片成品骨架 |
| `templates/mermaid-graphs.md` | **首选**：关系/资金/程序流程 Mermaid 自动布局模板 |
| `scripts/visual_layout_lint.py` | 门禁1：静态结构检查（黑底/裸rect/悬空filter/时间轴误用SVG/小字加粗） |
| `scripts/render_pixel_check.py` | 门禁2：渲染后像素采样，拦截一切黑带 |
| `references/chart-templates.md` | 8张图表逐张设计要点（数据提取规则） |
| `references/svg-pitfalls.md` | 历史 SVG 踩坑记录（仅手写 SVG 时参考） |
| `litigation-chart/references/style-claude-orange.md` | Claude Orange 风格 CSS 规范 |

---

## 依赖

- **litigation-chart**：通用可视化方法论和风格规范
- **html2png**：HTML→PNG 渲染引擎（已配 Playwright Chromium；门禁2 与肉眼验收都依赖它）
- **mermaid-cli (mmdc)**：节点连线图自动布局渲染（本机已装 11.x）
- **criminal-case-review**：数据来源（阅卷笔录）
- **scripts/visual_layout_lint.py + scripts/render_pixel_check.py**：双验收门禁，生成后必须全 PASS
