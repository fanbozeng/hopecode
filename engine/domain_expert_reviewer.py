"""
Domain Expert Reviewer Module
领域专家审查与修正模块

This module provides domain-specific expert review and correction for DAG structures.
本模块为DAG结构提供特定领域的专家审查与修正。

Key Functionality:
- Reviews DAGs for mathematical and physical correctness
- Identifies errors and violations of domain principles
- Actively corrects the DAG by generating a fixed version
- Returns a complete, corrected DAG ready for use

主要功能：
- 审查DAG的数学和物理正确性
- 识别错误和违反领域原则的问题
- 主动修正DAG，生成修复后的版本
- 返回完整的、可直接使用的修正后DAG
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class ProblemType(Enum):
    """Problem type classification / 问题类型分类"""
    MATH = "math"
    PHYSICS = "physics"
    GENERAL = "general"
    MIXED = "mixed"


class DomainExpertReviewer:
    """
    Domain Expert Reviewer for DAG validation, correction, and enhancement.
    领域专家审查器，用于DAG验证、修正和增强
    
    This class leverages domain experts (mathematicians/physicists) to:
    1. Validate formulas and theorems used in the DAG
    2. Check reasoning chain correctness
    3. Identify logical errors and violations
    4. Actively correct the DAG by generating a fixed version
    5. Return a complete, corrected DAG ready for downstream use
    
    本类利用领域专家（数学家/物理学家）来：
    1. 验证DAG中使用的公式和定理
    2. 检查推理链正确性
    3. 识别逻辑错误和违规问题
    4. 主动修正DAG，生成修复后的版本
    5. 返回完整的、可供下游使用的修正后DAG
    """
    
    def __init__(
        self,
        math_expert_client=None,
        physics_expert_client=None,
        verbose: bool = True
    ):
        """
        Initialize domain expert reviewer with multiple experts.
        使用多个专家初始化领域专家审查器
        
        Multi-agent design (aligned with Step1):
        - Math expert and Physics expert review in parallel
        - Reviews are fused to get comprehensive feedback
        
        多智能体设计（与Step1对齐）：
        - 数学专家和物理专家并行审查
        - 融合审查结果获得综合反馈
        
        Args:
            math_expert_client: LLM client for math expert
            physics_expert_client: LLM client for physics expert
            verbose: Whether to print progress
        """
        self.math_expert = math_expert_client
        self.physics_expert = physics_expert_client
        self.verbose = verbose
        
        # Unified expert (use math_expert as default unified expert)
        # 统一专家（使用math_expert作为默认的统一专家）
        self.expert = math_expert_client or physics_expert_client
        
        # Load review prompts
        self._load_prompts()
        
        if self.verbose:
            experts = []
            if self.math_expert:
                experts.append("Math Expert")
            if self.physics_expert:
                experts.append("Physics Expert")
            print(f"✓ DomainExpertReviewer initialized with {len(experts)} experts: {', '.join(experts) if experts else 'None'}")
    
    def _print(self, message: str, **kwargs):
        """Conditional print"""
        if self.verbose:
            print(message, **kwargs)
    
    def _load_prompts(self):
        """Load unified expert review prompt from file"""
        # Unified expert review prompt (Math + Physics)
        prompt_path = Path("prompts/expert_review_prompt.txt")
        
        # Try relative path first
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.review_prompt = f.read()
            if self.verbose:
                print(f"   ✓ Loaded expert review prompt from {prompt_path}")
        else:
            # Try absolute path
            project_root = Path(__file__).parent.parent
            absolute_path = project_root / prompt_path
            
            if absolute_path.exists():
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    self.review_prompt = f.read()
                if self.verbose:
                    print(f"   ✓ Loaded expert review prompt from {absolute_path}")
            else:
                # Use fallback
                self.review_prompt = self._get_default_prompt()
                if self.verbose:
                    print(f"   ⚠️  Prompt file not found at {prompt_path} or {absolute_path}")
                    print(f"   Using default prompt")
    
    def _get_default_prompt(self) -> str:
        """Default unified expert review and correction prompt (fallback)"""
        return """You are a rigorous expert in both mathematics and physics. Your task is to **review and actively correct** the following causal DAG.

**Problem:**
{problem}

**Causal DAG:**
{dag}

**Your Tasks:**
1. Automatically identify if this is math, physics, or mixed problem
2. Verify formulas, theorems, and physical laws are correctly applied
3. Check logical validity and unit consistency
4. Identify errors and provide specific corrections
5. **Generate a corrected DAG** with all fixes applied (this is the most important output!)

**Output JSON Format:**
{{
  "problem_domain": "math" | "physics" | "mixed",
  "issues": [
    {{"node": "...", "issue": "...", "severity": "high/medium/low", "category": "..."}}
  ],
  "corrections": [
    {{"node": "...", "original": "...", "corrected": "...", "reason": "..."}}
  ],
  "corrected_dag": {{
    "target_variable": "...",
    "knowns": {{...}},
    "causal_graph": [...],
    "computation_plan": [...]
  }},
  "overall_assessment": "summary"
}}

**Critical:** Always provide `corrected_dag` - if no errors, return the input DAG unchanged; if errors exist, return the fully corrected DAG.
"""
    
    def review_dag(
        self,
        dag: Dict[str, Any],
        problem_text: str,
        problem_type: Optional[ProblemType] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Review and correct DAG with unified expert (handles math, physics, and mixed problems).
        使用统一专家审查并修正DAG（处理数学、物理和混合问题）
        
        This method:
        1. Sends the DAG to an expert LLM for review
        2. Receives identified issues and corrections
        3. Gets a fully corrected DAG with all fixes applied
        4. Returns the corrected DAG for downstream use
        
        此方法：
        1. 将DAG发送给专家LLM进行审查
        2. 接收识别出的问题和修正方案
        3. 获取已应用所有修复的完整修正后DAG
        4. 返回修正后的DAG供下游使用
        
        Args:
            dag: The DAG structure to review
            problem_text: Original problem description
            problem_type: Deprecated parameter (kept for compatibility)
        
        Returns:
            Tuple of (reviewed_dag, review_report)
            - reviewed_dag: DAG with corrections applied
            - review_report: Detailed review information
        """
        if not self.expert:
            self._print("⚠️  Expert not available, skipping review")
            return dag, self._create_skip_report("no_expert")
        
        return self._review_with_expert(dag, problem_text)
    
    def _review_with_expert(
        self,
        dag: Dict[str, Any],
        problem_text: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Review DAG with unified expert (handles math, physics, and mixed problems)"""
        self._print("🔬 Expert reviewing DAG...", end=" ")
        
        try:
            # Check if expert client is available
            if self.expert is None:
                self._print("✗ Expert client not initialized")
                return dag, self._create_error_report("Expert client not initialized")
            
            # Format prompt with problem and DAG
            prompt = self.review_prompt.format(
                problem=problem_text,
                dag=json.dumps(dag, indent=2, ensure_ascii=False)
            )
            
            # Call expert LLM
            response = self.expert.complete(prompt, temperature=0.0)
            
            # Parse review report from response
            review_report = self._parse_review_response(response)
            
            if not isinstance(review_report, dict):
                self._print(f"✗ Invalid review report type: {type(review_report)}")
                return dag, self._create_error_report(f"Invalid review report type: {type(review_report)}")
            
            # Extract problem domain identified by expert
            domain = review_report.get('problem_domain', 'unknown')
            
            # Get corrected DAG from expert review
            corrected_dag = review_report.get('corrected_dag')
            
            if corrected_dag:
                # Validate corrected DAG structure
                if not self._validate_dag_structure(corrected_dag):
                    self._print(f"✗ [{domain}] Corrected DAG has invalid structure, keeping original")
                    return dag, review_report
                
                # Use corrected DAG
                reviewed_dag = corrected_dag
            else:
                # Fallback: no corrected_dag provided, keep original
                self._print(f"⚠️  [{domain}] No corrected DAG provided by expert, keeping original")
                reviewed_dag = dag
            
            # Print summary
            num_issues = len(review_report.get('issues', []))
            num_corrections = len(review_report.get('corrections', []))
            
            if num_corrections > 0:
                self._print(f"✓ [{domain}] Found {num_issues} issues, applied {num_corrections} corrections")
            else:
                self._print(f"✓ [{domain}] No issues found, DAG is correct")
            
            return reviewed_dag, review_report
        
        except Exception as e:
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}"
            self._print(f"✗ Failed: {error_detail}")
            if self.verbose:
                traceback.print_exc()
            return dag, self._create_error_report(error_detail)
    
    def _validate_dag_structure(self, dag: Dict[str, Any]) -> bool:
        """
        Validate that corrected DAG has required structure.
        验证修正后的DAG具有必需的结构
        
        Args:
            dag: DAG to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['target_variable', 'knowns', 'causal_graph', 'computation_plan']
        
        for field in required_fields:
            if field not in dag:
                if self.verbose:
                    print(f"      Missing required field: {field}")
                return False
        
        # Check causal_graph structure
        if not isinstance(dag['causal_graph'], list):
            if self.verbose:
                print(f"      causal_graph must be a list")
            return False
        
        for link in dag['causal_graph']:
            if not isinstance(link, dict):
                return False
            if 'cause' not in link or 'effect' not in link or 'rule' not in link:
                if self.verbose:
                    print(f"      Invalid causal_graph link: {link}")
                return False
        
        # Check computation_plan structure
        if not isinstance(dag['computation_plan'], list):
            if self.verbose:
                print(f"      computation_plan must be a list")
            return False
        
        for step in dag['computation_plan']:
            if not isinstance(step, dict):
                return False
            if 'id' not in step or 'target' not in step or 'inputs' not in step:
                if self.verbose:
                    print(f"      Invalid computation_plan step: {step}")
                return False
        
        return True
    
    def _parse_review_response(self, response: str) -> Dict[str, Any]:
        """Parse expert review response to extract JSON report"""
        import re
        
        # Try multiple parsing strategies
        
        # Strategy 1: Look for JSON code blocks (```json ... ```)
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_block_match:
            try:
                parsed = json.loads(json_block_match.group(1))
                if isinstance(parsed, dict):
                    return self._ensure_required_keys(parsed)
            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"   ⚠️  JSON code block decode error: {e}")
        
        # Strategy 2: Find JSON object with balanced braces
        # This is more robust than greedy matching
        brace_count = 0
        start_pos = -1
        for i, char in enumerate(response):
            if char == '{':
                if start_pos == -1:
                    start_pos = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    # Found a complete JSON object
                    json_str = response[start_pos:i+1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and 'problem_domain' in parsed:
                            return self._ensure_required_keys(parsed)
                    except json.JSONDecodeError:
                        # Continue searching for next JSON object
                        start_pos = -1
                        brace_count = 0
        
        # Strategy 3: Greedy match as fallback
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                if isinstance(parsed, dict):
                    return self._ensure_required_keys(parsed)
            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"   ⚠️  Greedy JSON decode error: {e}")
        
        # Fallback: create empty report
        if self.verbose:
            print(f"   ⚠️  Could not parse expert review, using fallback")
            print(f"   Response preview: {response[:200]}...")
        return {
            'problem_domain': 'unknown',
            'issues': [],
            'corrections': [],
            'overall_assessment': 'Could not parse expert review'
        }
    
    def _ensure_required_keys(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure parsed JSON has all required keys"""
        if 'problem_domain' not in parsed:
            parsed['problem_domain'] = 'unknown'
        if 'issues' not in parsed:
            parsed['issues'] = []
        if 'corrections' not in parsed:
            parsed['corrections'] = []
        if 'overall_assessment' not in parsed:
            parsed['overall_assessment'] = ''
        return parsed
    
    def _apply_corrections(
        self,
        dag: Dict[str, Any],
        corrections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply expert corrections to DAG"""
        if not corrections:
            return dag
        
        reviewed_dag = dag.copy()
        
        for correction in corrections:
            node = correction.get('node')
            corrected = correction.get('corrected')
            
            if node and corrected:
                # Apply correction to relevant part of DAG
                # (simplified implementation - can be enhanced)
                if 'computation_plan' in reviewed_dag:
                    for step in reviewed_dag['computation_plan']:
                        if step.get('target') == node or step.get('id') == node:
                            step['description'] = corrected
        
        return reviewed_dag
    
    def _create_skip_report(self, reason: str) -> Dict[str, Any]:
        """Create a report for skipped review"""
        return {
            'status': 'skipped',
            'reason': reason,
            'issues': [],
            'corrections': [],
            'problem_domain': 'unknown'
        }
    
    def _create_error_report(self, error: str) -> Dict[str, Any]:
        """Create a report for failed review"""
        return {
            'status': 'error',
            'error': error,
            'issues': [],
            'corrections': [],
            'problem_domain': 'unknown'
        }


# Export classes
__all__ = ['DomainExpertReviewer', 'ProblemType']
