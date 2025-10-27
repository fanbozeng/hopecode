"""
Batch Parallel Evaluator for Causal Reasoning Framework
批量并行评估器

This module provides batch processing capabilities similar to deep learning batch_size,
allowing multiple problems to be evaluated concurrently using asyncio or threading.

本模块提供类似深度学习 batch_size 的批量处理能力，
允许使用 asyncio 或线程并发评估多个问题。

Usage:
    python batch_evaluator.py --dataset gsm8k --limit 20 --batch-size 5 --methods baselines
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import asdict

# Import existing evaluation framework components
# 导入现有的评估框架组件（不修改原代码）
from evaluate_framework import (
    EvaluationMethod,
    EvaluationResult,
    DatasetLoader,
    FrameworkEvaluator
)


class BatchParallelEvaluator:
    """
    Batch parallel evaluator with concurrent processing support
    支持并发处理的批量并行评估器

    This class wraps the existing FrameworkEvaluator and adds batch processing
    capabilities without modifying the original code.

    此类包装现有的 FrameworkEvaluator 并添加批处理能力，无需修改原始代码。
    """

    def __init__(self, batch_size: int = 1, max_workers: Optional[int] = None, verbose: bool = False, enable_visualization: bool = False):
        """
        Initialize batch evaluator
        初始化批量评估器

        Args:
            batch_size: Number of problems to process concurrently (类似深度学习的 batch_size)
                       并发处理的问题数量（类似深度学习的 batch_size）
            max_workers: Maximum number of worker threads (默认为 batch_size)
                        最大工作线程数（默认为 batch_size）
            verbose: Verbose output
                    详细输出
            enable_visualization: Enable causal graph visualization (NEW!)
                                 启用因果图可视化（新功能！）
        """
        self.batch_size = batch_size
        self.max_workers = max_workers or batch_size
        self.verbose = verbose
        self.enable_visualization = enable_visualization

        # Create a single FrameworkEvaluator instance
        # 创建单个 FrameworkEvaluator 实例
        self.evaluator = FrameworkEvaluator(verbose=verbose)

        print(f"\n{'='*80}")
        print(f"Batch Parallel Evaluator Initialized")
        print(f"批量并行评估器已初始化")
        print(f"  Batch Size: {self.batch_size}")
        print(f"  批量大小: {self.batch_size}")
        print(f"  Max Workers: {self.max_workers}")
        print(f"  最大工作线程: {self.max_workers}")
        print(f"{'='*80}\n")

    def evaluate_single_wrapper(
        self,
        problem: Dict[str, Any],
        method: EvaluationMethod,
        index: int,
        total: int
    ) -> EvaluationResult:
        """
        Wrapper for single evaluation with progress tracking
        单个评估的包装器，带进度跟踪

        Args:
            problem: Problem to evaluate
            method: Evaluation method
            index: Problem index (1-based)
            total: Total number of problems

        Returns:
            EvaluationResult
        """
        if self.verbose:
            print(f"[{index}/{total}] Starting: {problem['id']}")

        # Call the original evaluator's evaluate_single method
        # 调用原始评估器的 evaluate_single 方法（不修改原代码）
        result = self.evaluator.evaluate_single(problem, method)

        # Generate visualization if enabled and scaffold is available
        # 如果启用可视化且脚手架可用，则生成可视化
        if self.enable_visualization and hasattr(result, 'causal_scaffold') and result.causal_scaffold:
            try:
                from engine.causal_graph_visualizer import visualize_causal_graph
                viz_dir = Path("batch_visualizations") / method.value
                viz_dir.mkdir(parents=True, exist_ok=True)
                viz_path = viz_dir / f"{problem['id']}.png"
                visualize_causal_graph(result.causal_scaffold, str(viz_path))
                if self.verbose:
                    print(f"  📊 Visualization: {viz_path}")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️ Visualization failed: {e}")

        # Print result
        # 打印结果
        status = "✓" if result.is_correct else ("⚠" if result.error else "✗")
        print(f"[{index}/{total}] {status} {problem['id']} ({result.execution_time:.2f}s)")

        return result

    def evaluate_batch_threading(
        self,
        problems: List[Dict[str, Any]],
        method: EvaluationMethod
    ) -> List[EvaluationResult]:
        """
        Evaluate a batch of problems using threading
        使用线程评估一批问题

        This method processes multiple problems concurrently using ThreadPoolExecutor.
        此方法使用 ThreadPoolExecutor 并发处理多个问题。

        Args:
            problems: List of problems to evaluate
            method: Evaluation method

        Returns:
            List of EvaluationResults
        """
        results = [None] * len(problems)  # Pre-allocate results list / 预分配结果列表

        # Use ThreadPoolExecutor for concurrent execution
        # 使用 ThreadPoolExecutor 进行并发执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            # 提交所有任务
            future_to_index = {
                executor.submit(
                    self.evaluate_single_wrapper,
                    problem,
                    method,
                    i + 1,
                    len(problems)
                ): i
                for i, problem in enumerate(problems)
            }

            # Collect results as they complete
            # 收集完成的结果
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    print(f"  Error in problem {index + 1}: {e}")
                    # Create error result
                    # 创建错误结果
                    problem = problems[index]
                    results[index] = EvaluationResult(
                        problem_id=problem['id'],
                        method=method.value,
                        problem_text=problem['question'],
                        expected_answer=problem['answer'],
                        predicted_answer=None,
                        is_correct=False,
                        execution_time=0.0,
                        error=str(e)
                    )

        return results

    def evaluate_single_method(
        self,
        problems: List[Dict[str, Any]],
        method: EvaluationMethod,
        method_idx: int,
        total_methods: int
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluate all problems using a single method (runs in parallel with other methods)
        使用单个方法评估所有问题（与其他方法并行运行）

        Args:
            problems: List of problems to evaluate
            method: Evaluation method
            method_idx: Method index for progress display
            total_methods: Total number of methods being evaluated

        Returns:
            Tuple of (method_name, method_results_dict)
        """
        print(f"\n{'-'*80}")
        print(f"[Method {method_idx}/{total_methods}] Starting: {method.value}")
        print(f"[方法 {method_idx}/{total_methods}] 开始: {method.value}")
        print(f"{'-'*80}")

        method_start_time = time.time()

        # Process problems in batches
        # 分批处理问题
        all_method_results = []

        # Split problems into batches
        # 将问题分成批次
        num_batches = (len(problems) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(problems))
            batch_problems = problems[start_idx:end_idx]

            print(f"  [{method.value}] Batch {batch_idx + 1}/{num_batches} (Problems {start_idx + 1}-{end_idx})")
            print(f"  [{method.value}] 批次 {batch_idx + 1}/{num_batches}（问题 {start_idx + 1}-{end_idx}）")

            batch_start_time = time.time()

            # Evaluate batch using threading
            # 使用线程评估批次
            batch_results = self.evaluate_batch_threading(batch_problems, method)
            all_method_results.extend(batch_results)

            batch_time = time.time() - batch_start_time
            print(f"  [{method.value}] Batch completed in {batch_time:.2f}s")
            print(f"  [{method.value}] 批次完成，耗时 {batch_time:.2f}s")

        # Calculate statistics
        # 计算统计信息
        method_time = time.time() - method_start_time
        correct_count = sum(1 for r in all_method_results if r.is_correct)
        error_count = sum(1 for r in all_method_results if r.error)
        accuracy = correct_count / len(problems) if problems else 0
        avg_time = method_time / len(problems) if problems else 0

        # Print summary
        # 打印摘要
        print(f"\n  [{method.value}] ✓ Accuracy: {accuracy*100:.2f}% ({correct_count}/{len(problems)})")
        print(f"  [{method.value}] ✓ 准确率: {accuracy*100:.2f}% ({correct_count}/{len(problems)})")
        print(f"  [{method.value}] ⏱ Total Time: {method_time:.2f}s (Avg: {avg_time:.2f}s per problem)")
        print(f"  [{method.value}] ⏱ 总时间: {method_time:.2f}s（平均: {avg_time:.2f}s 每题）")

        # Return method results
        # 返回方法结果
        method_results = {
            'results': all_method_results,
            'statistics': {
                'total': len(problems),
                'correct': correct_count,
                'wrong': len(problems) - correct_count - error_count,
                'errors': error_count,
                'accuracy': accuracy,
                'total_time': method_time,
                'avg_time': avg_time
            }
        }

        return (method.value, method_results)

    def evaluate_dataset_batch(
        self,
        problems: List[Dict[str, Any]],
        methods: List[EvaluationMethod],
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Evaluate dataset with multiple methods using batch processing
        使用批处理评估多个方法的数据集

        **NEW: All methods run concurrently in parallel!**
        **新功能：所有方法并发并行运行！**

        This is the main entry point that processes problems in batches.
        Each method runs in its own thread, and within each method,
        problems are processed in batches with multi-threading.

        这是以批次处理问题的主要入口点。
        每个方法在自己的线程中运行，在每个方法内部，
        问题以批次并发处理。

        Args:
            problems: List of problems to evaluate
            methods: List of evaluation methods
            dataset_name: Name of the dataset

        Returns:
            Evaluation results dictionary
        """
        print(f"\n{'='*80}")
        print(f"Batch Evaluating {dataset_name} with {len(methods)} methods on {len(problems)} problems")
        print(f"批量评估 {dataset_name}，{len(methods)} 个方法，{len(problems)} 个问题")
        print(f"Batch Size: {self.batch_size}")
        print(f"批量大小: {self.batch_size}")
        print(f"**ALL METHODS WILL RUN CONCURRENTLY**")
        print(f"**所有方法将并发运行**")
        print(f"{'='*80}\n")

        all_results = {}  # 所有结果
        overall_start_time = time.time()

        # Run all methods concurrently using ThreadPoolExecutor
        # 使用 ThreadPoolExecutor 并发运行所有方法
        with ThreadPoolExecutor(max_workers=len(methods)) as method_executor:
            # Submit all method evaluation tasks
            # 提交所有方法评估任务
            future_to_method = {
                method_executor.submit(
                    self.evaluate_single_method,
                    problems,
                    method,
                    idx + 1,
                    len(methods)
                ): method
                for idx, method in enumerate(methods)
            }

            # Collect results as they complete
            # 收集完成的结果
            for future in as_completed(future_to_method):
                method = future_to_method[future]
                try:
                    method_name, method_results = future.result()
                    all_results[method_name] = method_results
                    print(f"\n✓ Method '{method_name}' completed!")
                    print(f"✓ 方法 '{method_name}' 完成！")
                except Exception as e:
                    print(f"\n❌ Error in method {method.value}: {e}")
                    print(f"❌ 方法 {method.value} 出错: {e}")
                    import traceback
                    traceback.print_exc()

        overall_time = time.time() - overall_start_time
        print(f"\n{'='*80}")
        print(f"✓ All methods completed in {overall_time:.2f}s")
        print(f"✓ 所有方法在 {overall_time:.2f}s 内完成")
        print(f"{'='*80}\n")

        # Return results in the same format as FrameworkEvaluator
        # 以与 FrameworkEvaluator 相同的格式返回结果
        return {
            'dataset_name': dataset_name,
            'total_problems': len(problems),
            'methods': all_results,
            'evaluation_time': datetime.now().isoformat(),
            'batch_config': {
                'batch_size': self.batch_size,
                'max_workers': self.max_workers,
                'concurrent_methods': True  # NEW: Indicate methods run concurrently
            }
        }

    def save_results(self, results: Dict[str, Any], output_path: str):
        """
        Save results to JSON (reuses FrameworkEvaluator's save logic)
        保存结果到 JSON（复用 FrameworkEvaluator 的保存逻辑）
        """
        # Convert results to serializable format
        # 转换结果为可序列化格式
        serializable_results = {
            'dataset_name': results['dataset_name'],
            'total_problems': results['total_problems'],
            'evaluation_time': results['evaluation_time'],
            'batch_config': results.get('batch_config', {}),
            'methods': {}
        }

        # Convert dataclass results to dicts
        # 转换 dataclass 结果为字典
        for method_name, method_data in results['methods'].items():
            serializable_results['methods'][method_name] = {
                'statistics': method_data['statistics'],
                'results': [asdict(r) for r in method_data['results']]
            }

        # Save to file
        # 保存到文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to: {output_file}")
        print(f"✓ 结果已保存到: {output_file}")

    def print_comparison_table(self, results: Dict[str, Any]):
        """
        Print comparison table (reuses FrameworkEvaluator's print logic)
        打印对比表（复用 FrameworkEvaluator 的打印逻辑）
        """
        print(f"\n{'='*80}")
        print(f"COMPARISON TABLE / 对比表")
        print(f"{'='*80}")
        print(f"Dataset: {results['dataset_name']}")
        print(f"数据集: {results['dataset_name']}")

        if 'batch_config' in results:
            print(f"Batch Size: {results['batch_config']['batch_size']}")
            print(f"批量大小: {results['batch_config']['batch_size']}")

        print()

        # Print table header
        # 打印表头
        print(f"{'Method':<30} {'Accuracy':<15} {'Avg Time':<15} {'Total Time':<15}")
        print(f"{'方法':<30} {'准确率':<15} {'平均时间':<15} {'总时间':<15}")
        print(f"{'-'*80}")

        # Print results for each method
        # 打印每个方法的结果
        for method_name, method_data in results['methods'].items():
            stats = method_data['statistics']
            acc_str = f"{stats['accuracy']*100:.2f}%"
            avg_time_str = f"{stats['avg_time']:.2f}s"
            total_time_str = f"{stats['total_time']:.2f}s"
            print(f"{method_name:<30} {acc_str:<15} {avg_time_str:<15} {total_time_str:<15}")

        print(f"{'='*80}\n")


def main():
    """Main function for batch evaluation / 批量评估的主函数"""
    import argparse

    # Parse command line arguments
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="Batch Parallel Evaluation for Causal Reasoning Framework\n"
                    "批量并行评估因果推理框架"
    )

    # Dataset selection / 数据集选择
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['gsm8k', 'math', 'mydata', 'omnimath', 'olympiad'],  # 新增 / Added
        default='omnimath',
        help='Dataset to evaluate / 要评估的数据集'
    )

    # Problem limit / 问题数量限制
    parser.add_argument(
        '--limit',
        type=int,
        default=2,
        help='Limit number of problems / 限制问题数量'
    )

    # Batch size (NEW FEATURE!)
    # 批量大小（新功能！）
    parser.add_argument(
        '--batch-size',
        type=int,
        default=3,
        help='Number of problems to process concurrently (like batch_size in deep learning) / '
             '并发处理的问题数量（类似深度学习中的 batch_size）'
    )

    # Max workers / 最大工作线程数
    parser.add_argument(
        '--max-workers',
        type=int,
        default=None,
        help='Maximum number of worker threads (defaults to batch_size) / '
             '最大工作线程数（默认为 batch_size）'
    )

    # Methods to evaluate / 评估方法
    parser.add_argument(
        '--methods',
        type=str,
        nargs='+',
        choices=['baselines', 'ablations', 'all'],
        default=['baselines'],
        help='Evaluation methods / 评估方法'
    )

    # Output directory / 输出目录
    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_results',
        help='Output directory / 输出目录'
    )

    # Verbose output / 详细输出
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output / 详细输出'
    )

    # Enable visualization / 启用可视化 (NEW!)
    parser.add_argument(
        '--enable-viz',
        action='store_true',
        help='Enable causal graph visualization for each problem / 为每个问题生成因果图可视化'
    )

    args = parser.parse_args()

    # Determine which methods to run
    # 确定要运行的方法
    methods_to_run = []

    if 'baselines' in args.methods or 'all' in args.methods:
        methods_to_run.extend([
            EvaluationMethod.DIRECT_LLM,
            EvaluationMethod.ZERO_SHOT_COT,
            # EvaluationMethod.FEW_SHOT_COT,
            EvaluationMethod.FULL_FRAMEWORK
        ])

    if 'ablations' in args.methods or 'all' in args.methods:
        methods_to_run.extend([
            EvaluationMethod.NO_RETRIEVER,
            EvaluationMethod.NO_AI_RETRIEVER,
            EvaluationMethod.NO_SYMBOLIC_EXECUTION
        ])

    # Load dataset
    # 加载数据集
    loader = DatasetLoader()

    if args.dataset == 'gsm8k':
        dataset_path = "dataset/GSM8K/grade_school_math/data/test.jsonl"
        problems = loader.load_gsm8k(dataset_path, limit=args.limit)
        dataset_name = "GSM8K"
    elif args.dataset == 'math':
        dataset_path = "dataset/Math/test-00000-of-00001.parquet.json"
        problems = loader.load_math(dataset_path, limit=args.limit)
        dataset_name = "MATH"
    elif args.dataset == 'mydata':
        dataset_path = "dataset/mydata/data/2024A.json"
        problems = loader.load_mydata(dataset_path, limit=args.limit)
        dataset_name = "MyData_2024A"
    elif args.dataset == 'omnimath':
        # Omni-MATH（新增 / NEW!）
        dataset_path = "dataset/Omni-MATH/archive/main_test.jsonl"
        problems = loader.load_omnimath(dataset_path, limit=args.limit)
        dataset_name = "Omni-MATH"
    elif args.dataset == 'olympiad':
        # OlympiadBench（新增，多模态支持 / NEW! Multi-Modal）
        dataset_path = "dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/OE_TO_physics_zh_CEE.json"
        problems = loader.load_olympiadbench(dataset_path, limit=args.limit)
        dataset_name = "OlympiadBench"
        print("\n💡 Tip: Olympiad problems are very challenging!")
        print("💡 提示：奥林匹克问题非常有挑战性！\n")
    else:
        print(f"❌ Unknown dataset: {args.dataset}")
        return 1

    # Check if dataset exists
    # 检查数据集是否存在
    if not Path(dataset_path).exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return 1

    # Create batch evaluator (NEW!)
    # 创建批量评估器（新功能！）
    evaluator = BatchParallelEvaluator(
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        verbose=args.verbose,
        enable_visualization=args.enable_viz  # NEW: Enable visualization / 新增：启用可视化
    )

    # Run batch evaluation
    # 运行批量评估
    results = evaluator.evaluate_dataset_batch(problems, methods_to_run, dataset_name)

    # Print comparison table
    # 打印对比表
    evaluator.print_comparison_table(results)

    # Save results
    # 保存结果
    output_path = f"{args.output}/{dataset_name}_batch_comparison.json"
    evaluator.save_results(results, output_path)

    print(f"\n{'='*80}")
    print(f"✓ Batch evaluation completed successfully!")
    print(f"✓ 批量评估成功完成！")
    print(f"{'='*80}\n")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ Evaluation interrupted by user.")
        print("⚠ 用户中断评估。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
