"""
单文件CF/AC评估工具
Single File CF/AC Evaluation Tool

功能 / Features:
- 对指定的单个结果文件计算CF和AC分数
- Evaluate CF and AC scores for a single result file
- 总是重新评估，不检查缓存
- Always re-evaluate, no cache checking

使用方法 / Usage:
    # 评估指定文件
    python comparasion/evaluate_cf_ac_single.py <文件路径>
    
    # 示例
    python comparasion/evaluate_cf_ac_single.py comparasion/results/zero_shot_cot/zero_shot_cot_olympiad_physics_20251119_004656.json
    
    # 静默模式
    python comparasion/evaluate_cf_ac_single.py <文件路径> --quiet
    
    # 生成新文件而非覆盖原文件
    python comparasion/evaluate_cf_ac_single.py <文件路径> --output-mode separate
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 导入评估模块
from causal_evaluation import (
    CausalInterventionEvaluator,
    AbductiveReasoningEvaluator
)
from engine.scaffolder import LLMClient


def evaluate_file(file_path: Path, output_mode: str = "append", verbose: bool = True):
    """
    评估单个结果文件 / Evaluate single result file
    
    Args:
        file_path: JSON文件路径 / JSON file path
        output_mode: 输出模式 / Output mode
            - "append": 在原JSON中添加cf_score和ac_score
            - "separate": 生成新的 *_evaluated.json 文件
        verbose: 是否显示详细信息 / Whether to show detailed info
    """
    
    if verbose:
        print("="*80)
        print("📊 CF/AC 单文件评估 / Single File CF/AC Evaluation")
        print("="*80)
        print(f"📁 File: {file_path}")
        print(f"📁 文件: {file_path}")
        print(f"💾 Output mode: {output_mode}")
        print(f"💾 输出模式: {output_mode}")
        print("="*80 + "\n")
    
    # 初始化LLM客户端和评估器
    if verbose:
        print("🔧 Initializing LLM client and evaluators...")
        print("🔧 初始化LLM客户端和评估器...")
    
    try:
        llm_client = LLMClient()
        if verbose:
            print("✅ LLM client initialized")
            print("✅ LLM客户端已初始化")
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: Failed to initialize LLM client: {e}")
            print(f"⚠️  警告: LLM客户端初始化失败: {e}")
            print("⚠️  Using default scores (0.5)")
            print("⚠️  将使用默认分数(0.5)")
        llm_client = None
    
    causal_evaluator = CausalInterventionEvaluator(llm_client=llm_client, verbose=verbose)
    abductive_evaluator = AbductiveReasoningEvaluator(llm_client=llm_client, verbose=verbose)
    
    if verbose:
        print("✅ Evaluators ready!")
        print("✅ 评估器就绪！\n")
    
    # 加载JSON
    if verbose:
        print(f"📂 Loading file...")
        print(f"📂 加载文件...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取结果
    results = data.get('results', [])
    
    if not results:
        print("❌ No results found in file!")
        print("❌ 文件中未找到结果！")
        return
    
    if verbose:
        print(f"📊 Found {len(results)} problem(s)")
        print(f"📊 找到 {len(results)} 个问题\n")
        print("🔄 Evaluating...")
        print("🔄 评估中...\n")
    
    # 评估每个问题
    cf_scores = []
    ac_scores = []
    
    for i, result in enumerate(results):
        if verbose:
            print(f"  [{i+1}/{len(results)}] Evaluating problem {i+1}...")
        
        # 初始化默认分数
        cf_score = 0.0
        ac_score = 0.0
        
        # 提取必要字段
        dag = result.get('causal_dag') or result.get('causal_scaffold')
        problem_text = result.get('problem', '') or result.get('problem_text', '')
        
        if not dag:
            # 没有DAG，分数为0
            cf_scores.append(0.0)
            ac_scores.append(0.0)
            result['cf_score'] = 0.0
            result['ac_score'] = 0.0
            result['cf_details'] = "No DAG available"
            result['ac_details'] = "No DAG available"
            if verbose:
                print(f"      No DAG - CF=0.000, AC=0.000")
            continue
        
        # 计算CF分数
        try:
            cf_score, cf_details = causal_evaluator.evaluate_intervention(
                dag=dag,
                problem_text=problem_text
            )
            cf_scores.append(cf_score)
            result['cf_score'] = cf_score
            result['cf_details'] = cf_details
        except Exception as e:
            if verbose:
                print(f"      ⚠️  CF evaluation error - {e}")
            cf_scores.append(0.0)
            result['cf_score'] = 0.0
            result['cf_details'] = f"Error: {str(e)}"
            cf_score = 0.0
        
        # 计算AC分数
        try:
            ac_score, ac_details = abductive_evaluator.evaluate_abductive(
                dag=dag,
                problem_text=problem_text
            )
            ac_scores.append(ac_score)
            result['ac_score'] = ac_score
            result['ac_details'] = ac_details
        except Exception as e:
            if verbose:
                print(f"      ⚠️  AC evaluation error - {e}")
            ac_scores.append(0.0)
            result['ac_score'] = 0.0
            result['ac_details'] = f"Error: {str(e)}"
            ac_score = 0.0
        
        if verbose:
            print(f"      Result: CF={cf_score:.3f}, AC={ac_score:.3f}")
    
    # 计算平均分
    avg_cf = sum(cf_scores) / len(cf_scores) if cf_scores else 0.0
    avg_ac = sum(ac_scores) / len(ac_scores) if ac_scores else 0.0
    
    # 更新statistics
    if 'statistics' not in data:
        data['statistics'] = {}
    
    data['statistics']['cf_score'] = avg_cf
    data['statistics']['ac_score'] = avg_ac
    data['statistics']['cf_scores_per_problem'] = cf_scores
    data['statistics']['ac_scores_per_problem'] = ac_scores
    data['statistics']['cf_ac_evaluation_time'] = datetime.now().isoformat()
    
    # 保存文件
    if output_mode == "append":
        output_path = file_path
    else:
        output_path = file_path.parent / f"{file_path.stem}_evaluated.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 输出结果
    if verbose:
        print("\n" + "="*80)
        print("📊 Evaluation Complete / 评估完成")
        print("="*80)
        print(f"✅ Average CF Score: {avg_cf:.3f}")
        print(f"✅ 平均CF分数: {avg_cf:.3f}")
        print(f"✅ Average AC Score: {avg_ac:.3f}")
        print(f"✅ 平均AC分数: {avg_ac:.3f}")
        print(f"💾 Output file: {output_path}")
        print(f"💾 输出文件: {output_path}")
        print("="*80)
    else:
        print(f"✅ CF={avg_cf:.3f}, AC={avg_ac:.3f} -> {output_path.name}")


def main():
    """命令行入口 / CLI entry point"""
    parser = argparse.ArgumentParser(
        description="单文件CF/AC评估 / Single File CF/AC Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 示例:
  # 评估指定文件
  python comparasion/evaluate_cf_ac_single.py comparasion/results/zero_shot_cot/zero_shot_cot_olympiad_physics_20251119_004656.json
  
  # 静默模式
  python comparasion/evaluate_cf_ac_single.py comparasion/results/direct_llm/direct_llm_olympiad_physics_20251118_233335.json --quiet
  
  # 生成新文件
  python comparasion/evaluate_cf_ac_single.py comparasion/results/few_shot_cot/few_shot_cot_olympiad_physics_20251119_002347.json --output-mode separate
        """
    )
    
    parser.add_argument(
        'file',
        type=str,
        help='要评估的结果文件路径 / Path to result file to evaluate'
    )
    
    parser.add_argument(
        '--output-mode',
        type=str,
        choices=['append', 'separate'],
        default='append',
        help='输出模式 / Output mode: append=覆盖原文件, separate=生成新文件'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式 / Quiet mode'
    )
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    file_path = Path(args.file)
    
    # 如果是相对路径且文件不存在，尝试从项目根目录查找
    if not file_path.exists():
        # 尝试从项目根目录查找
        project_root = Path(__file__).resolve().parent.parent
        alternative_path = project_root / args.file
        
        if alternative_path.exists():
            file_path = alternative_path
            if not args.quiet:
                print(f"ℹ️  Using absolute path: {file_path}")
        else:
            print(f"❌ File not found: {args.file}")
            print(f"❌ 文件不存在: {args.file}")
            print(f"\n💡 Tried paths:")
            print(f"   - {Path(args.file).absolute()}")
            print(f"   - {alternative_path}")
            sys.exit(1)
    
    # 评估文件
    try:
        evaluate_file(
            file_path=file_path,
            output_mode=args.output_mode,
            verbose=not args.quiet
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user.")
        print("⚠️  评估被用户中断。")
        sys.exit(1)