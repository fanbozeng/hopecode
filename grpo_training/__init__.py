"""
GRPO Training Module
GRPO训练模块

This module contains all the independent training scripts for:
- Generator 1, 2, 3: Independent Generator training
- Critic: Critic fusion and training
- Experience Extractor: Universal experience extraction logic

此模块包含所有独立的训练脚本：
- Generator 1, 2, 3：独立的Generator训练
- Critic：Critic融合和训练
- Experience Extractor：通用经验提炼逻辑
"""

from .experience_extractor import ExperienceExtractor

__all__ = ['ExperienceExtractor']

