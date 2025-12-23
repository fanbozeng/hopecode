"""
Critic Training Script
Critic 独立训练脚本

This script trains the Critic by:
1. Loading all 3 Generators' rollouts
2. Fusing each Generator's 3 rollouts separately
3. Computing fusion rewards (including r_fusion)
4. Extracting Critic experiences using GRPO (when σ > τ)
5. Saving all fusion results

此脚本训练Critic：
1. 加载所有3个Generator的rollouts
2. 分别融合每个Generator的3个rollouts
3. 计算融合奖励（包括r_fusion）
4. 使用GRPO提炼Critic经验（当σ > τ时）
5. 保存所有融合结果
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from typing import List, Dict, Any, Optional

# Import engine components
from engine.api_manager import APIKeyManager
from grpo_training.experience_extractor import ExperienceExtractor
from engine.scaffolder import LLMClient
from engine.llm_computer import LLMComputer
from engine.reward_evaluator import RewardEvaluator
from engine.multi_agent_scaffolder import MultiAgentScaffolder


CRITIC_ID = "critic"


def load_generator_rollouts(generator_id: str) -> Dict[str, Dict]:
    """
    Load rollouts from a Generator's JSONL file.
    
    Args:
        generator_id: 'generator_1', 'generator_2', or 'generator_3'
    
    Returns:
        Dictionary mapping problem_id -> rollouts_data
    """
    # Get absolute path to project root
    project_root = Path(__file__).parent.parent
    rollouts_file = project_root / "grpo_training" / "cache" / f"{generator_id}_rollouts.jsonl"
    
    if not rollouts_file.exists():
        raise FileNotFoundError(
            f"Rollouts file not found: {rollouts_file}\n"
            f"Please run {generator_id}.py first!"
        )
    
    rollouts_dict = {}
    
    with open(rollouts_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                problem_id = data['problem_id']
                rollouts_dict[problem_id] = data
    
    return rollouts_dict


def fuse_rollouts(
    rollouts: List[Dict[str, Any]],
    llm_client,
    problem_text: str
) -> Dict[str, Any]:
    """
    Fuse multiple rollouts using Critic with LLM-based fusion.
    使用LLM进行Critic融合
    
    Args:
        rollouts: List of 3 rollouts from one Generator
        llm_client: LLM client for fusion
        problem_text: Problem text
    
    Returns:
        Fused scaffold (dict or str depending on parse success)
    """
    # Extract scaffolds from rollouts
    proposals = []
    for r in rollouts:
        scaffold = r.get('scaffold')
        if scaffold:
            # Keep scaffold as-is (could be string or dict)
            proposals.append(scaffold)
    
    # If less than 3 proposals, pad with empty or return best one
    if len(proposals) == 0:
        return None
    elif len(proposals) < 3:
        # Not enough proposals, return the best one based on reward
        best_idx = 0
        best_reward = -1
        for i, r in enumerate(rollouts):
            if r.get('r_total', 0) > best_reward:
                best_reward = r.get('r_total', 0)
                best_idx = i
        return rollouts[best_idx].get('scaffold')
    
    # Load Critic fusion prompt using absolute path
    project_root = Path(__file__).parent.parent
    fusion_prompt_path = project_root / "prompts" / "critic_fusion_prompt.txt"
    if not fusion_prompt_path.exists():
        print("⚠️ Critic fusion prompt not found, returning best proposal")
        # Fallback: return proposal with highest reward
        best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
        return rollouts[best_idx].get('scaffold')
    
    with open(fusion_prompt_path, 'r', encoding='utf-8') as f:
        fusion_prompt_template = f.read()
    
    # Format proposals as JSON strings
    proposal_strs = []
    for i, prop in enumerate(proposals[:3]):  # Take first 3
        if isinstance(prop, dict):
            proposal_strs.append(json.dumps(prop, indent=2, ensure_ascii=False))
        else:
            proposal_strs.append(str(prop))
    
    # Pad if needed
    while len(proposal_strs) < 3:
        proposal_strs.append(json.dumps({"error": "No proposal"}, indent=2))
    
    # Fill in the prompt
    try:
        fusion_prompt = fusion_prompt_template.format(
            problem_text=problem_text,
            retrieved_knowledge="",  # No retrieved knowledge in this context
            proposal_1=proposal_strs[0],
            proposal_2=proposal_strs[1],
            proposal_3=proposal_strs[2]
        )
        
        # Call LLM for fusion
        response = llm_client.complete(fusion_prompt, temperature=0.0)
        
        # Parse fused scaffold from response
        fused_scaffold = _parse_fused_scaffold(response)
        
        if fused_scaffold:
            return fused_scaffold
        else:
            print("⚠️ Failed to parse fused scaffold, returning best proposal")
            best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
            return rollouts[best_idx].get('scaffold')
            
    except Exception as e:
        print(f"⚠️ Fusion failed: {e}, returning best proposal")
        best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
        return rollouts[best_idx].get('scaffold')


def _parse_fused_scaffold(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse fused scaffold from LLM response.
    从LLM响应中解析融合后的scaffold
    
    Args:
        response: LLM response containing JSON
    
    Returns:
        Parsed scaffold dict or None
    """
    try:
        # Find JSON block in response
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)
            
            # Extract problem_analysis if it exists
            if 'problem_analysis' in data:
                return data['problem_analysis']
            else:
                return data
        
        return None
    except Exception as e:
        print(f"⚠️ JSON parsing error in fusion: {e}")
        return None


def compute_fusion_rewards(
    fused_scaffold: Dict[str, Any],
    rollouts: List[Dict[str, Any]],
    problem: Dict[str, Any],
    llm_computer: LLMComputer,
    reward_evaluator: RewardEvaluator
) -> Dict[str, float]:
    """
    Compute rewards for fused scaffold.
    
    Args:
        fused_scaffold: Fused scaffold from Critic
        rollouts: Original rollouts used for fusion
        problem: Problem data with answer
        llm_computer: LLM computer for answer computation
        reward_evaluator: Reward evaluator
    
    Returns:
        Dictionary with all reward components
    """
    # Compute answer from fused scaffold
    try:
        computation_result = llm_computer.compute_from_scaffold(
            causal_scaffold=fused_scaffold,
            problem_text=problem['text']
        )
        
        if computation_result['success']:
            answer = computation_result['result']
        else:
            answer = None
    except:
        answer = None
    
    # Compute rewards
    if answer is not None:
        r_ans = reward_evaluator.evaluate_answer(answer, problem['answer'], problem['text'])
        is_correct = (r_ans >= 0.99)  # Consider correct if score >= 0.99
    else:
        is_correct = False
        r_ans = 0.0
    
    # r_logic: Logic quality of fused scaffold
    r_logic = reward_evaluator.evaluate_logic(
        trajectory=str(fused_scaffold),
        problem_text=problem['text']
    )
    
    # r_graph: Graph quality of fused scaffold
    r_graph = reward_evaluator.evaluate_graph(fused_scaffold)
    
    # r_fusion: Fusion effectiveness
    proposals = [r.get('scaffold') for r in rollouts if r.get('scaffold')]
    r_fusion = reward_evaluator.evaluate_fusion(
        proposals=proposals,
        fused_result=fused_scaffold,
        ground_truth=problem['answer']
    )
    
    # Total reward (weighted sum for Critic)
    # Critic has different weights: emphasizes fusion quality
    r_total = 0.3 * r_ans + 0.2 * r_logic + 0.2 * r_graph + 0.3 * r_fusion
    
    return {
        'answer': answer,
        'is_correct': is_correct,
        'r_ans': r_ans,
        'r_logic': r_logic,
        'r_graph': r_graph,
        'r_fusion': r_fusion,
        'r_total': r_total
    }


def save_fusion_result(
    problem: Dict[str, Any],
    generator_id: str,
    fused_scaffold: Dict[str, Any],
    rewards: Dict[str, float],
    output_file: str
):
    """
    Save fusion result to JSONL file (append mode).
    
    Args:
        problem: Problem data
        generator_id: Which Generator's rollouts were fused
        fused_scaffold: Fused scaffold
        rewards: Computed rewards
        output_file: Output JSONL file path
    """
    record = {
        'problem_id': problem['id'],
        'problem_text': problem['text'],
        'ground_truth': problem['answer'],
        'generator_id': generator_id,
        'fused_scaffold': str(fused_scaffold),  # Convert to string for JSON
        'final_answer': rewards['answer'],
        'is_correct': rewards['is_correct'],
        'rewards': {
            'r_ans': rewards['r_ans'],
            'r_logic': rewards['r_logic'],
            'r_graph': rewards['r_graph'],
            'r_fusion': rewards['r_fusion'],
            'r_total': rewards['r_total']
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Append to JSONL file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Train Critic independently')
    
    parser.add_argument('--temperature', type=float, default=0.0,
                       help='Temperature for Critic (default: 0.0 for deterministic)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print(f"🧠 Critic Training")
    print(f"🧠 Critic 训练")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Temperature: {args.temperature}")
    print(f"  Critic ID: {CRITIC_ID}\n")
    
    # Step 1: Load API configuration
    print("Step 1: Loading API configuration...")
    import os
    from pathlib import Path
    # Get absolute path to project root
    project_root = Path(__file__).parent.parent
    config_path = project_root / "data" / "api_keys" / "api_config.json"
    print(f"  Config path: {config_path}")
    api_manager = APIKeyManager(config_path=str(config_path))
    api_key = api_manager.get_api_key(CRITIC_ID)
    print(f"  ✓ API key loaded for {CRITIC_ID}: {api_key[:15]}...")
    
    # Step 2: Set environment variable for LLMClient
    print("\nStep 2: Setting up environment...")
    os.environ["SILICONFLOW_API_KEY"] = api_key
    print(f"  ✓ Environment configured for {CRITIC_ID}")
    
    # Step 3: Initialize components
    print("\nStep 3: Initializing components...")
    llm_client = LLMClient(provider="siliconflow")
    critic_scaffolder = MultiAgentScaffolder(
        llm_client=llm_client,
        num_generators=1,  # Not used in fusion mode
        critic_temperature=args.temperature
    )
    llm_computer = LLMComputer(verbose=False)
    reward_evaluator = RewardEvaluator(llm_client=llm_client, verbose=False)
    experience_extractor = ExperienceExtractor(llm_client=llm_client, tau=0.05, verbose=True)
    print("  ✓ All components initialized")
    
    # Step 4: Load all Generators' rollouts
    print("\nStep 4: Loading Generators' rollouts...")
    gen1_rollouts = load_generator_rollouts('generator_1')
    gen2_rollouts = load_generator_rollouts('generator_2')
    gen3_rollouts = load_generator_rollouts('generator_3')
    print(f"  ✓ Loaded {len(gen1_rollouts)} problems from generator_1")
    print(f"  ✓ Loaded {len(gen2_rollouts)} problems from generator_2")
    print(f"  ✓ Loaded {len(gen3_rollouts)} problems from generator_3")
    
    # Verify all generators have same problems
    problem_ids = set(gen1_rollouts.keys()) & set(gen2_rollouts.keys()) & set(gen3_rollouts.keys())
    problem_ids = sorted(problem_ids)
    print(f"  ✓ Found {len(problem_ids)} common problems across all generators")
    
    # Step 5: Critic fusion loop
    print("\nStep 5: Starting Critic fusion loop...")
    print("="*80)
    
    # Use absolute path for output file
    output_file = str(project_root / "grpo_training" / "cache" / "critic_results.jsonl")
    
    for problem_id in tqdm(problem_ids, desc="Critic Fusion"):
        # Get problem data (same across all generators)
        problem = {
            'id': problem_id,
            'text': gen1_rollouts[problem_id]['problem_text'],
            'answer': gen1_rollouts[problem_id]['ground_truth']
        }
        
        # Fuse each Generator's rollouts separately
        fusion_results = []
        
        for gen_id, gen_rollouts_dict in [
            ('generator_1', gen1_rollouts),
            ('generator_2', gen2_rollouts),
            ('generator_3', gen3_rollouts)
        ]:
            rollouts = gen_rollouts_dict[problem_id]['rollouts']
            
            # Fuse this Generator's 3 rollouts
            fused_scaffold = fuse_rollouts(
                rollouts=rollouts,
                llm_client=llm_client,
                problem_text=problem['text']
            )
            
            # Compute fusion rewards
            rewards = compute_fusion_rewards(
                fused_scaffold=fused_scaffold,
                rollouts=rollouts,
                problem=problem,
                llm_computer=llm_computer,
                reward_evaluator=reward_evaluator
            )
            
            # Save fusion result
            save_fusion_result(
                problem=problem,
                generator_id=gen_id,
                fused_scaffold=fused_scaffold,
                rewards=rewards,
                output_file=output_file
            )
            
            # Store for experience extraction (include full fusion result)
            # 存储用于经验提取（包含完整的融合结果）
            fusion_results.append({
                **rewards,  # Include all reward scores / 包含所有奖励分数
                'fused_dag': fused_scaffold  # Include full DAG for analysis / 包含完整DAG用于分析
            })
        
        # Extract Critic experiences (GRPO)
        experience_extractor.extract_critic_experience(
            problem=problem,
            fusion_results=fusion_results,
            ground_truth=problem['answer']
        )
    
    print("\n" + "="*80)
    print(f"✅ Critic Training Complete!")
    print(f"✅ Critic 训练完成！")
    print("="*80)
    print(f"\nOutputs:")
    print(f"  - Fusion results: {output_file}")
    print(f"  - Experiences: data/grpo_experiences/{CRITIC_ID}_experiences.json")
    print()


if __name__ == "__main__":
    main()

