#!/usr/bin/env python3
"""
Ablation Study Runner for CFGO Framework
CFGO框架消融实验运行器

This script runs Level-1 ablation studies to validate core components.
该脚本运行一级消融实验以验证核心组件。

Level-1 Ablations (Core Components):
一级消融（核心组件）：
1. CFGO (Full) - 完整方法
2. CFGO-woGRPO - 无GRPO经验库
3. CFGO-woMultiAgent - 单Generator（无Critic）
4. CFGO-woEnhancement - 无增强流水线

Usage:
    # 运行完整方法
    python run_ablation.py --ablation full --dataset gsm8k --limit 30
    
    # 运行消融实验
    python run_ablation.py --ablation woGRPO --dataset gsm8k --limit 30
    python run_ablation.py --ablation woMultiAgent --dataset gsm8k --limit 30
    python run_ablation.py --ablation woEnhancement --dataset gsm8k --limit 30
    
    # 静默模式
    python run_ablation.py --ablation full --dataset gsm8k --limit 30 --quiet

Evaluation with CF & AC Metrics:
使用CF和AC指标进行评估：
    After running ablation studies, evaluate with causal metrics:
    运行消融实验后，使用因果指标评估：
    
    python -m comparasion.causal_evaluation \\
        --baseline-results comparasion/results/ablation/full/*.json \\
        --other-results comparasion/results/ablation/woGRPO/*.json
"""

import json
import argparse
import time
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import necessary modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from main import CausalReasoningEngine


class AblationRunner:
    """消融实验运行器"""
    
    VALID_ABLATIONS = ['full', 'woGRPO', 'woMultiAgent', 'woEnhancement']
    
    def __init__(self, ablation_type: str, output_dir: str = "results/ablation", verbose: bool = True):
        """
        初始化消融实验运行器
        
        Args:
            ablation_type: 消融类型 ('full', 'woGRPO', 'woMultiAgent', 'woEnhancement')
            output_dir: 输出目录
            verbose: 是否显示详细输出
        """
        if ablation_type not in self.VALID_ABLATIONS:
            raise ValueError(f"Invalid ablation type: {ablation_type}. Must be one of {self.VALID_ABLATIONS}")
        
        self.ablation_type = ablation_type
        self.output_dir = Path(output_dir) / ablation_type
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # 根据消融类型配置引擎
        self.engine = self._create_engine()
        
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"🔬 Ablation Study: {self._get_ablation_description()}")
            print(f"📁 Output Directory: {self.output_dir}")
            print(f"{'='*80}\n")
    
    def _get_ablation_description(self) -> str:
        """获取消融实验的描述"""
        descriptions = {
            'full': 'CFGO (Full) - 完整方法',
            'woGRPO': 'CFGO-woGRPO - 无GRPO经验库',
            'woMultiAgent': 'CFGO-woMultiAgent - 单Generator（无Critic）',
            'woEnhancement': 'CFGO-woEnhancement - 无增强流水线'
        }
        return descriptions.get(self.ablation_type, 'Unknown')
    
    def _create_engine(self) -> CausalReasoningEngine:
        """根据消融类型创建配置好的引擎"""
        
        if self.ablation_type == 'full':
            # 完整方法：所有功能开启
            print("✅ Configuration: Full CFGO Framework")
            print("  - GRPO Experience: ✓")
            print("  - Multi-Agent: ✓ (3 Generators + Critic)")
            print("  - Enhancement Pipeline: ✓ (Stage 1+2+3)")
            
            return CausalReasoningEngine(
                knowledge_base_path="data/knowledge_base.json",
                verbose=True,
                use_multi_agent=True,              # 使用多智能体
                enable_step2_enhancement=True,      # 启用增强
                use_expert_review=True,             # Stage 1
                use_rag_enhancement=True,           # Stage 2
                use_structure_optimization=True,    # Stage 3
                use_grpo_experience=True            # 加载GRPO经验
            )
        
        elif self.ablation_type == 'woGRPO':
            # 消融GRPO：不加载经验库
            print("❌ Ablation: Remove GRPO Experience")
            print("  - GRPO Experience: ✗")
            print("  - Multi-Agent: ✓ (3 Generators + Critic)")
            print("  - Enhancement Pipeline: ✓ (Stage 1+2+3)")
            
            return CausalReasoningEngine(
                knowledge_base_path="data/knowledge_base.json",
                verbose=True,
                use_multi_agent=True,
                enable_step2_enhancement=True,
                use_expert_review=True,
                use_rag_enhancement=True,
                use_structure_optimization=True,
                use_grpo_experience=False           # ❌ 不加载经验
            )
        
        elif self.ablation_type == 'woMultiAgent':
            # 消融多智能体：只用单个Generator
            print("❌ Ablation: Remove Multi-Agent")
            print("  - GRPO Experience: ✓")
            print("  - Multi-Agent: ✗ (1 Generator, No Critic)")
            print("  - Enhancement Pipeline: ✓ (Stage 1+2+3)")
            
            return CausalReasoningEngine(
                knowledge_base_path="data/knowledge_base.json",
                verbose=True,
                use_multi_agent=False,              # ❌ 不使用多智能体
                enable_step2_enhancement=True,
                use_expert_review=True,
                use_rag_enhancement=True,
                use_structure_optimization=True,
                use_grpo_experience=True
            )
        
        elif self.ablation_type == 'woEnhancement':
            # 消融增强流水线：跳过所有Stage
            print("❌ Ablation: Remove Enhancement Pipeline")
            print("  - GRPO Experience: ✓")
            print("  - Multi-Agent: ✓ (3 Generators + Critic)")
            print("  - Enhancement Pipeline: ✗ (Skip all stages)")
            
            return CausalReasoningEngine(
                knowledge_base_path="data/knowledge_base.json",
                verbose=True,
                use_multi_agent=True,
                enable_step2_enhancement=False,     # ❌ 禁用增强流水线
                use_expert_review=False,
                use_rag_enhancement=False,
                use_structure_optimization=False,
                use_grpo_experience=True
            )
        
        else:
            raise ValueError(f"Unknown ablation type: {self.ablation_type}")
    
    def solve_problem(self, problem: str, problem_id: str = None) -> Dict[str, Any]:
        """使用配置好的引擎解决问题"""
        try:
            start_time = time.time()
            
            # 运行因果推理引擎
            result = self.engine.solve_problem(
                problem_text=problem,
                include_validation=True,
                problem_id=problem_id
            )
            
            execution_time = time.time() - start_time
            
            # 格式化结果
            formatted_result = {
                'method': f'cfgo_{self.ablation_type}',
                'ablation_type': self.ablation_type,
                'problem_id': problem_id,
                'problem': problem,
                'answer': result.get('final_answer'),
                'reasoning': self._extract_reasoning_from_result(result),
                'causal_dag': result.get('causal_scaffold', {}),
                'raw_response': json.dumps(result, default=str),
                'execution_time': execution_time,
                'metadata': {
                    'ablation': self.ablation_type,
                    'scaffold_generated': 'causal_scaffold' in result,
                    'knowledge_enhanced': result.get('knowledge_enhanced', False),
                    'verification_passed': result.get('verification_passed', False),
                    'dag_complexity': self._calculate_dag_complexity(result.get('causal_scaffold', {}))
                }
            }
            
            return formatted_result
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # 打印错误信息以便调试
            print(f"❌ Error solving problem {problem_id}: {error_msg}")
            if self.verbose:
                traceback.print_exc()
            
            return {
                'method': f'cfgo_{self.ablation_type}',
                'ablation_type': self.ablation_type,
                'problem_id': problem_id,
                'problem': problem,
                'answer': None,
                'reasoning': '',
                'causal_dag': {},
                'raw_response': '',
                'error': error_msg,
                'execution_time': execution_time,
                'metadata': {
                    'error': True, 
                    'ablation': self.ablation_type,
                    'error_type': type(e).__name__
                }
            }
    
    def _extract_reasoning_from_result(self, result: Dict[str, Any]) -> str:
        """从CFGO结果中提取推理过程"""
        reasoning_parts = []
        
        # 添加计算步骤
        if 'computation_steps' in result:
            reasoning_parts.append("Computation Steps:")
            for step in result['computation_steps']:
                reasoning_parts.append(f"- {step}")
        
        # 添加推理链
        if 'reasoning_chain' in result:
            reasoning_parts.append("\nReasoning Chain:")
            reasoning_parts.append(str(result['reasoning_chain']))
        
        return '\n'.join(reasoning_parts) if reasoning_parts else "No reasoning available"
    
    def _calculate_dag_complexity(self, dag: Dict[str, Any]) -> float:
        """计算DAG复杂度"""
        if not dag:
            return 0.0
        
        complexity = 0
        complexity += len(dag.get('causal_graph', [])) * 2
        complexity += len(dag.get('computation_plan', [])) * 1
        complexity += len(dag.get('knowns', {})) * 0.5
        
        return complexity
    
    def run_on_dataset(self, dataset_name: str, limit: Optional[int] = None):
        """在数据集上运行消融实验"""
        print(f"\n{'='*80}")
        print(f"📊 Running {self.ablation_type} on {dataset_name} (limit: {limit})")
        print(f"{'='*80}\n")
        
        # 加载数据集
        problems = self._load_dataset(dataset_name, limit)
        
        if not problems:
            print(f"❌ Failed to load dataset: {dataset_name}")
            return
        
        print(f"✅ Loaded {len(problems)} problems\n")
        
        # 运行实验
        results = []
        correct = 0
        
        for i, problem_data in enumerate(problems, 1):
            problem_id = problem_data['id']
            problem = problem_data['question']
            expected_answer = problem_data['answer']
            
            print(f"\n[{i}/{len(problems)}] Problem: {problem_id}")
            print(f"Question: {problem[:100]}..." if len(problem) > 100 else f"Question: {problem}")
            
            # 解决问题
            result = self.solve_problem(problem, problem_id)
            
            # 检查答案
            is_correct = self._check_answer(result['answer'], expected_answer)
            result['expected_answer'] = expected_answer
            result['is_correct'] = is_correct
            
            if is_correct:
                correct += 1
                print(f"✓ Correct! Answer: {result['answer']}")
            else:
                print(f"✗ Wrong. Got: {result['answer']}, Expected: {expected_answer}")
            
            print(f"⏱️  Time: {result['execution_time']:.2f}s")
            
            results.append(result)
            
            # 实时准确率
            accuracy = correct / i
            print(f"📊 Current Accuracy: {correct}/{i} ({accuracy*100:.1f}%)")
        
        # 计算最终统计
        accuracy = correct / len(problems) if problems else 0
        total_time = sum(r['execution_time'] for r in results)
        avg_time = total_time / len(problems) if problems else 0
        error_count = sum(1 for r in results if r.get('error'))
        
        print(f"\n{'='*80}")
        print(f"📊 Final Results for {self.ablation_type}")
        print(f"{'='*80}")
        print(f"Total Problems: {len(problems)}")
        print(f"Correct: {correct}")
        print(f"Wrong: {len(problems) - correct - error_count}")
        print(f"Errors: {error_count}")
        print(f"Accuracy: {accuracy*100:.2f}%")
        print(f"Average Time: {avg_time:.2f}s")
        print(f"Total Time: {total_time:.2f}s")
        print(f"{'='*80}\n")
        
        # 保存结果
        self._save_results(dataset_name, results, accuracy, total_time, avg_time)
    
    def _load_dataset(self, dataset_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """加载数据集"""
        # 获取项目根目录
        project_root = Path(__file__).resolve().parent.parent
        
        dataset_map = {
            'gsm8k': project_root / "dataset/GSM8K/grade_school_math/data/test.jsonl",
            'math': project_root / "dataset/Math/test-00000-of-00001.parquet.json",
            'mydata': project_root / "dataset/mydata/data/2024A.json",
        }
        
        dataset_path = dataset_map.get(dataset_name.lower())
        
        if not dataset_path:
            print(f"❌ Unknown dataset: {dataset_name}")
            return []
        
        if not dataset_path.exists():
            print(f"❌ Dataset file not found: {dataset_path}")
            return []
        
        problems = []
        
        try:
            if dataset_name.lower() == 'gsm8k':
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if limit and i >= limit:
                            break
                        data = json.loads(line.strip())
                        answer_text = data['answer']
                        final_answer = answer_text.split('####')[-1].strip() if '####' in answer_text else answer_text
                        problems.append({
                            'id': f'gsm8k_{i}',
                            'question': data['question'],
                            'answer': final_answer
                        })
            
            elif dataset_name.lower() in ['math', 'mydata']:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if limit:
                        data = data[:limit]
                    
                    for i, item in enumerate(data):
                        problems.append({
                            'id': item.get('unique_id', f"{dataset_name}_{i}"),
                            'question': item.get('problem', item.get('question', '')),
                            'answer': item.get('answer', item.get('final_answer', ''))
                        })
        
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return []
        
        return problems
    
    def _check_answer(self, predicted: Any, expected: str) -> bool:
        """检查答案是否正确（增强的答案比较逻辑）"""
        if predicted is None:
            return False
        
        pred_str = str(predicted).strip().lower()
        exp_str = str(expected).strip().lower()
        
        # 1. 精确匹配
        if pred_str == exp_str:
            return True
        
        # 2. 移除空格后匹配
        pred_clean = pred_str.replace(" ", "")
        exp_clean = exp_str.replace(" ", "")
        if pred_clean == exp_clean:
            return True
        
        # 3. 尝试数值比较
        try:
            # 提取数字（支持小数和科学计数法）
            pred_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', pred_str)
            exp_nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', exp_str)
            
            if pred_nums and exp_nums:
                # 比较第一个数字（通常是答案）
                pred_val = float(pred_nums[0])
                exp_val = float(exp_nums[0])
                
                # 使用相对误差和绝对误差
                if abs(exp_val) > 1e-6:
                    relative_error = abs(pred_val - exp_val) / abs(exp_val)
                    if relative_error < 1e-4:  # 0.01% 相对误差
                        return True
                
                # 绝对误差
                if abs(pred_val - exp_val) < 1e-6:
                    return True
        except (ValueError, IndexError):
            pass
        
        # 4. 检查包含关系（但要小心 - 只在长度足够时使用）
        # 避免"3"匹配"30"这种情况
        if len(pred_clean) >= 3 and len(exp_clean) >= 3:
            if pred_clean in exp_clean or exp_clean in pred_clean:
                return True
        
        return False
    
    def _save_results(self, dataset_name: str, results: List[Dict[str, Any]], accuracy: float, total_time: float, avg_time: float):
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.ablation_type}_{dataset_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        error_count = sum(1 for r in results if r.get('error'))
        
        output = {
            'ablation_type': self.ablation_type,
            'description': self._get_ablation_description(),
            'dataset': dataset_name,
            'timestamp': timestamp,
            'statistics': {
                'total_problems': len(results),
                'correct': sum(1 for r in results if r.get('is_correct', False)),
                'wrong': len(results) - sum(1 for r in results if r.get('is_correct', False)) - error_count,
                'errors': error_count,
                'accuracy': accuracy,
                'total_time': total_time,
                'avg_time': avg_time
            },
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Ablation Study Runner for CFGO Framework"
    )
    
    parser.add_argument(
        '--ablation',
        type=str,
        required=True,
        choices=AblationRunner.VALID_ABLATIONS,
        help='Ablation type: full (完整), woGRPO (无GRPO), woMultiAgent (无多智能体), woEnhancement (无增强)'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        required=True,
        choices=['gsm8k', 'math', 'mydata'],
        help='Dataset to use'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of problems to test'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/ablation',
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='减少输出信息（Reduce output verbosity）'
    )
    
    args = parser.parse_args()
    
    # 创建运行器并执行
    runner = AblationRunner(
        ablation_type=args.ablation,
        output_dir=args.output_dir,
        verbose=not args.quiet
    )
    
    runner.run_on_dataset(args.dataset, args.limit)


if __name__ == "__main__":
    main()
