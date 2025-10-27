"""
Knowledge Retriever Module
知识检索模块

This module implements the RAG (Retrieval-Augmented Generation) component
that uses AI to generate relevant formulas, principles, and domain knowledge
to support problem-solving.

本模块实现了RAG（检索增强生成）组件，使用AI生成相关的公式、原理
和领域知识来支持问题求解。
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass


@dataclass
class KnowledgeEntry:
    """
    Data structure for a knowledge base entry.
    知识库条目的数据结构
    
    Attributes:
        keywords: List of keywords that trigger this entry
                  触发此条目的关键词列表
        rule: The formula or principle description
              公式或原理的描述
        category: Optional category for organization
                  可选的分类标签，用于组织
    """
    keywords: List[str]
    rule: str
    category: Optional[str] = None


class KnowledgeRetriever:
    """
    Knowledge Retrieval System using keyword matching.
    使用关键词匹配的知识检索系统
    
    This class manages a knowledge base and retrieves relevant entries
    based on keyword extraction from problem text.
    
    此类管理知识库，并基于从问题文本中提取的关键词检索相关条目。
    """

    def __init__(self, knowledge_base_path: str = "data/knowledge.json"):
        """
        Initialize the knowledge retriever.
        初始化知识检索器
        
        Args:
            knowledge_base_path: Path to the JSON knowledge base file
                                 JSON知识库文件的路径
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_entries: List[KnowledgeEntry] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """
        Load the knowledge base from a JSON file.
        从JSON文件加载知识库
        
        Raises:
            FileNotFoundError: If knowledge base file doesn't exist
                               如果知识库文件不存在
            json.JSONDecodeError: If JSON format is invalid
                                   如果JSON格式无效
        """
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base file not found: {self.knowledge_base_path}\n"
                f"知识库文件未找到: {self.knowledge_base_path}"
            )

        with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert JSON data to KnowledgeEntry objects
        # 将JSON数据转换为KnowledgeEntry对象
        self.knowledge_entries = [
            KnowledgeEntry(
                keywords=entry.get("keywords", []),
                rule=entry.get("rule", ""),
                category=entry.get("category")
            )
            for entry in data
        ]

        print(f"Loaded {len(self.knowledge_entries)} knowledge entries.")
        print(f"已加载 {len(self.knowledge_entries)} 个知识条目")

    def extract_keywords(self, problem_text: str) -> Set[str]:
        """
        Extract potential keywords from problem text.
        从问题文本中提取潜在关键词
        
        This method uses regex and word boundary detection to extract
        meaningful technical terms from the problem description, with
        comprehensive stopword filtering.
        
        此方法使用正则表达式和词边界检测从问题描述中提取有意义的技术术语，
        并进行全面的停用词过滤。
        
        Args:
            problem_text: The problem statement in natural language
                          自然语言的问题陈述
        
        Returns:
            A set of extracted keywords (lowercase)
            提取的关键词集合（小写）
        """
        # Use comprehensive stopwords database
        # 使用全面的停用词数据库
        from .stopwords import get_all_stopwords

        # Convert to lowercase for case-insensitive matching
        # 转换为小写以进行不区分大小写的匹配
        text_lower = problem_text.lower()

        # Extract words (alphanumeric sequences)
        # 提取单词（字母数字序列）
        words = re.findall(r'\b[a-z]+\b', text_lower)

        # Get comprehensive stopwords (1354 words: 807 English + 547 Chinese)
        # 获取全面的停用词（1354个词：807个英文 + 547个中文）
        stop_words = get_all_stopwords()

        # Filter out stop words and single characters
        # 过滤掉停用词和单个字符
        keywords = {
            word for word in words
            if word not in stop_words and len(word) > 1
        }

        return keywords

    def retrieve_knowledge(
        self,
        problem_text: str,
        min_overlap: int = 1,
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        Retrieve relevant knowledge entries based on problem text.
        根据问题文本检索相关的知识条目
        
        This method extracts keywords from the problem and finds all
        knowledge entries that share at least 'min_overlap' keywords.
        
        此方法从问题中提取关键词，并找到所有至少共享'min_overlap'个关键词的
        知识条目。
        
        Args:
            problem_text: The problem statement
                          问题陈述
            min_overlap: Minimum number of matching keywords required
                         所需的最小匹配关键词数量
            max_results: Maximum number of results to return (None for all)
                         返回的最大结果数（None表示全部）
        
        Returns:
            List of relevant rule descriptions
            相关规则描述的列表
        """
        # Extract keywords from problem
        # 从问题中提取关键词
        problem_keywords = self.extract_keywords(problem_text)

        if not problem_keywords:
            print("Warning: No keywords extracted from problem text.")
            print("警告：未从问题文本中提取到关键词")
            return []

        # Find matching entries with overlap count
        # 找到匹配的条目及其重叠计数
        matches: List[tuple[KnowledgeEntry, int]] = []

        for entry in self.knowledge_entries:
            # Convert entry keywords to lowercase set
            # 将条目关键词转换为小写集合
            entry_keywords = {kw.lower() for kw in entry.keywords}

            # Calculate overlap
            # 计算重叠数
            overlap = len(problem_keywords & entry_keywords)

            if overlap >= min_overlap:
                matches.append((entry, overlap))

        # Sort by overlap count (descending)
        # 按重叠计数排序（降序）
        matches.sort(key=lambda x: x[1], reverse=True)

        # Apply max_results limit if specified
        # 如果指定，应用max_results限制
        if max_results is not None:
            matches = matches[:max_results]

        # Extract rule strings
        # 提取规则字符串
        retrieved_rules = [entry.rule for entry, _ in matches]

        print(f"Retrieved {len(retrieved_rules)} relevant rules.")
        print(f"检索到 {len(retrieved_rules)} 条相关规则")

        return retrieved_rules

    def get_knowledge(self, problem_text: str) -> List[str]:
        """
        Main interface for knowledge retrieval (used by main orchestrator).
        知识检索的主接口（由主协调器使用）
        
        Args:
            problem_text: The problem statement
                          问题陈述
        
        Returns:
            List of relevant rule descriptions
            相关规则描述的列表
        """
        return self.retrieve_knowledge(problem_text, min_overlap=1, max_results=None)

    def add_knowledge(
        self,
        keywords: List[str],
        rule: str,
        category: Optional[str] = None
    ) -> None:
        """
        Add a new knowledge entry dynamically.
        动态添加新的知识条目
        
        Args:
            keywords: List of keywords for this entry
                      此条目的关键词列表
            rule: The rule or formula description
                  规则或公式描述
            category: Optional category label
                      可选的分类标签
        """
        new_entry = KnowledgeEntry(
            keywords=keywords,
            rule=rule,
            category=category
        )
        self.knowledge_entries.append(new_entry)
        print(f"Added new knowledge entry with {len(keywords)} keywords.")
        print(f"已添加包含 {len(keywords)} 个关键词的新知识条目")

    def save_knowledge_base(self) -> None:
        """
        Save the current knowledge base back to the JSON file.
        将当前知识库保存回JSON文件
        """
        data = [
            {
                "keywords": entry.keywords,
                "rule": entry.rule,
                "category": entry.category
            }
            for entry in self.knowledge_entries
        ]

        with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Knowledge base saved to {self.knowledge_base_path}")
        print(f"知识库已保存到 {self.knowledge_base_path}")


# Example usage / 使用示例
if __name__ == "__main__":
    # Initialize retriever / 初始化检索器
    retriever = KnowledgeRetriever("data/knowledge_base.json")

    # Test problem / 测试问题
    test_problem = """
    An object with a mass of 10 kg is initially at rest.
    A constant force of 50 Newtons is applied to it for 5 seconds.
    What is its final velocity?
    """

    # Retrieve knowledge / 检索知识
    rules = retriever.get_knowledge(test_problem)

    print("\n--- Retrieved Rules ---")
    for i, rule in enumerate(rules, 1):
        print(f"{i}. {rule}")
