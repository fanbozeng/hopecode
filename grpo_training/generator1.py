"""
Generator 1 Training Script
Generator 1 独立训练脚本

This script trains Generator 1 independently by:
1. Loading training problems
2. Generating 3 rollouts per problem
3. Computing rewards for each rollout
4. Extracting experiences using GRPO (when σ > τ)
5. Saving all rollouts to cache

此脚本独立训练Generator 1：
1. 加载训练问题
2. 每个问题生成3个rollouts
3. 计算每个rollout的奖励
4. 使用GRPO提炼经验（当σ > τ时）
5. 保存所有rollouts到缓存
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from typing import List, Dict, Any

# Import engine components
from engine.api_manager import APIKeyManager
from grpo_training.experience_extractor import ExperienceExtractor
from engine.scaffolder import LLMClient, CausalScaffolder
from engine.llm_computer import LLMComputer
from engine.reward_evaluator import RewardEvaluator


GENERATOR_ID = "generator_1"


def load_training_problems(dataset: str = "aime2024", max_problems: int = None) -> List[Dict[str, Any]]:
    """
    Load training problems from dataset.
    
    Args:
        dataset: Dataset name ('aime2024', 'aime2025', 'physics')
        max_problems: Maximum number of problems to load
    
    Returns:
        List of problems with format: [{"id": str, "text": str, "answer": str}, ...]
    """
    problems = []
    
    # Get absolute path to project root
    project_root = Path(__file__).parent.parent
    
    if dataset == "aime2024":
        dataset_path = project_root / "dataset" / "AIME_2024" / "aime_2024_problems.jsonl"
        if dataset_path.exists():
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if max_problems and i >= max_problems:
                        break
                    data = json.loads(line.strip())
                    problems.append({
                        'id': f"aime2024_{i+1:03d}",
                        'text': data.get('Problem', data.get('problem', '')),
                        'answer': str(data.get('Answer', data.get('answer', '')))
                    })
        else:
            print(f"⚠️ Dataset file not found: {dataset_path}")
    
    elif dataset == "aime2025":
        dataset_paths = [
            project_root / "dataset" / "AIME2025" / "aime_2025_problems.jsonl",
            project_root / "dataset" / "AIME2025" / "aime2025-I.jsonl"
        ]
        for dataset_path in dataset_paths:
            if dataset_path.exists():
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if max_problems and len(problems) >= max_problems:
                            break
                        data = json.loads(line.strip())
                        problems.append({
                            'id': f"aime2025_{len(problems)+1:03d}",
                            'text': data.get('question', data.get('problem', '')),
                            'answer': str(data.get('answer', ''))
                        })
                break
            else:
                print(f"⚠️ Dataset file not found: {dataset_path}")
    
    elif dataset == "physics":
        dataset_path = project_root / "dataset" / "physics_problems.json"
        if dataset_path.exists():
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for i, item in enumerate(data):
                    if max_problems and i >= max_problems:
                        break
                    problems.append({
                        'id': f"physics_{i+1:03d}",
                        'text': item.get('problem', ''),
                        'answer': str(item.get('answer', ''))
                    })
        else:
            print(f"⚠️ Dataset file not found: {dataset_path}")
    
    return problems


def generate_rollouts_with_rewards(
    problem: Dict[str, Any],
    scaffolder: CausalScaffolder,
    llm_computer: LLMComputer,
    reward_evaluator: RewardEvaluator,
    experience_extractor: ExperienceExtractor,
    generator_id: str,
    num_rollouts: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate multiple rollouts for a problem and compute their rewards.
    
    Args:
        problem: Problem data
        scaffolder: Causal scaffolder for DAG generation
        llm_computer: LLM computer for answer computation
        reward_evaluator: Reward evaluator
        experience_extractor: Experience extractor (for loading experiences)
        generator_id: Generator ID (e.g., "generator_1")
        num_rollouts: Number of rollouts to generate (default: 3)
    
    Returns:
        List of rollouts with rewards
    """
    rollouts = []
    
    for i in range(1, num_rollouts + 1):
        try:
            # Load current experiences dynamically (may change after each problem)
            # 动态加载当前经验库（每个问题后可能会更新）
            experiences_list = experience_extractor._load_experiences(generator_id)
            experiences = [exp['content'] for exp in experiences_list]
            
            # Generate causal scaffold (DAG) with experiences
            # Note: retrieved_knowledge is for RAG, experiences is for GRPO
            scaffold = scaffolder.generate_scaffold(
                problem_text=problem['text'],
                retrieved_knowledge=[],  # RAG knowledge (currently disabled)
                experiences=experiences  # GRPO experiences (dynamically loaded)
            )
            
            # Compute answer from scaffold
            computation_result = llm_computer.compute_from_scaffold(
                causal_scaffold=scaffold,
                problem_text=problem['text']
            )
            
            if computation_result['success']:
                answer = computation_result['result']
            else:
                answer = None
            
            # Compute rewards
            if answer is not None:
                # r_ans: Answer correctness
                r_ans = reward_evaluator.evaluate_answer(answer, problem['answer'], problem['text'])
                is_correct = (r_ans >= 0.99)  # Consider correct if score >= 0.99
            else:
                r_ans = 0.0
                is_correct = False
            
            # r_logic: Logic quality
            r_logic = reward_evaluator.evaluate_logic(
                trajectory=str(scaffold),
                problem_text=problem['text']
            )
            
            # r_graph: Graph quality
            r_graph = reward_evaluator.evaluate_graph(scaffold)
            
            # Total reward (weighted sum)
            r_total = 0.5 * r_ans + 0.25 * r_logic + 0.25 * r_graph
            
            rollouts.append({
                'rollout_id': i,
                'scaffold': scaffold,
                'answer': answer,
                'is_correct': is_correct,
                'r_ans': r_ans,
                'r_logic': r_logic,
                'r_graph': r_graph,
                'r_total': r_total
            })
            
        except Exception as e:
            print(f"    ⚠️  Rollout {i} failed: {e}")
            # Add a failed rollout with zero rewards
            rollouts.append({
                'rollout_id': i,
                'scaffold': None,
                'answer': None,
                'is_correct': False,
                'r_ans': 0.0,
                'r_logic': 0.0,
                'r_graph': 0.0,
                'r_total': 0.0,
                'error': str(e)
            })
    
    return rollouts


def save_rollouts(problem: Dict[str, Any], rollouts: List[Dict[str, Any]], output_file: str):
    """
    Save rollouts to JSONL file (append mode).
    
    Args:
        problem: Problem data
        rollouts: List of rollouts with rewards
        output_file: Output JSONL file path
    """
    # Convert scaffolds to serializable format
    rollouts_serializable = []
    for r in rollouts:
        r_copy = r.copy()
        if r_copy['scaffold'] is not None:
            r_copy['scaffold'] = str(r_copy['scaffold'])  # Convert to string for JSON
        rollouts_serializable.append(r_copy)
    
    # Prepare record
    record = {
        'problem_id': problem['id'],
        'problem_text': problem['text'],
        'ground_truth': problem['answer'],
        'rollouts': rollouts_serializable,
        'timestamp': datetime.now().isoformat()
    }
    
    # Append to JSONL file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Train Generator 1 independently')
    
    parser.add_argument('--dataset', type=str, default='aime2024',
                       choices=['aime2024', 'aime2025', 'physics'],
                       help='Training dataset')
    
    parser.add_argument('--max-problems', type=int, default=None,
                       help='Maximum number of problems (None for all)')
    
    parser.add_argument('--rollouts', type=int, default=3,
                       help='Number of rollouts per problem')
    
    parser.add_argument('--temperature', type=float, default=0.3,
                       help='Temperature for Generator 1')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print(f"🤖 Generator 1 Training")
    print(f"🤖 Generator 1 训练")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Dataset: {args.dataset}")
    print(f"  Rollouts per problem: {args.rollouts}")
    print(f"  Temperature: {args.temperature}")
    print(f"  Generator ID: {GENERATOR_ID}\n")
    
    # Step 1: Load API configuration
    print("Step 1: Loading API configuration...")
    import os
    from pathlib import Path
    # Get absolute path to project root
    project_root = Path(__file__).parent.parent
    config_path = project_root / "data" / "api_keys" / "api_config.json"
    print(f"  Config path: {config_path}")
    api_manager = APIKeyManager(config_path=str(config_path))
    api_key = api_manager.get_api_key(GENERATOR_ID)
    print(f"  ✓ API key loaded for {GENERATOR_ID}: {api_key[:15]}...")
    
    # Step 2: Set environment variable for LLMClient
    print("\nStep 2: Setting up environment...")
    os.environ["SILICONFLOW_API_KEY"] = api_key
    print(f"  ✓ Environment configured for {GENERATOR_ID}")
    
    # Step 3: Initialize components
    print("\nStep 3: Initializing components...")
    llm_client = LLMClient(provider="siliconflow")
    scaffolder = CausalScaffolder(llm_client=llm_client)
    llm_computer = LLMComputer(verbose=False)
    reward_evaluator = RewardEvaluator(llm_client=llm_client, verbose=False)
    experience_extractor = ExperienceExtractor(llm_client=llm_client, tau=0.05, verbose=True)
    print("  ✓ All components initialized")
    
    # Step 4: Load training problems
    print("\nStep 4: Loading training problems...")
    problems = load_training_problems(args.dataset, args.max_problems)
    print(f"  ✓ Loaded {len(problems)} problems from {args.dataset}")
    
    # Step 5: Training loop
    print("\nStep 5: Starting training loop...")
    print("="*80)
    
    # Use absolute path for output file
    output_file = str(project_root / "grpo_training" / "cache" / f"{GENERATOR_ID}_rollouts.jsonl")
    
    for idx, problem in enumerate(tqdm(problems, desc=f"{GENERATOR_ID}"), 1):
        # Show current experience library size
        # 显示当前经验库大小
        current_experiences = experience_extractor._load_experiences(GENERATOR_ID)
        print(f"\n[Problem {idx}/{len(problems)}] Current experience library: {len(current_experiences)} items")
        print(f"[问题 {idx}/{len(problems)}] 当前经验库：{len(current_experiences)} 条")
        
        # Generate rollouts with rewards (using dynamically loaded experiences)
        # 生成rollouts（使用动态加载的经验库）
        rollouts = generate_rollouts_with_rewards(
            problem=problem,
            scaffolder=scaffolder,
            llm_computer=llm_computer,
            reward_evaluator=reward_evaluator,
            experience_extractor=experience_extractor,
            generator_id=GENERATOR_ID,
            num_rollouts=args.rollouts
        )
        
        # Save rollouts
        save_rollouts(problem, rollouts, output_file)
        
        # Extract experiences (GRPO) - will update experience library
        # 提取经验（GRPO）- 将更新经验库
        experience_extractor.extract_generator_experience(
            generator_id=GENERATOR_ID,
            problem=problem,
            rollouts=rollouts,
            ground_truth=problem['answer']
        )
        
        # Show updated experience library size
        # 显示更新后的经验库大小
        updated_experiences = experience_extractor._load_experiences(GENERATOR_ID)
        print(f"   → Updated experience library: {len(updated_experiences)} items")
        print(f"   → 更新后经验库：{len(updated_experiences)} 条")
    
    print("\n" + "="*80)
    print(f"✅ Generator 1 Training Complete!")
    print(f"✅ Generator 1 训练完成！")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  - Rollouts: {output_file}")
    print(f"  - Experiences: data/grpo_experiences/{GENERATOR_ID}_experiences.json")
    print()


if __name__ == "__main__":
    main()

