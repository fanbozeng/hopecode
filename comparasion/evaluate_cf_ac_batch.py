"""
批量CF/AC评估工具
Batch CF/AC Evaluation Tool

功能 / Features:
1. 扫描 comparasion/results/ 目录下的所有结果JSON
   Scan all result JSON files in comparasion/results/
2. 对每个结果调用 causal_evaluation.py 计算CF和AC
   Call causal_evaluation.py to compute CF and AC for each result
3. 将CF/AC分数写回JSON文件
   Write CF/AC scores back to JSON files
4. 支持断点续传（已评估的跳过）
   Support resume (skip already evaluated files)
5. 进度条显示
   Progress bar display

使用方法 / Usage:
    # 评估所有结果文件
    python comparasion/evaluate_cf_ac_batch.py

    # 指定结果目录
    python comparasion/evaluate_cf_ac_batch.py --results-dir comparasion/results

    # 重新评估所有文件（忽略缓存）
    python comparasion/evaluate_cf_ac_batch.py --no-cache

    # 只评估指定方法
    python comparasion/evaluate_cf_ac_batch.py --methods direct_llm cfgo

    # 静默模式
    python comparasion/evaluate_cf_ac_batch.py --quiet
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 导入评估模块
from causal_evaluation import (
    CausalInterventionEvaluator,
    AbductiveReasoningEvaluator,
    RewardEvaluator
)


class CFACBatchEvaluator:
    """批量CF/AC评估器 / Batch CF/AC Evaluator"""
    
    def __init__(
        self,
        results_dir: str = "comparasion/results",
        output_mode: str = "append",
        use_cache: bool = True,
        verbose: bool = True
    ):
        """
        初始化批量评估器 / Initialize batch evaluator
        
        Args:
            results_dir: 结果目录 / Results directory
            output_mode: 输出模式 / Output mode
                - "append": 在原JSON中添加cf_score和ac_score
                - "separate": 生成新的 *_evaluated.json 文件
            use_cache: 是否跳过已评估的文件 / Whether to skip already evaluated files
            verbose: 是否显示详细进度 / Whether to show detailed progress
        """
        self.results_dir = Path(results_dir)
        self.output_mode = output_mode
        self.use_cache = use_cache
        self.verbose = verbose
        
        # 初始化评估器 / Initialize evaluators
        if self.verbose:
            print("🔧 Initializing evaluators...")
            print("🔧 初始化评估器...")
        
        # CF评估器：Causal Intervention + Logic Quality + Graph Quality
        self.causal_evaluator = CausalInterventionEvaluator(verbose=False)
        
        # AC评估器：Abductive Reasoning
        self.abductive_evaluator = AbductiveReasoningEvaluator(verbose=False)
        
        # 奖励评估器（用于Logic Quality和Graph Quality）
        self.reward_evaluator = RewardEvaluator(verbose=False)
        
        if self.verbose:
            print("✅ Evaluators initialized successfully!")
            print("✅ 评估器初始化成功！\n")
    
    def evaluate_all(self, method_filter: Optional[List[str]] = None):
        """
        评估所有结果文件 / Evaluate all result files
        
        Args:
            method_filter: 只评估指定方法（如 ['direct_llm', 'cfgo']）
                          Only evaluate specified methods
        """
        print("="*80)
        print("📊 批量CF/AC评估 / Batch CF/AC Evaluation")
        print("="*80)
        print(f"📁 Results directory: {self.results_dir}")
        print(f"📁 结果目录: {self.results_dir}")
        print(f"💾 Output mode: {self.output_mode}")
        print(f"💾 输出模式: {self.output_mode}")
        print(f"🔄 Use cache: {self.use_cache}")
        print(f"🔄 使用缓存: {self.use_cache}")
        print("="*80 + "\n")
        
        # 1. 扫描所有JSON文件 / Scan all JSON files
        json_files = self._scan_result_files(method_filter)
        
        if not json_files:
            print("❌ No result files found!")
            print("❌ 未找到结果文件！")
            return
        
        print(f"📂 Found {len(json_files)} result file(s)")
        print(f"📂 找到 {len(json_files)} 个结果文件\n")
        
        # 2. 过滤已评估的（如果use_cache=True）/ Filter evaluated files
        if self.use_cache:
            json_files = self._filter_unevaluated(json_files)
            print(f"🔍 After filtering: {len(json_files)} file(s) to evaluate")
            print(f"🔍 过滤后: {len(json_files)} 个文件需要评估\n")
        
        if not json_files:
            print("✅ All files already evaluated!")
            print("✅ 所有文件已评估！")
            return
        
        # 3. 批量评估 / Batch evaluation
        success_count = 0
        error_count = 0
        
        for json_file in tqdm(json_files, desc="Evaluating", disable=not self.verbose):
            try:
                self._evaluate_single_file(json_file)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"\n❌ Error evaluating {json_file.name}: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
        
        # 4. 总结 / Summary
        print("\n" + "="*80)
        print("📊 Evaluation Summary / 评估总结")
        print("="*80)
        print(f"✅ Success: {success_count} / 成功: {success_count}")
        print(f"❌ Errors: {error_count} / 错误: {error_count}")
        print(f"📁 Total: {len(json_files)} / 总计: {len(json_files)}")
        print("="*80 + "\n")
    
    def _scan_result_files(self, method_filter: Optional[List[str]] = None) -> List[Path]:
        """
        扫描所有结果JSON文件 / Scan all result JSON files
        
        Args:
            method_filter: 只扫描指定方法 / Only scan specified methods
        
        Returns:
            List of JSON file paths / JSON文件路径列表
        """
        json_files = []
        
        # 遍历results目录 / Traverse results directory
        for json_path in self.results_dir.rglob("*.json"):
            # 排除已评估的文件 / Exclude already evaluated files
            if "_evaluated.json" in str(json_path):
                continue
            
            # 如果指定了方法过滤 / If method filter is specified
            if method_filter:
                # 检查文件路径是否包含指定方法 / Check if path contains specified method
                matched = False
                for method in method_filter:
                    if method in str(json_path):
                        matched = True
                        break
                if not matched:
                    continue
            
            json_files.append(json_path)
        
        # 按修改时间排序 / Sort by modification time
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return json_files
    
    def _filter_unevaluated(self, json_files: List[Path]) -> List[Path]:
        """
        过滤掉已评估的文件 / Filter out already evaluated files
        
        Args:
            json_files: 文件列表 / File list
        
        Returns:
            未评估的文件列表 / List of unevaluated files
        """
        unevaluated = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查statistics中是否已有cf_score和ac_score
                # Check if cf_score and ac_score exist in statistics
                stats = data.get('statistics', {})
                if 'cf_score' in stats and 'ac_score' in stats:
                    if self.verbose:
                        print(f"⏭️  Skipping (already evaluated): {json_file.name}")
                    continue
                
                unevaluated.append(json_file)
            except Exception as e:
                # 如果读取失败，也加入待评估列表 / If read fails, add to evaluation list
                unevaluated.append(json_file)
        
        return unevaluated
    
    def _evaluate_single_file(self, json_path: Path):
        """
        评估单个结果文件 / Evaluate single result file
        
        Args:
            json_path: JSON文件路径 / JSON file path
        """
        # 1. 加载JSON / Load JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 2. 提取所有问题的结果 / Extract all problem results
        results = data.get('results', [])
        
        if not results:
            if self.verbose:
                print(f"⚠️  No results found in {json_path.name}")
            return
        
        # 3. 对每个问题计算CF和AC / Compute CF and AC for each problem
        cf_scores = []
        ac_scores = []
        
        for i, result in enumerate(results):
            # 检查是否有DAG / Check if DAG exists
            dag = result.get('causal_dag') or result.get('causal_scaffold')
            problem_text = result.get('problem', '') or result.get('problem_text', '')
            reasoning = result.get('reasoning', '') or result.get('reasoning_steps', '')
            
            if not dag:
                # 如果没有DAG，分数为0 / If no DAG, score is 0
                cf_scores.append(0.0)
                ac_scores.append(0.0)
                result['cf_score'] = 0.0
                result['ac_score'] = 0.0
                result['cf_details'] = "No DAG available"
                result['ac_details'] = "No DAG available"
                continue
            
            try:
                # 计算CF（三个维度的平均）/ Compute CF (average of 3 dimensions)
                # CF = (Causal Intervention + Logic Quality + Graph Quality) / 3
                
                # 1) Causal Intervention Score
                causal_score = self.causal_evaluator.evaluate_causal_intervention(
                    dag=dag,
                    problem_text=problem_text
                )
                
                # 2) Logic Quality Score
                logic_score = self.reward_evaluator.evaluate_logic_quality(
                    reasoning_text=reasoning,
                    problem_text=problem_text
                )
                
                # 3) Graph Quality Score
                graph_score = self.reward_evaluator.evaluate_graph_quality(dag)
                
                # CF综合分数 / CF composite score
                cf_score = (causal_score + logic_score + graph_score) / 3.0
                cf_scores.append(cf_score)
                
                # 保存详细信息 / Save details
                result['cf_score'] = cf_score
                result['cf_details'] = {
                    'causal_intervention': causal_score,
                    'logic_quality': logic_score,
                    'graph_quality': graph_score
                }
                
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  CF evaluation error for problem {i}: {e}")
                cf_scores.append(0.0)
                result['cf_score'] = 0.0
                result['cf_details'] = f"Error: {str(e)}"
            
            try:
                # 计算AC / Compute AC
                ac_score = self.abductive_evaluator.evaluate_abductive_reasoning(
                    dag=dag,
                    problem_text=problem_text,
                    final_answer=result.get('answer', '') or result.get('predicted_answer', '')
                )
                ac_scores.append(ac_score)
                result['ac_score'] = ac_score
                
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  AC evaluation error for problem {i}: {e}")
                ac_scores.append(0.0)
                result['ac_score'] = 0.0
                result['ac_details'] = f"Error: {str(e)}"
        
        # 4. 计算平均分 / Compute average scores
        avg_cf = sum(cf_scores) / len(cf_scores) if cf_scores else 0.0
        avg_ac = sum(ac_scores) / len(ac_scores) if ac_scores else 0.0
        
        # 5. 更新statistics / Update statistics
        if 'statistics' not in data:
            data['statistics'] = {}
        
        data['statistics']['cf_score'] = avg_cf
        data['statistics']['ac_score'] = avg_ac
        data['statistics']['cf_scores_per_problem'] = cf_scores
        data['statistics']['ac_scores_per_problem'] = ac_scores
        data['statistics']['cf_ac_evaluation_time'] = datetime.now().isoformat()
        
        # 6. 保存 / Save
        if self.output_mode == "append":
            # 覆盖原文件 / Overwrite original file
            output_path = json_path
        else:
            # 生成新文件 / Generate new file
            output_path = json_path.parent / f"{json_path.stem}_evaluated.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"✅ {json_path.name}: CF={avg_cf:.3f}, AC={avg_ac:.3f}")


def main():
    """命令行入口 / CLI entry point"""
    parser = argparse.ArgumentParser(
        description="批量评估CF和AC / Batch evaluate CF and AC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 示例:
  # 评估所有结果文件
  python comparasion/evaluate_cf_ac_batch.py

  # 指定结果目录
  python comparasion/evaluate_cf_ac_batch.py --results-dir comparasion/results

  # 重新评估所有文件（忽略缓存）
  python comparasion/evaluate_cf_ac_batch.py --no-cache

  # 只评估指定方法
  python comparasion/evaluate_cf_ac_batch.py --methods direct_llm cfgo

  # 静默模式
  python comparasion/evaluate_cf_ac_batch.py --quiet
        """
    )
    
    parser.add_argument(
        '--results-dir',
        type=str,
        default='comparasion/results',
        help='结果目录路径 / Results directory path'
    )
    
    parser.add_argument(
        '--output-mode',
        type=str,
        choices=['append', 'separate'],
        default='append',
        help='输出模式 / Output mode: append=追加到原文件, separate=生成新文件'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='重新评估所有文件（忽略已评估的）/ Re-evaluate all files (ignore cache)'
    )
    
    parser.add_argument(
        '--methods',
        type=str,
        nargs='+',
        help='只评估指定方法 / Only evaluate specified methods (e.g., direct_llm cfgo)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式 / Quiet mode'
    )
    
    args = parser.parse_args()
    
    # 创建评估器 / Create evaluator
    evaluator = CFACBatchEvaluator(
        results_dir=args.results_dir,
        output_mode=args.output_mode,
        use_cache=not args.no_cache,
        verbose=not args.quiet
    )
    
    # 执行评估 / Execute evaluation
    evaluator.evaluate_all(method_filter=args.methods)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user.")
        print("⚠️  评估被用户中断。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

