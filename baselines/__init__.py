"""
Baseline Methods for Comparison


This package contains various baseline methods for evaluating the framework:
- Direct LLM: 
- Zero-shot CoT: 
- Few-shot CoT: 
- Answer Extractor: 
- Prompt Loader: 统一的prompt加载和管理


"""

from .direct_llm import DirectLLM
from .zero_shot_cot import ZeroShotCoT
from .few_shot_cot import FewShotCoT
from .answer_extractor import extract_answer, clean_markdown, extract_number, normalize_answer
from .prompt_loader import (
    PromptLoader,
    StructuredAnswerExtractor,
    extract_structured_answer,
    extract_structured_reasoning,
    extract_structured_both
)

__all__ = [
    "DirectLLM",
    "ZeroShotCoT",
    "FewShotCoT",
    "extract_answer",
    "clean_markdown",
    "extract_number",
    "normalize_answer",
    "PromptLoader",
    "StructuredAnswerExtractor",
    "extract_structured_answer",
    "extract_structured_reasoning",
    "extract_structured_both",
]
