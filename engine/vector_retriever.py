"""
Vector-based Knowledge Retriever Module
基于向量的知识检索模块

This module implements true RAG (Retrieval-Augmented Generation) using
semantic similarity search with sentence embeddings instead of keyword matching.

本模块使用句子嵌入的语义相似度搜索实现真正的RAG（检索增强生成），
而不是关键词匹配。
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pickle


@dataclass
class VectorKnowledgeEntry:
    """
    Data structure for a vector-based knowledge entry.
    基于向量的知识条目数据结构
    
    Attributes:
        rule: The formula or principle description
              公式或原理的描述
        category: Optional category for organization
                  可选的分类标签
        embedding: The vector embedding of the rule
                   规则的向量嵌入
    """
    rule: str
    category: Optional[str] = None
    embedding: Optional[np.ndarray] = None


class VectorKnowledgeRetriever:
    """
    Vector-based Knowledge Retrieval System using semantic similarity.
    基于向量的知识检索系统，使用语义相似度
    
    This class uses sentence embeddings to find semantically similar
    knowledge entries rather than relying on keyword matching.
    
    此类使用句子嵌入来找到语义相似的知识条目，而不是依赖关键词匹配。
    """

    def __init__(
        self,
        knowledge_base_path: str = "data/knowledge_base.json",
        model_name: str = "all-MiniLM-L6-v2",
        cache_path: Optional[str] = "data/knowledge_embeddings.pkl",
        use_cache: bool = True
    ):
        """
        Initialize the vector-based knowledge retriever.
        初始化基于向量的知识检索器
        
        Args:
            knowledge_base_path: Path to the JSON knowledge base file
                                 JSON知识库文件的路径
            model_name: Name or path of the sentence transformer model
                        句子转换器模型的名称或路径
            cache_path: Path to cache embeddings (None to disable caching)
                       缓存嵌入的路径（None表示禁用缓存）
            use_cache: Whether to use cached embeddings
                      是否使用缓存的嵌入
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.cache_path = Path(cache_path) if cache_path else None
        self.use_cache = use_cache
        
        # Initialize sentence transformer model
        print(f"Loading sentence transformer model: {model_name}")
        print(f"正在加载句子转换器模型: {model_name}")
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # Check if local model exists
            model_path = Path(model_name)
            if model_path.exists():
                self.model = SentenceTransformer(str(model_path))
                print(f"✓ Loaded local model from: {model_path}")
            else:
                self.model = SentenceTransformer(model_name)
                print(f"✓ Loaded model from HuggingFace: {model_name}")
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Please install: pip install sentence-transformers")
            raise
        
        self.knowledge_entries: List[VectorKnowledgeEntry] = []
        self.embeddings_matrix: Optional[np.ndarray] = None
        
        # Load knowledge base and compute embeddings
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """
        Load the knowledge base and compute/load embeddings.
        加载知识库并计算/加载嵌入
        """
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base file not found: {self.knowledge_base_path}\n"
                f"知识库文件未找到: {self.knowledge_base_path}"
            )

        # Load JSON data
        with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} knowledge entries from JSON")
        print(f"从JSON加载了 {len(data)} 个知识条目")
        
        # Handle empty knowledge base
        # 处理空知识库
        if len(data) == 0:
            print("⚠️ Warning: Knowledge base is empty!")
            print("⚠️ 警告：知识库为空！")
            print("   Please add some rules to the knowledge base or use AI retriever.")
            print("   请向知识库添加规则或使用AI检索器。")
            self.knowledge_entries = []
            self.embeddings_matrix = None
            return

        # Check if we can use cached embeddings
        if self.use_cache and self.cache_path and self.cache_path.exists():
            print(f"Loading cached embeddings from: {self.cache_path}")
            print(f"从缓存加载嵌入: {self.cache_path}")
            
            try:
                with open(self.cache_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Verify cache validity
                if len(cache_data['entries']) == len(data):
                    self.knowledge_entries = cache_data['entries']
                    self.embeddings_matrix = cache_data['embeddings']
                    print("✓ Successfully loaded cached embeddings")
                    print("✓ 成功加载缓存的嵌入")
                    return
                else:
                    print("⚠ Cache size mismatch, recomputing embeddings")
                    print("⚠ 缓存大小不匹配，重新计算嵌入")
            except Exception as e:
                print(f"⚠ Failed to load cache: {e}")
                print(f"⚠ 加载缓存失败: {e}")

        # Compute embeddings from scratch
        print("Computing embeddings for all knowledge entries...")
        print("正在为所有知识条目计算嵌入...")
        
        rules = []
        for entry in data:
            rule_text = entry.get("rule", "")
            category = entry.get("category")
            
            self.knowledge_entries.append(VectorKnowledgeEntry(
                rule=rule_text,
                category=category,
                embedding=None  # Will be filled after batch encoding
            ))
            rules.append(rule_text)
        
        # Batch encode all rules
        embeddings = self.model.encode(
            rules,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=32
        )
        
        # Ensure embeddings is 2D (n_samples, n_features)
        # 确保embeddings是2维的 (样本数, 特征数)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Store embeddings
        self.embeddings_matrix = embeddings
        for i, entry in enumerate(self.knowledge_entries):
            entry.embedding = embeddings[i]
        
        print(f"✓ Computed embeddings with shape: {embeddings.shape}")
        print(f"✓ 计算完成，嵌入形状: {embeddings.shape}")
        
        # Cache embeddings
        if self.cache_path:
            self._cache_embeddings()

    def _cache_embeddings(self) -> None:
        """
        Cache embeddings to disk for faster loading.
        将嵌入缓存到磁盘以加快加载速度
        """
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'entries': self.knowledge_entries,
                'embeddings': self.embeddings_matrix
            }
            
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"✓ Cached embeddings to: {self.cache_path}")
            print(f"✓ 嵌入已缓存到: {self.cache_path}")
        except Exception as e:
            print(f"⚠ Failed to cache embeddings: {e}")
            print(f"⚠ 缓存嵌入失败: {e}")

    def _compute_similarity(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Compute cosine similarity between query and all knowledge entries.
        计算查询与所有知识条目之间的余弦相似度
        
        Args:
            query_embedding: The query vector
                            查询向量
            top_k: Number of top results to return
                   返回的顶部结果数量
        
        Returns:
            List of (index, similarity_score) tuples
            (索引, 相似度分数)元组列表
        """
        # Check if knowledge base is empty
        # 检查知识库是否为空
        if self.embeddings_matrix is None or len(self.knowledge_entries) == 0:
            print("⚠️ Warning: Knowledge base is empty, no results to return")
            print("⚠️ 警告：知识库为空，无结果返回")
            return []
        
        # Ensure embeddings_matrix is 2D
        # 确保embeddings_matrix是2维的
        if self.embeddings_matrix.ndim == 1:
            # Single entry, reshape to (1, n)
            # 单条数据，重塑为(1, n)
            embeddings_2d = self.embeddings_matrix.reshape(1, -1)
        else:
            embeddings_2d = self.embeddings_matrix
        
        # Normalize embeddings for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        kb_norms = embeddings_2d / np.linalg.norm(
            embeddings_2d, axis=1, keepdims=True
        )
        
        # Compute cosine similarity
        similarities = np.dot(kb_norms, query_norm)
        
        # Limit top_k to actual number of entries
        # 限制top_k为实际条目数
        actual_k = min(top_k, len(self.knowledge_entries))
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-actual_k:][::-1]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    def retrieve_knowledge(
        self,
        problem_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[str]:
        """
        Retrieve relevant knowledge entries using semantic similarity.
        使用语义相似度检索相关的知识条目
        
        Args:
            problem_text: The problem statement
                          问题陈述
            top_k: Maximum number of results to return
                   返回的最大结果数量
            similarity_threshold: Minimum similarity score (0-1)
                                 最小相似度分数（0-1）
        
        Returns:
            List of relevant rule descriptions
            相关规则描述的列表
        """
        if not problem_text.strip():
            print("Warning: Empty problem text provided")
            print("警告：提供了空的问题文本")
            return []
        
        # Encode the query
        print(f"\n🔍 Encoding query: {problem_text[:100]}...")
        query_embedding = self.model.encode(
            problem_text,
            convert_to_numpy=True
        )
        
        # Find similar entries
        similar_entries = self._compute_similarity(query_embedding, top_k=top_k)
        
        # Filter by threshold and extract rules
        retrieved_rules = []
        print(f"\n📊 Top {top_k} similar knowledge entries:")
        print(f"📊 最相似的 {top_k} 个知识条目:")
        
        for idx, similarity in similar_entries:
            if similarity >= similarity_threshold:
                entry = self.knowledge_entries[idx]
                retrieved_rules.append(entry.rule)
                
                # Print similarity info
                category_str = f"[{entry.category}]" if entry.category else ""
                print(f"  {len(retrieved_rules)}. {category_str} Similarity: {similarity:.3f}")
                print(f"     {entry.rule[:80]}...")
            else:
                print(f"  ✗ Similarity {similarity:.3f} below threshold {similarity_threshold}")
                break
        
        print(f"\n✓ Retrieved {len(retrieved_rules)} relevant rules (threshold: {similarity_threshold})")
        print(f"✓ 检索到 {len(retrieved_rules)} 条相关规则（阈值: {similarity_threshold})")
        
        return retrieved_rules

    def retrieve_with_scores(
        self,
        problem_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Tuple[str, float, Optional[str]]]:
        """
        Retrieve knowledge with similarity scores.
        检索知识并返回相似度分数
        
        Args:
            problem_text: The problem statement
            top_k: Maximum number of results
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of (rule, score, category) tuples
            (规则, 分数, 类别)元组列表
        """
        if not problem_text.strip():
            return []
        
        query_embedding = self.model.encode(problem_text, convert_to_numpy=True)
        similar_entries = self._compute_similarity(query_embedding, top_k=top_k)
        
        results = []
        for idx, similarity in similar_entries:
            if similarity >= similarity_threshold:
                entry = self.knowledge_entries[idx]
                results.append((entry.rule, similarity, entry.category))
        
        return results

    def get_knowledge(self, problem_text: str) -> List[str]:
        """
        Main interface for knowledge retrieval (compatible with old API).
        知识检索的主接口（与旧API兼容）
        
        Args:
            problem_text: The problem statement
                          问题陈述
        
        Returns:
            List of relevant rule descriptions
            相关规则描述的列表
        """
        return self.retrieve_knowledge(
            problem_text,
            top_k=5,
            similarity_threshold=0.3
        )

    def add_knowledge(
        self,
        rule: str,
        category: Optional[str] = None,
        save_to_disk: bool = True
    ) -> None:
        """
        Add a new knowledge entry and compute its embedding.
        添加新的知识条目并计算其嵌入
        
        Args:
            rule: The rule or formula description
                  规则或公式描述
            category: Optional category label
                      可选的分类标签
            save_to_disk: Whether to save to JSON file
                         是否保存到JSON文件
        """
        # Compute embedding for new rule
        embedding = self.model.encode(rule, convert_to_numpy=True)
        
        # Create new entry
        new_entry = VectorKnowledgeEntry(
            rule=rule,
            category=category,
            embedding=embedding
        )
        
        self.knowledge_entries.append(new_entry)
        
        # Update embeddings matrix
        if self.embeddings_matrix is not None:
            self.embeddings_matrix = np.vstack([self.embeddings_matrix, embedding])
        else:
            self.embeddings_matrix = embedding.reshape(1, -1)
        
        print(f"✓ Added new knowledge entry with embedding")
        print(f"✓ 已添加新知识条目并计算嵌入")
        
        # Optionally save to disk
        if save_to_disk:
            self.save_knowledge_base()
            if self.cache_path:
                self._cache_embeddings()

    def save_knowledge_base(self) -> None:
        """
        Save the current knowledge base back to JSON file.
        将当前知识库保存回JSON文件
        """
        data = [
            {
                "rule": entry.rule,
                "category": entry.category
            }
            for entry in self.knowledge_entries
        ]
        
        self.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Knowledge base saved to {self.knowledge_base_path}")
        print(f"✓ 知识库已保存到 {self.knowledge_base_path}")

    def search_by_category(self, category: str, top_k: int = 5) -> List[str]:
        """
        Get knowledge entries by category.
        按类别获取知识条目
        
        Args:
            category: Category name
            top_k: Maximum number of results
        
        Returns:
            List of rules in the category
        """
        results = [
            entry.rule for entry in self.knowledge_entries
            if entry.category == category
        ][:top_k]
        
        return results


# Example usage / 使用示例
if __name__ == "__main__":
    print("="*80)
    print("Vector-based Knowledge Retriever Test")
    print("="*80 + "\n")
    
    # Initialize retriever with local model
    retriever = VectorKnowledgeRetriever(
        knowledge_base_path="data/knowledge_base.json",
        model_name="all-MiniLM-L6-v2",  # Will use local model if exists
        cache_path="data/knowledge_embeddings.pkl",
        use_cache=True
    )
    
    # Test problems
    test_problems = [
        """
        An object with a mass of 10 kg is initially at rest.
        A constant force of 50 Newtons is applied to it for 5 seconds.
        What is its final velocity?
        """,
        """
        A projectile is launched at an angle of 45 degrees with initial velocity 20 m/s.
        What is the maximum height reached?
        """,
        """
        Calculate the area of a circle with radius 5 meters.
        """
    ]
    
    for i, problem in enumerate(test_problems, 1):
        print(f"\n{'='*80}")
        print(f"Test Problem {i}:")
        print(f"{'='*80}")
        print(problem.strip())
        
        # Retrieve knowledge with scores
        results = retriever.retrieve_with_scores(
            problem,
            top_k=3,
            similarity_threshold=0.2
        )
        
        print(f"\n📚 Retrieved Knowledge:")
        for j, (rule, score, category) in enumerate(results, 1):
            cat_str = f"[{category}]" if category else ""
            print(f"\n{j}. {cat_str} (Score: {score:.3f})")
            print(f"   {rule}")

