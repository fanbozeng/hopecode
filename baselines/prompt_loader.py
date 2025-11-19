"""
Prompt Loader and Answer Extractor for Baseline Methods
基线方法的Prompt加载器和答案提取器

This module provides:
1. Load prompts from files
2. Extract answers from \answerbox{}
3. Extract reasoning from \reasoningbox{}
"""

import re
from pathlib import Path
from typing import Dict, Tuple, Optional


class PromptLoader:
    """加载和管理prompt文件"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._prompt_cache = {}
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        加载prompt文件
        
        Args:
            prompt_name: prompt文件名（不含.txt后缀）
        
        Returns:
            Prompt内容
        """
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._prompt_cache[prompt_name] = content
        return content
    
    def format_direct_llm_prompt(self, problem: str) -> str:
        """格式化Direct LLM prompt"""
        template = self.load_prompt("direct_llm_prompt")
        return template.format(problem=problem)
    
    def format_zero_shot_cot_prompt(self, problem: str) -> str:
        """格式化Zero-Shot CoT prompt"""
        template = self.load_prompt("zero_shot_cot_prompt")
        return template.format(problem=problem)
    
    def format_few_shot_cot_prompt(self, problem: str) -> str:
        """格式化Few-Shot CoT prompt"""
        # 加载examples
        examples = self.load_prompt("few_shot_examples")
        # 加载template
        template = self.load_prompt("few_shot_cot_prompt")
        return template.format(examples=examples, problem=problem)


class StructuredAnswerExtractor:
    """从结构化输出中提取答案和推理过程"""
    
    @staticmethod
    def extract_answer(response: str) -> Optional[str]:
        """
        从 \answerbox{} 中提取答案
        
        Args:
            response: LLM响应
        
        Returns:
            提取的答案，如果没找到返回None
        """
        # 尝试匹配 \answerbox{...}，使用平衡括号匹配
        answer = StructuredAnswerExtractor._extract_latex_box(response, 'answerbox')
        if answer:
            return answer
        
        # 回退：尝试旧的提取方法
        return StructuredAnswerExtractor._fallback_extract(response)
    
    @staticmethod
    def extract_reasoning(response: str) -> Optional[str]:
        """
        从 \reasoningbox{} 中提取推理过程
        
        Args:
            response: LLM响应
        
        Returns:
            提取的推理过程，如果没找到返回None
        """
        # 尝试匹配 \reasoningbox{...}，使用平衡括号匹配
        reasoning = StructuredAnswerExtractor._extract_latex_box(response, 'reasoningbox')
        if reasoning:
            return reasoning
        
        # 回退：返回整个response（去除answerbox部分）
        # 使用平衡括号匹配来移除answerbox
        cleaned = StructuredAnswerExtractor._remove_latex_box(response, 'answerbox')
        return cleaned.strip() if cleaned else response.strip()
    
    @staticmethod
    def extract_both(response: str) -> Tuple[Optional[str], Optional[str]]:
        """
        同时提取推理过程和答案
        
        Args:
            response: LLM响应
        
        Returns:
            Tuple of (reasoning, answer)
        """
        reasoning = StructuredAnswerExtractor.extract_reasoning(response)
        answer = StructuredAnswerExtractor.extract_answer(response)
        return reasoning, answer
    
    @staticmethod
    def _extract_latex_box(text: str, box_name: str) -> Optional[str]:
        """
        提取LaTeX box内容，支持嵌套的大括号
        
        Args:
            text: 文本内容
            box_name: box名称（如 'answerbox', 'reasoningbox'）
            
        Returns:
            提取的内容，如果没找到返回None
        """
        # 查找 \boxname{ 的位置
        pattern = rf'\\{box_name}\s*\{{'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if not match:
            return None
        
        # 从匹配位置开始，手动匹配平衡的大括号
        start = match.end()
        brace_count = 1
        i = start
        
        while i < len(text) and brace_count > 0:
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
            i += 1
        
        if brace_count == 0:
            # 找到了匹配的闭合括号
            content = text[start:i-1]
            return content.strip()
        
        return None
    
    @staticmethod
    def _remove_latex_box(text: str, box_name: str) -> str:
        """
        从文本中移除LaTeX box
        
        Args:
            text: 文本内容
            box_name: box名称
            
        Returns:
            移除box后的文本
        """
        # 查找 \boxname{ 的位置
        pattern = rf'\\{box_name}\s*\{{'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if not match:
            return text
        
        # 从匹配位置开始，手动匹配平衡的大括号
        box_start = match.start()
        start = match.end()
        brace_count = 1
        i = start
        
        while i < len(text) and brace_count > 0:
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
            i += 1
        
        if brace_count == 0:
            # 移除整个box
            return text[:box_start] + text[i:]
        
        return text
    
    @staticmethod
    def _fallback_extract(response: str) -> Optional[str]:
        """
        回退的答案提取方法（兼容旧格式）
        """
        # 尝试常见的答案模式
        patterns = [
            r'Final answer:\s*(.+?)(?:\n|$)',
            r'The final answer is\s*(.+?)(?:\n|$)',
            r'Therefore, the answer is\s*(.+?)(?:\n|$)',
            r'Answer:\s*(.+?)(?:\n|$)',
            r'####\s*(.+?)(?:\n|$)',  # GSM8K格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 最后尝试：返回最后一行非空内容
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            return lines[-1]
        
        return None


# 便捷函数
def load_prompt(prompt_name: str) -> str:
    """便捷函数：加载prompt"""
    loader = PromptLoader()
    return loader.load_prompt(prompt_name)


def extract_structured_answer(response: str) -> Optional[str]:
    """便捷函数：提取答案"""
    return StructuredAnswerExtractor.extract_answer(response)


def extract_structured_reasoning(response: str) -> Optional[str]:
    """便捷函数：提取推理"""
    return StructuredAnswerExtractor.extract_reasoning(response)


def extract_structured_both(response: str) -> Tuple[Optional[str], Optional[str]]:
    """便捷函数：同时提取答案和推理"""
    return StructuredAnswerExtractor.extract_both(response)


# 测试
if __name__ == "__main__":
    # 测试prompt加载
    loader = PromptLoader()
    
    print("="*60)
    print("Testing Prompt Loader")
    print("="*60)
    
    # 测试Direct LLM
    prompt = loader.format_direct_llm_prompt("What is 2 + 2?")
    print("\nDirect LLM Prompt:")
    print(prompt[:200] + "...")
    
    # 测试Zero-Shot CoT
    prompt = loader.format_zero_shot_cot_prompt("What is 2 + 2?")
    print("\nZero-Shot CoT Prompt:")
    print(prompt[:200] + "...")
    
    # 测试Few-Shot CoT
    prompt = loader.format_few_shot_cot_prompt("What is 2 + 2?")
    print("\nFew-Shot CoT Prompt:")
    print(prompt[:200] + "...")
    
    print("\n" + "="*60)
    print("Testing Answer Extractor")
    print("="*60)
    
    # 测试答案提取
    test_response = """
\\reasoningbox{
Step 1: We need to add 2 and 2
Step 2: 2 + 2 = 4
}

\\answerbox{
4
}
"""
    
    answer, reasoning = StructuredAnswerExtractor.extract_both(test_response)
    print(f"\nExtracted Answer: {answer}")
    print(f"Extracted Reasoning: {reasoning[:100]}...")
    
    print("\n✅ All tests passed!")

