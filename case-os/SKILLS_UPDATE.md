# 子技能更新日志

## case-ocr (A2: 材料扫描+OCR转换)

### v2.0 (2026-05-13)
**重大升级**：OCR工具从VisionOCR升级到MinerU Pro

**主要改动**：
- 主要工具：MinerU Pro (vlm模型)，准确率大幅提升
- 新增功能：自动扫描件检测 (detect-scanned)
- 容错机制：MinerU失败时自动降级到VisionOCR
- 技术对比：
  - 人名识别："丁思利"正确（vs VisionOCR经常错误）
  - 身份证号：准确识别（vs VisionOCR可能错误）
  - 手写字：支持（vs VisionOCR困难）

**工具依赖**：
- `~/.local/bin/mineru-pro` — MinerU Pro API（vlm模型）
- `~/.local/bin/detect-scanned` — 扫描件检测
- `~/.local/bin/vision-ocr-pdf` — 备用工具

**备份**：
- 原始文件：`~/.claude/skills/case-ocr/SKILL.md.backup`
- GitHub仓库：https://github.com/goacheng001/case-ocr

---

## 其他子技能

### 待更新

其他子技能暂无重大更新。
