#!/usr/bin/env python3
"""
批量证据提取Agent - 实现脚本
多个证据文件同时提取，大幅加速A5步骤
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ==================== 配置 ====================
MAX_WORKERS = 3  # 最大并发数
TIMEOUT = 120  # 单个任务超时时间（秒）
MODE = "process"  # process=进程池, thread=线程池

# 证据文件后缀
EVIDENCE_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".docx", ".doc"]

# ==================== 工具函数 ====================
def find_evidence_files(case_dir: Path) -> List[Path]:
    """发现证据文件"""
    evidence_files = []

    # 扫描00_原始材料目录
    material_dir = case_dir / "00_原始材料"
    if material_dir.exists():
        for ext in EVIDENCE_EXTENSIONS:
            evidence_files.extend(material_dir.glob(f"*{ext}"))
            evidence_files.extend(material_dir.glob(f"*{ext.upper()}"))

    return sorted(evidence_files)


def filter_processed(files: List[Path], evidence_cards_dir: Path) -> List[Path]:
    """过滤已处理的文件"""
    if not evidence_cards_dir.exists():
        return files

    processed = {f.stem for f in evidence_cards_dir.glob("*.md")}
    return [f for f in files if f.stem not in processed]


def extract_single_evidence(file_path: Path) -> Dict:
    """提取单个证据（实际调用case-evidence-cards Skill）

    Args:
        file_path: 证据文件路径

    Returns:
        提取结果
    """
    # TODO: 实际调用case-evidence-cards Skill
    # 这里是模拟实现
    try:
        start_time = time.time()

        # 模拟提取过程（实际应该调用Skill）
        time.sleep(0.5)  # 模拟耗时

        return {
            "file": file_path,
            "file_name": file_path.name,
            "success": True,
            "output": f"{file_path.stem}_证据卡片.md",
            "duration": time.time() - start_time,
        }
    except Exception as e:
        return {
            "file": file_path,
            "file_name": file_path.name,
            "success": False,
            "error": str(e),
        }


def extract_with_timeout(file_path: Path, timeout: int = TIMEOUT) -> Dict:
    """带超时的提取

    Args:
        file_path: 证据文件路径
        timeout: 超时时间（秒）

    Returns:
        提取结果
    """
    try:
        if MODE == "process":
            # 使用进程池
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(extract_single_evidence, file_path)
                result = future.result(timeout=timeout)
                return result
        else:
            # 使用线程池
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(extract_single_evidence, file_path)
                result = future.result(timeout=timeout)
                return result
    except Exception as e:
        return {
            "file": file_path,
            "file_name": file_path.name,
            "success": False,
            "error": f"超时或错误: {str(e)}",
        }


# ==================== 批量提取 ====================
class BatchEvidenceExtractor:
    """批量证据提取器"""

    def __init__(self, case_dir: Path, max_workers: int = MAX_WORKERS):
        self.case_dir = case_dir
        self.max_workers = max_workers
        self.evidence_cards_dir = case_dir / "_intermediate" / "证据卡片库"

    def find_files(self) -> List[Path]:
        """发现需要处理的证据文件"""
        files = find_evidence_files(self.case_dir)

        if not files:
            print("⚠️  未发现证据文件")
            return []

        # 过滤已处理的
        files = filter_processed(files, self.evidence_cards_dir)

        print(f"📁 发现 {len(files)} 个待处理证据文件")
        return files

    def extract_parallel(self, files: List[Path]) -> List[Dict]:
        """并行提取证据

        Args:
            files: 证据文件列表

        Returns:
            提取结果列表
        """
        print(f"🚀 启动并行提取（{MODE}模式，{self.max_workers}并发）")
        print()

        results = []

        if MODE == "process":
            # 使用进程池
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(extract_with_timeout, f): f
                    for f in files
                }

                # 收集结果（带进度显示）
                completed = 0
                total = len(futures)

                for future in as_completed(futures):
                    file_path = futures[future]
                    completed += 1

                    try:
                        result = future.result()
                        results.append(result)

                        # 显示进度
                        percent = (completed / total) * 100
                        status = "✅" if result["success"] else "❌"
                        print(f"[{completed}/{total} {percent:.0f}%] {status} {result['file_name']}")

                    except Exception as e:
                        results.append({
                            "file": file_path,
                            "file_name": file_path.name,
                            "success": False,
                            "error": str(e),
                        })
                        print(f"[{completed}/{total}] ❌ {file_path.name}: {e}")

        else:
            # 使用线程池
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(extract_with_timeout, f): f
                    for f in files
                }

                completed = 0
                total = len(futures)

                for future in as_completed(futures):
                    file_path = futures[future]
                    completed += 1

                    try:
                        result = future.result()
                        results.append(result)

                        percent = (completed / total) * 100
                        status = "✅" if result["success"] else "❌"
                        print(f"[{completed}/{total} {percent:.0f}%] {status} {result['file_name']}")

                    except Exception as e:
                        results.append({
                            "file": file_path,
                            "file_name": file_path.name,
                            "success": False,
                            "error": str(e),
                        })
                        print(f"[{completed}/{total}] ❌ {file_path.name}: {e}")

        return results

    def extract_sequential(self, files: List[Path]) -> List[Dict]:
        """串行提取（对比用）

        Args:
            files: 证据文件列表

        Returns:
            提取结果列表
        """
        print(f"🐌 串行提取模式")
        print()

        results = []
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] 处理：{file_path.name}")
            result = extract_with_timeout(file_path)
            results.append(result)

            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result.get('error', '完成')}")

        return results

    def summarize(self, results: List[Dict]) -> Dict:
        """汇总结果

        Args:
            results: 提取结果列表

        Returns:
            汇总信息
        """
        total = len(results)
        success = sum(1 for r in results if r["success"])
        failed = total - success

        total_duration = sum(r.get("duration", 0) for r in results if r["success"])

        summary = {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "total_duration": total_duration,
            "avg_duration": total_duration / success if success > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

        return summary

    def print_summary(self, summary: Dict, parallel: bool = True):
        """打印汇总信息

        Args:
            summary: 汇总信息
            parallel: 是否并行模式
        """
        print()
        print("=" * 50)
        print("📊 批量提取完成")
        print("=" * 50)
        print(f"模式：{'并行' if parallel else '串行'}")
        print(f"总数：{summary['total']} 个")
        print(f"成功：{summary['success']} 个")
        print(f"失败：{summary['failed']} 个")
        print(f"成功率：{summary['success_rate']:.1f}%")
        print(f"总耗时：{summary['total_duration']:.1f} 秒")
        print(f"平均耗时：{summary['avg_duration']:.1f} 秒/个")

        if parallel and summary['success'] > 1:
            # 计算加速比
            sequential_time = summary['total_duration'] * summary['success']
            speedup = sequential_time / summary['total_duration']
            print(f"加速比：{speedup:.1f}x")

        print("=" * 50)

    def run(self, mode: str = "parallel") -> List[Dict]:
        """运行批量提取

        Args:
            mode: parallel=并行, sequential=串行

        Returns:
            提取结果列表
        """
        # 发现文件
        files = self.find_files()
        if not files:
            return []

        # 提取
        start_time = time.time()

        if mode == "parallel":
            results = self.extract_parallel(files)
        else:
            results = self.extract_sequential(files)

        # 汇总
        summary = self.summarize(results)
        summary["total_duration"] = time.time() - start_time
        self.print_summary(summary, parallel=(mode == "parallel"))

        # 保存结果
        self.save_results(results, summary)

        return results

    def save_results(self, results: List[Dict], summary: Dict):
        """保存提取结果

        Args:
            results: 提取结果列表
            summary: 汇总信息
        """
        # 确保输出目录存在
        self.evidence_cards_dir.parent.mkdir(parents=True, exist_ok=True)

        # 保存汇总信息
        summary_file = self.case_dir / "_intermediate" / "batch_extract_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "results": [
                    {
                        "file_name": r["file_name"],
                        "success": r["success"],
                        "error": r.get("error"),
                    }
                    for r in results
                ],
            }, f, ensure_ascii=False, indent=2)

        print(f"💾 汇总信息已保存：{summary_file}")


# ==================== 命令行接口 ====================
def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="批量证据提取Agent")
    parser.add_argument("case_dir", help="案件目录路径")
    parser.add_argument("--mode", choices=["parallel", "sequential"], default="parallel", help="提取模式")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="最大并发数")

    args = parser.parse_args()

    case_dir = Path(args.case_dir)
    if not case_dir.exists():
        print(f"❌ 错误：案件目录不存在：{case_dir}")
        return 1

    # 创建提取器
    extractor = BatchEvidenceExtractor(case_dir, max_workers=args.workers)

    # 运行
    try:
        extractor.run(mode=args.mode)
        return 0
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        return 1
    except Exception as e:
        print(f"❌ 错误：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
