"""
Causal Structure Optimizer Module
因果结构优化模块

This module optimizes causal DAG structures by:
1. Identifying three fundamental causal patterns (Chain/Fork/Collider)
2. Validating causal direction correctness
3. Optimizing structural consistency

本模块通过以下方式优化因果DAG结构：
1. 识别三种基本因果模式（链/叉/对撞）
2. 验证因果方向正确性
3. 优化结构一致性
"""

import json
import re
import copy
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set


class CausalStructureOptimizer:
    """
    Causal Structure Optimizer for DAG structural analysis and optimization.
    因果结构优化器，用于DAG结构分析和优化
    
    This class leverages causal inference principles to:
    1. Identify causal patterns (Chain, Fork, Collider)
    2. Validate causal direction logic
    3. Detect and fix structural issues
    4. Optimize DAG for causal soundness
    
    本类利用因果推断原理来：
    1. 识别因果模式（链、叉、对撞）
    2. 验证因果方向逻辑
    3. 检测并修复结构问题
    4. 优化DAG的因果合理性
    """
    
    def __init__(
        self,
        causal_expert_client=None,
        verbose: bool = True
    ):
        """
        Initialize causal structure optimizer.
        
        Args:
            causal_expert_client: Optional LLM client with causal knowledge expertise
            verbose: Whether to print progress
        """
        self.causal_expert = causal_expert_client
        self.verbose = verbose
        
        # Load optimization prompt
        self._load_prompts()
        
        if self.verbose:
            print(f"✓ CausalStructureOptimizer initialized")
    
    def _print(self, message: str, **kwargs):
        """Conditional print"""
        if self.verbose:
            print(message, **kwargs)
    
    def _load_prompts(self):
        """Load causal structure optimization prompt"""
        prompt_path = Path("prompts/causal_structure_optimization_prompt.txt")
        
        # Try relative path first
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.optimization_prompt = f.read()
            if self.verbose:
                print(f"   ✓ Loaded optimization prompt from {prompt_path}")
        else:
            # Try absolute path
            project_root = Path(__file__).parent.parent
            absolute_path = project_root / prompt_path
            
            if absolute_path.exists():
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    self.optimization_prompt = f.read()
                if self.verbose:
                    print(f"   ✓ Loaded optimization prompt from {absolute_path}")
            else:
                # Use fallback
                self.optimization_prompt = self._get_default_optimization_prompt()
                if self.verbose:
                    print(f"   ⚠️  Prompt file not found, using default prompt")
    
    def _get_default_optimization_prompt(self) -> str:
        """Default causal structure optimization prompt"""
        return """Analyze the following causal DAG for structural patterns and validate causal directions.

**Problem Context:**
{problem}

**Current Causal DAG:**
{dag}

**Tasks:**
1. Identify Chain, Fork, and Collider structures
2. Validate causal directions
3. Suggest structural optimizations

**Output JSON Format:**
{{
  "patterns": {{
    "chains": [...],
    "forks": [...],
    "colliders": [...]
  }},
  "direction_validations": [...],
  "optimization_suggestions": [...]
}}
"""
    
    def optimize_causal_structure(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Optimize causal DAG structure using LLM-based analysis and optimization.
        使用基于LLM的分析和优化来优化因果DAG结构
        
        Args:
            dag: Knowledge-enhanced DAG from previous step
            problem_text: Original problem description
        
        Returns:
            Tuple of (optimized_dag, structure_report)
        """
        self._print("🔗 Optimizing causal structure...")
        
        try:
            # Check if causal expert is available
            if not self.causal_expert:
                self._print("  ⚠️  No causal expert available, skipping optimization")
                return dag, {
                    'status': 'skipped',
                    'reason': 'No causal expert client provided'
                }
            
            # Build graph for quick checks
            G = self._build_graph(dag)
            
            if G.number_of_nodes() == 0:
                self._print("  ✓ Empty graph, skipping optimization")
                return dag, self._create_empty_report()
            
            # Use LLM to analyze and optimize
            self._print("  🤖 Analyzing DAG structure with LLM...")
            optimized_dag, structure_report = self._llm_optimize_structure(dag, problem_text, G)
            
            # Print summary
            if structure_report.get('status') == 'success':
                num_mods = len(structure_report.get('modifications_made', []))
                num_issues = len(structure_report.get('issues_detected', []))
                
                if num_mods > 0:
                    self._print(f"  ✓ Optimization complete: {num_issues} issues detected, {num_mods} modifications applied")
                else:
                    self._print(f"  ✓ No optimization needed: DAG structure is already good")
            
            return optimized_dag, structure_report
        
        except Exception as e:
            import traceback
            self._print(f"  ✗ Failed: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            return dag, {
                'status': 'failed',
                'error': str(e),
                'issues_detected': [],
                'modifications_made': []
            }
    
    def _llm_optimize_structure(
        self,
        dag: Dict[str, Any],
        problem_text: str,
        G: nx.DiGraph
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Use LLM to analyze and optimize DAG structure.
        使用LLM分析和优化DAG结构
        
        Args:
            dag: Current DAG
            problem_text: Problem description
            G: NetworkX graph representation
        
        Returns:
            Tuple of (optimized_dag, structure_report)
        """
        # Prepare prompt
        prompt = self.optimization_prompt.format(
            problem=problem_text,
            dag=json.dumps(dag, indent=2, ensure_ascii=False)
        )
        
        # Call LLM
        self._print("    Calling causal expert LLM...")
        response = self.causal_expert.complete(prompt, temperature=0.0)
        
        # Parse response
        optimization_result = self._parse_optimization_response(response)
        
        if not optimization_result:
            self._print("    ⚠️  Could not parse LLM response")
            return dag, {
                'status': 'failed',
                'error': 'Could not parse LLM optimization response',
                'issues_detected': [],
                'modifications_made': []
            }
        
        # Extract optimized DAG
        optimized_dag = optimization_result.get('optimized_dag')
        
        if not optimized_dag:
            self._print("    ⚠️  LLM did not return optimized DAG")
            return dag, {
                'status': 'failed',
                'error': 'No optimized DAG in LLM response',
                'issues_detected': optimization_result.get('issues_detected', []),
                'modifications_made': []
            }
        
        # Validate optimized DAG structure
        if not self._validate_dag_structure(optimized_dag):
            self._print("    ⚠️  Optimized DAG has invalid structure, keeping original")
            return dag, {
                'status': 'validation_failed',
                'error': 'Optimized DAG failed validation',
                'issues_detected': optimization_result.get('issues_detected', []),
                'modifications_made': optimization_result.get('modifications_made', [])
            }
        
        # Build report
        structure_report = {
            'status': 'success',
            'issues_detected': optimization_result.get('issues_detected', []),
            'modifications_made': optimization_result.get('modifications_made', []),
            'causal_patterns': optimization_result.get('causal_patterns', {}),
            'validation': optimization_result.get('validation', {}),
            'reasoning': optimization_result.get('reasoning', ''),
            'num_chains': len(optimization_result.get('causal_patterns', {}).get('chains', [])),
            'num_forks': len(optimization_result.get('causal_patterns', {}).get('forks', [])),
            'num_colliders': len(optimization_result.get('causal_patterns', {}).get('colliders', []))
        }
        
        # Print modifications
        modifications = structure_report.get('modifications_made', [])
        if modifications and self.verbose:
            self._print("    Modifications applied:")
            for mod in modifications[:5]:  # Show first 5
                self._print(f"      • {mod}")
            if len(modifications) > 5:
                self._print(f"      ... and {len(modifications)-5} more")
        
        return optimized_dag, structure_report
    
    def _validate_dag_structure(self, dag: Dict[str, Any]) -> bool:
        """
        Validate that optimized DAG has required structure.
        验证优化后的DAG具有必需的结构
        
        Args:
            dag: DAG to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['target_variable', 'knowns', 'causal_graph', 'computation_plan']
        
        for field in required_fields:
            if field not in dag:
                self._print(f"      Missing required field: {field}")
                return False
        
        # Check causal_graph structure
        if not isinstance(dag['causal_graph'], list):
            self._print(f"      causal_graph must be a list")
            return False
        
        for link in dag['causal_graph']:
            if not isinstance(link, dict):
                return False
            if 'cause' not in link or 'effect' not in link or 'rule' not in link:
                self._print(f"      Invalid causal_graph link: {link}")
                return False
        
        # Check computation_plan structure
        if not isinstance(dag['computation_plan'], list):
            self._print(f"      computation_plan must be a list")
            return False
        
        for step in dag['computation_plan']:
            if not isinstance(step, dict):
                return False
            if 'id' not in step or 'target' not in step or 'inputs' not in step:
                self._print(f"      Invalid computation_plan step: {step}")
                return False
        
        return True
    
    def _build_graph(self, dag: Dict[str, Any]) -> nx.DiGraph:
        """
        Build NetworkX directed graph from DAG structure.
        从DAG结构构建NetworkX有向图
        
        Args:
            dag: DAG dictionary with causal_graph field
        
        Returns:
            NetworkX DiGraph object
        """
        G = nx.DiGraph()
        
        if 'causal_graph' not in dag:
            return G
        
        # Add edges from causal_graph
        for link in dag['causal_graph']:
            causes = link.get('cause', [])
            effect = link.get('effect')
            
            if not effect:
                continue
            
            # Handle multiple causes
            if isinstance(causes, list):
                for cause in causes:
                    if cause:
                        G.add_edge(cause, effect, rule=link.get('rule', ''))
            elif causes:
                G.add_edge(causes, effect, rule=link.get('rule', ''))
        
        return G
    
    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM optimization response to extract JSON.
        解析LLM优化响应以提取JSON
        
        Args:
            response: LLM response text
        
        Returns:
            Parsed JSON dictionary or empty dict if parsing fails
        """
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            return {}
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"   ⚠️  JSON decode error: {e}")
            return {}
    
    def _create_empty_report(self) -> Dict[str, Any]:
        """Create report for empty graph"""
        return {
            'status': 'empty_graph',
            'patterns_found': {'chains': [], 'forks': [], 'colliders': []},
            'direction_validations': [],
            'structural_issues': [],
            'num_chains': 0,
            'num_forks': 0,
            'num_colliders': 0,
            'is_dag': True,
            'is_connected': False
        }




