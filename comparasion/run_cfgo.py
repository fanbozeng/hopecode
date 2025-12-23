#!/usr/bin/env python3
"""
CFGO (Causal Framework with GRPO) Baseline Runner
CFGO (带GRPO的因果框架) 基线方法运行器

Based on main.py's CausalReasoningEngine with batch processing capabilities.
基于 main.py 的 CausalReasoningEngine，具有批处理能力。

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

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from main.py
from main import CausalReasoningEngine

# Import evaluation tools
from baselines.llm_answer_evaluator import LLMAnswerEvaluator
from engine.scaffolder import LLMClient


class CFGORunner:
    """
    CFGO runner that uses CausalReasoningEngine from main.py for batch evaluation.
    CFGO运行器，使用main.py的CausalReasoningEngine进行批量评估。
    """

    def __init__(
        self,
        output_dir: str = "comparasion/results/cfgo",
        verbose: bool = False,
        **engine_kwargs
    ) -> None:
        """
        Initialize CFGO runner.
        
        Args:
            output_dir: Directory to save results
            verbose: Whether to show detailed output (False for batch processing)
            **engine_kwargs: Additional arguments to pass to CausalReasoningEngine
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # Initialize CausalReasoningEngine with provided kwargs
        print("🔧 Initializing CFGO Engine...")
        self.engine = CausalReasoningEngine(
            verbose=verbose,
            **engine_kwargs
        )
        print("✅ CFGO Engine initialized\n")
        
        # Initialize LLM evaluator
        llm_client = LLMClient()
        self.answer_evaluator = LLMAnswerEvaluator(llm_client=llm_client)
        print("🤖 Using LLM-based answer evaluation\n")

    def solve_problem(self, problem: str, problem_id: str = None) -> Dict[str, Any]:
        """
        Solve a single problem using CFGO pipeline.
        
        Args:
            problem: Problem statement
            problem_id: Unique problem identifier
            
        Returns:
            Dictionary containing answer and metadata
        """
        try:
            start_time = time.time()
            
            # Use CausalReasoningEngine to solve problem
            results = self.engine.solve_problem(
                problem_text=problem,
                include_validation=False,
                save_output=None,
                problem_id=problem_id,
                method_name='cfgo'
            )
            
            execution_time = time.time() - start_time
            
            # Extract answer and reasoning
            answer = results.get('final_answer', '')
            reasoning = results.get('reasoning', '')
            causal_dag = results.get('enhanced_dag') or results.get('causal_scaffold', {})
            
            return {
                'method': 'cfgo',
                'problem_id': problem_id,
                'problem': problem,
                'answer': answer,
                'reasoning': reasoning,
                'causal_scaffold': results.get('causal_scaffold', {}),
                'enhanced_dag': results.get('enhanced_dag', {}),
                'causal_dag': causal_dag,  # For compatibility
                'enhancement_report': results.get('enhancement_report', {}),
                'computation_result': results.get('computation_result', {}),
                'execution_time': execution_time,
                'success': results.get('success', False),
                'error': results.get('error', None)
            }
        except Exception as e:
            import traceback
            return {
                'method': 'cfgo',
                'problem_id': problem_id,
                'problem': problem,
                'answer': None,
                'reasoning': '',
                'causal_dag': {},
                'error': str(e),
                'traceback': traceback.format_exc(),
                'success': False,
                'execution_time': 0
            }

    def run_on_dataset(self, dataset_name: str, limit: Optional[int] = None) -> None:
        """
        Run CFGO on specified dataset.
        
        Args:
            dataset_name: Name of dataset to evaluate
            limit: Maximum number of problems to process
        """
        print(f"\n{'='*80}")
        print(f"Running CFGO on {dataset_name} (limit: {limit or 'all'})")
        print(f"{'='*80}\n")
        
        problems = self._load_dataset(dataset_name, limit)
        if not problems:
            print(f"❌ Failed to load dataset: {dataset_name}")
            return
        
        print(f"📊 Loaded {len(problems)} problems\n")
        
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
            
            print(f"[{i}/{len(problems)}] Problem {problem_id}: ", end='', flush=True)
            
            result = self.solve_problem(problem, problem_id)
            
            # Use LLM evaluator
            if result['success'] and result['answer']:
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
            else:
                is_correct = False
                result['evaluation'] = {
                    'confidence': 0.0,
                    'reasoning': 'Execution failed',
                    'result_type': 'error'
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
            print(f"❌ Dataset path not found: {dataset_path}")
            return []
        
        try:
            return self._parse_dataset_file(dataset_path, dataset_name, limit)
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            import traceback
            traceback.print_exc()
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
                for i, item in enumerate(data):
                    if limit and i >= limit:
                        break
                    # OlympiadBench uses 'question' and 'final_answer' fields
                    answer = item.get('final_answer', [''])[0] if isinstance(item.get('final_answer'), list) else item.get('final_answer', '')
                    problems.append({
                        'id': item.get('id', f'{dataset_name}_{i}'),
                        'question': item['question'],
                        'answer': answer
                    })
        
        elif dataset_name.lower() == 'math':
            # MATH dataset JSON format
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for i, item in enumerate(data):
                    if limit and i >= limit:
                        break
                    problems.append({
                        'id': f'math_{i}',
                        'question': item['problem'],
                        'answer': item['solution']
                    })
        
        elif dataset_name.lower() == 'mydata':
            # MyData JSON format
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for i, item in enumerate(data):
                    if limit and i >= limit:
                        break
                    problems.append({
                        'id': item.get('id', f'mydata_{i}'),
                        'question': item['problem'],
                        'answer': item.get('answer', '')
                    })
        
        return problems

    def _print_summary(self, dataset_name: str, total: int, correct: int, accuracy: float) -> None:
        """Print evaluation summary."""
        print(f"\n{'='*80}")
        print(f"📊 CFGO Evaluation Summary on {dataset_name}")
        print(f"{'='*80}")
        print(f"Total problems: {total}")
        print(f"Correct: {correct}")
        print(f"Accuracy: {accuracy:.2%}")
        print(f"{'='*80}\n")

    def _save_results(self, dataset_name: str, results: List[Dict[str, Any]], accuracy: float) -> None:
        """Save results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"cfgo_{dataset_name}_{timestamp}.json"
        
        output_data = {
            'method': 'cfgo',
            'dataset': dataset_name,
            'timestamp': timestamp,
            'statistics': {
                'total_problems': len(results),
                'correct': sum(1 for r in results if r.get('is_correct', False)),
                'accuracy': accuracy,
                'avg_execution_time': sum(r.get('execution_time', 0) for r in results) / len(results) if results else 0
            },
            'results': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="CFGO (Causal Framework with GRPO) Baseline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 示例:
  # Run on OlympiadBench Physics (first 10 problems)
  python comparasion/run_cfgo.py olympiad_physics --limit 10
  
  # Run with all enhancements enabled (default)
  python comparasion/run_cfgo.py olympiad_math --limit 10
  
  # Ablation: Disable Step2 enhancement
  python comparasion/run_cfgo.py olympiad_physics --limit 10 --no-step2
  
  # Ablation: Single-agent mode
  python comparasion/run_cfgo.py olympiad_physics --limit 10 --single-agent
  
  # Ablation: Disable GRPO experience
  python comparasion/run_cfgo.py olympiad_physics --limit 10 --no-grpo
        """
    )
    
    parser.add_argument(
        'dataset',
        type=str,
        choices=['gsm8k', 'math', 'mydata', 'omnimath', 'olympiad_math', 'olympiad_physics'],
        help='Dataset to evaluate on'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of problems to process'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='comparasion/results/cfgo',
        help='Output directory for results'
    )
    
    # CausalReasoningEngine arguments (from main.py)
    parser.add_argument(
        '--kb',
        type=str,
        default='data/knowledge_base.json',
        help='Knowledge base path'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output (not recommended for batch)'
    )
    
    # Multi-agent settings
    parser.add_argument(
        '--single-agent',
        action='store_true',
        help='Use single-agent instead of multi-agent (default: multi-agent)'
    )
    
    parser.add_argument(
        '--num-generators',
        type=int,
        default=3,
        help='Number of generators in multi-agent mode (default: 3)'
    )
    
    parser.add_argument(
        '--generator-temp',
        type=float,
        default=0.3,
        help='Temperature for generators (default: 0.3)'
    )
    
    parser.add_argument(
        '--critic-temp',
        type=float,
        default=0.0,
        help='Temperature for critic (default: 0.0)'
    )
    
    # Step2 enhancement settings
    parser.add_argument(
        '--no-step2',
        action='store_true',
        help='Disable Step2 DAG enhancement'
    )
    
    parser.add_argument(
        '--no-expert',
        action='store_true',
        help='Disable expert review in Step2'
    )
    
    parser.add_argument(
        '--no-rag',
        action='store_true',
        help='Disable RAG enhancement in Step2'
    )
    
    parser.add_argument(
        '--no-structure',
        action='store_true',
        help='Disable structure optimization in Step2'
    )
    
    # GRPO settings
    parser.add_argument(
        '--no-grpo',
        action='store_true',
        help='Disable GRPO experience loading'
    )
    
    args = parser.parse_args()
    
    # Prepare engine kwargs with absolute path for knowledge base
    kb_path = Path(args.kb)
    if not kb_path.is_absolute():
        kb_path = project_root / kb_path
    
    engine_kwargs = {
        'knowledge_base_path': str(kb_path),
        'use_multi_agent': not args.single_agent,
        'num_generators': args.num_generators,
        'generator_temperature': args.generator_temp,
        'critic_temperature': args.critic_temp,
        'use_grpo_experience': not args.no_grpo,
        'enable_step2_enhancement': not args.no_step2,
        'use_expert_review': not args.no_expert,
        'use_rag_enhancement': not args.no_rag,
        'use_structure_optimization': not args.no_structure,
    }
    
    # Initialize runner
    runner = CFGORunner(
        output_dir=args.output_dir,
        verbose=args.verbose,
        **engine_kwargs
    )
    
    # Run on dataset
    runner.run_on_dataset(args.dataset, args.limit)


if __name__ == "__main__":
    main()