"""
三维奖励评估器 - 简化版
计算GRPO训练的三个维度奖励：
1. r_ans: 答案正确性
2. r_logic: 推理逻辑质量
3. r_graph: 因果图质量
4. r_fusion: 融合质量（仅Critic使用）
"""

import re
import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional


class RewardEvaluator:
    """三维奖励评估器"""

    def __init__(
        self,
        llm_client=None,
        alpha: float = 0.6,   # 答案正确性权重
        beta: float = 0.25,   # 逻辑质量权重
        gamma: float = 0.15,  # 图质量权重
        verbose: bool = False
    ):
        """
        初始化奖励评估器

        Args:
            llm_client: LLM客户端
            alpha: r_ans权重
            beta: r_logic权重
            gamma: r_graph权重
            verbose: 是否打印详细信息
        """
        self.llm_client = llm_client
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.verbose = verbose
        self._load_prompts()

    def _print(self, message: str):
        """条件打印"""
        if self.verbose:
            print(message)

    def _load_prompts(self):
        """加载评分prompts"""
        logic_prompt_path = Path("prompts/logic_scoring_prompt.txt")
        if logic_prompt_path.exists():
            with open(logic_prompt_path, 'r', encoding='utf-8') as f:
                self.logic_prompt = f.read()
        else:
            self.logic_prompt = self._get_default_logic_prompt()

    def _get_default_logic_prompt(self) -> str:
        """默认逻辑评分prompt"""
        return """You are a rigorous mathematical reasoning evaluator. Evaluate the following reasoning trajectory.

**Problem:**
{problem}

**Reasoning Trajectory:**
{trajectory}

**Output JSON format:**
{{"score": 0.85, "breakdown": {{"coherence": 0.9, "completeness": 0.8, "verification": 0.7, "no_errors": 0.9, "tool_consistency": 1.0}}, "errors": []}}
"""

    # ==================== 1. 答案评估 ====================

    def evaluate_answer(
        self,
        predicted: str,
        expected: str,
        problem_text: str = ""
    ) -> float:
        """
        评估答案正确性

        Args:
            predicted: 预测答案
            expected: 期望答案
            problem_text: 问题文本

        Returns:
            float: 0.0-1.0之间的分数
        """
        if not predicted or predicted.lower() in ['none', 'null', '']:
            return 0.0

        # 精确匹配
        if str(predicted).strip() == str(expected).strip():
            self._print(f"答案精确匹配: {predicted}")
            return 1.0

        # LLM比较
        if self.llm_client:
            try:
                llm_score = self._llm_answer_comparison(predicted, expected, problem_text)
                self._print(f"LLM答案比较分数: {llm_score}")
                return llm_score
            except Exception as e:
                self._print(f"LLM答案比较失败: {e}")
                return 0.0

        self._print("无LLM客户端，返回默认分数")
        return 0.0

    def _llm_answer_comparison(
        self,
        predicted: str,
        expected: str,
        problem_text: str
    ) -> float:
        """LLM-based answer comparison"""
        prompt = f"""Compare two answers for equivalence in the context of the given problem.

**Problem:**
{problem_text}

**Expected Answer:**
{expected}

**Predicted Answer:**
{predicted}

**Question:** Are these two answers equivalent? Consider mathematical equivalence, unit conversions, and different representations.

**Output:** Reply with ONLY "YES" or "NO"
"""
        response = self.llm_client.complete(prompt, temperature=0.0)
        response_text = response.strip().upper()

        return 1.0 if 'YES' in response_text else 0.0

    # ==================== 2. 逻辑评估 ====================

    def evaluate_logic(self, trajectory: str, problem_text: str = "") -> float:
        """
        评估推理逻辑质量

        Args:
            trajectory: 推理轨迹文本
            problem_text: 问题文本

        Returns:
            float: 0.0-1.0之间的分数
        """
        if not trajectory or trajectory.strip() == "":
            return 0.5

        if self.llm_client:
            try:
                score = self._llm_logic_scoring(trajectory, problem_text)
                if score is not None:
                    self._print(f"LLM逻辑评分: {score}")
                    return score
            except Exception as e:
                self._print(f"LLM逻辑评分失败: {e}")

        return 0.5

    def _llm_logic_scoring(self, trajectory: str, problem_text: str) -> Optional[float]:
        """LLM逻辑评分"""
        prompt = self.logic_prompt.format(
            problem=problem_text,
            trajectory=trajectory
        )

        response = self.llm_client.complete(prompt, temperature=0.0)

        try:
            # 提取JSON中的score
            json_match = re.search(r'\{[^{}]*"score"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                score = float(data.get('score', 0.5))
                return max(0.0, min(1.0, score))
        except Exception as e:
            self._print(f"解析逻辑评分JSON失败: {e}")

        return None

    # ==================== 3. 图评估 ====================

    def evaluate_graph(self, scaffold: Dict[str, Any]) -> float:
        """
        评估因果图质量

        Args:
            scaffold: 包含causal_graph的scaffold数据

        Returns:
            float: 0.0-1.0之间的分数
        """
        if not scaffold:
            return 0.0

        causal_graph = scaffold.get('causal_graph', [])
        knowns = scaffold.get('knowns', {})
        target_variable = scaffold.get('target_variable', '')

        if not causal_graph:
            return 0.0

        # 4个子指标
        acyclicity_score = self._evaluate_acyclicity(causal_graph)
        node_coverage_score = self._evaluate_node_coverage(causal_graph, knowns, target_variable)
        edge_plausibility_score = self._evaluate_edge_plausibility(causal_graph, knowns)
        structural_quality_score = self._evaluate_structural_quality(causal_graph)

        # 加权平均
        total_score = (
            0.3 * acyclicity_score +
            0.2 * node_coverage_score +
            0.4 * edge_plausibility_score +
            0.1 * structural_quality_score
        )

        self._print(f"图质量评分: {total_score:.3f}")
        return total_score

    def _evaluate_acyclicity(self, causal_graph: List[Dict]) -> float:
        """评估是否有环"""
        try:
            G = nx.DiGraph()
            for edge in causal_graph:
                G.add_edge(edge['cause'], edge['effect'])

            # 检查是否为DAG
            return 1.0 if nx.is_directed_acyclic_graph(G) else 0.0
        except:
            return 0.0

    def _evaluate_node_coverage(self, causal_graph: List[Dict], knowns: Dict, target_variable: str) -> float:
        """评估节点覆盖率"""
        try:
            # 收集所有节点
            graph_nodes = set()
            for edge in causal_graph:
                graph_nodes.add(edge['cause'])
                graph_nodes.add(edge['effect'])

            # 必须包含的节点
            required_nodes = set(knowns.keys())
            if target_variable:
                required_nodes.add(target_variable)

            if not required_nodes:
                return 1.0

            coverage = len(graph_nodes & required_nodes) / len(required_nodes)
            return min(1.0, coverage)
        except:
            return 0.0

    def _evaluate_edge_plausibility(self, causal_graph: List[Dict], knowns: Dict) -> float:
        """评估边合理性"""
        if not causal_graph:
            return 0.0

        plausible_edges = 0
        total_edges = len(causal_graph)

        for edge in causal_graph:
            # 简单的合理性检查
            if 'rule' in edge and edge['rule']:
                plausible_edges += 1

        return plausible_edges / total_edges if total_edges > 0 else 0.0

    def _evaluate_structural_quality(self, causal_graph: List[Dict]) -> float:
        """评估结构质量"""
        if not causal_graph:
            return 0.0

        # 简单的结构质量评估
        try:
            G = nx.DiGraph()
            for edge in causal_graph:
                G.add_edge(edge['cause'], edge['effect'])

            # 检查连通性和结构合理性
            if len(G.nodes()) == 0:
                return 0.0

            # 基本的结构完整性
            return 1.0 if nx.is_weakly_connected(G) else 0.5
        except:
            return 0.0

    # ==================== 4. 融合评估 ====================

    def evaluate_fusion(
        self,
        proposals: List[Any],
        fused_result: Any,
        ground_truth: str
    ) -> float:
        """
        评估融合质量（仅Critic使用）

        Args:
            proposals: 原始提案列表
            fused_result: 融合结果
            ground_truth: 真实答案

        Returns:
            float: 0.0-1.0之间的分数
        """
        if not proposals or not fused_result:
            return 0.0

        try:
            # 简化的融合质量评估
            # 这里可以实现更复杂的融合质量评估逻辑
            return 0.8  # 暂时返回默认分数
        except:
            return 0.0