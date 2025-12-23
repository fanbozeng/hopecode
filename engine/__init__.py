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
# from .executor import SymbolicExecutor  # Removed: never used (zombie code)
# from .synthesizer import CausalSynthesizer  # Removed: synthesis/validation not needed
from .llm_computer import LLMComputer
from .grpo_experience_manager import GRPOExperienceManager
from .grpo_trainer import TrainingFreeGRPOTrainer
from .api_manager import APIKeyManager
# Step2 Enhancement modules
from .domain_expert_reviewer import DomainExpertReviewer, ProblemType
from .rag_knowledge_enhancer import RAGKnowledgeEnhancer
from .causal_structure_optimizer import CausalStructureOptimizer
from .dag_enhancement_pipeline import DAGEnhancementPipeline

__all__ = [
    "KnowledgeRetriever",
    "AIKnowledgeRetriever",
    "VectorKnowledgeRetriever",
    "CausalScaffolder",
    # "SymbolicExecutor",  # Removed: zombie code
    # "CausalSynthesizer",  # Removed
    "LLMComputer",
    "GRPOExperienceManager",
    "TrainingFreeGRPOTrainer",
    "APIKeyManager",
    # Step2 Enhancement
    "DomainExpertReviewer",
    "ProblemType",
    "RAGKnowledgeEnhancer",
    "CausalStructureOptimizer",
    "DAGEnhancementPipeline",
]
