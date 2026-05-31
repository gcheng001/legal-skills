# case-ocr

案件材料OCR转换技能

## 功能

扫描案件目录中的所有材料文件，批量转换为Markdown格式，供后续分析使用。

## 支持的文件类型

- **文档类**：PDF、图片（JPG/PNG等）、Word、Excel
- **音频类**：MP3、M4A、WAV → 转换为逐字稿
- **视频类**：MP4、MOV、AVI → 需手动提取截图

## OCR工具

### 主要工具
- **MinerU Pro (vlm模型)**：高质量OCR，自动检测扫描件
- **detect-scanned**：扫描件检测工具

### 备用工具
- 无（MinerU失败时记录错误，跳过该文件）

## 使用方法

由案件OS总控自动调度，或手动触发：

```bash
# 通过Claude Code调用/skill case-ocr
```

## 输出目录

- `_archive/markdown/` — 所有转换后的Markdown文件
- `截图证据/` — 视频截图PDF原件

## 版本历史

### v2.0 (2026-05-13)
- 升级到MinerU Pro (vlm模型)
- 添加自动扫描件检测
- 添加失败重试机制

### v1.0
- 初始版本
