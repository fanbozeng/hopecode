"""
Baseline Methods for Comparison


This package contains various baseline methods for evaluating the framework:
- Direct LLM: 
- Zero-shot CoT: 
- Few-shot CoT: 
- Answer Extractor: 


"""

from .direct_llm import DirectLLM
from .zero_shot_cot import ZeroShotCoT
from .few_shot_cot import FewShotCoT
from .answer_extractor import extract_answer, clean_markdown, extract_number, normalize_answer

__all__ = [
    "DirectLLM",
    "ZeroShotCoT",
    "FewShotCoT",
    "extract_answer",
    "clean_markdown",
    "extract_number",
    "normalize_answer",
]
