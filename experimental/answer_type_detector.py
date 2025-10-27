"""
Answer Type Detection Module
答案类型检测模块

This module analyzes a problem and determines the expected answer type
to guide the scaffolding and code generation process.

本模块分析问题并确定预期的答案类型，以指导脚手架和代码生成过程。
"""

import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from .scaffolder import LLMClient


class AnswerTypeDetector:
    """
    Detects the expected answer type for a given problem.
    检测给定问题的预期答案类型
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_path: str = "prompts/answer_type_detection_prompt.txt"
    ):
        """
        Initialize the answer type detector.
        初始化答案类型检测器

        Args:
            llm_client: LLM client instance
            prompt_path: Path to the detection prompt template
        """
        self.llm_client = llm_client or LLMClient()
        self.prompt_path = Path(prompt_path)
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load the prompt template."""
        if self.prompt_path.exists():
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Get default prompt if file doesn't exist."""
        return """Analyze this problem and determine the answer type.
        
Problem: {problem_text}

Return JSON with: primary_answer_type, secondary_answer_types, is_multiple_answer, reasoning, output_format_hint
"""

    def detect(self, problem_text: str) -> Dict[str, Any]:
        """
        Detect the answer type for a problem.
        检测问题的答案类型

        Args:
            problem_text: The problem statement

        Returns:
            Dictionary with answer type information
        """
        print("Detecting answer type...")
        print("检测答案类型...")

        # Quick heuristic detection (fast path)
        # 快速启发式检测（快速路径）
        heuristic_result = self._heuristic_detection(problem_text)
        
        # Use LLM for more accurate detection if needed
        # 如果需要，使用LLM进行更准确的检测
        if heuristic_result.get('confidence', 0) < 0.8:
            try:
                llm_result = self._llm_detection(problem_text)
                if llm_result:
                    print(f"  Detected type: {llm_result.get('primary_answer_type')}")
                    print(f"  检测类型: {llm_result.get('primary_answer_type')}")
                    return llm_result
            except Exception as e:
                print(f"  LLM detection failed, using heuristics: {e}")
                print(f"  LLM检测失败，使用启发式: {e}")

        print(f"  Detected type (heuristic): {heuristic_result.get('primary_answer_type')}")
        print(f"  检测类型（启发式）: {heuristic_result.get('primary_answer_type')}")
        return heuristic_result

    def _heuristic_detection(self, problem_text: str) -> Dict[str, Any]:
        """
        Fast heuristic-based detection.
        基于启发式的快速检测
        """
        text_lower = problem_text.lower()
        
        # Check for interval/range keywords
        # 检查区间/范围关键词
        interval_keywords = [
            'range', 'interval', 'between', 'from', 'to',
            '范围', '区间', '之间', '从', '到'
        ]
        if any(kw in text_lower for kw in interval_keywords):
            return {
                'primary_answer_type': 'Interval',
                'secondary_answer_types': [],
                'is_multiple_answer': False,
                'reasoning': 'Keywords suggest range/interval answer',
                'output_format_hint': 'Calculate boundaries, print((min_val, max_val))',
                'confidence': 0.85
            }

        # Check for tuple/coordinate keywords
        # 检查元组/坐标关键词
        tuple_keywords = [
            'in the form', 'coordinates', 'polar', 'pair',
            '坐标', '形式', '极坐标'
        ]
        if any(kw in text_lower for kw in tuple_keywords):
            return {
                'primary_answer_type': 'Tuple',
                'secondary_answer_types': ['Expression'],
                'is_multiple_answer': False,
                'reasoning': 'Keywords suggest coordinate/tuple answer',
                'output_format_hint': 'print((val1, val2))',
                'confidence': 0.9
            }

        # Check for symbolic expression keywords
        # 检查符号表达式关键词
        expression_keywords = [
            'express in terms of', 'symbolic', 'exact form', 'in terms of',
            '用.*表示', '符号', '表达式'
        ]
        if any(kw in text_lower for kw in expression_keywords):
            return {
                'primary_answer_type': 'Expression',
                'secondary_answer_types': [],
                'is_multiple_answer': False,
                'reasoning': 'Keywords suggest symbolic expression',
                'output_format_hint': 'print(result)  # Keep symbols',
                'confidence': 0.9
            }

        # Default to Numerical
        # 默认为数值型
        return {
            'primary_answer_type': 'Numerical',
            'secondary_answer_types': [],
            'is_multiple_answer': False,
            'reasoning': 'No specific keywords, assuming numerical answer',
            'output_format_hint': 'print(float(result))',
            'confidence': 0.6
        }

    def _llm_detection(self, problem_text: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM for accurate detection.
        使用LLM进行准确检测
        """
        prompt = self.prompt_template.format(problem_text=problem_text)

        try:
            response = self.llm_client.complete(prompt, temperature=0.0)
            result = self._extract_json(response)
            if result:
                result['confidence'] = 1.0
                return result
        except Exception as e:
            print(f"Error in LLM detection: {e}")

        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        # Try to find JSON code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


# Example usage
if __name__ == "__main__":
    detector = AnswerTypeDetector()
    
    test_problems = [
        "What is 3 + 5?",
        "Express the velocity in terms of acceleration a and time t.",
        "Convert (0, 3) to polar coordinates in the form (r, θ).",
        "Find the range of positions where the insect can land."
    ]
    
    for problem in test_problems:
        print(f"\nProblem: {problem}")
        result = detector.detect(problem)
        print(f"Type: {result['primary_answer_type']}")
        print(f"Hint: {result['output_format_hint']}")


