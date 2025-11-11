#!/usr/bin/env python3
"""
Zero-Shot CoT Baseline Runner
Zero-Shot CoT 基线方法运行器

This script runs the Zero-Shot CoT baseline method independently.
该脚本独立运行 Zero-Shot CoT 基线方法。

Usage:
    python run_zero_shot_cot.py --dataset gsm8k --limit 30
    python run_zero_shot_cot.py --dataset math --limit 20 --output-dir results/zero_shot_cot
"""

import json
import argparse
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import necessary modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from engine.scaffolder import LLMClient
from baselines.prompt_loader import PromptLoader, StructuredAnswerExtractor


class ZeroShotCoTRunner:
    """Zero-Shot CoT独立运行器"""

    def __init__(self, output_dir: str = "comparasion/results/zero_shot_cot"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = LLMClient()
        self.temperature = 0.0
        
        # 使用项目根目录的prompts文件夹
        project_root = Path(__file__).resolve().parent.parent
        prompts_dir = project_root / "prompts"
        self.prompt_loader = PromptLoader(prompts_dir=str(prompts_dir))
        
        print(f"🤖 Zero-Shot CoT Runner Initialized")
        print(f"📁 Output Directory: {self.output_dir}")

    def solve_problem(self, problem: str, problem_id: str = None) -> Dict[str, Any]:
        """使用Zero-Shot CoT解决问题"""
        try:
            start_time = time.time()
            
            # 构建prompt
            enhanced_prompt = self._build_prompt(problem)
            
            # 调用LLM
            response = self.llm_client.complete(enhanced_prompt, temperature=self.temperature)
            
            # 提取答案和推理
            reasoning, answer = StructuredAnswerExtractor.extract_both(response)
            
            # 转换为DAG
            causal_dag = self._convert_to_dag(problem, reasoning, answer)
            
            execution_time = time.time() - start_time
            
            return {
                'method': 'zero_shot_cot',
                'problem_id': problem_id,
                'problem': problem,
                'answer': answer,
                'reasoning': reasoning,
                'causal_dag': causal_dag,
                'raw_response': response,
                'execution_time': execution_time,
                'error': None
            }
        
        except Exception as e:
            return {
                'method': 'zero_shot_cot',
                'problem_id': problem_id,
                'problem': problem,
                'answer': None,
                'reasoning': '',
                'causal_dag': {},
                'raw_response': '',
                'error': str(e),
                'execution_time': 0
            }

    def _build_prompt(self, problem: str) -> str:
        """构建Zero-Shot CoT的prompt"""
        return self.prompt_loader.format_zero_shot_cot_prompt(problem)

    def _convert_to_dag(self, problem: str, reasoning: str, answer: str) -> Dict[str, Any]:
        """将推理转换为因果图"""
        if not reasoning:
            return self._create_empty_dag()
        
        causal_prompt = f"""**IMPORTANT**: You are converting an existing reasoning process into a causal DAG structure. 
**DO NOT re-reason or change the logic**. Strictly follow the given reasoning steps.

Problem: {problem}

Reasoning Process:
{reasoning}

Final Answer: {answer}

**Instructions**:
1. **STRICTLY follow the reasoning trajectory** - do not add extra steps or change the order
2. **Extract causal relationships exactly as shown** in the reasoning process
3. **Preserve the computation sequence** - each step must match the reasoning
4. **Do not infer or guess** - only extract what is explicitly stated

Extract the causal relationships and create a causal DAG with the following structure:
{{
  "target_variable": "the final quantity being solved for",
  "expected_answer_type": "Numerical|Expression|Tuple|...",
  "knowns": {{"variable_name": "value", ...}},
  "causal_graph": [
    {{"cause": ["input_variable"], "effect": "output_variable", "rule": "explanation of relationship"}}
  ],
  "computation_plan": [
    {{"id": "step1", "target": "intermediate_variable", "inputs": ["input"], "description": "what to compute"}}
  ]
}}

**Remember**: Your task is to CONVERT, not to RE-REASON. Follow the given reasoning exactly.

Respond with valid JSON only:"""

        try:
            response = self.llm_client.complete(causal_prompt, temperature=0.0)
            dag = self._parse_dag_response(response)
            return dag if dag else self._create_empty_dag()
        except Exception as e:
            print(f"  ⚠️ DAG conversion failed: {e}")
            return self._create_empty_dag()

    def _parse_dag_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM返回的DAG"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                dag = json.loads(json_match.group(0))
                return dag
            return None
        except Exception as e:
            print(f"  ⚠️ JSON parse error: {e}")
            return None

    def _create_empty_dag(self) -> Dict[str, Any]:
        """创建空的DAG结构"""
        return {
            "target_variable": "result",
            "expected_answer_type": "Numerical",
            "knowns": {},
            "causal_graph": [],
            "computation_plan": []
        }

    def run_on_dataset(self, dataset_name: str, limit: Optional[int] = None):
        """在指定数据集上运行Zero-Shot CoT"""
        print(f"\n{'='*80}")
        print(f"📊 Running Zero-Shot CoT on {dataset_name} (limit: {limit})")
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
            
            print(f"[{i}/{len(problems)}] Problem: {problem_id}")
            print(f"Question: {problem[:100]}..." if len(problem) > 100 else f"Question: {problem}")
            
            result = self.solve_problem(problem, problem_id)
            
            is_correct = self._check_answer(result['answer'], expected_answer)
            result['expected_answer'] = expected_answer
            result['is_correct'] = is_correct
            
            if is_correct:
                correct_count += 1
                print(f"✓ Correct! Answer: {result['answer']}")
            else:
                print(f"✗ Wrong. Got: {result['answer']}, Expected: {expected_answer}")
                if result.get('error'):
                    print(f"  Error: {result['error']}")
            
            print(f"⏱️  Time: {result['execution_time']:.2f}s\n")
            
            all_results.append(result)
        
        accuracy = correct_count / len(problems) if problems else 0
        
        print(f"{'='*80}")
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
        filename = f"zero_shot_cot_{dataset_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        output = {
            'method': 'zero_shot_cot',
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
    parser = argparse.ArgumentParser(description="Run Zero-Shot CoT Baseline")
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['gsm8k', 'math', 'mydata'],
                       help='Dataset to evaluate')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of problems')
    parser.add_argument('--output-dir', type=str, default='comparasion/results/zero_shot_cot',
                       help='Output directory')
    
    args = parser.parse_args()
    
    runner = ZeroShotCoTRunner(output_dir=args.output_dir)
    runner.run_on_dataset(args.dataset, args.limit)


if __name__ == "__main__":
    main()
