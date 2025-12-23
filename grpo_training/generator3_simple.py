"""
Generator 1 简化版训练脚本
功能：加载数据集，生成rollouts，计算奖励，提取经验
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 导入需要的组件
from engine.api_manager import APIKeyManager
from grpo_training.experience_extractor import ExperienceExtractor
from engine.scaffolder import LLMClient, CausalScaffolder
from engine.llm_computer import LLMComputer
from engine.reward_evaluator import RewardEvaluator
from grpo_training.training_stats import TrainingStats

GENERATOR_ID = "generator_1"


def load_problems(dataset="full", max_problems=None):
    """
    加载训练题目
    - full: 完整90题（AIME2024 30题 + AIME2025 30题 + 物理 30题）
    - aime2024: 单独AIME2024
    - aime2025: 单独AIME2025
    - physics: 单独物理题
    """
    problems = []
    project_root = Path(__file__).parent.parent

    if dataset == "full":
        # 从配置文件读取
        config_path = project_root / "grpo_training" / "dataset_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)

        for source in config['full_dataset']['datasets']:
            dataset_path = project_root / source['path']

            if source['format'] == 'jsonl':
                # JSONL格式文件
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if max_problems and len(problems) >= max_problems:
                            break
                        data = json.loads(line.strip())
                        problems.append({
                            'id': f"{source['id_prefix']}_{i+1:03d}",
                            'text': data.get(source['problem_field'], ''),
                            'answer': str(data.get(source['answer_field'], ''))
                        })

            elif source['format'] == 'json':
                # JSON格式文件
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for i, item in enumerate(data):
                        if max_problems and len(problems) >= max_problems:
                            break
                        problems.append({
                            'id': f"{source['id_prefix']}_{i+1:03d}",
                            'text': item.get(source['problem_field'], ''),
                            'answer': str(item.get(source['answer_field'], ''))
                        })

        print(f"✓ 加载完成: {len(problems)} 道题目")

    else:
        # 单独数据集加载逻辑
        print(f"✓ 暂时只支持 full 数据集")

    return problems


def generate_rollouts(problem, scaffolder, computer, evaluator, extractor, num_rollouts=3):
    """
    为一道题生成多个rollouts并计算奖励
    """
    rollouts = []

    # 加载当前经验库
    experiences_list = extractor._load_experiences(GENERATOR_ID)
    experiences = [exp['content'] for exp in experiences_list]

    for i in range(1, num_rollouts + 1):
        try:
            print(f"  生成Rollout {i}...")

            # 生成因果图
            scaffold = scaffolder.generate_scaffold(
                problem_text=problem['text'],
                retrieved_knowledge=[],
                experiences=experiences
            )

            # 计算答案
            result = computer.compute_from_scaffold(
                causal_scaffold=scaffold,
                problem_text=problem['text']
            )

            if result['success']:
                answer = result['result']
                is_correct = evaluator.evaluate_answer(answer, problem['answer'], problem['text']) >= 0.99
            else:
                answer = None
                is_correct = False

            # 计算奖励
            r_ans = evaluator.evaluate_answer(answer, problem['answer'], problem['text']) if answer else 0.0
            r_logic = evaluator.evaluate_logic(str(scaffold), problem['text'])
            r_graph = evaluator.evaluate_graph(scaffold)
            r_total = 0.5 * r_ans + 0.25 * r_logic + 0.25 * r_graph

            rollouts.append({
                'rollout_id': i,
                'scaffold': scaffold,
                'answer': answer,
                'is_correct': is_correct,
                'r_total': r_total
            })

            print(f"  ✓ Rollout {i}: {'正确' if is_correct else '错误'} (奖励: {r_total:.2f})")

        except Exception as e:
            print(f"  ✗ Rollout {i} 失败: {e}")
            rollouts.append({
                'rollout_id': i,
                'error': str(e),
                'r_total': 0.0
            })

    return rollouts


def save_results(problem, rollouts, output_file):
    """
    保存结果到文件
    """
    record = {
        'problem_id': problem['id'],
        'problem_text': problem['text'],
        'ground_truth': problem['answer'],
        'rollouts': rollouts,
        'timestamp': datetime.now().isoformat()
    }

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Generator 1 训练脚本')
    parser.add_argument('--dataset', type=str, default='full', help='数据集选择')
    parser.add_argument('--max-problems', type=int, help='最大题目数量')
    parser.add_argument('--rollouts', type=int, default=3, help='每题生成rollouts数量')
    parser.add_argument('--temperature', type=float, default=0.3, help='生成温度')

    args = parser.parse_args()

    print("=" * 60)
    print("🤖 Generator 1 开始训练")
    print("=" * 60)

    # 1. 初始化组件
    print("1. 初始化组件...")
    project_root = Path(__file__).parent.parent

    # 加载API密钥
    api_manager = APIKeyManager(str(project_root / "data" / "api_keys" / "api_config.json"))
    api_key = api_manager.get_api_key(GENERATOR_ID)

    # 设置环境变量
    import os
    os.environ["SILICONFLOW_API_KEY"] = api_key

    # 初始化各个组件
    llm_client = LLMClient(provider="siliconflow")
    scaffolder = CausalScaffolder(llm_client=llm_client)
    computer = LLMComputer(verbose=False)
    evaluator = RewardEvaluator(llm_client=llm_client, verbose=False)
    extractor = ExperienceExtractor(llm_client=llm_client, tau=0.05, verbose=False)

    # 初始化正确率统计
    stats = TrainingStats(GENERATOR_ID)

    print("✓ 组件初始化完成")

    # 2. 加载数据
    print("\n2. 加载训练数据...")
    problems = load_problems(args.dataset, args.max_problems)
    print(f"✓ 加载了 {len(problems)} 道题目")

    # 3. 开始训练
    print("\n3. 开始训练...")
    output_file = str(project_root / "grpo_training" / "cache" / f"{GENERATOR_ID}_results.json")

    # 统计数据
    total_correct_problems = 0
    total_correct_rollouts = 0
    total_rollouts = 0
    total_reward = 0.0

    for idx, problem in enumerate(tqdm(problems, desc="训练进度"), 1):
        print(f"\n--- 题目 {idx}/{len(problems)}: {problem['id']} ---")

        # 显示当前经验库大小
        current_experiences = extractor._load_experiences(GENERATOR_ID)
        print(f"当前经验库: {len(current_experiences)} 条")

        # 生成rollouts
        rollouts = generate_rollouts(problem, scaffolder, computer, evaluator, extractor, args.rollouts)

        # 保存结果
        save_results(problem, rollouts, output_file)

        # 提取经验
        extractor.extract_generator_experience(
            generator_id=GENERATOR_ID,
            problem=problem,
            rollouts=rollouts,
            ground_truth=problem['answer']
        )

        # 显示更新后的经验库
        updated_experiences = extractor._load_experiences(GENERATOR_ID)
        print(f"更新后经验库: {len(updated_experiences)} 条")

        # 统计正确率
        correct_count = sum(1 for r in rollouts if r.get('is_correct', False))
        print(f"本题目正确率: {correct_count}/{len(rollouts)} = {correct_count/len(rollouts)*100:.1f}%")

        # 累计统计数据
        total_rollouts += len(rollouts)
        total_correct_rollouts += correct_count
        if correct_count > 0:  # 至少有一个rollout正确
            total_correct_problems += 1
        total_reward += sum(r.get('r_total', 0) for r in rollouts)

    # 计算正确率
    problem_accuracy = total_correct_problems / len(problems) if problems else 0.0
    rollout_accuracy = total_correct_rollouts / total_rollouts if total_rollouts > 0 else 0.0
    avg_reward = total_reward / total_rollouts if total_rollouts > 0 else 0.0

    # 记录统计
    additional_metrics = {
        "rollout_accuracy": rollout_accuracy,
        "total_experiences": len(extractor._load_experiences(GENERATOR_ID)),
        "total_rollouts": total_rollouts
    }

    stats.record_epoch(
        epoch_num=len(stats.stats_data["epochs"]) + 1,
        total_problems=len(problems),
        correct_answers=total_correct_problems,
        total_reward=total_reward,
        avg_reward=avg_reward,
        additional_metrics=additional_metrics
    )

    print("\n" + "=" * 60)
    print("✅ Generator 1 训练完成!")
    print(f"📁 结果保存至: {output_file}")
    print(f"🧠 经验保存至: data/grpo_experiences/{GENERATOR_ID}_experiences.json")
    print(f"📊 统计保存至: training_stats/{GENERATOR_ID}_stats.json")

    # 打印正确率统计
    print(f"\n📊 本次训练统计:")
    print(f"总题目数: {len(problems)}")
    print(f"题目正确率: {total_correct_problems}/{len(problems)} = {problem_accuracy:.3f} ({problem_accuracy*100:.1f}%)")
    print(f"Rollout正确率: {total_correct_rollouts}/{total_rollouts} = {rollout_accuracy:.3f} ({rollout_accuracy*100:.1f}%)")
    print(f"平均奖励: {avg_reward:.3f}")

    # 生成统计图表和报告
    try:
        chart_path = f"training_stats/{GENERATOR_ID}_progress.png"
        stats.plot_progress(save_path=chart_path)
        report_path = stats.export_detailed_report()
    except Exception as e:
        print(f"生成统计图表失败: {e}")

    print("=" * 60)


if __name__ == "__main__":
    main()