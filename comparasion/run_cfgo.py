#!/usr/bin/env python3
"""
CFGO Framework Runner
CFGO框架运行器

This script runs the complete CFGO framework independently.
该脚本独立运行完整的CFGO框架。

Usage:
    python run_cfgo.py --dataset gsm8k --limit 30
    python run_cfgo.py --dataset math --limit 20 --output-dir results/cfgo
"""

import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import necessary modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from main import CausalReasoningEngine


class CFGORunner:
    """CFGO框架独立运行器"""

    def __init__(self, output_dir: str = "comparasion/results/cfgo"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化CFGO引擎
        self.engine = CausalReasoningEngine(
            knowledge_base_path="data/knowledge_base.json",
            verbose=True,
            use_ai_retriever=True,
            auto_enrich_kb=True,
            min_rules_threshold=5,
            use_multi_agent=True  # 使用多智能体
        )
        
        print(f"🚀 CFGO Framework Runner Initialized")
        print(f"📁 Output Directory: {self.output_dir}")

    def solve_problem(self, problem: str, problem_id: str = None) -> Dict[str, Any]:
        """使用CFGO框架解决问题"""
        try:
            start_time = time.time()
            
            # 运行CFGO框架
            result = self.engine.solve_problem(
                problem_text=problem,
                include_validation=True,
                problem_id=problem_id
            )
            
            execution_time = time.time() - start_time
            
            # 格式化结果
            formatted_result = {
                'method': 'cfgo',
                'problem_id': problem_id,
                'problem': problem,
                'answer': result.get('final_answer'),
                'reasoning': self._extract_reasoning(result),
                'causal_dag': result.get('causal_scaffold', {}),
                'raw_response': json.dumps(result, default=str),
                'execution_time': execution_time,
                'metadata': {
                    'scaffold_generated': 'causal_scaffold' in result,
                    'knowledge_enhanced': result.get('knowledge_enhanced', False),
                    'verification_passed': result.get('verification_passed', False)
                }
            }
            
            return formatted_result
        
        except Exception as e:
            return {
                'method': 'cfgo',
                'problem_id': problem_id,
                'problem': problem,
                'answer': None,
                'reasoning': '',
                'causal_dag': {},
                'raw_response': '',
                'error': str(e),
                'execution_time': 0,
                'metadata': {'error': True}
            }

    def _extract_reasoning(self, result: Dict[str, Any]) -> str:
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

    def run_on_dataset(self, dataset_name: str, limit: Optional[int] = None):
        """在指定数据集上运行CFGO"""
        print(f"\n{'='*80}")
        print(f"📊 Running CFGO on {dataset_name} (limit: {limit})")
        print(f"{'='*80}\n")
        
        problems = self._load_dataset(dataset_name, limit)
        
        if not problems:
            print(f"❌ Failed to load dataset: {dataset_name}")
            return
        
        print(f"✅ Loaded {len(problems)} problems\n")
        
        all_results = []
        correct_count = 0
        
        for i, problem_data in enumerate(problems, 1):
            problem_id = problem_data['id']
            problem = problem_data['question']
            expected_answer = problem_data['answer']
            
            print(f"\n{'='*80}")
            print(f"[{i}/{len(problems)}] Problem: {problem_id}")
            print(f"{'='*80}")
            print(f"Question: {problem[:100]}..." if len(problem) > 100 else f"Question: {problem}")
            
            result = self.solve_problem(problem, problem_id)
            
            is_correct = self._check_answer(result['answer'], expected_answer)
            result['expected_answer'] = expected_answer
            result['is_correct'] = is_correct
            
            if is_correct:
                correct_count += 1
                print(f"\n✅ Correct! Answer: {result['answer']}")
            else:
                print(f"\n❌ Wrong. Got: {result['answer']}, Expected: {expected_answer}")
                if result.get('error'):
                    print(f"  Error: {result['error']}")
            
            print(f"⏱️  Time: {result['execution_time']:.2f}s")
            
            all_results.append(result)
            
            # 实时准确率
            accuracy = correct_count / i
            print(f"📊 Current Accuracy: {correct_count}/{i} ({accuracy*100:.1f}%)")
        
        accuracy = correct_count / len(problems) if problems else 0
        
        print(f"\n{'='*80}")
        print(f"📊 Final Results")
        print(f"{'='*80}")
        print(f"Dataset: {dataset_name}")
        print(f"Total Problems: {len(problems)}")
        print(f"Correct: {correct_count}")
        print(f"Wrong: {len(problems) - correct_count}")
        print(f"Accuracy: {accuracy*100:.2f}%")
        print(f"{'='*80}\n")
        
        self._save_results(dataset_name, all_results, accuracy)

    def _load_dataset(self, dataset_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """加载数据集"""
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
        """检查答案是否正确"""
        if predicted is None:
            return False
        
        pred_str = str(predicted).strip().lower()
        exp_str = str(expected).strip().lower()
        
        return pred_str == exp_str or pred_str in exp_str or exp_str in pred_str

    def _save_results(self, dataset_name: str, results: List[Dict[str, Any]], accuracy: float):
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cfgo_{dataset_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        output = {
            'method': 'cfgo',
            'dataset': dataset_name,
            'total_problems': len(results),
            'correct': sum(1 for r in results if r.get('is_correct', False)),
            'accuracy': accuracy,
            'timestamp': timestamp,
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Run CFGO Framework")
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['gsm8k', 'math', 'mydata'],
                       help='Dataset to evaluate')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of problems')
    parser.add_argument('--output-dir', type=str, default='comparasion/results/cfgo',
                       help='Output directory')
    
    args = parser.parse_args()
    
    runner = CFGORunner(output_dir=args.output_dir)
    runner.run_on_dataset(args.dataset, args.limit)


if __name__ == "__main__":
    main()
