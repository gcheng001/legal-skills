# SVG 渲染踩坑记录

> ⚠️ 本文档仅在走"手写 SVG"极简图路线时参考（见 SKILL.md 附录A）。**默认路线是 HTML 模板 + Mermaid，不会落到这些坑**。
> 黑底卡片的真实根因（跨 SVG 悬空 `filter` 引用）已在 SKILL.md"黑底卡片的真实根因"段单列，并由 `gate_dangling_filter_refs` 自动拦截。
> 日期：2026-05-28（历史记录，案例数据仅作示意）

---

## 坑1：SVG text 默认不居中（text-anchor 问题）

### 现象
方框内的文字从中心点向右延伸，导致文字溢出方框右边界。

### 根因
SVG `<text>` 元素默认 `text-anchor="start"`（左对齐）。当 x 坐标设为方框中心点时，文字会从中心开始向右绘制，而不是以中心为对称轴居中。

### CSS 继承陷阱
```css
/* 这样定义不会继承到其他容器类 */
.node text { text-anchor: middle; }

/* 以下容器类必须单独定义 */
.flow-node text { text-anchor: middle; }  /* 资金流向图方框 */
.process-box text { text-anchor: middle; } /* 程序流程图方框 */
```

`.node text` 选择器只会匹配 `<g class="node">` 内的 `<text>`，不会匹配 `<g class="flow-node">` 内的文字。注意：如果 `class="process-box"` 写在 `<rect>` 上，`.process-box text` 也匹配不到任何文字；流程节点必须使用 `<g class="process-box">` 包住 `rect + text`，或给每个 `<text>` 直接写 `text-anchor="middle"`。

### 解决方案
为每个容器类型单独定义 text-anchor：

```css
.node text,
.flow-node text,
.process-box text {
  text-anchor: middle;
  font-family: "PingFang SC", -apple-system, sans-serif;
}
```

更稳妥的写法是在所有居中文本元素上直接写属性：

```xml
<text x="80" y="30" text-anchor="middle" font-size="12">审查起诉</text>
```

---

## 坑2：中文字体 font-weight: 600 笔画粘连

### 现象
方框内的绿色/红色/橙色文字加粗后完全看不清，笔画糊在一起。

### 根因
中文字体（PingFang SC、Microsoft YaHei等）的字形复杂，笔画密度高。font-weight: 600 在英文字体中是"半粗体"，但在中文字体中会导致笔画严重粘连，特别是字号 < 14px 时。

### 具体案例
```xml
<!-- ❌ 错误：小字号加粗，完全看不清 -->
<text font-size="11" font-weight="600" fill="#10B981">✓ 获利较少，无决定权</text>

<!-- ✅ 正确：小字号不加粗 -->
<text font-size="11" fill="#10B981">✓ 获利较少，无决定权</text>
```

### 规则
| 字号范围 | 允许的 font-weight | 用途 |
|----------|-------------------|------|
| ≥ 16px | 400-600 | 图表标题、章节标题 |
| 12-15px | 400 | 模块标题、标签标题 |
| 10-11px | 400 | 正文、标注、备注 |
| ≤ 9px | 400 | 小标注 |

### 优先级陷阱
SVG 中的 `font-weight="600"` **属性优先级高于 CSS class**。即使 CSS 中改了 `.process-title { font-weight: 400; }`，如果 HTML 中有 `font-weight="600"` 属性，后者会覆盖 CSS。

**必须同时清除两处**：
1. CSS class 定义中的 `font-weight`
2. SVG 元素上的 `font-weight="xxx"` 属性

---

## 坑3：SVG text 不支持自动换行

### 现象
一行文字超出方框宽度，直接溢出到方框外面。

### 根因
SVG `<text>` 是单行元素，不像 HTML `<div>` 会自动换行。超长文字不会被截断。

### 解决方案
手动拆分为多个 `<text>` 元素：

```xml
<!-- ❌ 错误：一行太长 -->
<text x="20" y="55" font-size="12">
  马锦武：犯意提起者（"投标敲诈的主意是马锦武提出来的"）
</text>

<!-- ✅ 正确：拆成两行 -->
<text x="20" y="45" font-size="11">
  马锦武：犯意提起者
</text>
<text x="20" y="62" font-size="11">
  （"投标敲诈主意是马锦武提出的"）
</text>
```

### 行宽计算公式
```
最大字符数 = (方框宽度 - 左右padding × 2) ÷ (字号 × 1.1)
```

经验值：
- font-size: 11px，方框宽 300px → 每行约 22 字
- font-size: 12px，方框宽 300px → 每行约 20 字
- font-size: 11px，方框宽 660px → 每行约 52 字

---

## 坑4：方框尺寸不足导致文字被盖住

### 现象
方框底部或侧面的文字被截断，看不到完整内容。

### 根因
方框的 `<rect>` 高度或宽度不足以容纳所有文字元素。

### 计算公式
```
方框最小高度 = 标题行(25px) + 内容行数 × 行高(17px) + 上下padding(各15px)
方框最小宽度 = 最长文字行 × 字号 × 1.1 + 左右padding(各20px)
```

### 具体案例
综合分析框从 560×120 增大到 640×140：

```xml
<!-- ❌ 太小 -->
<rect x="-280" y="-60" width="560" height="120"/>

<!-- ✅ 增大 -->
<rect x="-320" y="-70" width="640" height="140"/>
```

---

## 坑5：position:absolute legend 盖住 SVG 内容

### 现象
图表右下角的文字被图例（legend）遮盖。

### 根因
`.legend` 使用 `position: absolute; bottom: 20px; right: 20px;`，浮在 SVG 上方。

### 解决方案
1. **推荐**：将 legend 改为 SVG 内部元素（用 `<g>` 包裹）
2. **备选**：SVG 内最后一个元素的 y 坐标预留 legend 空间（约 80px）
3. **备选**：给 `.chart-body` 添加 `padding-bottom: 100px;`

---

## 坑6：多维度对比卡片文字溢出

### 现象
4个并排的对比卡片（维度1-4）中的文字溢出卡片边界。

### 根因
卡片宽度（300px）固定，但文字长度不一致。某些行的文字过长。

### 解决方案
1. 缩短文字（"曾程炜、徐才学、伍伟其：3起" → "曾、徐、伍：3起"）
2. 减小字体（12px → 11px）
3. 减小 padding（20px → 15px）
4. 底部结论行进一步缩短

---

## 坑7：程序流程图方框文字不居中重叠

### 现象
流程图方框内的标题、日期、备注三行文字不居中，向右偏移导致重叠。

### 根因
`.process-title`、`.process-date`、`.process-duration` 三个 CSS class 都没有定义 `text-anchor`，默认左对齐。而 HTML 中 x 坐标设为方框中心(80)，导致文字从中心向右延伸。

### 解决方案
在 CSS 中统一添加 `text-anchor: middle`：

```css
.process-title { text-anchor: middle; }
.process-date { text-anchor: middle; }
.process-duration { text-anchor: middle; }
```

---

## 坑8：复杂图不能靠手写坐标硬撑

### 现象
同一张图里节点很多、文字很多、连线很多，第一次生成看似完整，但实际打开 PNG 后会出现文字重叠、方框压住文字、图例盖住右下角内容。

### 根因
模型手写 SVG 坐标时没有真实执行浏览器排版，也不会可靠测量中文文本宽高。规则写得再细，也只能降低概率，不能替代自动布局和渲染验收。

### 解决方案
1. 时间轴、矩阵、量刑计算等文字密集图，改用 HTML table/grid。
2. 关系图、流程图、资金流向图，优先用 Mermaid、Graphviz 或 draw.io 自动布局。
3. 需要最终庭审展示和人工微调时，优先输出 draw.io / Excalidraw，而不是不可编辑的手写 SVG。
4. 手写 SVG 只用于节点少、文字短的图，并运行：

```bash
python3 ~/.claude/skills/criminal-case-visualization/scripts/visual_layout_lint.py <file.html>
```

---

## 通用排查命令

```bash
# 先跑本 skill 的布局检查
python3 ~/.claude/skills/criminal-case-visualization/scripts/visual_layout_lint.py <file.html>

# 检查所有 font-weight="600" 的地方
grep -n 'font-weight="600"' *.html

# 检查 CSS 中是否有 font-weight: 600
grep -n 'font-weight: 600' *.html

# 检查哪些容器类没有 text-anchor 定义
grep -n 'text-anchor' *.html

# 检查 viewBox 尺寸是否合理
grep -n 'viewBox' *.html
```
