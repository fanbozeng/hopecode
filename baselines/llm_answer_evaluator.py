"""
LLM-based Answer Evaluator
基于大语言模型的答案评判器

This module provides intelligent answer evaluation using LLM instead of simple string matching.
该模块使用大语言模型进行智能答案评判，而非简单的字符串匹配。
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from engine.scaffolder import LLMClient


@dataclass
class EvaluationResult:
    """答案评判结果数据类"""
    is_correct: bool
    confidence: float
    reasoning: str
    result_type: str  # "correct", "partially_correct", "incorrect"
    semantic_match: bool = False
    numerical_match: bool = False
    key_differences: list = None
    
    def __post_init__(self):
        if self.key_differences is None:
            self.key_differences = []


class LLMAnswerEvaluator:
    """
    基于LLM的智能答案评判器
    
    使用大语言模型进行语义级别的答案正确性判断，
    支持数学表达式、数值、文本等多种答案类型。
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None, temperature: float = 0.0):
        """
        初始化评判器
        
        Args:
            llm_client: LLM客户端实例，如果为None则创建新实例
            temperature: LLM采样温度，默认0.0以确保确定性
        """
        self.llm_client = llm_client or LLMClient()
        self.temperature = temperature
        self._load_prompt_template()
    
    def _load_prompt_template(self) -> None:
        """加载评判prompt模板"""
        prompt_file = Path(__file__).parent.parent / "prompts" / "answer_evaluation_prompt.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def evaluate(
        self,
        student_answer: Any,
        standard_answer: Any,
        question: str = "",
        fallback_on_error: bool = True
    ) -> EvaluationResult:
        """
        评判学生答案是否正确
        
        Args:
            student_answer: 学生的答案
            standard_answer: 标准答案
            question: 题目内容（可选，提供更多上下文）
            fallback_on_error: 发生错误时是否回退到简单字符串匹配
        
        Returns:
            EvaluationResult: 包含判断结果、置信度和理由的评判结果
        
        Examples:
            >>> evaluator = LLMAnswerEvaluator()
            >>> result = evaluator.evaluate("0.5", "1/2", "What is one half?")
            >>> print(result.is_correct)  # True
            >>> print(result.confidence)  # 0.95
        """
        # 处理None值
        if student_answer is None:
            return EvaluationResult(
                is_correct=False,
                confidence=1.0,
                reasoning="Student answer is None",
                result_type="incorrect"
            )
        
        # 转换为字符串
        student_str = str(student_answer).strip()
        standard_str = str(standard_answer).strip()
        
        # 快速检查：完全相同
        if self._quick_match(student_str, standard_str):
            return EvaluationResult(
                is_correct=True,
                confidence=1.0,
                reasoning="Exact match",
                result_type="correct",
                semantic_match=True,
                numerical_match=True
            )
        
        try:
            # 使用LLM进行评判
            return self._llm_evaluate(student_str, standard_str, question)
        
        except Exception as e:
            if fallback_on_error:
                # 回退到简单匹配
                return self._fallback_evaluate(student_str, standard_str, str(e))
            else:
                raise
    
    def _quick_match(self, student: str, standard: str) -> bool:
        """快速匹配：移除格式后比较"""
        clean_student = self._clean_answer(student)
        clean_standard = self._clean_answer(standard)
        return clean_student == clean_standard
    
    def _clean_answer(self, answer: str) -> str:
        """清理答案：移除空格、$符号、逗号等格式字符"""
        cleaned = answer.lower()
        cleaned = cleaned.replace('$', '').replace(',', '').replace(' ', '')
        cleaned = cleaned.replace('\\', '').replace('{', '').replace('}', '')
        return cleaned
    
    def _llm_evaluate(
        self,
        student_answer: str,
        standard_answer: str,
        question: str
    ) -> EvaluationResult:
        """使用LLM进行评判"""
        # 构建prompt
        prompt = self.prompt_template.format(
            question=question or "N/A",
            standard_answer=standard_answer,
            student_answer=student_answer
        )
        
        # 调用LLM
        response = self.llm_client.complete(prompt, temperature=self.temperature)
        
        # 解析响应
        evaluation_data = self._parse_llm_response(response)
        
        # 转换为EvaluationResult
        is_correct = evaluation_data.get('result') in ['correct', 'partially_correct']
        
        return EvaluationResult(
            is_correct=is_correct,
            confidence=evaluation_data.get('confidence', 0.5),
            reasoning=evaluation_data.get('reasoning', 'No reasoning provided'),
            result_type=evaluation_data.get('result', 'incorrect'),
            semantic_match=evaluation_data.get('semantic_match', False),
            numerical_match=evaluation_data.get('numerical_match', False),
            key_differences=evaluation_data.get('key_differences', [])
        )
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data
            
            # 如果没有找到JSON，尝试其他解析方式
            return self._parse_fallback_response(response)
        
        except json.JSONDecodeError:
            return self._parse_fallback_response(response)
    
    def _parse_fallback_response(self, response: str) -> Dict[str, Any]:
        """回退的响应解析方法"""
        # 简单的关键词检测
        response_lower = response.lower()
        
        if 'correct' in response_lower and 'incorrect' not in response_lower:
            result = 'correct'
            confidence = 0.7
        elif 'partially' in response_lower:
            result = 'partially_correct'
            confidence = 0.6
        else:
            result = 'incorrect'
            confidence = 0.7
        
        return {
            'result': result,
            'confidence': confidence,
            'reasoning': response[:200],
            'semantic_match': 'semantic' in response_lower and 'match' in response_lower,
            'numerical_match': 'numerical' in response_lower and 'match' in response_lower,
            'key_differences': []
        }
    
    def _fallback_evaluate(
        self,
        student_answer: str,
        standard_answer: str,
        error_msg: str
    ) -> EvaluationResult:
        """回退评判方法：使用简单字符串匹配"""
        clean_student = self._clean_answer(student_answer)
        clean_standard = self._clean_answer(standard_answer)
        
        # 检查包含关系
        is_correct = (
            clean_student == clean_standard or
            clean_student in clean_standard or
            clean_standard in clean_student
        )
        
        return EvaluationResult(
            is_correct=is_correct,
            confidence=0.5,  # 低置信度
            reasoning=f"Fallback evaluation due to error: {error_msg}",
            result_type="correct" if is_correct else "incorrect",
            semantic_match=is_correct,
            numerical_match=False
        )
    
    def batch_evaluate(
        self,
        answer_pairs: list[Tuple[Any, Any]],
        questions: list[str] = None
    ) -> list[EvaluationResult]:
        """
        批量评判答案
        
        Args:
            answer_pairs: [(student_answer, standard_answer), ...]
            questions: 对应的题目列表（可选）
        
        Returns:
            评判结果列表
        """
        if questions is None:
            questions = [""] * len(answer_pairs)
        
        results = []
        for i, (student, standard) in enumerate(answer_pairs):
            question = questions[i] if i < len(questions) else ""
            result = self.evaluate(student, standard, question)
            results.append(result)
        
        return results


# 便捷函数
def evaluate_answer(
    student_answer: Any,
    standard_answer: Any,
    question: str = "",
    llm_client: Optional[LLMClient] = None
) -> bool:
    """
    便捷函数：快速评判答案是否正确
    
    Args:
        student_answer: 学生答案
        standard_answer: 标准答案
        question: 题目（可选）
        llm_client: LLM客户端（可选）
    
    Returns:
        布尔值，表示答案是否正确
    """
    evaluator = LLMAnswerEvaluator(llm_client=llm_client)
    result = evaluator.evaluate(student_answer, standard_answer, question)
    return result.is_correct


# 测试代码
if __name__ == "__main__":
    print("="*80)
    print("LLM Answer Evaluator 测试")
    print("="*80)
    
    evaluator = LLMAnswerEvaluator()
    
    # 测试用例
    test_cases = [
        ("0.5", "1/2", "What is one half?"),
        ("42", "42.0", "What is the answer?"),
        ("2022.2", "$2022.2$", "Calculate the density"),
        ("The answer is 5", "5", "Solve for x"),
        ("incorrect", "correct", "Test wrong answer"),
    ]
    
    print("\n测试结果:")
    print("-"*80)
    
    for student, standard, question in test_cases:
        result = evaluator.evaluate(student, standard, question)
        print(f"\n问题: {question}")
        print(f"学生答案: {student}")
        print(f"标准答案: {standard}")
        print(f"判断结果: {'✓ 正确' if result.is_correct else '✗ 错误'}")
        print(f"置信度: {result.confidence:.2f}")
        print(f"理由: {result.reasoning[:100]}...")
    
    print("\n" + "="*80)
    print("测试完成！")