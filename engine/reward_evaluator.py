"""
Three-Dimensional Reward Evaluator
三维奖励评估器

Computes rewards for GRPO training based on:
基于以下三个维度计算GRPO训练的奖励：
1. r_ans: Answer correctness / 答案正确性
2. r_logic: Reasoning quality / 推理逻辑质量
3. r_graph: Causal graph quality / 因果图质量

Total reward: r_total = α·r_ans + β·r_logic + γ·r_graph
总奖励: r_total = α·r_ans + β·r_logic + γ·r_graph
"""

import re
import json
import statistics
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


class RewardEvaluator:
    """
    Three-dimensional reward evaluator for GRPO
    用于GRPO的三维奖励评估器
    """
    
    def __init__(
        self,
        llm_client=None,
        alpha: float = 0.6,   # Weight for answer correctness
        beta: float = 0.25,   # Weight for logic quality
        gamma: float = 0.15,  # Weight for graph quality
        tau: float = 0.05,    # Threshold for experience extraction
        verbose: bool = False
    ):
        """
        Initialize reward evaluator
        
        Args:
            llm_client: LLM client for answer comparison and logic scoring
            alpha: Weight for r_ans (default 0.6)
            beta: Weight for r_logic (default 0.25)
            gamma: Weight for r_graph (default 0.15)
            tau: Threshold for triggering experience extraction (default 0.05)
            verbose: Whether to print detailed evaluation info
        """
        self.llm_client = llm_client
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.tau = tau
        self.verbose = verbose
        
        # Load prompts
        self._load_prompts()
    
    def _print(self, message: str):
        """条件打印"""
        if self.verbose:
            print(message)
    
    def _load_prompts(self):
        """加载评分prompts"""
        # Logic scoring prompt
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
    
    # ==================== 1. 答案评估 r_ans ====================
    
    def evaluate_answer(
        self,
        predicted: str,
        expected: str,
        problem_text: str = ""
    ) -> float:
        """
        评估答案正确性
        
        策略：
        1. 精确匹配
        2. LLM判分（带问题上下文）
        3. LLM失败时返回默认分数0.0
        
        Args:
            predicted: 预测答案
            expected: 期望答案
            problem_text: 问题文本（提供上下文）
        
        Returns:
            float: 0.0-1.0之间的分数
        """
        if not predicted or predicted.lower() in ['none', 'null', '']:
            return 0.0
        
        # 精确匹配
        if str(predicted).strip() == str(expected).strip():
            self._print(f"✓ Answer exact match: {predicted}")
            return 1.0
        
        # 尝试LLM判分
        if self.llm_client:
            try:
                llm_score = self._llm_answer_comparison(
                    predicted, expected, problem_text
                )
                self._print(f"✓ LLM answer comparison: {llm_score}")
                return llm_score
            except Exception as e:
                self._print(f"⚠️ LLM answer comparison failed: {e}")
                return 0.0  # LLM失败时返回默认分数
        
        # 没有LLM客户端时返回默认分数
        self._print(f"⚠️ No LLM client available for answer comparison")
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
    
    # ==================== 2. 逻辑评估 r_logic ====================
    
    def evaluate_logic(self, trajectory: str, problem_text: str = "") -> float:
        """
        评估推理逻辑质量
        
        策略：
        1. LLM评分（单次调用）
        2. LLM失败时返回默认分数0.5
        
        Args:
            trajectory: 推理轨迹文本
            problem_text: 问题文本
        
        Returns:
            float: 0.0-1.0之间的分数
        """
        if not trajectory or trajectory.strip() == "":
            return 0.5  # 默认分数
        
        # 尝试LLM评分（单次调用）
        if self.llm_client:
            try:
                score = self._llm_logic_scoring(trajectory, problem_text)
                if score is not None:
                    self._print(f"✓ LLM logic score: {score}")
                    return score
            except Exception as e:
                self._print(f"⚠️ LLM logic scoring failed: {e}")
        
        # LLM失败或不可用时返回默认分数
        self._print(f"⚠️ LLM logic scoring unavailable, returning default score")
        return 0.5
    
    def _llm_logic_scoring(self, trajectory: str, problem_text: str) -> Optional[float]:
        """LLM逻辑评分"""
        prompt = self.logic_prompt.format(
            problem=problem_text,
            trajectory=trajectory
        )
        
        response = self.llm_client.complete(prompt, temperature=0.0)
        
        # 解析JSON
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[^{}]*"score"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                score = float(data.get('score', 0.5))
                return max(0.0, min(1.0, score))
        except Exception as e:
            self._print(f"  Failed to parse logic scoring JSON: {e}")
        
        return None
    
    # ==================== 3. 图评估 r_graph ====================
    
    def evaluate_graph(self, scaffold: Dict[str, Any]) -> float:
        """
        评估因果图质量
        
        4个子指标（加权）：
        - acyclicity (30%): 是否DAG
        - node_coverage (20%): 节点覆盖率
        - edge_plausibility (40%): 边合理性
        - structural_quality (10%): 结构质量
        
        Args:
            scaffold: 包含causal_graph的scaffold数据
        
        Returns:
            float: 0.0-1.0之间的分数
        """
        if not scaffold:
            self._print("⚠️ No scaffold provided")
            return 0.5  # 默认分数
        
        # Handle different causal_graph formats
        # 处理不同的 causal_graph 格式
        if 'causal_graph' not in scaffold:
            self._print("⚠️ No causal_graph in scaffold")
            return 0.5
        
        causal_graph = scaffold['causal_graph']
        
        # Case 1: causal_graph is a list (standard format from scaffolder)
        # 情况1：causal_graph 是列表（scaffolder的标准格式）
        if isinstance(causal_graph, list):
            causal_links = causal_graph
        # Case 2: causal_graph is a dict with 'causal_links' field
        # 情况2：causal_graph 是包含 'causal_links' 字段的字典
        elif isinstance(causal_graph, dict) and 'causal_links' in causal_graph:
            causal_links = causal_graph.get('causal_links', [])
        else:
            self._print(f"⚠️ Unknown causal_graph format: {type(causal_graph)}")
            return 0.5
        
        if not causal_links:
            self._print("⚠️ Empty causal graph")
            return 0.3  # 空图给低分
        
        # 计算4个子指标
        acyclicity = self._check_acyclicity(causal_links)
        coverage = self._check_node_coverage(causal_links, scaffold)
        edge_quality = self._check_edge_quality(causal_links)
        structure = self._check_structure(causal_links)
        
        # 加权计算
        r_graph = (
            0.3 * acyclicity +
            0.2 * coverage +
            0.4 * edge_quality +
            0.1 * structure
        )
        
        self._print(f"  Graph metrics: acyclicity={acyclicity:.2f}, coverage={coverage:.2f}, "
                   f"edge_quality={edge_quality:.2f}, structure={structure:.2f}")
        self._print(f"✓ Graph score: {r_graph:.3f}")
        
        return r_graph
    
    def _check_acyclicity(self, causal_links: List[Dict]) -> float:
        """检查是否为DAG（无环）"""
        try:
            G = nx.DiGraph()
            for link in causal_links:
                # Standard format: cause (list) -> effect (string)
                # 标准格式：cause (列表) -> effect (字符串)
                causes = link.get('cause', [])
                effect = link.get('effect')
                
                # Fallback: try 'from'/'to' or 'source'/'target' format
                # 备用：尝试 'from'/'to' 或 'source'/'target' 格式
                if not causes and not effect:
                    from_node = link.get('from') or link.get('source')
                    to_node = link.get('to') or link.get('target')
                    if from_node and to_node:
                        G.add_edge(from_node, to_node)
                else:
                    # Add edges from each cause to effect
                    # 从每个原因到结果添加边
                    if effect:
                        if isinstance(causes, list):
                            for cause in causes:
                                if cause:
                                    G.add_edge(cause, effect)
                        elif causes:  # Single cause as string
                            G.add_edge(causes, effect)
            
            return 1.0 if nx.is_directed_acyclic_graph(G) else 0.0
        except Exception as e:
            self._print(f"  Acyclicity check error: {e}")
            return 0.5
    
    def _check_node_coverage(self, causal_links: List[Dict], scaffold: Dict) -> float:
        """检查节点覆盖率"""
        try:
            # 期望节点：knowns中的变量 + target_variable
            expected_nodes = set()
            if 'knowns' in scaffold:
                expected_nodes.update(scaffold['knowns'].keys())
            if 'target_variable' in scaffold:
                expected_nodes.add(scaffold['target_variable'])
            
            if not expected_nodes:
                return 1.0  # 如果没有期望节点，给满分
            
            # 实际节点：所有边的源和目标
            actual_nodes = set()
            for link in causal_links:
                # Standard format: cause -> effect
                causes = link.get('cause', [])
                effect = link.get('effect')
                
                # Add causes to actual nodes
                if isinstance(causes, list):
                    actual_nodes.update(causes)
                elif causes:
                    actual_nodes.add(causes)
                
                # Add effect to actual nodes
                if effect:
                    actual_nodes.add(effect)
                
                # Fallback: try alternative field names
                from_node = link.get('from') or link.get('source')
                to_node = link.get('to') or link.get('target')
                if from_node:
                    actual_nodes.add(from_node)
                if to_node:
                    actual_nodes.add(to_node)
            
            # 覆盖率
            covered = len(actual_nodes & expected_nodes)
            total = len(expected_nodes)
            return covered / total if total > 0 else 1.0
        except Exception as e:
            self._print(f"  Coverage check error: {e}")
            return 0.5
    
    def _check_edge_quality(self, causal_links: List[Dict]) -> float:
        """检查边的合理性（是否有rule/reasoning字段）"""
        try:
            if not causal_links:
                return 0.0
            
            edges_with_reason = 0
            for link in causal_links:
                # Check for rule (standard), reasoning, relation, or description
                # 检查 rule（标准）、reasoning、relation 或 description
                rule_or_reason = (
                    link.get('rule') or 
                    link.get('reasoning') or 
                    link.get('relation') or 
                    link.get('description')
                )
                if rule_or_reason and str(rule_or_reason).strip():
                    edges_with_reason += 1
            
            return edges_with_reason / len(causal_links)
        except Exception as e:
            self._print(f"  Edge quality check error: {e}")
            return 0.5
    
    def _check_structure(self, causal_links: List[Dict]) -> float:
        """检查结构质量（弱连通性）"""
        try:
            G = nx.DiGraph()
            for link in causal_links:
                # Standard format: cause -> effect
                causes = link.get('cause', [])
                effect = link.get('effect')
                
                if effect:
                    if isinstance(causes, list):
                        for cause in causes:
                            if cause:
                                G.add_edge(cause, effect)
                    elif causes:
                        G.add_edge(causes, effect)
                
                # Fallback: alternative formats
                from_node = link.get('from') or link.get('source')
                to_node = link.get('to') or link.get('target')
                if from_node and to_node:
                    G.add_edge(from_node, to_node)
            
            if G.number_of_nodes() == 0:
                return 0.0
            
            # 检查弱连通性
            if nx.is_weakly_connected(G):
                return 1.0
            else:
                # 最大连通分量占比
                largest_cc = max(nx.weakly_connected_components(G), key=len)
                return len(largest_cc) / G.number_of_nodes()
        except Exception as e:
            self._print(f"  Structure check error: {e}")
            return 0.5
    
    # ==================== 4. 总奖励计算 ====================
    
    def compute_total_reward(
        self,
        r_ans: float,
        r_logic: float,
        r_graph: float
    ) -> float:
        """
        计算总奖励
        
        r_total = α·r_ans + β·r_logic + γ·r_graph
        
        Args:
            r_ans: 答案分数
            r_logic: 逻辑分数
            r_graph: 图分数
        
        Returns:
            float: 总奖励分数
        """
        r_total = (
            self.alpha * r_ans +
            self.beta * r_logic +
            self.gamma * r_graph
        )
        return max(0.0, min(1.0, r_total))
    
    # ==================== 5. 组内统计 ====================
    
    def evaluate_group(
        self,
        rollouts: List[Dict[str, float]]
    ) -> Tuple[List[float], Dict[str, float]]:
        """
        评估一组rollouts的统计信息
        
        Args:
            rollouts: List of dicts containing r_ans, r_logic, r_graph
        
        Returns:
            Tuple of (total_rewards, group_stats)
            - total_rewards: List of r_total for each rollout
            - group_stats: Dict with mean, std, min, max
        """
        total_rewards = []
        for rollout in rollouts:
            r_total = self.compute_total_reward(
                rollout.get('r_ans', 0.0),
                rollout.get('r_logic', 0.0),
                rollout.get('r_graph', 0.0)
            )
            total_rewards.append(r_total)
        
        # 计算统计信息
        if len(total_rewards) > 0:
            mean_reward = statistics.mean(total_rewards)
            std_reward = statistics.stdev(total_rewards) if len(total_rewards) > 1 else 0.0
            min_reward = min(total_rewards)
            max_reward = max(total_rewards)
        else:
            mean_reward = std_reward = min_reward = max_reward = 0.0
        
        group_stats = {
            'mean': mean_reward,
            'std': std_reward,
            'min': min_reward,
            'max': max_reward,
            'should_extract': std_reward > self.tau  # 是否触发经验提取
        }
        
        return total_rewards, group_stats
    
    # ==================== 6. Critic融合质量评估 r_fusion ====================
    
    def evaluate_fusion(
        self,
        proposals: List[Dict[str, Any]],
        fused_result: Dict[str, Any],
        ground_truth: str = None
    ) -> float:
        """
        评估Critic的融合质量
        
        4个子指标（加权）：
        - consistency (30%): 一致性 - 融合结果是否整合多个rollout优点
        - conflict_resolution (30%): 冲突解决 - 是否正确处理rollout间矛盾
        - information_preservation (20%): 信息保留 - 关键信息是否丢失
        - improvement (20%): 优化度 - 是否优于单个rollout
        
        Args:
            proposals: 输入的多个rollout proposals（来自同一个generator）
            fused_result: Critic融合后的结果
            ground_truth: 正确答案（可选，用于评估improvement）
        
        Returns:
            float: 0.0-1.0之间的融合质量分数
        """
        if not proposals or not fused_result:
            self._print("⚠️ No proposals or fused result provided")
            return 0.5
        
        if len(proposals) < 2:
            self._print("⚠️ Need at least 2 proposals to evaluate fusion")
            return 0.5
        
        # 计算4个子指标
        consistency = self._check_fusion_consistency(proposals, fused_result)
        conflict_resolution = self._check_conflict_resolution(proposals, fused_result)
        information_preservation = self._check_information_preservation(proposals, fused_result)
        improvement = self._check_fusion_improvement(proposals, fused_result, ground_truth)
        
        # 加权计算
        r_fusion = (
            0.3 * consistency +
            0.3 * conflict_resolution +
            0.2 * information_preservation +
            0.2 * improvement
        )
        
        self._print(f"  Fusion metrics: consistency={consistency:.2f}, "
                   f"conflict_resolution={conflict_resolution:.2f}, "
                   f"information_preservation={information_preservation:.2f}, "
                   f"improvement={improvement:.2f}")
        self._print(f"✓ Fusion score (r_fusion): {r_fusion:.3f}")
        
        return r_fusion
    
    def _check_fusion_consistency(
        self,
        proposals: List[Dict[str, Any]],
        fused_result: Dict[str, Any]
    ) -> float:
        """
        检查融合一致性：融合结果的每个元素是否来自至少一个proposal
        
        Returns:
            1.0: 所有元素都有来源
            0.5: 部分元素有来源
            0.0: 引入了大量不存在的信息
        """
        try:
            # 提取融合结果的causal_graph
            fused_graph = fused_result.get('causal_graph', [])
            if not fused_graph:
                return 0.5
            
            # 收集所有proposals中的节点和边
            all_nodes = set()
            all_edges = set()
            
            for proposal in proposals:
                graph = proposal.get('causal_graph', [])
                for link in graph:
                    causes = link.get('cause', [])
                    effect = link.get('effect')
                    
                    # 添加节点
                    if isinstance(causes, list):
                        all_nodes.update(causes)
                    elif causes:
                        all_nodes.add(causes)
                    if effect:
                        all_nodes.add(effect)
                    
                    # 添加边（表示为tuple）
                    if effect and causes:
                        if isinstance(causes, list):
                            for cause in causes:
                                all_edges.add((cause, effect))
                        else:
                            all_edges.add((causes, effect))
            
            # 检查融合结果的元素是否来自proposals
            fused_nodes = set()
            fused_edges = set()
            valid_nodes = 0
            valid_edges = 0
            
            for link in fused_graph:
                causes = link.get('cause', [])
                effect = link.get('effect')
                
                # 检查节点
                if isinstance(causes, list):
                    for cause in causes:
                        fused_nodes.add(cause)
                        if cause in all_nodes:
                            valid_nodes += 1
                elif causes:
                    fused_nodes.add(causes)
                    if causes in all_nodes:
                        valid_nodes += 1
                
                if effect:
                    fused_nodes.add(effect)
                    if effect in all_nodes:
                        valid_nodes += 1
                
                # 检查边
                if effect and causes:
                    if isinstance(causes, list):
                        for cause in causes:
                            edge = (cause, effect)
                            fused_edges.add(edge)
                            if edge in all_edges:
                                valid_edges += 1
                    else:
                        edge = (causes, effect)
                        fused_edges.add(edge)
                        if edge in all_edges:
                            valid_edges += 1
            
            # 计算一致性分数（节点和边的加权平均）
            node_consistency = valid_nodes / len(fused_nodes) if fused_nodes else 1.0
            edge_consistency = valid_edges / len(fused_edges) if fused_edges else 1.0
            
            consistency = 0.4 * node_consistency + 0.6 * edge_consistency
            return consistency
        
        except Exception as e:
            self._print(f"  Consistency check error: {e}")
            return 0.5
    
    def _check_conflict_resolution(
        self,
        proposals: List[Dict[str, Any]],
        fused_result: Dict[str, Any]
    ) -> float:
        """
        检查冲突解决质量：是否正确处理了proposals之间的矛盾
        
        策略：
        1. 找出proposals之间的冲突边（同一对节点有不同的连接方向或规则）
        2. 检查Critic如何解决这些冲突
        3. 如果LLM可用，让LLM评判解决方案的合理性
        
        Returns:
            1.0: 冲突解决合理
            0.5: 部分合理或无冲突
            0.0: 冲突解决不当
        """
        try:
            # 找出proposals之间的冲突
            conflicts = self._identify_conflicts(proposals)
            
            if not conflicts:
                # 无冲突，给中等分数（因为没有展示冲突解决能力）
                return 0.7
            
            # 检查融合结果如何处理这些冲突
            fused_graph = fused_result.get('causal_graph', [])
            if not fused_graph:
                return 0.3
            
            # 统计冲突处理情况
            resolved_conflicts = 0
            for conflict in conflicts:
                node_pair = conflict['node_pair']
                options = conflict['options']
                
                # 在融合结果中查找这个节点对的连接
                fused_connection = self._find_connection_in_graph(
                    fused_graph, node_pair
                )
                
                if fused_connection:
                    # 检查是否选择了某个option或做了合理的综合
                    resolved_conflicts += 1
            
            resolution_rate = resolved_conflicts / len(conflicts) if conflicts else 1.0
            
            # 如果LLM可用，让LLM评判冲突解决的合理性
            if self.llm_client and conflicts:
                try:
                    llm_score = self._llm_evaluate_conflict_resolution(
                        conflicts, fused_result
                    )
                    # 结合规则分数和LLM分数
                    return 0.5 * resolution_rate + 0.5 * llm_score
                except Exception:
                    pass
            
            return resolution_rate
        
        except Exception as e:
            self._print(f"  Conflict resolution check error: {e}")
            return 0.5
    
    def _identify_conflicts(
        self,
        proposals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别proposals之间的冲突"""
        conflicts = []
        
        # 为每个proposal建立边字典
        proposal_edges = []
        for proposal in proposals:
            edges_dict = {}
            graph = proposal.get('causal_graph', [])
            for link in graph:
                causes = link.get('cause', [])
                effect = link.get('effect')
                rule = link.get('rule', '')
                
                if effect and causes:
                    if isinstance(causes, list):
                        for cause in causes:
                            key = f"{cause}->{effect}"
                            edges_dict[key] = rule
                    else:
                        key = f"{causes}->{effect}"
                        edges_dict[key] = rule
            proposal_edges.append(edges_dict)
        
        # 找出不同proposals对同一节点对的不同处理
        all_keys = set()
        for edges in proposal_edges:
            all_keys.update(edges.keys())
        
        for key in all_keys:
            rules = []
            for edges in proposal_edges:
                if key in edges:
                    rules.append(edges[key])
            
            # 如果有不同的规则，说明有冲突
            if len(set(rules)) > 1:
                conflicts.append({
                    'node_pair': key,
                    'options': list(set(rules))
                })
        
        return conflicts
    
    def _find_connection_in_graph(
        self,
        graph: List[Dict],
        node_pair: str
    ) -> Optional[Dict]:
        """在图中查找特定的节点对连接"""
        for link in graph:
            causes = link.get('cause', [])
            effect = link.get('effect')
            
            if isinstance(causes, list):
                for cause in causes:
                    key = f"{cause}->{effect}"
                    if key == node_pair:
                        return link
            elif causes and effect:
                key = f"{causes}->{effect}"
                if key == node_pair:
                    return link
        
        return None
    
    def _llm_evaluate_conflict_resolution(
        self,
        conflicts: List[Dict],
        fused_result: Dict[str, Any]
    ) -> float:
        """LLM评估冲突解决的合理性"""
        prompt = f"""Evaluate how well the conflicts were resolved in the fused causal graph.

Conflicts identified:
{json.dumps(conflicts, indent=2)}

Fused result:
{json.dumps(fused_result.get('causal_graph', []), indent=2)}

Rate the conflict resolution quality from 0.0 to 1.0:
- 1.0: Excellent resolution, chose the most reasonable option
- 0.5: Acceptable resolution
- 0.0: Poor resolution, missed conflicts or chose unreasonable options

Output only a number between 0.0 and 1.0.
"""
        
        response = self.llm_client.complete(prompt, temperature=0.0)
        
        # 提取分数
        try:
            score = float(response.strip())
            return max(0.0, min(1.0, score))
        except ValueError:
            return 0.5
    
    def _check_information_preservation(
        self,
        proposals: List[Dict[str, Any]],
        fused_result: Dict[str, Any]
    ) -> float:
        """
        检查信息保留度：融合结果是否保留了proposals中的关键信息
        
        策略：
        1. 统计proposals中高频出现的节点和边（认为是重要信息）
        2. 检查融合结果是否保留了这些关键信息
        
        Returns:
            1.0: 完全保留关键信息
            0.5: 部分保留
            0.0: 丢失大量关键信息
        """
        try:
            # 统计所有proposals中节点和边的出现频率
            node_counts = {}
            edge_counts = {}
            
            for proposal in proposals:
                graph = proposal.get('causal_graph', [])
                seen_nodes = set()
                seen_edges = set()
                
                for link in graph:
                    causes = link.get('cause', [])
                    effect = link.get('effect')
                    
                    # 统计节点
                    if isinstance(causes, list):
                        for cause in causes:
                            if cause not in seen_nodes:
                                node_counts[cause] = node_counts.get(cause, 0) + 1
                                seen_nodes.add(cause)
                    elif causes and causes not in seen_nodes:
                        node_counts[causes] = node_counts.get(causes, 0) + 1
                        seen_nodes.add(causes)
                    
                    if effect and effect not in seen_nodes:
                        node_counts[effect] = node_counts.get(effect, 0) + 1
                        seen_nodes.add(effect)
                    
                    # 统计边
                    if effect and causes:
                        if isinstance(causes, list):
                            for cause in causes:
                                edge = (cause, effect)
                                if edge not in seen_edges:
                                    edge_counts[edge] = edge_counts.get(edge, 0) + 1
                                    seen_edges.add(edge)
                        else:
                            edge = (causes, effect)
                            if edge not in seen_edges:
                                edge_counts[edge] = edge_counts.get(edge, 0) + 1
                                seen_edges.add(edge)
            
            # 定义关键信息：出现在50%以上proposals中的节点和边
            threshold = len(proposals) * 0.5
            key_nodes = {node for node, count in node_counts.items() if count >= threshold}
            key_edges = {edge for edge, count in edge_counts.items() if count >= threshold}
            
            if not key_nodes and not key_edges:
                # 没有高频信息，给中等分数
                return 0.6
            
            # 检查融合结果保留了多少关键信息
            fused_graph = fused_result.get('causal_graph', [])
            preserved_nodes = set()
            preserved_edges = set()
            
            for link in fused_graph:
                causes = link.get('cause', [])
                effect = link.get('effect')
                
                # 检查节点
                if isinstance(causes, list):
                    preserved_nodes.update([c for c in causes if c in key_nodes])
                elif causes and causes in key_nodes:
                    preserved_nodes.add(causes)
                
                if effect and effect in key_nodes:
                    preserved_nodes.add(effect)
                
                # 检查边
                if effect and causes:
                    if isinstance(causes, list):
                        for cause in causes:
                            edge = (cause, effect)
                            if edge in key_edges:
                                preserved_edges.add(edge)
                    else:
                        edge = (causes, effect)
                        if edge in key_edges:
                            preserved_edges.add(edge)
            
            # 计算保留率
            node_preservation = len(preserved_nodes) / len(key_nodes) if key_nodes else 1.0
            edge_preservation = len(preserved_edges) / len(key_edges) if key_edges else 1.0
            
            preservation = 0.4 * node_preservation + 0.6 * edge_preservation
            return preservation
        
        except Exception as e:
            self._print(f"  Information preservation check error: {e}")
            return 0.5
    
    def _check_fusion_improvement(
        self,
        proposals: List[Dict[str, Any]],
        fused_result: Dict[str, Any],
        ground_truth: str = None
    ) -> float:
        """
        检查融合优化度：融合结果是否优于单个最好的proposal
        
        策略：
        1. 对每个proposal评估质量（使用r_graph）
        2. 对融合结果评估质量
        3. 比较：融合结果 vs 最好的单个proposal
        
        Returns:
            1.0: 融合结果显著优于最好的单个
            0.5: 融合结果与最好的单个相当
            0.0: 融合结果还不如最好的单个
        """
        try:
            # 评估每个proposal的图质量
            proposal_scores = []
            for proposal in proposals:
                score = self.evaluate_graph(proposal)
                proposal_scores.append(score)
            
            if not proposal_scores:
                return 0.5
            
            best_proposal_score = max(proposal_scores)
            
            # 评估融合结果的图质量
            fused_score = self.evaluate_graph(fused_result)
            
            # 计算改进度
            if best_proposal_score >= 0.95:
                # 如果最好的proposal已经很好了，融合很难再提升
                if fused_score >= best_proposal_score:
                    return 1.0
                else:
                    return 0.5
            
            # 计算相对改进
            improvement_space = 1.0 - best_proposal_score
            actual_improvement = fused_score - best_proposal_score
            
            if improvement_space > 0:
                improvement_ratio = actual_improvement / improvement_space
                # 归一化到 [0, 1]
                return max(0.0, min(1.0, 0.5 + 0.5 * improvement_ratio))
            else:
                return 0.5
        
        except Exception as e:
            self._print(f"  Fusion improvement check error: {e}")
            return 0.5

