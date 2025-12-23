"""
DAG Converter - Convert reasoning to Causal DAG structure
DAG转换器 - 将推理过程转换为因果DAG结构

This module provides a unified DAG conversion utility that can be shared
across all baseline methods (Direct LLM, Zero-Shot CoT, Few-Shot CoT, etc.)
"""

import json
import re
from typing import Dict, Any, Optional


class DAGConverter:
    """
    Unified DAG Converter for all baseline methods
    统一的DAG转换器，供所有基线方法使用
    """
    
    def __init__(self, llm_client=None, temperature: float = 0.0):
        """
        Initialize DAG Converter
        
        Args:
            llm_client: LLM client for DAG generation
            temperature: Temperature for LLM sampling
        """
        self.llm_client = llm_client
        self.temperature = temperature
    
    def convert_to_dag(
        self, 
        problem: str, 
        reasoning: str, 
        answer: str
    ) -> Dict[str, Any]:
        """
        Convert reasoning to causal DAG structure.
        将推理过程转换为因果DAG结构
        
        Args:
            problem: Problem statement
            reasoning: Reasoning process
            answer: Final answer
            
        Returns:
            Causal DAG dictionary with structure:
            {
                "target_variable": str,
                "expected_answer_type": str,
                "knowns": dict,
                "causal_graph": list,
                "computation_plan": list
            }
        """
        # 如果没有推理过程，返回空DAG
        if not reasoning:
            return self._create_empty_dag()
        
        # 如果没有LLM客户端，返回空DAG
        if not self.llm_client:
            return self._create_empty_dag()
        
        # 构建DAG转换prompt
        causal_prompt = self._build_dag_prompt(problem, reasoning, answer)
        
        try:
            # 调用LLM生成DAG
            response = self.llm_client.complete(
                causal_prompt, 
                temperature=self.temperature
            )
            
            # 解析响应
            dag = self._parse_dag_response(response)
            
            # 如果解析失败，返回空DAG
            return dag if dag else self._create_empty_dag()
            
        except Exception as e:
            # 出错时返回空DAG
            print(f"Warning: DAG conversion failed: {e}")
            return self._create_empty_dag()
    
    def _build_dag_prompt(
        self, 
        problem: str, 
        reasoning: str, 
        answer: str
    ) -> str:
        """
        Build prompt for DAG conversion
        构建DAG转换prompt
        """
        return f"""**IMPORTANT**: Convert the reasoning into a causal DAG structure.

Problem: {problem}
Reasoning: {reasoning}
Final Answer: {answer}

**Instructions**:
1. Extract causal relationships from the reasoning
2. Preserve computation sequence
3. Only extract explicitly stated information

Output JSON structure:
{{
  "target_variable": "final quantity",
  "expected_answer_type": "Numerical|Expression|Tuple|...",
  "knowns": {{"variable": "value"}},
  "causal_graph": [{{"cause": ["input"], "effect": "output", "rule": "explanation"}}],
  "computation_plan": [{{"id": "step1", "target": "var", "inputs": ["input"], "description": "..."}}]
}}

Respond with valid JSON only:"""
    
    def _parse_dag_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse DAG from LLM response
        从LLM响应中解析DAG
        
        Args:
            response: LLM response string
            
        Returns:
            Parsed DAG dictionary or None if parsing fails
        """
        try:
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                dag = json.loads(json_match.group(0))
                return self._validate_dag(dag)
            return None
        except json.JSONDecodeError:
            return None
        except Exception:
            return None
    
    def _validate_dag(self, dag: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate DAG structure
        验证DAG结构
        
        Args:
            dag: DAG dictionary to validate
            
        Returns:
            Validated DAG or None if invalid
        """
        # 检查必需字段
        required_fields = [
            "target_variable",
            "expected_answer_type",
            "knowns",
            "causal_graph",
            "computation_plan"
        ]
        
        for field in required_fields:
            if field not in dag:
                return None
        
        return dag
    
    def _create_empty_dag(self) -> Dict[str, Any]:
        """
        Create empty DAG structure
        创建空DAG结构
        
        Returns:
            Empty DAG with default values
        """
        return {
            "target_variable": "result",
            "expected_answer_type": "Numerical",
            "knowns": {},
            "causal_graph": [],
            "computation_plan": []
        }


# 便捷函数 - Convenience function
def convert_to_dag(
    problem: str,
    reasoning: str,
    answer: str,
    llm_client=None,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Convert reasoning to DAG - standalone function
    将推理转换为DAG - 独立函数
    
    Args:
        problem: Problem statement
        reasoning: Reasoning process
        answer: Final answer
        llm_client: LLM client (optional)
        temperature: Temperature for LLM (default: 0.0)
        
    Returns:
        Causal DAG dictionary
    """
    converter = DAGConverter(llm_client=llm_client, temperature=temperature)
    return converter.convert_to_dag(problem, reasoning, answer)