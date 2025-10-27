"""
Causal Reasoning Engine Package
因果推理引擎包

This package implements a hybrid causal reasoning system that combines
Large Language Models (LLMs) with symbolic computation for solving
mathematical and physics problems.

本包实现了一个混合因果推理系统，结合了大语言模型（LLM）的语义理解能力
和符号计算的精确性，用于解决数学和物理问题。
"""

__version__ = "1.0.1"
__author__ = "Your Name"

from .retriever import KnowledgeRetriever
from .ai_retriever import AIKnowledgeRetriever
from .vector_retriever import VectorKnowledgeRetriever
from .scaffolder import CausalScaffolder
from .executor import SymbolicExecutor
from .synthesizer import CausalSynthesizer
from .llm_computer import LLMComputer
from .grpo_experience_manager import GRPOExperienceManager
from .grpo_trainer import TrainingFreeGRPOTrainer

__all__ = [
    "KnowledgeRetriever",
    "AIKnowledgeRetriever",
    "VectorKnowledgeRetriever",
    "CausalScaffolder",
    "SymbolicExecutor",
    "CausalSynthesizer",
    "LLMComputer",
    "GRPOExperienceManager",
    "TrainingFreeGRPOTrainer",
]
