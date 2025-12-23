"""
Critic 简化版训练脚本
功能：融合3个Generator的rollouts，计算奖励，提取经验
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 导入需要的组件
from engine.api_manager import APIKeyManager
from grpo_training.experience_extractor import ExperienceExtractor
from engine.scaffolder import LLMClient
from engine.llm_computer import LLMComputer
from engine.reward_evaluator import RewardEvaluator
from engine.multi_agent_scaffolder import MultiAgentScaffolder
from grpo_training.training_stats import TrainingStats

CRITIC_ID = "critic"


def load_generator_rollouts(generator_id):
    """
    加载Generator的rollouts文件
    """
    project_root = Path(__file__).parent.parent
    rollouts_file = project_root / "grpo_training" / "cache" / f"{generator_id}_rollouts.jsonl"

    if not rollouts_file.exists():
        print(f"❌ 找不到文件: {rollouts_file}")
        print(f"请先运行 {generator_id}.py!")
        return {}

    rollouts_dict = {}

    with open(rollouts_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                problem_id = data['problem_id']
                rollouts_dict[problem_id] = data

    return rollouts_dict


def fuse_rollouts(rollouts, llm_client, problem_text):
    """
    融合多个rollouts，生成一个更好的scaffold
    """
    print(f"  融合 {len(rollouts)} 个rollouts...")

    # 提取scaffolds
    proposals = []
    for r in rollouts:
        scaffold = r.get('scaffold')
        if scaffold:
            proposals.append(scaffold)

    # 如果没有足够的proposals，返回最好的一个
    if len(proposals) == 0:
        return None
    elif len(proposals) < 3:
        # 返回奖励最高的那个
        best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
        return rollouts[best_idx].get('scaffold')

    # 加载融合prompt
    project_root = Path(__file__).parent.parent
    fusion_prompt_path = project_root / "prompts" / "critic_fusion_prompt.txt"

    if not fusion_prompt_path.exists():
        print("  ⚠️ 找不到融合prompt，返回最好的proposal")
        best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
        return rollouts[best_idx].get('scaffold')

    # 格式化proposals为JSON字符串
    proposal_strs = []
    for i, prop in enumerate(proposals[:3]):
        if isinstance(prop, dict):
            proposal_strs.append(json.dumps(prop, indent=2, ensure_ascii=False))
        else:
            proposal_strs.append(str(prop))

    # 补齐到3个
    while len(proposal_strs) < 3:
        proposal_strs.append(json.dumps({"error": "No proposal"}, indent=2))

    try:
        # 读取prompt模板
        with open(fusion_prompt_path, 'r', encoding='utf-8') as f:
            fusion_prompt_template = f.read()

        # 填充prompt
        fusion_prompt = fusion_prompt_template.format(
            problem_text=problem_text,
            retrieved_knowledge="",
            proposal_1=proposal_strs[0],
            proposal_2=proposal_strs[1],
            proposal_3=proposal_strs[2]
        )

        # 调用LLM进行融合
        response = llm_client.complete(fusion_prompt, temperature=0.0)

        # 解析融合结果
        fused_scaffold = parse_fused_scaffold(response)

        if fused_scaffold:
            print(f"  ✓ 融合成功")
            return fused_scaffold
        else:
            print("  ⚠️ 融合失败，返回最好的proposal")
            best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
            return rollouts[best_idx].get('scaffold')

    except Exception as e:
        print(f"  ⚠️ 融合失败: {e}，返回最好的proposal")
        best_idx = max(range(len(rollouts)), key=lambda i: rollouts[i].get('r_total', 0))
        return rollouts[best_idx].get('scaffold')


def parse_fused_scaffold(response):
    """
    从LLM响应中解析融合后的scaffold
    """
    try:
        # 找JSON部分
        start = response.find('{')
        end = response.rfind('}') + 1

        if start >= 0 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)

            # 提取problem_analysis字段
            if 'problem_analysis' in data:
                return data['problem_analysis']
            else:
                return data

        return None
    except Exception as e:
        print(f"  ⚠️ JSON解析错误: {e}")
        return None


def compute_rewards(fused_scaffold, rollouts, problem, computer, evaluator):
    """
    计算融合后的奖励
    """
    print(f"  计算奖励...")

    # 计算答案
    try:
        result = computer.compute_from_scaffold(
            causal_scaffold=fused_scaffold,
            problem_text=problem['text']
        )

        if result['success']:
            answer = result['result']
        else:
            answer = None
    except:
        answer = None

    # 计算各项奖励
    if answer is not None:
        r_ans = evaluator.evaluate_answer(answer, problem['answer'], problem['text'])
        is_correct = (r_ans >= 0.99)
    else:
        is_correct = False
        r_ans = 0.0

    # 逻辑质量
    r_logic = evaluator.evaluate_logic(str(fused_scaffold), problem['text'])

    # 图质量
    r_graph = evaluator.evaluate_graph(fused_scaffold)

    # 融合质量
    proposals = [r.get('scaffold') for r in rollouts if r.get('scaffold')]
    r_fusion = evaluator.evaluate_fusion(
        proposals=proposals,
        fused_result=fused_scaffold,
        ground_truth=problem['answer']
    )

    # 总奖励（Critic权重不同，更重视融合质量）
    r_total = 0.3 * r_ans + 0.2 * r_logic + 0.2 * r_graph + 0.3 * r_fusion

    print(f"  ✓ 答案: {'正确' if is_correct else '错误'} (奖励: {r_total:.3f})")

    return {
        'answer': answer,
        'is_correct': is_correct,
        'r_ans': r_ans,
        'r_logic': r_logic,
        'r_graph': r_graph,
        'r_fusion': r_fusion,
        'r_total': r_total
    }


def save_result(problem, generator_id, fused_scaffold, rewards, output_file):
    """
    保存融合结果到文件
    """
    record = {
        'problem_id': problem['id'],
        'problem_text': problem['text'],
        'ground_truth': problem['answer'],
        'generator_id': generator_id,
        'fused_scaffold': str(fused_scaffold),
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

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Critic 训练脚本')
    parser.add_argument('--temperature', type=float, default=0.0, help='Critic温度设置')

    args = parser.parse_args()

    print("=" * 60)
    print("🧠 Critic 开始训练")
    print("=" * 60)

    # 1. 初始化组件
    print("1. 初始化组件...")
    project_root = Path(__file__).parent.parent

    # 加载API密钥
    api_manager = APIKeyManager(str(project_root / "data" / "api_keys" / "api_config.json"))
    api_key = api_manager.get_api_key(CRITIC_ID)

    # 设置环境变量
    import os
    os.environ["SILICONFLOW_API_KEY"] = api_key

    # 初始化组件
    llm_client = LLMClient(provider="siliconflow")
    critic_scaffolder = MultiAgentScaffolder(
        llm_client=llm_client,
        num_generators=1,
        critic_temperature=args.temperature
    )
    computer = LLMComputer(verbose=False)
    evaluator = RewardEvaluator(llm_client=llm_client, verbose=False)
    extractor = ExperienceExtractor(llm_client=llm_client, tau=0.05, verbose=False)

    # 初始化正确率统计
    stats = TrainingStats(CRITIC_ID)

    print("✓ 组件初始化完成")

    # 2. 加载所有Generator的rollouts
    print("\n2. 加载Generator的rollouts...")
    gen1_rollouts = load_generator_rollouts('generator_1')
    gen2_rollouts = load_generator_rollouts('generator_2')
    gen3_rollouts = load_generator_rollouts('generator_3')

    print(f"✓ Generator 1: {len(gen1_rollouts)} 个问题")
    print(f"✓ Generator 2: {len(gen2_rollouts)} 个问题")
    print(f"✓ Generator 3: {len(gen3_rollouts)} 个问题")

    # 找到所有Generator都有的共同问题
    problem_ids = set(gen1_rollouts.keys()) & set(gen2_rollouts.keys()) & set(gen3_rollouts.keys())
    problem_ids = sorted(problem_ids)
    print(f"✓ 共同问题: {len(problem_ids)} 个")

    # 3. 开始融合
    print("\n3. 开始融合...")
    output_file = str(project_root / "grpo_training" / "cache" / "critic_results.json")

    # 统计数据
    total_problems = len(problem_ids)
    total_correct_fusions = 0
    total_fusion_attempts = 0
    total_reward = 0.0

    for idx, problem_id in enumerate(tqdm(problem_ids, desc="融合进度"), 1):
        print(f"\n--- 问题 {idx}/{len(problem_ids)}: {problem_id} ---")

        # 获取问题信息
        problem = {
            'id': problem_id,
            'text': gen1_rollouts[problem_id]['problem_text'],
            'answer': gen1_rollouts[problem_id]['ground_truth']
        }

        # 显示当前经验库
        current_experiences = extractor._load_experiences(CRITIC_ID)
        print(f"当前经验库: {len(current_experiences)} 条")

        # 分别融合每个Generator的rollouts
        fusion_results = []
        problem_correct = 0
        problem_attempts = 0

        for gen_id, gen_rollouts_dict in [
            ('generator_1', gen1_rollouts),
            ('generator_2', gen2_rollouts),
            ('generator_3', gen3_rollouts)
        ]:
            print(f"  融合 {gen_id}...")
            rollouts = gen_rollouts_dict[problem_id]['rollouts']

            # 融合rollouts
            fused_scaffold = fuse_rollouts(rollouts, llm_client, problem['text'])

            if fused_scaffold:
                # 计算奖励
                rewards = compute_rewards(fused_scaffold, rollouts, problem, computer, evaluator)

                # 保存结果
                save_result(problem, gen_id, fused_scaffold, rewards, output_file)

                # 记录用于经验提取
                fusion_results.append({
                    **rewards,
                    'fused_dag': fused_scaffold
                })

                problem_attempts += 1
                total_fusion_attempts += 1
                total_reward += rewards['r_total']

                if rewards['is_correct']:
                    problem_correct += 1
                    total_correct_fusions += 1
            else:
                print(f"  ❌ {gen_id} 融合失败")

        problem_accuracy = problem_correct / problem_attempts if problem_attempts > 0 else 0.0
        print(f"本问题融合成功率: {problem_correct}/{problem_attempts} = {problem_accuracy*100:.1f}%")

        # 提取Critic经验
        experience_result = extractor.extract_critic_experience(
            problem=problem,
            fusion_results=fusion_results,
            ground_truth=problem['answer']
        )

        # 显示更新后的经验库
        updated_experiences = extractor._load_experiences(CRITIC_ID)
        print(f"更新后经验库: {len(updated_experiences)} 条")

    # 计算正确率
    fusion_accuracy = total_correct_fusions / total_fusion_attempts if total_fusion_attempts > 0 else 0.0
    avg_reward = total_reward / total_fusion_attempts if total_fusion_attempts > 0 else 0.0

    # 记录统计
    additional_metrics = {
        "fusion_accuracy": fusion_accuracy,
        "total_fusion_attempts": total_fusion_attempts,
        "total_experiences": len(extractor._load_experiences(CRITIC_ID)),
        "extraction_triggered": experience_result is not None
    }

    stats.record_epoch(
        epoch_num=len(stats.stats_data["epochs"]) + 1,
        total_problems=total_problems,
        correct_answers=total_correct_fusions,
        total_reward=total_reward,
        avg_reward=avg_reward,
        additional_metrics=additional_metrics
    )

    print("\n" + "=" * 60)
    print("✅ Critic 训练完成!")
    print(f"📁 结果保存至: {output_file}")
    print(f"🧠 经验保存至: data/grpo_experiences/{CRITIC_ID}_experiences.json")
    print(f"📊 统计保存至: training_stats/{CRITIC_ID}_stats.json")

    # 打印正确率统计
    print(f"\n📊 本次训练统计:")
    print(f"总问题数: {total_problems}")
    print(f"总融合尝试: {total_fusion_attempts}")
    print(f"融合正确率: {total_correct_fusions}/{total_fusion_attempts} = {fusion_accuracy:.3f} ({fusion_accuracy*100:.1f}%)")
    print(f"平均奖励: {avg_reward:.3f}")

    # 生成统计图表和报告
    try:
        chart_path = f"training_stats/{CRITIC_ID}_progress.png"
        stats.plot_progress(save_path=chart_path)
        report_path = stats.export_detailed_report()
    except Exception as e:
        print(f"生成统计图表失败: {e}")

    print("=" * 60)


if __name__ == "__main__":
    main()