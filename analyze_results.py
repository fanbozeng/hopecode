#!/usr/bin/env python3
"""
Evaluation Results Analyzer
评估结果分析器

This script analyzes JSON results from batch_evaluator.py or evaluate_framework.py
to provide detailed insights into which methods succeed or fail on specific problems.

此脚本分析来自 batch_evaluator.py 或 evaluate_framework.py 的 JSON 结果，
提供关于哪些方法在特定问题上成功或失败的详细洞察。

Usage / 用法:
    python analyze_results.py --file evaluation_results/MATH_batch_comparison.json
    python analyze_results.py --file evaluation_results/GSM8K_comparison.json --problem-id gsm8k_5
    python analyze_results.py --file evaluation_results/*.json --export csv
"""

import json
import argparse
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import pandas as pd


class EvaluationAnalyzer:
    """
    Evaluation Results Analyzer
    评估结果分析器
    """

    def __init__(self, file_path: str):
        """
        Initialize analyzer with a JSON results file
        用JSON结果文件初始化分析器
        """
        self.file_path = Path(file_path)
        self.data = self._load_results()
        self.dataset_name = self.data.get('dataset_name', 'Unknown')
        self.methods = self.data.get('methods', {})
        self.problems_count = self.data.get('total_problems', 0)

    def _load_results(self) -> Dict[str, Any]:
        """Load JSON results file / 加载JSON结果文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load {self.file_path}: {e}")

    def print_overview(self):
        """Print overview of evaluation results / 打印评估结果概览"""
        print(f"\n{'='*80}")
        print(f"EVALUATION RESULTS OVERVIEW")
        print(f"评估结果概览")
        print(f"{'='*80}")
        print(f"Dataset: {self.dataset_name}")
        print(f"数据集: {self.dataset_name}")
        print(f"Total Problems: {self.problems_count}")
        print(f"总问题数: {self.problems_count}")
        print(f"Methods Evaluated: {len(self.methods)}")
        print(f"评估方法数: {len(self.methods)}")

        if 'batch_config' in self.data:
            config = self.data['batch_config']
            print(f"Batch Size: {config.get('batch_size', 'N/A')}")
            print(f"批量大小: {config.get('batch_size', 'N/A')}")
            if config.get('concurrent_methods'):
                print(f"Concurrent Methods: Yes")
                print(f"并发方法: 是")

        print(f"\nMethod Performance Summary:")
        print(f"方法性能摘要:")
        print(f"{'Method':<25} {'Accuracy':<12} {'Correct':<10} {'Wrong':<10} {'Errors':<10}")
        print(f"{'方法':<25} {'准确率':<12} {'正确':<10} {'错误':<10} {'异常':<10}")
        print(f"{'-'*80}")

        for method_name, method_data in self.methods.items():
            stats = method_data['statistics']
            acc = stats['accuracy'] * 100
            print(f"{method_name:<25} {acc:<12.2f}% {stats['correct']:<10} {stats['wrong']:<10} {stats['errors']:<10}")

        print(f"{'='*80}")

    def analyze_problem_performance(self, problem_id: Optional[str] = None):
        """
        Analyze performance on specific problem or all problems
        分析特定问题或所有问题的性能

        Args:
            problem_id: Specific problem ID to analyze (None for all problems)
        """
        if problem_id:
            self._analyze_single_problem(problem_id)
        else:
            self._analyze_all_problems()

    def _analyze_single_problem(self, problem_id: str):
        """Analyze performance on a single problem / 分析单个问题的性能"""
        print(f"\n{'='*80}")
        print(f"ANALYSIS FOR PROBLEM: {problem_id}")
        print(f"问题分析: {problem_id}")
        print(f"{'='*80}")

        found = False
        method_results = {}

        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                if result['problem_id'] == problem_id:
                    found = True
                    method_results[method_name] = result
                    break

        if not found:
            print(f"❌ Problem {problem_id} not found in results!")
            print(f"❌ 在结果中未找到问题 {problem_id}！")
            return

        # Display problem
        problem_text = next(iter(method_results.values()))['problem_text']
        expected_answer = next(iter(method_results.values()))['expected_answer']

        print(f"\n📋 Problem:")
        print(f"📋 问题:")
        print(f"{problem_text[:200]}..." if len(problem_text) > 200 else problem_text)
        print(f"\n🎯 Expected Answer: {expected_answer}")
        print(f"🎯 期望答案: {expected_answer}")

        # Display method results
        print(f"\n📊 Method Results:")
        print(f"📊 方法结果:")
        print(f"{'Method':<25} {'Status':<10} {'Predicted':<30} {'Time(s)':<10}")
        print(f"{'方法':<25} {'状态':<10} {'预测':<30} {'时间(秒)':<10}")
        print(f"{'-'*80}")

        correct_methods = []
        wrong_methods = []
        error_methods = []

        for method_name, result in method_results.items():
            status = "✓ Correct" if result['is_correct'] else ("⚠ Error" if result['error'] else "✗ Wrong")
            predicted = str(result['predicted_answer'] or 'None')[:28]
            time_taken = f"{result['execution_time']:.2f}"

            print(f"{method_name:<25} {status:<10} {predicted:<30} {time_taken:<10}")

            if result['is_correct']:
                correct_methods.append(method_name)
            elif result['error']:
                error_methods.append(method_name)
            else:
                wrong_methods.append(method_name)

        # Summary
        print(f"\n📈 Summary:")
        print(f"📈 摘要:")
        print(f"  Correct methods ({len(correct_methods)}): {', '.join(correct_methods) if correct_methods else 'None'}")
        print(f"  正确的方法 ({len(correct_methods)}): {', '.join(correct_methods) if correct_methods else '无'}")
        print(f"  Wrong methods ({len(wrong_methods)}): {', '.join(wrong_methods) if wrong_methods else 'None'}")
        print(f"  错误的方法 ({len(wrong_methods)}): {', '.join(wrong_methods) if wrong_methods else '无'}")
        print(f"  Error methods ({len(error_methods)}): {', '.join(error_methods) if error_methods else 'None'}")
        print(f"  异常的方法 ({len(error_methods)}): {', '.join(error_methods) if error_methods else '无'}")

    def _analyze_all_problems(self):
        """Analyze performance across all problems / 分析所有问题的性能"""
        print(f"\n{'='*80}")
        print(f"CROSS-PROBLEM ANALYSIS")
        print(f"跨问题分析")
        print(f"{'='*80}")

        # Problem difficulty analysis
        problem_difficulty = self._analyze_problem_difficulty()

        # Method comparison
        method_comparison = self._compare_methods()

        # Error analysis
        error_analysis = self._analyze_errors()

    def _analyze_problem_difficulty(self) -> Dict[str, Any]:
        """Analyze problem difficulty based on success rates / 基于成功率分析问题难度"""
        print(f"\n📊 Problem Difficulty Analysis:")
        print(f"📊 问题难度分析:")

        problem_stats = {}
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                problem_id = result['problem_id']
                if problem_id not in problem_stats:
                    problem_stats[problem_id] = {
                        'correct_count': 0,
                        'total_attempts': 0,
                        'methods_correct': [],
                        'methods_wrong': [],
                        'methods_error': []
                    }

                problem_stats[problem_id]['total_attempts'] += 1
                if result['is_correct']:
                    problem_stats[problem_id]['correct_count'] += 1
                    problem_stats[problem_id]['methods_correct'].append(method_name)
                elif result['error']:
                    problem_stats[problem_id]['methods_error'].append(method_name)
                else:
                    problem_stats[problem_id]['methods_wrong'].append(method_name)

        # Calculate difficulty and categorize
        easy_problems = []
        medium_problems = []
        hard_problems = []

        for problem_id, stats in problem_stats.items():
            success_rate = stats['correct_count'] / stats['total_attempts']
            if success_rate >= 0.75:
                easy_problems.append((problem_id, success_rate))
            elif success_rate >= 0.25:
                medium_problems.append((problem_id, success_rate))
            else:
                hard_problems.append((problem_id, success_rate))

        # Sort by difficulty
        easy_problems.sort(key=lambda x: x[1], reverse=True)
        hard_problems.sort(key=lambda x: x[1])

        print(f"\n  Easy Problems (>=75% success rate):")
        print(f"  简单问题 (成功率>=75%):")
        for problem_id, rate in easy_problems[:5]:
            print(f"    {problem_id}: {rate*100:.1f}%")

        print(f"\n  Hard Problems (<=25% success rate):")
        print(f"  困难问题 (成功率<=25%):")
        for problem_id, rate in hard_problems[:5]:
            print(f"    {problem_id}: {rate*100:.1f}%")

        return problem_stats

    def _compare_methods(self) -> Dict[str, Any]:
        """Compare methods across all problems / 在所有问题上比较方法"""
        print(f"\n🔍 Method Comparison:")
        print(f"🔍 方法比较:")

        # Find problems where methods differ
        disagreement_problems = []
        unique_correct = defaultdict(list)
        problem_details = {}  # Store problem details for reference

        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                problem_id = result['problem_id']
                if problem_id not in problem_details:
                    problem_details[problem_id] = {
                        'question': result['problem_text'],
                        'expected_answer': result['expected_answer']
                    }

                if result['is_correct']:
                    unique_correct[problem_id].append(method_name)

        # Find disagreements and categorize
        exclusive_correct = defaultdict(list)  # Only one method correct
        multiple_correct = []  # Multiple methods correct
        all_wrong = []  # All methods wrong

        all_methods = set(self.methods.keys())

        for problem_id, correct_methods in unique_correct.items():
            if len(correct_methods) == 1 and len(correct_methods) < len(all_methods):
                # Only one method correct, others wrong - THIS IS WHAT WE WANT!
                exclusive_correct[correct_methods[0]].append(problem_id)
                disagreement_problems.append((problem_id, correct_methods))
            elif len(correct_methods) > 1 and len(correct_methods) < len(all_methods):
                # Multiple methods correct, some wrong
                multiple_correct.append((problem_id, correct_methods))
                disagreement_problems.append((problem_id, correct_methods))

        # Find problems where all methods failed
        all_evaluated_problems = set()
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                all_evaluated_problems.add(result['problem_id'])

        for problem_id in all_evaluated_problems:
            if problem_id not in unique_correct:
                all_wrong.append(problem_id)

        # **重点显示：各方法独有的优势题目**
        print(f"\n🎯 EXCLUSIVE ADVANTAGE PROBLEMS (Only this method succeeded):")
        print(f"🎯 独有优势题目（只有此方法成功）:")

        for method_name in sorted(self.methods.keys()):
            exclusive_problems = exclusive_correct.get(method_name, [])
            if exclusive_problems:
                print(f"\n  🏆 {method_name} EXCLUSIVE WINS ({len(exclusive_problems)} problems):")
                print(f"  🏆 {method_name} 独有成功 ({len(exclusive_problems)} 个问题):")
                print(f"    {'Problem ID':<15} {'Expected Answer':<25} {'Question Preview':<40}")
                print(f"    {'问题ID':<15} {'期望答案':<25} {'问题预览':<40}")
                print(f"    {'-'*80}")

                for problem_id in exclusive_problems[:10]:  # Show first 10
                    details = problem_details.get(problem_id, {})
                    question_preview = details.get('question', '')[:35] + "..." if details.get('question') else "N/A"
                    expected_answer = str(details.get('expected_answer', 'N/A'))[:23]
                    print(f"    {problem_id:<15} {expected_answer:<25} {question_preview:<40}")

                if len(exclusive_problems) > 10:
                    print(f"    ... and {len(exclusive_problems) - 10} more problems")
                    print(f"    ... 还有 {len(exclusive_problems) - 10} 个问题")
            else:
                print(f"\n  ❌ {method_name}: No exclusive wins (no problems solved only by this method)")
                print(f"  ❌ {method_name}: 无独有成功（没有只有此方法解决的问题）")

        # Show problems where multiple methods succeeded
        if multiple_correct:
            print(f"\n🤝 Problems with Multiple Correct Methods:")
            print(f"🤝 多个方法都正确的问题:")
            print(f"  {'Problem ID':<15} {'Correct Methods':<40}")
            print(f"  {'问题ID':<15} {'正确方法':<40}")
            print(f"  {'-'*60}")

            for problem_id, correct_methods in sorted(multiple_correct, key=lambda x: len(x[1]), reverse=True)[:10]:
                correct_str = ', '.join(correct_methods)
                print(f"  {problem_id:<15} {correct_str:<40}")

        # Show problems where all methods failed
        if all_wrong:
            print(f"\n💀 Problems Where ALL Methods Failed ({len(all_wrong)} problems):")
            print(f"💀 所有方法都失败的问题 ({len(all_wrong)} 个问题):")
            for problem_id in all_wrong[:5]:
                print(f"    {problem_id}")

        # Summary statistics
        print(f"\n📊 Summary Statistics:")
        print(f"📊 统计摘要:")
        print(f"  Total problems analyzed: {len(all_evaluated_problems)}")
        print(f"  分析的总问题数: {len(all_evaluated_problems)}")

        for method_name in sorted(self.methods.keys()):
            exclusive_count = len(exclusive_correct.get(method_name, []))
            print(f"  {method_name}: {exclusive_count} exclusive wins ({exclusive_count/len(all_evaluated_problems)*100:.1f}%)")
            print(f"  {method_name}: {exclusive_count} 个独有成功 ({exclusive_count/len(all_evaluated_problems)*100:.1f}%)")

        return {
            'exclusive_correct': exclusive_correct,
            'multiple_correct': multiple_correct,
            'all_wrong': all_wrong,
            'problem_details': problem_details
        }

    def _analyze_errors(self):
        """Analyze common errors across methods / 分析各方法的常见错误"""
        print(f"\n❌ Error Analysis:")
        print(f"❌ 错误分析:")

        error_stats = defaultdict(list)
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                if result['error']:
                    error_stats[method_name].append(result['error'])

        print(f"\n  Error Counts by Method:")
        print(f"  各方法错误计数:")
        for method_name, errors in error_stats.items():
            print(f"    {method_name}: {len(errors)} errors")

            # Show unique error types (first 3)
            unique_errors = list(set(errors))[:3]
            for error in unique_errors:
                print(f"      - {error[:80]}...")

    def generate_comparison_table(self):
        """Generate detailed comparison table / 生成详细对比表"""
        print(f"\n{'='*80}")
        print(f"DETAILED COMPARISON TABLE")
        print(f"详细对比表")
        print(f"{'='*80}")

        # Create DataFrame for easier analysis
        data_rows = []
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                data_rows.append({
                    'Problem_ID': result['problem_id'],
                    'Method': method_name,
                    'Status': 'Correct' if result['is_correct'] else ('Error' if result['error'] else 'Wrong'),
                    'Expected': result['expected_answer'],
                    'Predicted': str(result['predicted_answer'] or ''),
                    'Time': result['execution_time'],
                    'Error': result['error'] or ''
                })

        if not data_rows:
            print("No data available for table generation!")
            return

        df = pd.DataFrame(data_rows)

        # Summary by problem
        print(f"\n📊 Problem-wise Summary (first 20 problems):")
        print(f"📊 按问题总结 (前20个问题):")
        problem_summary = df.groupby('Problem_ID').agg({
            'Method': 'count',
            'Status': lambda x: (x == 'Correct').sum(),
            'Time': 'mean'
        }).round(2)
        problem_summary.columns = ['Total_Attempts', 'Correct_Count', 'Avg_Time']
        problem_summary = problem_summary.head(20)
        print(problem_summary.to_string())

    def export_analysis(self, format_type: str = 'csv'):
        """
        Export analysis to file
        导出分析到文件

        Args:
            format_type: Export format ('csv' or 'excel')
        """
        print(f"\n📤 Exporting analysis to {format_type.upper()}...")

        # Create basic data for export
        export_data = []
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                export_data.append({
                    'Problem_ID': result['problem_id'],
                    'Method': method_name,
                    'Dataset': self.dataset_name,
                    'Is_Correct': result['is_correct'],
                    'Expected_Answer': result['expected_answer'],
                    'Predicted_Answer': str(result['predicted_answer'] or ''),
                    'Execution_Time': result['execution_time'],
                    'Error_Message': result['error'] or '',
                    'Reasoning_Steps': str(result.get('reasoning_steps', '') or '')
                })

        df = pd.DataFrame(export_data)

        # **重点：生成独有优势题目分析**
        exclusive_wins = []
        problem_results = defaultdict(dict)  # problem_id -> {method: is_correct}

        # Build problem results matrix
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                problem_results[result['problem_id']][method_name] = result['is_correct']

        # Find exclusive wins
        for problem_id, method_results in problem_results.items():
            correct_methods = [method for method, is_correct in method_results.items() if is_correct]
            wrong_methods = [method for method, is_correct in method_results.items() if not is_correct]

            if len(correct_methods) == 1 and len(correct_methods) < len(self.methods):
                # Only one method correct, others wrong - EXCLUSIVE WIN!
                winning_method = correct_methods[0]

                # Get problem details
                problem_details = None
                for method_data in self.methods.values():
                    for result in method_data['results']:
                        if result['problem_id'] == problem_id:
                            problem_details = result
                            break
                    if problem_details:
                        break

                exclusive_wins.append({
                    'Problem_ID': problem_id,
                    'Winning_Method': winning_method,
                    'Question': problem_details['problem_text'] if problem_details else '',
                    'Expected_Answer': problem_details['expected_answer'] if problem_details else '',
                    'Failing_Methods': ', '.join(wrong_methods),
                    'Winning_Prediction': str(problem_details['predicted_answer'] or '') if problem_details else '',
                    'Total_Methods': len(self.methods),
                    'Correct_Methods': len(correct_methods),
                    'Wrong_Methods': len(wrong_methods)
                })

        # Generate filename
        base_name = self.file_path.stem
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

        if format_type == 'csv':
            output_path = f"{base_name}_analysis_{timestamp}.csv"
            df.to_csv(output_path, index=False, encoding='utf-8')

            # **导出独有优势题目到单独文件**
            if exclusive_wins:
                exclusive_df = pd.DataFrame(exclusive_wins)
                exclusive_path = f"{base_name}_exclusive_wins_{timestamp}.csv"
                exclusive_df.to_csv(exclusive_path, index=False, encoding='utf-8')
                print(f"🏆 Exclusive wins exported to: {exclusive_path}")

        elif format_type == 'excel':
            output_path = f"{base_name}_analysis_{timestamp}.xlsx"
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # All results
                df.to_excel(writer, sheet_name='All_Results', index=False)

                # Summary sheet
                summary_df = df.groupby('Method').agg({
                    'Is_Correct': ['count', 'sum', 'mean'],
                    'Execution_Time': 'mean'
                }).round(4)
                summary_df.columns = ['Total', 'Correct', 'Accuracy', 'Avg_Time']
                summary_df.to_excel(writer, sheet_name='Summary', index=True)

                # **重点：按题目组织的对比表（用户想要的格式）**
                problem_comparison_df = self._create_problem_comparison_table()
                problem_comparison_df.to_excel(writer, sheet_name='Problem_Comparison', index=False)

                # **独有优势题目表**
                if exclusive_wins:
                    exclusive_df = pd.DataFrame(exclusive_wins)
                    exclusive_df.to_excel(writer, sheet_name='Exclusive_Wins', index=False)

                # **方法对比矩阵**
                comparison_matrix = self._create_comparison_matrix()
                comparison_matrix.to_excel(writer, sheet_name='Method_Matrix', index=False)

        print(f"✅ Analysis exported to: {output_path}")
        if exclusive_wins:
            print(f"🏆 Found {len(exclusive_wins)} exclusive advantage problems!")

    def _create_problem_comparison_table(self) -> pd.DataFrame:
        """
        Create WIDE FORMAT comparison table - methods as columns:
        Problem_ID | direct_llm | zero_shot_cot | few_shot_cot | full_framework | Expected_Answer | Question

        创建宽格式对比表 - 方法作为列并列显示：
        题号 | 方法1 | 方法2 | 方法3 | 方法4 | 期望答案 | 问题
        """
        print(f"\n📊 Creating WIDE FORMAT comparison table (methods as columns)...")

        # Collect problem data
        problem_data = {}
        method_names = sorted(self.methods.keys())

        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                problem_id = result['problem_id']

                if problem_id not in problem_data:
                    problem_data[problem_id] = {
                        'Problem_ID': problem_id,
                        'Expected_Answer': result['expected_answer'],
                        'Dataset': self.dataset_name,
                        'Question': result['problem_text']
                    }

                # Store method's predicted answer directly
                problem_data[problem_id][method_name] = str(result['predicted_answer'] or '')

        # Convert to DataFrame
        df_data = [problem_data[pid] for pid in sorted(problem_data.keys())]
        df = pd.DataFrame(df_data)

        # Reorder columns: Problem_ID, methods (sorted), Expected_Answer, Dataset, Question
        columns = ['Problem_ID'] + method_names + ['Expected_Answer', 'Dataset', 'Question']
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]

        print(f"✅ Created comparison table: {len(df)} problems × {len(method_names)} methods")
        print(f"📊 Columns: Problem_ID | {' | '.join(method_names)} | Expected_Answer | Dataset | Question")

        return df

    def _create_comparison_matrix(self) -> pd.DataFrame:
        """
        Create a simple comparison matrix: Problem_ID | Method_A | Method_B | Method_C | Status
        创建简单的对比矩阵：题号 | 方法A | 方法B | 方法C | 状态
        """
        print(f"\n📊 Creating method comparison matrix...")

        problem_results = {}
        method_names = sorted(self.methods.keys())

        # Build results matrix
        for method_name, method_data in self.methods.items():
            for result in method_data['results']:
                problem_id = result['problem_id']

                if problem_id not in problem_results:
                    problem_results[problem_id] = {
                        'Problem_ID': problem_id,
                        'Expected_Answer': result['expected_answer']
                    }
                    for method in method_names:
                        problem_results[problem_id][method] = '❌'

                if result['is_correct']:
                    problem_results[problem_id][method_name] = '✅'
                elif result['error']:
                    problem_results[problem_id][method_name] = '⚠️'
                else:
                    problem_results[problem_id][method_name] = '❌'

        # Determine overall status
        matrix_data = []
        for problem_id in sorted(problem_results.keys()):
            row = problem_results[problem_id]

            # Count correct methods
            correct_count = sum(1 for method in method_names if row[method] == '✅')
            total_methods = len(method_names)

            if correct_count == total_methods:
                status = '🟢 All Correct'
            elif correct_count == 0:
                status = '🔴 All Wrong'
            elif correct_count == 1:
                status = '🏆 Exclusive Win'
            else:
                status = f'🟡 Partial ({correct_count}/{total_methods})'

            row['Status'] = status
            matrix_data.append(row)

        df = pd.DataFrame(matrix_data)

        # Reorder columns
        columns = ['Problem_ID', 'Status'] + method_names + ['Expected_Answer']
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]

        print(f"✅ Created comparison matrix with {len(df)} problems")

        return df


def main():
    """Main function / 主函数"""
    parser = argparse.ArgumentParser(
        description="Analyze evaluation results from batch evaluation"
    )

    parser.add_argument(
        '--file', '-f',
        type=str,
        required=True,
        help='Path to evaluation results JSON file (supports wildcards like *.json)'
    )

    parser.add_argument(
        '--problem-id', '-p',
        type=str,
        help='Analyze specific problem ID'
    )

    parser.add_argument(
        '--export', '-e',
        type=str,
        choices=['csv', 'excel'],
        help='Export analysis to CSV or Excel file'
    )

    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed comparison table'
    )

    args = parser.parse_args()

    # Handle wildcards in file path
    file_paths = glob.glob(args.file)
    if not file_paths:
        print(f"❌ No files found matching: {args.file}")
        return

    # Analyze each file
    for file_path in file_paths:
        print(f"\n🔍 Analyzing: {file_path}")
        print("=" * 100)

        try:
            analyzer = EvaluationAnalyzer(file_path)
            analyzer.print_overview()

            if args.problem_id:
                analyzer.analyze_problem_performance(args.problem_id)
            else:
                analyzer.analyze_problem_performance()

            if args.detailed:
                analyzer.generate_comparison_table()

            if args.export:
                analyzer.export_analysis(args.export)

        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*100}")
    print("✅ Analysis complete!")
    print("✅ 分析完成！")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()