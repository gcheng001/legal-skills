---
name: batch-evidence-extract
description: 批量证据提取Agent（Phase A内部并行）。多个证据文件同时提取，大幅加速A5步骤。
schedule: "手动触发"
model: claude-sonnet-4-6
permissions:
  read: true
  write: true
  network: false
  tools:
    - read_file
    - write_file
    - parallel_exec
---

# 批量证据提取Agent

## 工作定位

**角色**：并行处理Agent（Phase A内部加速）
**触发**：手动触发（case-evidence-cards Skill调用）
**目标**：多个证据文件同时提取，大幅加速A5步骤

## 并行策略

### 传统串行处理

```
证据1.pdf → Agent → 证据卡片1.md (耗时2分钟)
    ↓
证据2.pdf → Agent → 证据卡片2.md (耗时2分钟)
    ↓
证据3.pdf → Agent → 证据卡片3.md (耗时2分钟)
    ↓
总耗时：6分钟
```

### 并行处理

```
证据1.pdf → Agent1 → 证据卡片1.md ─┐
                                  ├→ 同时进行 (耗时2分钟)
证据2.pdf → Agent2 → 证据卡片2.md ─┤
                                  │
证据3.pdf → Agent3 → 证据卡片3.md ─┘
总耗时：2分钟（3倍加速）
```

## 技术实现

### 使用进程池并行

```python
from concurrent.futures import ProcessPoolExecutor

def extract_evidence(file_path):
    """提取单个证据"""
    # 调用case-evidence-cards Skill
    return skill.execute(file_path)

def batch_extract(files):
    """批量提取"""
    with ProcessPoolExecutor(max_workers=3) as executor:
        results = executor.map(extract_evidence, files)
    return list(results)
```

### 使用线程池（轻量级）

```python
from concurrent.futures import ThreadPoolExecutor

def batch_extract_lightweight(files):
    """批量提取（线程池）"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(extract_evidence, files)
    return list(results)
```

## 工作流程

### 第一步：发现证据文件

扫描案件文件夹，发现需要提取的证据：
```python
def find_evidence_files(case_dir):
    """发现证据文件"""
    evidence_dir = case_dir / "00_原始材料"
    files = []

    for ext in ["*.pdf", "*.jpg", "*.jpeg", "*.png", "*.docx"]:
        files.extend(evidence_dir.glob(ext))

    return files
```

### 第二步：过滤已处理

跳过已经生成卡片的证据：
```python
def filter_processed(files, evidence_cards_dir):
    """过滤已处理的文件"""
    processed = {f.stem for f in evidence_cards_dir.glob("*.md")}
    return [f for f in files if f.stem not in processed]
```

### 第三步：并行提取

启动多个进程/线程同时提取：
```python
def parallel_extract(files):
    """并行提取"""
    # 使用进程池（CPU密集型）
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(extract_single_evidence, f)
            for f in files
        ]
        results = [f.result() for f in futures]

    return results
```

### 第四步：汇总结果

将所有提取结果汇总：
```python
def summarize_results(results):
    """汇总结果"""
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "files": results,
    }

    return summary
```

## 配置

### 并发数控制

```yaml
parallel:
  max_workers: 3  # 最大并发数
  mode: process  # process=进程池, thread=线程池

evidence:
  input_dir: "00_原始材料"
  output_dir: "_intermediate/证据卡片库"
  extensions: [".pdf", ".jpg", ".jpeg", ".png", ".docx"]
```

### 资源限制

```yaml
resources:
  max_memory: "4GB"  # 最大内存使用
  max_cpu: 80%  # 最大CPU使用率
```

## 错误处理

### 单个失败不影响整体

```python
def extract_with_retry(file_path, max_retries=2):
    """带重试的提取"""
    for attempt in range(max_retries):
        try:
            return extract_single_evidence(file_path)
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "file": file_path,
                    "success": False,
                    "error": str(e),
                }
            time.sleep(1)
```

### 超时控制

```python
from concurrent.futures import TimeoutError

def extract_with_timeout(file_path, timeout=120):
    """带超时的提取"""
    with ProcessPoolExecutor() as executor:
        future = executor.submit(extract_single_evidence, file_path)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            future.cancel()
            return {
                "file": file_path,
                "success": False,
                "error": "超时",
            }
```

## 进度显示

### 实时进度

```python
def show_progress(results, total):
    """显示进度"""
    completed = len(results)
    percent = (completed / total) * 100

    print(f"进度：{completed}/{total} ({percent:.1f}%)")

    for result in results:
        if result["success"]:
            print(f"  ✅ {result['file'].name}")
        else:
            print(f"  ❌ {result['file'].name}: {result['error']}")
```

### 进度条（可选）

```python
from tqdm import tqdm

def batch_extract_with_progress(files):
    """带进度条的批量提取"""
    with ThreadPoolExecutor() as executor:
        results = list(tqdm(
            executor.map(extract_single_evidence, files),
            total=len(files),
            desc="提取证据",
        ))
    return results
```

## 集成到案件OS

### 在case-evidence-cards中调用

```python
# case-evidence-cards Skill中

def main():
    """主函数"""
    # 发现证据文件
    files = find_evidence_files(case_dir)

    if len(files) > 1:
        # 多个文件，使用并行提取
        print(f"发现{len(files)}个证据文件，启动并行提取...")
        results = batch_extract(files)
    else:
        # 单个文件，直接提取
        results = [extract_single_evidence(files[0])]

    # 汇总结果
    summary = summarize_results(results)
    print(summary)
```

## 性能对比

| 证据数量 | 串行耗时 | 并行耗时(3worker) | 加速比 |
|---------|---------|------------------|--------|
| 3个 | 6分钟 | 2分钟 | 3x |
| 10个 | 20分钟 | 7分钟 | 2.86x |
| 20个 | 40分钟 | 14分钟 | 2.86x |

## 版本历史

- v1.0 - 初始版本（2026-05-16）
  - 进程池并行
  - 错误处理和重试
  - 进度显示
