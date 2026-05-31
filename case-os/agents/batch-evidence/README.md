# 批量证据提取Agent

> 多个证据文件同时提取，大幅加速A5步骤（Phase A内部并行）

## 功能概述

### 传统串行处理

```
证据1.pdf → 2分钟 → 证据卡片1.md
证据2.pdf → 2分钟 → 证据卡片2.md
证据3.pdf → 2分钟 → 证据卡片3.md
总耗时：6分钟
```

### 并行处理

```
证据1.pdf ─┐
证据2.pdf ─┼→ 同时进行 → 2分钟完成（3倍加速）
证据3.pdf ─┘
```

## 性能对比

| 证据数量 | 串行耗时 | 并行耗时(3worker) | 加速比 |
|---------|---------|------------------|--------|
| 3个 | 6分钟 | 2分钟 | **3x** |
| 10个 | 20分钟 | 7分钟 | **2.86x** |
| 20个 | 40分钟 | 14分钟 | **2.86x** |

## 使用方法

### 命令行

```bash
# 并行提取（默认）
python3 batch_extract.py /path/to/case/dir

# 串行提取（对比）
python3 batch_extract.py /path/to/case/dir --mode sequential

# 指定并发数
python3 batch_extract.py /path/to/case/dir --workers 5
```

### 在case-evidence-cards Skill中调用

```python
# case-evidence-cards/SKILL.md

def main():
    """主函数"""
    case_dir = Path.cwd()

    # 发现证据文件
    extractor = BatchEvidenceExtractor(case_dir)

    files = extractor.find_files()
    if len(files) > 1:
        # 多个文件，使用并行提取
        print(f"发现{len(files)}个证据文件，启动并行提取...")
        results = extractor.run(mode="parallel")
    else:
        # 单个文件，直接提取
        results = [extract_single_evidence(files[0])]
```

## 工作流程

### 第一步：发现证据文件

扫描案件文件夹的`00_原始材料`目录：
```
案件目录/
└── 00_原始材料/
    ├── 证据1.pdf
    ├── 证据2.jpg
    ├── 证据3.png
    └── ...
```

### 第二步：过滤已处理

跳过已经生成卡片的证据：
```
案件目录/_intermediate/证据卡片库/
├── 证据1_证据卡片.md  ← 已存在，跳过
└── ...
```

### 第三步：并行提取

启动多个进程/线程同时处理：
```
Worker 1 → 处理证据1.pdf
Worker 2 → 处理证据2.jpg
Worker 3 → 处理证据3.png
    (同时进行)
```

### 第四步：汇总结果

生成提取报告：
```
========================================
📊 批量提取完成
========================================
模式：并行
总数：10 个
成功：9 个
失败：1 个
成功率：90.0%
总耗时：120.5 秒
平均耗时：13.4 秒/个
加速比：2.8x
========================================
```

## 配置

### 并发数

```python
MAX_WORKERS = 3  # 默认3个并发
```

**建议值**：
- CPU密集型（OCR）：= CPU核心数
- I/O密集型（文件读取）：= CPU核心数 × 2

### 超时时间

```python
TIMEOUT = 120  # 单个任务超时120秒
```

### 处理模式

```python
MODE = "process"  # process=进程池, thread=线程池
```

| 模式 | 适用场景 | 优缺点 |
|------|---------|--------|
| process | CPU密集型（OCR） | 优点：真正并行<br>缺点：内存开销大 |
| thread | I/O密集型（文件读取） | 优点：内存开销小<br>缺点：Python GIL限制 |

## 错误处理

### 单个失败不影响整体

```
证据1.pdf → ✅ 成功
证据2.pdf → ❌ 失败（但继续处理）
证据3.pdf → ✅ 成功
```

### 自动重试

```python
def extract_with_retry(file_path, max_retries=2):
    """带重试的提取"""
    for attempt in range(max_retries):
        try:
            return extract_single_evidence(file_path)
        except Exception as e:
            if attempt == max_retries - 1:
                return {"success": False, "error": str(e)}
            time.sleep(1)
```

### 超时控制

单个任务超过120秒自动终止，继续处理其他任务。

## 输出文件

### 汇总信息

保存在：`<案件目录>/_intermediate/batch_extract_summary.json`

```json
{
  "summary": {
    "total": 10,
    "success": 9,
    "failed": 1,
    "success_rate": 90.0,
    "total_duration": 120.5,
    "avg_duration": 13.4,
    "timestamp": "2026-05-16T20:00:00"
  },
  "results": [
    {
      "file_name": "证据1.pdf",
      "success": true,
      "error": null
    },
    {
      "file_name": "证据2.pdf",
      "success": false,
      "error": "文件损坏"
    }
  ]
}
```

## 进阶功能

### 自定义提取函数

```python
def my_custom_extract(file_path):
    """自定义提取逻辑"""
    # 调用你的Skill
    result = call_skill("case-evidence-cards", file_path)
    return result

# 替换默认提取函数
extractor.extractor = my_custom_extract
```

### 进度回调

```python
def progress_callback(completed, total, result):
    """进度回调"""
    percent = (completed / total) * 100
    print(f"[{completed}/{total} {percent:.0f}%] {result['file_name']}")

extractor.run(progress_callback=progress_callback)
```

## 故障排除

### 问题：内存占用过高

**解决**：减少并发数
```bash
python3 batch_extract.py /path/to/case --workers 2
```

### 问题：OCR速度慢

**解决**：使用更快的OCR引擎
- Tesseract（默认）
- Apple Vision（更快，但仅限macOS）
- 在线OCR API

### 问题：某些文件处理失败

**查看**：
1. 检查`batch_extract_summary.json`
2. 单独处理失败的文件
3. 检查文件格式是否支持

## 技术细节

### 进程池 vs 线程池

```python
# 进程池（CPU密集型）
with ProcessPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(extract, f) for f in files]

# 线程池（I/O密集型）
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(extract, f) for f in files]
```

### 超时处理

```python
future = executor.submit(extract, file_path)
try:
    result = future.result(timeout=120)  # 120秒超时
except TimeoutError:
    future.cancel()
    result = {"success": False, "error": "超时"}
```

## 版本历史

- v1.0 - 初始版本（2026-05-16）
  - 进程池并行
  - 错误处理和重试
  - 进度显示
  - 性能对比
