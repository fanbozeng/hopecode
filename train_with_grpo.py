"""
Training Script for Training-Free GRPO
训练自由GRPO训练脚本

This script trains the multi-agent causal reasoning system using Training-Free GRPO:
- Loads training problems from AIME2024, AIME2025, and physics datasets
- Trains experience libraries for 3 generators + 1 critic
- Saves learned experiences for deployment

此脚本使用训练自由GRPO训练多智能体因果推理系统：
- 从AIME2024、AIME2025和物理数据集加载训练问题
- 为3个生成器+1个批判者训练经验库
- 保存学到的经验用于部署

Usage:
    python train_with_grpo.py --epochs 3 --group-size 3
    python train_with_grpo.py --dataset aime2024 --epochs 5
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Import components
from main import CausalReasoningEngine
from engine import GRPOExperienceManager, TrainingFreeGRPOTrainer


def load_training_problems(
    datasets: List[str] = ['aime2024', 'aime2025', 'physics'],
    max_problems: int = None
) -> List[Dict[str, Any]]:
    """
    Load training problems from specified datasets.
    从指定数据集加载训练问题
    
    Args:
        datasets: List of dataset names to load
        max_problems: Maximum number of problems to load (None for all)
    
    Returns:
        List of problems with format:
        [{"problem": str, "answer": str, "subject": str, "dataset": str}, ...]
    """
    training_problems = []
    
    print("\n📚 Loading training problems...")
    print("📚 正在加载训练问题...")
    
    for dataset_name in datasets:
        dataset_name_lower = dataset_name.lower()
        
        if dataset_name_lower == 'aime2024':
            problems = load_aime2024()
            training_problems.extend(problems)
            print(f"  ✓ Loaded {len(problems)} problems from AIME 2024")
            
        elif dataset_name_lower == 'aime2025':
            problems = load_aime2025()
            training_problems.extend(problems)
            print(f"  ✓ Loaded {len(problems)} problems from AIME 2025")
            
        elif dataset_name_lower == 'physics':
            problems = load_physics_problems()
            training_problems.extend(problems)
            print(f"  ✓ Loaded {len(problems)} problems from Physics dataset")
        
        else:
            print(f"  ⚠ Unknown dataset: {dataset_name}")
    
    # Limit number of problems if specified
    if max_problems and len(training_problems) > max_problems:
        training_problems = training_problems[:max_problems]
        print(f"\n✂️ Limited to {max_problems} problems")
    
    print(f"\n✅ Total training problems: {len(training_problems)}")
    
    return training_problems


def load_aime2024() -> List[Dict[str, Any]]:
    """Load AIME 2024 problems."""
    problems = []
    
    # Try .jsonl first (correct format), then .json as fallback
    dataset_paths = [
        Path("dataset/AIME_2024/aime_2024_problems.jsonl"),
        Path("dataset/AIME_2024/aime_2024_problems.json")
    ]
    
    for dataset_path in dataset_paths:
        if not dataset_path.exists():
            continue
        
        try:
            # JSONL format (one JSON object per line)
            if dataset_path.suffix == '.jsonl':
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            item = json.loads(line)
                            # Handle both formats
                            problem_text = item.get('Problem', item.get('problem', ''))
                            answer = item.get('Answer', item.get('answer', ''))
                            
                            if problem_text:  # Only add if problem exists
                                problems.append({
                                    'problem': problem_text,
                                    'answer': str(answer),
                                    'subject': 'mathematics',
                                    'dataset': 'AIME 2024'
                                })
                return problems  # Success, return immediately
            
            # JSON format (single JSON object or array)
            else:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # AIME format: list of problems with "problem", "answer", etc.
                if isinstance(data, list):
                    for item in data:
                        problems.append({
                            'problem': item.get('problem', ''),
                            'answer': str(item.get('answer', '')),
                            'subject': 'mathematics',
                            'dataset': 'AIME 2024'
                        })
                elif isinstance(data, dict):
                    # Handle dict format
                    for key, value in data.items():
                        if isinstance(value, dict):
                            problems.append({
                                'problem': value.get('problem', ''),
                                'answer': str(value.get('answer', '')),
                                'subject': 'mathematics',
                                'dataset': 'AIME 2024'
                            })
                return problems  # Success, return immediately
        
        except Exception as e:
            print(f"  ⚠ Error loading {dataset_path.name}: {e}")
            continue
    
    # If we get here, no file was found
    print(f"  ⚠ AIME 2024 dataset not found")
    return problems


def load_aime2025() -> List[Dict[str, Any]]:
    """Load AIME 2025 problems."""
    problems = []
    
    # Try various AIME 2025 file formats
    dataset_paths = [
        Path("dataset/AIME2025/aime_2025_problems.jsonl"),  # New format
        Path("dataset/AIME2025/aime2025-I.jsonl"),          # AIME I
        Path("dataset/AIME2025/aime2025-II.jsonl")          # AIME II
    ]
    
    for dataset_path in dataset_paths:
        if not dataset_path.exists():
            continue
        
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        # Handle both 'question' and 'problem' keys
                        problem_text = item.get('question', item.get('problem', ''))
                        answer = item.get('answer', '')
                        
                        if problem_text:  # Only add if problem exists
                            problems.append({
                                'problem': problem_text,
                                'answer': str(answer),
                                'subject': 'mathematics',
                                'dataset': f'AIME 2025 ({dataset_path.stem})'
                            })
        
        except Exception as e:
            print(f"  ⚠ Error loading {dataset_path.name}: {e}")
            continue
    
    if not problems:
        print(f"  ⚠ AIME 2025 dataset not found")
    
    return problems


def load_physics_problems() -> List[Dict[str, Any]]:
    """
    Load physics problems.
    加载物理问题
    
    Note: You need to create a physics_problems.json file with your 30 physics problems.
    注意：您需要创建一个physics_problems.json文件，包含您的30道物理问题。
    
    Format:
    [
        {
            "problem": "A ball is dropped from a height of 10m. Calculate the time to reach the ground.",
            "answer": "1.43",
            "subject": "physics",
            "topic": "free_fall"
        },
        ...
    ]
    """
    problems = []
    dataset_path = Path("dataset/physics_problems.json")
    
    if not dataset_path.exists():
        print(f"  ℹ Physics dataset not found at {dataset_path}")
        print(f"  ℹ Please create this file with your 30 physics problems")
        return problems
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            problems.append({
                'problem': item.get('problem', ''),
                'answer': str(item.get('answer', '')),
                'subject': item.get('subject', 'physics'),
                'dataset': 'Physics',
                'topic': item.get('topic', '')
            })
    
    except Exception as e:
        print(f"  ✗ Error loading physics problems: {e}")
    
    return problems


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(
        description='Train multi-agent causal reasoning system with Training-Free GRPO'
    )
    
    parser.add_argument(
        '--datasets',
        nargs='+',
        default=['aime2024', 'aime2025', 'physics'],
        help='Datasets to use for training (default: aime2024 aime2025 physics)'
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs (default: 3)'
    )
    
    parser.add_argument(
        '--group-size',
        type=int,
        default=3,
        help='Number of rollouts per problem (default: 3, uses 3 generators)'
    )

    # Execution mode controls
    parser.add_argument(
        '--gen-exec',
        choices=['parallel', 'serial'],
        default='parallel',
        help='Execution across 3 generators: parallel or serial (default: parallel)'
    )

    parser.add_argument(
        '--rollout-exec',
        choices=['parallel', 'serial'],
        default='parallel',
        help='Execution inside each generator for its N rollouts: parallel or serial (default: parallel)'
    )
    
    parser.add_argument(
        '--max-problems',
        type=int,
        default=None,
        help='Maximum number of problems to use (default: all)'
    )
    
    parser.add_argument(
        '--experience-dir',
        type=str,
        default='data/grpo_experiences',
        help='Directory to save experience libraries'
    )
    
    parser.add_argument(
        '--use-existing-experiences',
        action='store_true',
        help='Continue training from existing experiences'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🎓 Training-Free GRPO Training")
    print("🎓 训练自由GRPO训练")
    print("="*80)
    
    print(f"\n⚙️ Configuration:")
    print(f"   - Datasets: {', '.join(args.datasets)}")
    print(f"   - Epochs: {args.epochs}")
    print(f"   - Group size: {args.group_size}")
    print(f"   - Experience dir: {args.experience_dir}")
    print(f"   - Generator execution: {args.gen_exec}")
    print(f"   - Rollout execution: {args.rollout_exec}")
    
    # Step 1: Initialize Experience Manager
    print("\n" + "─"*80)
    print("Step 1: Initializing Experience Manager")
    print("步骤1：初始化经验管理器")
    print("─"*80)
    # 加载历史经验 可以理解加载历史经验库 没什么实际意义在这里
    experience_manager = GRPOExperienceManager(
        experience_dir=args.experience_dir,
        verbose=True
    )
    
    # Step 2: Initialize Causal Reasoning Engine with Experience Manager
    print("\n" + "─"*80)
    print("Step 2: Initializing Causal Reasoning Engine")
    print("步骤2：初始化因果推理引擎")
    print("─"*80)
    
    engine = CausalReasoningEngine(
        verbose=True,
        use_multi_agent=True,
        num_generators=3,
        generator_temperature=0.3,
        critic_temperature=0.0,
        computation_mode='llm',  # Use LLM mode for training
        use_vector_retriever=True  # Use vector retriever for better knowledge retrieval
    )
    
    # Inject experience manager and rollouts_per_generator into the multi-agent scaffolder
    if hasattr(engine, 'scaffolder') and hasattr(engine.scaffolder, '__class__'):
        # Check if it's a MultiAgentScaffolder 给multiagent加载数据
        if 'MultiAgent' in engine.scaffolder.__class__.__name__:
            engine.scaffolder.experience_manager = experience_manager
            engine.scaffolder.rollouts_per_generator = args.group_size  # Set rollouts per generator
            # Configure execution modes for GRPO training (if supported)
            try:
                engine.scaffolder.parallel_generators = (args.gen_exec == 'parallel')
                engine.scaffolder.parallel_rollouts = (args.rollout_exec == 'parallel')
            except Exception:
                pass
            # Report effective execution modes
            try:
                print(f"? Generator execution mode: {args.gen_exec}")
                print(f"? Rollout execution mode: {args.rollout_exec}")
            except Exception:
                pass
            print("✓ Experience manager injected into scaffolder")
            print("✓ 经验管理器已注入脚手架器")
            print(f"✓ Rollouts per generator set to: {args.group_size}")
            print(f"✓ 每个生成器的rollouts设置为: {args.group_size}")
        else:
            print("⚠ Warning: Not using MultiAgentScaffolder, experiences won't be injected")
    
    # Step 3: Load Training Problems
    print("\n" + "─"*80)
    print("Step 3: Loading Training Problems")
    print("步骤3：加载训练问题")
    print("─"*80)
    
    training_problems = load_training_problems(
        datasets=args.datasets,
        max_problems=args.max_problems
    )
    
    if len(training_problems) == 0:
        print("\n❌ No training problems loaded. Exiting.")
        return
    
    # Step 4: Initialize Trainer
    print("\n" + "─"*80)
    print("Step 4: Initializing Trainer")
    print("步骤4：初始化训练器")
    print("─"*80)
    
    trainer = TrainingFreeGRPOTrainer(
        causal_engine=engine,
        experience_manager=experience_manager,
        rollouts_per_generator=args.group_size,
        num_epochs=args.epochs,
        verbose=True
    )
    
    # Step 5: Train
    print("\n" + "─"*80)
    print("Step 5: Starting Training")
    print("步骤5：开始训练")
    print("─"*80)
    
    trainer.train(
        training_problems=training_problems,
        save_checkpoint=True
    )
    
    # Step 6: Export Final Experiences
    print("\n" + "─"*80)
    print("Step 6: Exporting Final Experiences")
    print("步骤6：导出最终经验")
    print("─"*80)
    
    export_path = Path("data/grpo_experiences_final.json")
    experience_manager.export_for_deployment(str(export_path))
    
    print(f"\n✅ Training complete!")
    print(f"✅ 训练完成！")
    print(f"\n📦 Final experiences saved to: {export_path}")
    print(f"📦 最终经验已保存到: {export_path}")
    
    # Print final summary
    experience_manager.print_summary()
    
    print("\n" + "="*80)
    print("🎉 Training-Free GRPO Training Complete!")
    print("🎉 训练自由GRPO训练完成！")
    print("="*80)
    
    print("\n📝 Next Steps:")
    print("1. Review the learned experiences in:", args.experience_dir)
    print("2. Use the trained system for evaluation:")
    print("   python evaluate_framework.py --use-grpo-experiences")
    print("\n📝 后续步骤：")
    print("1. 查看学到的经验:", args.experience_dir)
    print("2. 使用训练好的系统进行评估:")
    print("   python evaluate_framework.py --use-grpo-experiences")


if __name__ == "__main__":
    main()
