"""
Causal Evaluation Module for Step3
Step3 因果评估模块

This module implements two independent evaluation metrics:
本模块实现两个独立的评估指标：

1. CF (Counterfactual Faithfulness) - 反事实忠诚度
   CF = (Causal Intervention Score + Logic Quality + Graph Quality) / 3
   
2. AF (Abductive Faithfulness) - 溯因忠诚度
   AF = Abductive Reasoning Score

Components:
组件：

【CF Components - CF组件】
1. Causal Intervention Evaluator - 因果干预评估器
   - Uses do-calculus to evaluate node importance
   - 使用do算子评估节点重要性
   
2. Logic Quality Evaluator - 逻辑推理质量评估
   - Borrowed from RewardEvaluator
   - 借鉴自RewardEvaluator
   
3. Graph Quality Evaluator - DAG图质量评估
   - Borrowed from RewardEvaluator
   - 借鉴自RewardEvaluator

【AF Component - AF组件】
4. Abductive Reasoning Evaluator - 溯因推理评估器
   - Tests reasoning reversibility (from effect to cause)
   - 测试推理可逆性（从果到因）
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from engine.reward_evaluator import RewardEvaluator


class CausalInterventionEvaluator:
    """
    Causal Intervention Evaluator using do-calculus
    使用do算子的因果干预评估器
    
    For each non-target node in the DAG, we ask:
    对于DAG中的每个非目标节点，我们问：
    "If we perform causal intervention do(X|other_vars), how much does it affect the result?"
    "如果我们执行因果干预do(X|其他变量)，对结果的影响有多大？"
    
    Scoring:
    评分：
    - Total pool: 100 points
    - 总分池：100分
    - Each non-target node gets equal share: 100/N points
    - 每个非目标节点获得平等份额：100/N分
    - LLM evaluates impact and assigns score (0 to max_per_node)
    - LLM评估影响并分配分数（0到max_per_node）
    - Final score: sum of all scores / 100 (normalized to 0-1)
    - 最终分数：所有分数之和 / 100（归一化到0-1）
    """
    
    def __init__(self, llm_client=None, verbose: bool = True):
        """
        Initialize Causal Intervention Evaluator
        
        Args:
            llm_client: LLM client for intervention evaluation
            verbose: Whether to print progress
        """
        self.llm_client = llm_client
        self.verbose = verbose
        
        # Load prompt
        self._load_prompts()
    
    def _print(self, message: str):
        """Conditional print"""
        if self.verbose:
            print(message)
    
    def _load_prompts(self):
        """Load causal intervention evaluation prompt"""
        prompt_path = Path("prompts/causal_intervention_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.intervention_prompt = f.read()
        else:
            self.intervention_prompt = self._get_default_intervention_prompt()
    
    def _get_default_intervention_prompt(self) -> str:
        """Default causal intervention evaluation prompt"""
        return """You are a causal reasoning expert. Evaluate the importance of a node in a causal DAG using do-calculus.

**Problem:**
{problem}

**Causal DAG:**
{dag}

**Target Variable (Result):**
{target_variable}

**Node to Evaluate:**
{node_name}

**Question:**
If we perform a causal intervention do({node_name} | other_variables) in this DAG, what is the impact on the final result {target_variable}?

**Instructions:**
1. Consider what happens if we **intervene on (or remove) {node_name}**
2. Think about the causal path from {node_name} to {target_variable}
3. Evaluate the impact: How critical is this node for reaching the correct result?
4. **Do NOT calculate actual numbers** - only think about the causal influence magnitude

**Scoring Guidelines (5-level scale):**
- **critical** (score: 0.8-{max_score}): Node is absolutely essential, removing it would completely break the reasoning chain or make the result impossible to determine
- **high** (score: 0.6-0.8): Node is very important, removing it would significantly alter the result or require major adjustments
- **medium** (score: 0.4-0.6): Node contributes meaningfully, but the result could still be approximated or derived through alternative paths
- **low** (score: 0.2-0.4): Node has minor influence, removing it would have limited impact on the final result
- **minimal** (score: 0.0-0.2): Node is peripheral or redundant, negligible effect on the final result

**Output JSON Format:**
{{
  "impact_level": "critical" | "high" | "medium" | "low" | "minimal",
  "score": 0.0 to {max_score},
  "reasoning": "Explain why this node has this level of impact on the causal chain",
  "causal_path": "Describe the causal path from this node to the target (if exists)"
}}

Now evaluate the node {node_name}. Output ONLY the JSON.
"""
    
    def evaluate_intervention(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate causal interventions on all non-target nodes
        评估所有非目标节点的因果干预
        
        Args:
            dag: Causal DAG structure
            problem_text: Problem description
        
        Returns:
            Tuple of (intervention_score, detailed_report)
            - intervention_score: 0.0-1.0
            - detailed_report: Details about each node evaluation
        """
        self._print("\n" + "="*60)
        self._print("Causal Intervention Evaluation")
        self._print("因果干预评估")
        self._print("="*60)
        
        # Extract target variable
        target_variable = dag.get('target_variable', 'result')
        self._print(f"\nTarget Variable: {target_variable}")
        
        # Extract all nodes from causal_graph
        all_nodes = self._extract_nodes_from_dag(dag)
        self._print(f"Total nodes in DAG: {len(all_nodes)}")
        
        # Filter out target variable
        non_target_nodes = [n for n in all_nodes if n != target_variable]
        self._print(f"Non-target nodes to evaluate: {len(non_target_nodes)}")
        
        if len(non_target_nodes) == 0:
            self._print("⚠️  No non-target nodes to evaluate")
            return 0.5, {'status': 'no_nodes', 'nodes_evaluated': []}
        
        # Calculate max score per node
        total_pool = 100.0
        max_score_per_node = total_pool / len(non_target_nodes)
        self._print(f"Max score per node: {max_score_per_node:.2f}")
        
        # Evaluate each node
        node_evaluations = []
        total_score = 0.0
        
        for i, node in enumerate(non_target_nodes, 1):
            self._print(f"\n[{i}/{len(non_target_nodes)}] Evaluating node: {node}")
            
            node_score, node_report = self._evaluate_single_node(
                dag, problem_text, node, target_variable, max_score_per_node
            )
            
            total_score += node_score
            node_evaluations.append({
                'node': node,
                'score': node_score,
                'max_score': max_score_per_node,
                'report': node_report
            })
            
            self._print(f"  Score: {node_score:.2f}/{max_score_per_node:.2f}")
        
        # Normalize to 0-1
        intervention_score = total_score / total_pool
        
        self._print("\n" + "="*60)
        self._print(f"Total Intervention Score: {total_score:.2f}/100")
        self._print(f"Normalized Score: {intervention_score:.4f}")
        self._print("="*60)
        
        detailed_report = {
            'status': 'success',
            'total_nodes': len(all_nodes),
            'non_target_nodes': len(non_target_nodes),
            'max_score_per_node': max_score_per_node,
            'total_score': total_score,
            'normalized_score': intervention_score,
            'node_evaluations': node_evaluations
        }
        
        return intervention_score, detailed_report
    
    def _extract_nodes_from_dag(self, dag: Dict[str, Any]) -> List[str]:
        """
        Extract all unique nodes from DAG
        从DAG中提取所有唯一节点
        """
        nodes = set()
        
        # Add target variable
        if 'target_variable' in dag:
            nodes.add(dag['target_variable'])
        
        # Add nodes from knowns
        if 'knowns' in dag and isinstance(dag['knowns'], dict):
            nodes.update(dag['knowns'].keys())
        
        # Add nodes from causal_graph
        if 'causal_graph' in dag:
            for link in dag['causal_graph']:
                # Add causes
                causes = link.get('cause', [])
                if isinstance(causes, list):
                    nodes.update(causes)
                elif isinstance(causes, str):
                    nodes.add(causes)
                
                # Add effect
                effect = link.get('effect', '')
                if effect:
                    nodes.add(effect)
        
        return list(nodes)
    
    def _evaluate_single_node(
        self,
        dag: Dict[str, Any],
        problem_text: str,
        node_name: str,
        target_variable: str,
        max_score: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate a single node using LLM
        使用LLM评估单个节点
        
        Returns:
            Tuple of (score, evaluation_report)
        """
        # If no LLM, use default scoring
        if not self.llm_client:
            self._print("  ⚠️  No LLM available, using default score")
            return max_score * 0.5, {'method': 'default', 'reason': 'no_llm'}
        
        try:
            # Prepare prompt
            prompt = self.intervention_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False),
                target_variable=target_variable,
                node_name=node_name,
                max_score=max_score
            )
            
            # Call LLM
            response = self.llm_client.complete(prompt, temperature=0.0)
            
            # Parse response
            evaluation = self._parse_intervention_response(response, max_score)
            
            if evaluation:
                score = evaluation.get('score', max_score * 0.5)
                return score, evaluation
            else:
                self._print("  ⚠️  Failed to parse LLM response, using default")
                return max_score * 0.5, {'method': 'default', 'reason': 'parse_failed'}
        
        except Exception as e:
            self._print(f"  ⚠️  Error evaluating node: {e}")
            return max_score * 0.5, {'method': 'default', 'reason': f'error: {str(e)}'}
    
    def _parse_intervention_response(
        self,
        response: str,
        max_score: float
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM intervention evaluation response"""
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Validate and clamp score
                score = float(result.get('score', max_score * 0.5))
                score = max(0.0, min(max_score, score))
                result['score'] = score
                
                return result
            else:
                return None
        except Exception as e:
            self._print(f"    JSON parse error: {e}")
            return None


class AbductiveReasoningEvaluator:
    """
    Abductive Reasoning Evaluator (溯因推理评估器)
    
    Evaluates the reversibility of causal reasoning by:
    评估因果推理的可逆性：
    - Starting from the result (effect)
    - 从结果（效果）开始
    - Removing one cause node at a time
    - 每次移除一个原因节点
    - Testing if the reasoning chain still holds with remaining information
    - 测试推理链在剩余信息下是否仍然成立
    
    Scoring:
    评分：
    - For each cause node: 1 if reasoning holds, 0 if not
    - 对每个原因节点：成立返回1，不成立返回0
    - Final score: average of all cause nodes (0-1)
    - 最终分数：所有原因节点的平均分（0-1）
    """
    
    def __init__(self, llm_client=None, verbose: bool = True):
        """
        Initialize Abductive Reasoning Evaluator
        
        Args:
            llm_client: LLM client for abductive reasoning evaluation
            verbose: Whether to print progress
        """
        self.llm_client = llm_client
        self.verbose = verbose
        
        # Load prompt
        self._load_prompts()
    
    def _print(self, message: str):
        """Conditional print"""
        if self.verbose:
            print(message)
    
    def _load_prompts(self):
        """Load abductive reasoning evaluation prompt"""
        prompt_path = Path("prompts/abductive_reasoning_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.abductive_prompt = f.read()
        else:
            self.abductive_prompt = self._get_default_abductive_prompt()
    
    def _get_default_abductive_prompt(self) -> str:
        """Default abductive reasoning evaluation prompt"""
        return """You are a causal reasoning expert evaluating abductive reasoning capabilities.

**Problem:**
{problem}

**Causal DAG:**
{dag}

**EVALUATION SETUP:**
This is a hypothetical scenario to test backward reasoning from effects to causes.

**Hidden Variable (to be inferred):**
{removed_node}

**Available Information:**
- Target Variable (Result): {target_variable} = {target_value}
- Other Known Nodes: {other_nodes}

**Task:**
Using ONLY the following information:
1. The causal DAG structure
2. The value of the target variable (result)
3. The values of other nodes (excluding {removed_node})

Determine whether you can logically infer or deduce the value of "{removed_node}".

**Critical Instructions:**
- Treat "{removed_node}" as UNKNOWN, even if it appears in the original problem statement
- This is a counterfactual reasoning test: assume the value of "{removed_node}" was never provided
- Attempt to work backwards from the observed result and intermediate nodes to deduce "{removed_node}"
- Only mark "can_infer: true" if you can definitively determine the value through logical deduction

**Output Format (JSON only):**
{{
  "can_infer": true | false,
  "inferred_value": "the deduced value of {removed_node}, or null if cannot infer",
  "reasoning": "detailed explanation of the deduction process or why inference is impossible"
}}

Output ONLY valid JSON.
"""
    
    def evaluate_abductive(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate abductive reasoning (从果溯因)
        
        For each cause node in knowns:
        对每个knowns中的原因节点：
        1. Remove it
        2. Give the result and all other nodes
        3. Ask if reasoning chain still holds
        4. Score: 1 if holds, 0 if not
        
        Args:
            dag: Causal DAG structure
            problem_text: Problem description
        
        Returns:
            Tuple of (abductive_score, detailed_report)
            - abductive_score: 0.0-1.0
            - detailed_report: Details about each cause node test
        """
        self._print("\n" + "="*60)
        self._print("Abductive Reasoning Evaluation")
        self._print("溯因推理评估")
        self._print("="*60)
        
        # Extract target variable
        target_variable = dag.get('target_variable', 'result')
        self._print(f"\nTarget Variable: {target_variable}")
        
        # Extract cause nodes (from knowns)
        cause_nodes = list(dag.get('knowns', {}).keys())
        self._print(f"Cause nodes to test: {len(cause_nodes)}")
        self._print(f"Cause nodes: {cause_nodes}")
        
        if len(cause_nodes) == 0:
            self._print("⚠️  No cause nodes to evaluate")
            return 0.5, {'status': 'no_cause_nodes', 'tests': []}
        
        # Test each cause node
        node_tests = []
        total_score = 0.0
        
        for i, removed_node in enumerate(cause_nodes, 1):
            self._print(f"\n[{i}/{len(cause_nodes)}] Testing with {removed_node} removed...")
            
            can_infer, test_report = self._test_single_cause(
                dag, problem_text, removed_node, target_variable, cause_nodes
            )
            
            score = 1.0 if can_infer else 0.0
            total_score += score
            
            node_tests.append({
                'removed_node': removed_node,
                'can_infer': can_infer,
                'score': score,
                'report': test_report
            })
            
            status = "✓ Can infer" if can_infer else "✗ Cannot infer"
            self._print(f"  {status} (score: {score})")
        
        # Calculate average
        abductive_score = total_score / len(cause_nodes)
        
        self._print("\n" + "="*60)
        self._print(f"Total tests: {len(cause_nodes)}")
        self._print(f"Passed tests: {int(total_score)}")
        self._print(f"Abductive Score: {abductive_score:.4f}")
        self._print("="*60)
        
        detailed_report = {
            'status': 'success',
            'total_cause_nodes': len(cause_nodes),
            'passed_tests': int(total_score),
            'abductive_score': abductive_score,
            'node_tests': node_tests
        }
        
        return abductive_score, detailed_report
    
    def _test_single_cause(
        self,
        dag: Dict[str, Any],
        problem_text: str,
        removed_node: str,
        target_variable: str,
        all_cause_nodes: List[str]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Test if reasoning holds when one cause is removed
        测试移除一个原因后推理是否成立
        
        Returns:
            Tuple of (holds, test_report)
        """
        # If no LLM, return failure (cannot evaluate without LLM)
        if not self.llm_client:
            self._print("  ⚠️  No LLM available, cannot evaluate")
            return False, {'method': 'default', 'reason': 'no_llm'}
        
        try:
            # Prepare other nodes (all causes except removed one)
            other_nodes = [n for n in all_cause_nodes if n != removed_node]
            other_nodes_str = ", ".join([f"{n}={dag['knowns'].get(n, '?')}" for n in other_nodes])
            
            # Get target value (if available from computation_plan)
            target_value = self._extract_target_value(dag)
            
            # Prepare prompt
            prompt = self.abductive_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False),
                target_variable=target_variable,
                removed_node=removed_node,
                target_value=target_value,
                other_nodes=other_nodes_str
            )
            
            # Call LLM
            response = self.llm_client.complete(prompt, temperature=0.0)
            
            # Parse response
            result = self._parse_abductive_response(response)
            
            if result:
                # Use the new 'can_infer' field from updated prompt
                can_infer = result.get('can_infer', False)
                return can_infer, result
            else:
                self._print("  ⚠️  Failed to parse LLM response")
                return False, {'method': 'default', 'reason': 'parse_failed', 'raw_response': response[:200]}
        
        except Exception as e:
            self._print(f"  ⚠️  Error testing abductive reasoning: {e}")
            return False, {'method': 'default', 'reason': f'error: {str(e)}'}
    
    def _extract_target_value(self, dag: Dict[str, Any]) -> str:
        """Extract target value from computation_plan if available"""
        target_var = dag.get('target_variable', 'result')
        
        # Try to find in computation_plan
        if 'computation_plan' in dag:
            for step in dag['computation_plan']:
                if step.get('target') == target_var:
                    # Try to extract value from description
                    desc = step.get('description', '')
                    # Simple extraction (can be improved)
                    return f"(from computation plan: {desc})"
        
        return "?"
    
    def _parse_abductive_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM abductive reasoning evaluation response"""
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                return None
        except Exception as e:
            self._print(f"    JSON parse error: {e}")
            return None


class CausalFaithfulnessEvaluator:
    """
    Counterfactual Faithfulness (CF) Evaluator
    反事实忠诚度（CF）评估器
    
    Combines four components:
    结合四个组件：
    1. Causal Intervention Score (因果干预分数)
    2. Logic Quality Score (逻辑推理质量分数)
    3. Graph Quality Score (DAG图质量分数)
    4. Abductive Reasoning Score (溯因推理分数)
    
    CF = (intervention_score + logic_score + graph_score + abductive_score) / 4
    """
    
    def __init__(self, llm_client=None, verbose: bool = True):
        """
        Initialize CF Evaluator
        
        Args:
            llm_client: LLM client for evaluations
            verbose: Whether to print progress
        """
        self.llm_client = llm_client
        self.verbose = verbose
        
        # Initialize sub-evaluators
        self.intervention_evaluator = CausalInterventionEvaluator(
            llm_client=llm_client,
            verbose=verbose
        )
        
        self.abductive_evaluator = AbductiveReasoningEvaluator(
            llm_client=llm_client,
            verbose=verbose
        )
        
        self.reward_evaluator = RewardEvaluator(
            llm_client=llm_client,
            verbose=verbose
        )
    
    def _print(self, message: str):
        """Conditional print"""
        if self.verbose:
            print(message)
    
    def evaluate_cf(
        self,
        dag: Dict[str, Any],
        problem_text: str,
        reasoning_trajectory: str = ""
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Evaluate Counterfactual Faithfulness (CF) and Abductive Faithfulness (AF) for a single problem
        评估单个问题的反事实忠诚度（CF）和溯因忠诚度（AF）
        
        Args:
            dag: Causal DAG structure
            problem_text: Problem description
            reasoning_trajectory: Reasoning steps (optional, for logic evaluation)
        
        Returns:
            Tuple of (cf_score, af_score, detailed_report)
            - cf_score: 0.0-1.0 (Counterfactual Faithfulness)
            - af_score: 0.0-1.0 (Abductive Faithfulness)
            - detailed_report: Breakdown of all components
        """
        self._print("\n" + "="*80)
        self._print("CAUSAL EVALUATION: CF & AF")
        self._print("因果评估：反事实忠诚度（CF）& 溯因忠诚度（AF）")
        self._print("="*80)
        
        # 1. Causal Intervention Score (for CF)
        self._print("\n[1/4] Evaluating Causal Intervention...")
        intervention_score, intervention_report = self.intervention_evaluator.evaluate_intervention(
            dag, problem_text
        )
        
        # 2. Abductive Reasoning Score (for AF)
        self._print("\n[2/4] Evaluating Abductive Reasoning...")
        abductive_score, abductive_report = self.abductive_evaluator.evaluate_abductive(
            dag, problem_text
        )
        
        # 3. Logic Quality Score (for CF)
        self._print("\n[3/4] Evaluating Logic Quality...")
        if reasoning_trajectory:
            logic_score = self.reward_evaluator.evaluate_logic(
                reasoning_trajectory, problem_text
            )
        else:
            self._print("  ⚠️  No reasoning trajectory provided, using default score")
            logic_score = 0.5
        self._print(f"  Logic Score: {logic_score:.4f}")
        
        # 4. Graph Quality Score (for CF)
        self._print("\n[4/4] Evaluating Graph Quality...")
        graph_score = self.reward_evaluator.evaluate_graph(dag)
        self._print(f"  Graph Score: {graph_score:.4f}")
        
        # Compute CF (3 components: intervention + logic + graph)
        cf_score = (intervention_score + logic_score + graph_score) / 3.0
        
        # AF is the abductive score itself
        af_score = abductive_score
        
        self._print("\n" + "="*80)
        self._print("EVALUATION RESULTS:")
        self._print("\n【CF - Counterfactual Faithfulness】")
        self._print(f"  Causal Intervention:  {intervention_score:.4f} (33.3%)")
        self._print(f"  Logic Quality:        {logic_score:.4f} (33.3%)")
        self._print(f"  Graph Quality:        {graph_score:.4f} (33.3%)")
        self._print(f"  ─────────────────────────────────────")
        self._print(f"  CF Score:             {cf_score:.4f}")
        self._print("\n【AF - Abductive Faithfulness】")
        self._print(f"  AF Score:             {af_score:.4f}")
        self._print("="*80)
        
        detailed_report = {
            'cf_score': cf_score,
            'af_score': af_score,
            'cf_components': {
                'causal_intervention': {
                    'score': intervention_score,
                    'weight': 1/3,
                    'details': intervention_report
                },
                'logic_quality': {
                    'score': logic_score,
                    'weight': 1/3
                },
                'graph_quality': {
                    'score': graph_score,
                    'weight': 1/3
                }
            },
            'af_component': {
                'abductive_reasoning': {
                    'score': abductive_score,
                    'weight': 1.0,
                    'details': abductive_report
                }
            }
        }
        
        return cf_score, af_score, detailed_report
    
    def evaluate_cf_batch(
        self,
        problems: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate CF and AF for a batch of problems
        评估一批问题的CF和AF
        
        Args:
            problems: List of problem dictionaries, each containing:
                     - 'dag': Causal DAG
                     - 'problem_text': Problem description
                     - 'reasoning_trajectory': Reasoning steps (optional)
        
        Returns:
            Batch evaluation report with:
            - average_cf: Average CF score across all problems (0-1)
            - average_af: Average AF score across all problems (0-1)
            - individual_cf_scores: List of CF scores for each problem
            - individual_af_scores: List of AF scores for each problem
            - detailed_reports: Detailed reports for each problem
        """
        self._print("\n" + "="*80)
        self._print("BATCH CF & AF EVALUATION")
        self._print(f"Total problems: {len(problems)}")
        self._print("="*80)
        
        individual_cf_scores = []
        individual_af_scores = []
        detailed_reports = []
        
        for i, problem_data in enumerate(problems, 1):
            self._print(f"\n{'='*80}")
            self._print(f"Problem {i}/{len(problems)}")
            self._print(f"{'='*80}")
            
            dag = problem_data.get('dag', {})
            problem_text = problem_data.get('problem_text', '')
            reasoning_trajectory = problem_data.get('reasoning_trajectory', '')
            
            cf_score, af_score, report = self.evaluate_cf(dag, problem_text, reasoning_trajectory)
            
            individual_cf_scores.append(cf_score)
            individual_af_scores.append(af_score)
            detailed_reports.append(report)
        
        # Compute averages
        average_cf = sum(individual_cf_scores) / len(individual_cf_scores) if individual_cf_scores else 0.0
        average_af = sum(individual_af_scores) / len(individual_af_scores) if individual_af_scores else 0.0
        
        self._print("\n" + "="*80)
        self._print("BATCH RESULTS:")
        self._print("\n【CF - Counterfactual Faithfulness】")
        self._print(f"  Average CF Score: {average_cf:.4f}")
        self._print(f"  Min CF Score:     {min(individual_cf_scores):.4f}")
        self._print(f"  Max CF Score:     {max(individual_cf_scores):.4f}")
        self._print("\n【AF - Abductive Faithfulness】")
        self._print(f"  Average AF Score: {average_af:.4f}")
        self._print(f"  Min AF Score:     {min(individual_af_scores):.4f}")
        self._print(f"  Max AF Score:     {max(individual_af_scores):.4f}")
        self._print("="*80)
        
        return {
            'average_cf': average_cf,
            'average_af': average_af,
            'individual_cf_scores': individual_cf_scores,
            'individual_af_scores': individual_af_scores,
            'detailed_reports': detailed_reports,
            'total_problems': len(problems),
            'summary': {
                'cf': {
                    'min': min(individual_cf_scores) if individual_cf_scores else 0.0,
                    'max': max(individual_cf_scores) if individual_cf_scores else 0.0,
                    'avg': average_cf
                },
                'af': {
                    'min': min(individual_af_scores) if individual_af_scores else 0.0,
                    'max': max(individual_af_scores) if individual_af_scores else 0.0,
                    'avg': average_af
                }
            }
        }


# ==================== Usage Example ====================

def example_usage():
    """
    Example usage of CausalFaithfulnessEvaluator
    使用示例
    """
    from engine.scaffolder import LLMClient
    
    # Initialize
    llm_client = LLMClient()
    cf_evaluator = CausalFaithfulnessEvaluator(llm_client=llm_client, verbose=True)
    
    # Example DAG
    example_dag = {
        "target_variable": "time_at_max_height",
        "knowns": {"v0": 20, "g": 9.8},
        "causal_graph": [
            {
                "cause": ["v0", "g"],
                "effect": "time_at_max_height",
                "rule": "At max height v=0. Using v=v0-gt, t=v0/g"
            }
        ],
        "computation_plan": [
            {
                "id": "step1",
                "target": "time_at_max_height",
                "inputs": ["v0", "g"],
                "description": "Calculate t = v0/g = 20/9.8 = 2.04 s"
            }
        ]
    }
    
    problem_text = "A ball is thrown upward with v0=20 m/s. Find time to max height."
    reasoning_trajectory = "At max height, velocity = 0. Using v = v0 - gt, solve for t: t = v0/g = 20/9.8 = 2.04 seconds."
    
    # Evaluate single problem
    cf_score, af_score, report = cf_evaluator.evaluate_cf(
        example_dag, problem_text, reasoning_trajectory
    )
    
    print(f"\nFinal CF Score: {cf_score:.4f}")
    print(f"Final AF Score: {af_score:.4f}")
    print(f"\nDetailed Report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Batch evaluation
    problems = [
        {
            'dag': example_dag,
            'problem_text': problem_text,
            'reasoning_trajectory': reasoning_trajectory
        }
        # Add more problems...
    ]
    
    batch_results = cf_evaluator.evaluate_cf_batch(problems)
    print(f"\nBatch Average CF: {batch_results['average_cf']:.4f}")
    print(f"Batch Average AF: {batch_results['average_af']:.4f}")


if __name__ == "__main__":
    example_usage()






