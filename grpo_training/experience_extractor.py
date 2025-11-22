"""
经验提取器 - 简化版
用于GRPO训练的通用经验提炼器
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from engine.scaffolder import LLMClient


class ExperienceExtractor:
    """经验提取器"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        tau: float = 0.05,
        verbose: bool = False
    ):
        """
        初始化经验提取器

        Args:
            llm_client: LLM客户端
            tau: GRPO阈值（σ > τ时触发提取）
            verbose: 是否打印详细信息
        """
        self.llm_client = llm_client or LLMClient()
        self.tau = tau
        self.verbose = verbose

        # 加载prompts
        project_root = Path(__file__).parent.parent
        self.generator_prompt = self._load_prompt(str(project_root / "prompts" / "generator_experience_extraction.txt"))
        self.critic_prompt = self._load_prompt(str(project_root / "prompts" / "critic_experience_extraction.txt"))

    def _print(self, message: str, **kwargs):
        """条件打印"""
        if self.verbose:
            print(message, **kwargs)

    def _load_prompt(self, path: str) -> str:
        """加载prompt模板"""
        prompt_path = Path(path)
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """默认prompt"""
        return "提取经验教训：{rollouts} 问题：{problem}"

    def extract_generator_experience(
        self,
        generator_id: str,
        problem: Dict[str, Any],
        rollouts: List[Dict[str, Any]],
        ground_truth: str
    ) -> Optional[Dict[str, Any]]:
        """
        提取Generator经验

        Args:
            generator_id: Generator标识
            problem: 问题数据
            rollouts: rollout列表
            ground_truth: 真实答案

        Returns:
            提取的经验，或None
        """
        try:
            import numpy as np

            # 计算奖励统计
            rewards = [r.get('r_total', 0) for r in rollouts]
            μ = float(np.mean(rewards))
            σ = float(np.std(rewards))

            self._print(f"  {generator_id}: μ={μ:.3f}, σ={σ:.3f} ", end="")

            # 检查GRPO阈值
            if σ <= self.tau:
                self._print("→ 跳过 (σ≤τ)")
                return None

            self._print("→ 提取经验 (σ>τ)")

            # 加载当前经验
            current_experiences = self._load_experiences(generator_id)

            # 构造prompt
            prompt = self._format_generator_prompt(
                problem=problem,
                rollouts=rollouts,
                ground_truth=ground_truth,
                current_experiences=current_experiences
            )

            # 调用LLM提取经验
            response = self.llm_client.complete(prompt, temperature=0.0)

            # 解析响应
            experience = self._parse_experience(response)

            if experience:
                # 保存经验
                self._save_experience(generator_id, experience)

                return experience

        except Exception as e:
            self._print(f"经验提取失败: {e}")

        return None

    def extract_critic_experience(
        self,
        problem: Dict[str, Any],
        fusion_results: List[Dict[str, Any]],
        ground_truth: str
    ) -> Optional[Dict[str, Any]]:
        """
        提取Critic经验

        Args:
            problem: 问题数据
            fusion_results: 融合结果列表
            ground_truth: 真实答案

        Returns:
            提取的经验，或None
        """
        try:
            import numpy as np

            # 计算奖励统计
            rewards = [r.get('r_total', 0) for r in fusion_results]
            μ = float(np.mean(rewards))
            σ = float(np.std(rewards))

            self._print(f"  Critic: μ={μ:.3f}, σ={σ:.3f} ", end="")

            # 检查GRPO阈值
            if σ <= self.tau:
                self._print("→ 跳过 (σ≤τ)")
                return None

            self._print("→ 提取经验 (σ>τ)")

            # 加载当前经验
            current_experiences = self._load_experiences("critic")

            # 构造prompt
            prompt = self._format_critic_prompt(
                problem=problem,
                fusion_results=fusion_results,
                ground_truth=ground_truth,
                current_experiences=current_experiences
            )

            # 调用LLM提取经验
            response = self.llm_client.complete(prompt, temperature=0.0)

            # 解析响应
            experience = self._parse_experience(response)

            if experience:
                # 保存经验
                self._save_experience("critic", experience)

                return experience

        except Exception as e:
            self._print(f"Critic经验提取失败: {e}")

        return None

    def _format_generator_prompt(
        self,
        problem: Dict[str, Any],
        rollouts: List[Dict[str, Any]],
        ground_truth: str,
        current_experiences: List[Dict[str, Any]]
    ) -> str:
        """格式化Generator经验提取prompt"""

        # 格式化rollouts
        def format_scaffold(scaffold):
            if scaffold is None:
                return "生成失败"
            try:
                return json.dumps(scaffold, indent=2, ensure_ascii=False)
            except:
                return str(scaffold)

        rollouts_str = "\n".join([
            f"Rollout {r.get('rollout_id', '?')}: "
            f"奖励={r.get('r_total', 0):.3f}, "
            f"正确={'✓' if r.get('is_correct') else '✗'}\n"
            f"{format_scaffold(r.get('scaffold'))}"
            for r in rollouts
        ])

        # 格式化当前经验
        current_exp_str = "\n".join([
            f"{exp.get('id', '?')}: {exp.get('content', '')}"
            for exp in current_experiences
        ]) if current_experiences else "暂无经验"

        return self.generator_prompt.format(
            problem_text=problem.get('text', ''),
            ground_truth=ground_truth,
            rollouts=rollouts_str,
            prior_experiences=current_exp_str
        )

    def _format_critic_prompt(
        self,
        problem: Dict[str, Any],
        fusion_results: List[Dict[str, Any]],
        ground_truth: str,
        current_experiences: List[Dict[str, Any]]
    ) -> str:
        """格式化Critic经验提取prompt"""

        # 格式化融合结果
        def format_dag(dag):
            if dag is None:
                return "融合失败"
            try:
                return json.dumps(dag, indent=2, ensure_ascii=False)
            except:
                return str(dag)

        fusion_str = "\n".join([
            f"融合结果: "
            f"奖励={r.get('r_total', 0):.3f}, "
            f"正确={'✓' if r.get('is_correct') else '✗'}\n"
            f"{format_dag(r.get('fused_dag'))}"
            for r in fusion_results
        ])

        # 格式化当前经验
        current_exp_str = "\n".join([
            f"{exp.get('id', '?')}: {exp.get('content', '')}"
            for exp in current_experiences
        ]) if current_experiences else "暂无经验"

        return self.critic_prompt.format(
            problem_text=problem.get('text', ''),
            ground_truth=ground_truth,
            fusion_results=fusion_str,
            prior_experiences=current_exp_str
        )

    def _parse_experience(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM响应中的经验"""
        try:
            # 查找JSON格式
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                experience = json.loads(json_match.group(0))

                # 添加时间戳和ID
                experience['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                if 'id' not in experience:
                    experience['id'] = f"exp_{int(time.time())}"

                return experience
        except:
            pass

        return None

    def _load_experiences(self, role: str) -> List[Dict[str, Any]]:
        """加载指定角色的经验"""
        project_root = Path(__file__).parent.parent
        exp_file = project_root / "data" / "grpo_experiences" / f"{role}_experiences.json"

        if exp_file.exists():
            try:
                with open(exp_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []

        return []

    def _save_experience(self, role: str, experience: Dict[str, Any]) -> None:
        """保存经验到文件"""
        project_root = Path(__file__).parent.parent
        exp_file = project_root / "data" / "grpo_experiences" / f"{role}_experiences.json"

        # 确保目录存在
        exp_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载现有经验
        experiences = self._load_experiences(role)

        # 添加新经验
        experiences.append(experience)

        # 保存到文件
        with open(exp_file, 'w', encoding='utf-8') as f:
            json.dump(experiences, f, indent=2, ensure_ascii=False)