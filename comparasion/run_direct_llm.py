#!/usr/bin/env python3
"""
Direct LLM Baseline Runner
Direct LLM 基线方法运行器

Supports datasets: Omni-MATH, OlympiadBench (Math/Physics), GSM8K, MATH, MyData
Supports LLM-based answer evaluation for more accurate results
"""

import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import sys

sys.path.append(str(Path(__file__).parent.parent))

from engine.scaffolder import LLMClient
from baselines.prompt_loader import PromptLoader, StructuredAnswerExtractor
from baselines.llm_answer_evaluator import LLMAnswerEvaluator
from baselines.dag_converter import DAGConverter


class DirectLLMRunner:
    """Direct LLM baseline runner with optimized structure."""

    def __init__(self, output_dir: str = "results/direct_llm") -> None:
        """
        Initialize runner with output directory and LLM client.
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = LLMClient()
        self.temperature = 0.0
        
        project_root = Path(__file__).resolve().parent.parent
        self.prompt_loader = PromptLoader(prompts_dir=str(project_root / "prompts"))
        
        # 初始化DAG转换器
        self.dag_converter = DAGConverter(llm_client=self.llm_client, temperature=0.0)
        
        # 初始化LLM评判器（默认启用）
        self.answer_evaluator = LLMAnswerEvaluator(llm_client=self.llm_client)
        print("🤖 Using LLM-based answer evaluation")

    def solve_problem(self, problem: str, problem_id: str = None) -> Dict[str, Any]:
        """
        Solve a single problem using Direct LLM.
        
        Args:
            problem: Problem statement
            problem_id: Unique problem identifier
            
        Returns:
            Dictionary containing answer and metadata
        """
        try:
            start_time = time.time()
            prompt = self.prompt_loader.format_direct_llm_prompt(problem)
            response = self.llm_client.complete(prompt, temperature=self.temperature)
            reasoning, answer = StructuredAnswerExtractor.extract_both(response)
            
            # 使用通用DAG转换器
            causal_dag = self.dag_converter.convert_to_dag(problem, reasoning, answer)
            
            return {
                'method': 'direct_llm',
                'problem_id': problem_id,
                'problem': problem,
                'answer': answer,
                'reasoning': reasoning,
                'causal_dag': causal_dag,
                'raw_response': response,
                'execution_time': time.time() - start_time,
                'error': None
            }
        except Exception as e:
            return {
                'method': 'direct_llm',
                'problem_id': problem_id,
                'problem': problem,
                'answer': None,
                'reasoning': '',
                'causal_dag': {},
                'raw_response': '',
                'error': str(e),
                'execution_time': 0
            }


    def run_on_dataset(self, dataset_name: str, limit: Optional[int] = None) -> None:
        """
        Run Direct LLM on specified dataset.
        
        Args:
            dataset_name: Name of dataset to evaluate
            limit: Maximum number of problems to process
        """
        print(f"\n{'='*80}")
        print(f"Running Direct LLM on {dataset_name} (limit: {limit or 'all'})")
        print(f"{'='*80}\n")
        
        problems = self._load_dataset(dataset_name, limit)
        if not problems:
            print(f"Failed to load dataset: {dataset_name}")
            return
        
        print(f"Loaded {len(problems)} problems\n")
        
        results, correct_count = self._evaluate_problems(problems)
        accuracy = correct_count / len(problems) if problems else 0
        
        self._print_summary(dataset_name, len(problems), correct_count, accuracy)
        self._save_results(dataset_name, results, accuracy)

    def _evaluate_problems(self, problems: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Evaluate list of problems and return results with correct count."""
        results = []
        correct_count = 0
        
        for i, problem_data in enumerate(problems, 1):
            problem_id = problem_data['id']
            problem = problem_data['question']
            expected_answer = problem_data['answer']
            
            print(f"[{i}/{len(problems)}] Problem {problem_id}: ", end='')
            
            result = self.solve_problem(problem, problem_id)
            
            # 使用LLM评判器
            eval_result = self.answer_evaluator.evaluate(
                result['answer'],
                expected_answer,
                question=problem
            )
            is_correct = eval_result.is_correct
            result['evaluation'] = {
                'confidence': eval_result.confidence,
                'reasoning': eval_result.reasoning,
                'result_type': eval_result.result_type
            }
            
            result['expected_answer'] = expected_answer
            result['is_correct'] = is_correct
            
            if is_correct:
                correct_count += 1
                print(f"✓ ({result['execution_time']:.1f}s)")
            else:
                print(f"✗ ({result['execution_time']:.1f}s)")
            
            results.append(result)
        
        return results, correct_count

    def _load_dataset(self, dataset_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load dataset from file."""
        project_root = Path(__file__).resolve().parent.parent
        
        dataset_paths = {
            'gsm8k': project_root / "dataset/GSM8K/grade_school_math/data/test.jsonl",
            'math': project_root / "dataset/Math/test-00000-of-00001.parquet.json",
            'mydata': project_root / "dataset/mydata/data/2024A.json",
            'omnimath': project_root / "dataset/Omni-MATH/archive/main_test.jsonl",
            'olympiad_math': project_root / "dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/OE_TO_maths_en_COMP.json",
            'olympiad_physics': project_root / "dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/OE_TO_physics_en_COMP.json",
        }
        
        dataset_path = dataset_paths.get(dataset_name.lower())
        if not dataset_path or not dataset_path.exists():
            return []
        
        try:
            return self._parse_dataset_file(dataset_path, dataset_name, limit)
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return []

    def _parse_dataset_file(self, path: Path, dataset_name: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Parse dataset file based on format."""
        problems = []
        
        if dataset_name.lower() in ['gsm8k', 'omnimath']:
            # JSONL format
            with open(path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break
                    data = json.loads(line.strip())
                    answer = data['answer'].split('####')[-1].strip() if '####' in data['answer'] else data['answer']
                    problems.append({
                        'id': f'{dataset_name}_{i}',
                        'question': data['question'],
                        'answer': answer
                    })
        
        elif dataset_name.lower() in ['olympiad_math', 'olympiad_physics']:
            # OlympiadBench JSON format
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if limit:
                    data = data[:limit]
                
                for item in data:
                    # Extract first answer from final_answer list
                    answer = item['final_answer'][0] if item.get('final_answer') else ''
                    # Remove LaTeX formatting
                    answer = answer.replace('$', '').strip()
                    
                    problems.append({
                        'id': f"{dataset_name}_{item['id']}",
                        'question': item['question'],
                        'answer': answer
                    })
        
        else:
            # Standard JSON format
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if limit:
                    data = data[:limit]
                
                for i, item in enumerate(data):
                    problems.append({
                        'id': item.get('unique_id', f"{dataset_name}_{i}"),
                        'question': item.get('problem', item.get('question', '')),
                        'answer': item.get('answer', item.get('final_answer', ''))
                    })
        
        return problems

    def _print_summary(self, dataset_name: str, total: int, correct: int, accuracy: float) -> None:
        """Print evaluation summary."""
        print(f"\n{'='*80}")
        print(f"Results Summary")
        print(f"{'='*80}")
        print(f"Dataset: {dataset_name}")
        print(f"Total: {total} | Correct: {correct} | Wrong: {total - correct}")
        print(f"Accuracy: {accuracy*100:.2f}%")
        print(f"{'='*80}\n")

    def _save_results(self, dataset_name: str, results: List[Dict[str, Any]], accuracy: float) -> None:
        """Save evaluation results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"direct_llm_{dataset_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        output = {
            'method': 'direct_llm',
            'dataset': dataset_name,
            'total_problems': len(results),
            'correct': sum(1 for r in results if r.get('is_correct', False)),
            'accuracy': accuracy,
            'timestamp': timestamp,
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved: {filepath}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Direct LLM Baseline with LLM-based Answer Evaluation")
    parser.add_argument('--dataset', type=str, required=True,
                       choices=['gsm8k', 'math', 'mydata', 'omnimath', 'olympiad_math', 'olympiad_physics'],
                       help='Dataset to evaluate')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of problems')
    parser.add_argument('--output-dir', type=str, default='results/direct_llm',
                       help='Output directory')
    
    args = parser.parse_args()
    
    runner = DirectLLMRunner(output_dir=args.output_dir)
    runner.run_on_dataset(args.dataset, args.limit)


if __name__ == "__main__":
    main()