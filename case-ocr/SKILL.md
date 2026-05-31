---
author: Legal Skills Project

# case-ocr（A2）材料扫描+OCR转换

## 工作定位

扫描案件目录中的所有材料文件，批量转换为Markdown格式，供后续分析使用。

**前置条件**：A1（Git初始化）完成
**必须确认**：否（但视频截图需人工审阅）
**执行后**：调用Hook脚本更新状态

---
author: Legal Skills Project

## 执行流程

### 第一步：创建输出目录

```bash
mkdir -p "[案件根目录]/_archive/markdown/"
mkdir -p "[案件根目录]/截图证据/"
```

### 第二步：扫描并分离文件类型

扫描案件根目录及所有子目录，识别以下文件类型：

```bash
# 扫描案件目录，收集文件列表
cd "[案件根目录]"

# 文档类（PDF/图片/Word）
DOC_FILES=($(find . -type f \( -iname "*.pdf" -o -iname "*.docx" -o -iname "*.doc" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) ! -path "./_archive/*" ! -path "./.git/*"))

# 音频类
AUDIO_FILES=($(find . -type f \( -iname "*.mp3" -o -iname "*.m4a" -o -iname "*.wav" \) ! -path "./_archive/*" ! -path "./.git/*"))

# 视频类
VIDEO_FILES=($(find . -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.avi" \) ! -path "./_archive/*" ! -path "./.git/*"))

# 验证文件存在性
for file in "${DOC_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "⚠️ 文件不存在，跳过: $file"
    fi
done
```

### 第三步：文档类处理（批量转换）

**OCR工具优先级（红线）**：
1. **首选**：`mineru-ocr` Skill — 调用 `/usr/bin/osascript -l JavaScript .claude/skills/mineru-ocr/scripts/convert.js "<文件路径>"`
2. **备用**：`mineru-pro` CLI — `mineru-pro "$file" --upload --ocr --model vlm`

> **MinerU全部失败时记录错误并跳过该文件，不使用其他OCR工具。**

```bash
# 检查是否有文档需要处理
if [ ${#DOC_FILES[@]} -eq 0 ]; then
    echo "⚠️ 未找到需要转换的文档文件"
else
    echo "📄 找到 ${#DOC_FILES[@]} 个文档文件，开始转换..."

    # 创建临时输出目录
    OCR_TMP_DIR=$(mktemp -d)

    # 使用CLI版本转换（可以看到实时进度）
    for file in "${DOC_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo "⚠️ 文件不存在，跳过: $file"
            continue
        fi

        echo "🔄 正在转换: $(basename "$file")"

        # 根据文件类型选择处理方式
        ext="${file##*.}"
        ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

        case "$ext_lower" in
            pdf|jpg|jpeg|png|tif|tiff|bmp|gif|heic|webp)
                # PDF/图片 → MinerU OCR转Markdown（首选）
                stem=$(basename "$file" | sed 's/\.[^.]*$//')
                output="$OCR_TMP_DIR/${stem}.md"

                echo "  📄 使用MinerU OCR转换..."
                # 首选：mineru-ocr Skill
                mineru_result=$(/usr/bin/osascript -l JavaScript $HOME/.claude/skills/mineru-ocr/scripts/convert.js "$file" 2>&1)

                if [ -f "./full.md" ]; then
                    mv "./full.md" "$output"
                    echo "  ✅ MinerU转换完成"
                else
                    echo "  ⚠️ mineru-ocr Skill失败，尝试mineru-pro CLI..."
                    # 备用：mineru-pro CLI
                    mineru-pro "$file" --upload --ocr --model vlm > /tmp/mineru.log 2>&1
                    if [ -f "./full.md" ]; then
                        mv "./full.md" "$output"
                        echo "  ✅ mineru-pro转换完成"
                    else
                        echo "  ❌ MinerU全部失败，跳过: $(basename "$file")"
                        echo "  $(date): MinerU转换失败: $file" >> "$OCR_TMP_DIR/转换失败.log"
                    fi
                fi
                ;;
            mp3|m4a|wav|aac|flac|ogg|wma)
                # 音频 → 逐字稿
                stem=$(basename "$file" | sed 's/\.[^.]*$//')
                output="$OCR_TMP_DIR/${stem}_逐字稿.md"
                media-to-transcript "$file" --output "$output" 2>&1 | while IFS= read -r line; do
                    echo "  $line"
                done
                ;;
            docx|doc|xlsx|xls|csv|html|htm|epub)
                # Office文档 → Markdown
                stem=$(basename "$file" | sed 's/\.[^.]*$//')
                output="$OCR_TMP_DIR/${stem}.md"
                office-to-markdown "$file" -o "$output" 2>&1 | while IFS= read -r line; do
                    echo "  $line"
                done
                ;;
            *)
                echo "⚠️ 不支持的文件类型: $ext_lower"
                ;;
        esac

        echo "✅ 完成: $(basename "$file")"
        echo "---"
    done
fi
```

- **主要使用MinerU Pro (vlm模型)**：高质量OCR，适合法律文档，自动检测扫描件
- MinerU全部失败时记录错误并跳过，不降级到其他工具
- 自动按类型分流：PDF→MinerU、音频→whisper、Office→markitdown
- 每个文件转换完成后有明确提示

### 第四步：视频类处理（如需要）

```bash
# 检查是否有视频需要处理
if [ ${#VIDEO_FILES[@]} -eq 0 ]; then
    echo "✓ 未找到视频文件，跳过视频处理"
else
    echo "📹 发现 ${#VIDEO_FILES[@]} 个视频文件："
    printf '  - %s\n' "${VIDEO_FILES[@]}"
    echo ""
    echo "⚠️ 视频文件需要手动处理（如需提取截图作为证据）："
    echo "   1. 使用第三方工具（如ffmpeg）提取关键帧"
    echo "   2. 或使用 '/Applications/办案工具集/微信录屏取证导出.app' 手动处理"
    echo ""
    echo "💡 如需自动处理，可以运行："
    echo "   open -a '/Applications/办案工具集/微信录屏取证导出.app' ${VIDEO_FILES[0]}"
    echo ""
    echo "⏭️  跳过视频处理，继续处理其他文件..."
fi
```

- 视频文件不自动处理（避免打开GUI应用）
- 如需视频截图，用户可手动操作或按提示运行命令
- 音频文件（MP3/M4A/WAV）会自动转文字

### 第五步：等待处理完成

检查输出目录PDF生成完毕。

### 第六步：⚠️ 人工卡点（必须等待用户确认）

```
视频录屏截图已生成PDF，位于 ~/Desktop/录屏取证输出/
请打开PDF审阅：
- 删除无关截图（如微信首页、切换界面等非证据帧）
- 补充遗漏的关键截图（如有需要可手动添加）
审阅完成后请回复"确认"
```

**红线**：
- 步骤6是人工卡点，必须等待用户确认后才能继续
- 禁止自动跳过此步

### 第七步：视频类第二阶段（PDF转Markdown）

```bash
# 检查录屏取证输出目录
SCREENSHOT_DIR="$HOME/Desktop/录屏取证输出"
SCREENSHOT_PDF=($(find "$SCREENSHOT_DIR" -maxdepth 1 -type f -iname "*.pdf" 2>/dev/null))

if [ ${#SCREENSHOT_PDF[@]} -eq 0 ]; then
    echo "⚠️ 未找到视频截图PDF，跳过转换"
else
    echo "📄 找到 ${#SCREENSHOT_PDF[@]} 个截图PDF，开始转换..."

    # 创建临时输出目录
    OCR_TMP_DIR=$(mktemp -d)

    # 使用CLI版本转换（可以看到实时进度）
    for pdf in "${SCREENSHOT_PDF[@]}"; do
        if [ ! -f "$pdf" ]; then
            echo "⚠️ 文件不存在，跳过: $pdf"
            continue
        fi

        echo "🔄 正在转换: $(basename "$pdf")"

        stem=$(basename "$pdf" | sed 's/\.[^.]*$//')
        output="$OCR_TMP_DIR/${stem}.md"

        # 首选：mineru-ocr Skill
        /usr/bin/osascript -l JavaScript $HOME/.claude/skills/mineru-ocr/scripts/convert.js "$pdf" 2>&1

        # 移动生成的md文件
        if [ -f "./full.md" ]; then
            mv "./full.md" "$output"
            echo "  ✅ MinerU转换完成"
        else
            echo "  ⚠️ mineru-ocr Skill失败，尝试mineru-pro CLI..."
            mineru-pro "$pdf" --upload --ocr --model vlm > /tmp/mineru.log 2>&1
            if [ -f "./full.md" ]; then
                mv "./full.md" "$output"
                echo "  ✅ mineru-pro转换完成"
            else
                echo "  ❌ MinerU全部失败，跳过: $(basename "$pdf")"
            fi
        fi

        echo "✅ 完成: $(basename "$pdf")"
        echo "---"
    done
fi
```

### 第八步：自动移动到项目目录

```bash
# OCR输出 → markdown目录
mv "$OCR_TMP_DIR"/*.md "[案件根目录]/_archive/markdown/"
# 视频截图PDF原件 → 截图证据目录
mv ~/Desktop/录屏取证输出/*.pdf "[案件根目录]/截图证据/"
```

### 第九步：清理桌面

```bash
rm -rf "$OCR_TMP_DIR"
rm -rf ~/Desktop/录屏取证输出
```

### 第十步：Git提交

```bash
cd "[案件根目录]"
git add -A
git commit -m "feat: A2 材料OCR转换完成"
```

### 第十一步：调用Hook

```bash
~/.claude/skills/case-os/scripts/case-post-step.sh [案件路径] A2
```

---
author: Legal Skills Project

## 红线

- ❌ 原始文件保留不动（不删除原告/被告材料中的PDF/Word/MP4）
- ❌ 步骤6是人工卡点，必须等待用户确认
- ✅ 步骤8-9必须由AI自动连续执行完成，禁止提示用户手动操作

---
author: Legal Skills Project

## 工具依赖

### CLI工具（按优先级）
- `mineru-ocr` Skill — `/usr/bin/osascript -l JavaScript $HOME/.claude/skills/mineru-ocr/scripts/convert.js`【首选，必须优先尝试】
- `~/.local/bin/mineru-pro` — MinerU Pro API（vlm模型，高质量OCR）【备用】
- `~/.local/bin/detect-scanned` — 扫描件检测工具（可选）
- `~/.local/bin/media-to-transcript` — 音视频转逐字稿
- `~/.local/bin/office-to-markdown` — Word/Excel转Markdown

### GUI应用（仅视频截图使用）
- `/Applications/办案工具集/微信录屏取证导出.app` — 视频证据截图提取

### 工具安装检查

执行前应检查CLI工具是否存在：
```bash
# 主要工具检查
if [ ! -f ~/.local/bin/mineru-pro ]; then
    echo "❌ mineru-pro未安装，请先安装"
    exit 1
fi

if [ ! -f ~/.local/bin/detect-scanned ]; then
    echo "❌ detect-scanned未安装，请先安装"
    exit 1
fi
```

---
author: Legal Skills Project

## 输出

- `_archive/markdown/` — 所有转换后的Markdown文件
- `截图证据/` — 视频截图PDF原件（审阅后）

---
author: Legal Skills Project

## 错误处理

- **文件不存在** → 跳过该文件，记录到LOG.md
- 文件损坏 → 跳过该文件，记录到LOG.md
- MinerU转换失败 → 记录错误，继续处理其他文件

## 执行示例

**正确的执行流程**：
1. 先使用find命令扫描文件，存储到数组
2. 检查数组是否为空
3. 验证每个文件是否存在
4. 使用数组展开方式调用open命令
5. 等待处理完成

**错误示例（禁止）**：
```bash
# ❌ 错误：直接硬编码文件路径
mineru-pro ~/Desktop/input.pdf --upload --ocr --model vlm

# ❌ 错误：使用不存在的占位符
mineru-pro <PDF文件1> --upload --ocr --model vlm
```

**正确示例**：
```bash
# ✅ 正确：先扫描再验证后调用
DOC_FILES=($(find . -type f -iname "*.pdf" ! -path "./_archive/*"))
if [ ${#DOC_FILES[@]} -gt 0 ]; then
    for file in "${DOC_FILES[@]}"; do
        mineru-pro "$file" --upload --ocr --model vlm
    done
fi
```
