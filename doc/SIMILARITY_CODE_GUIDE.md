# RAG 相似度代码位置指南
# Similarity Code Location Guide

---

## 📍 核心代码位置

你问的 **通过相似度提取规则** 和 **通过相似度判断是否保存规则** 的代码在以下两个文件：

---

## 1️⃣ **VectorKnowledgeRetriever** (真正的 RAG)

**文件**: `engine/vector_retriever.py`

### 🔍 A. 相似度计算（余弦相似度）

**位置**: 第 217-268 行

```python
def _compute_similarity(
    self,
    query_embedding: np.ndarray,
    top_k: int = 10
) -> List[Tuple[int, float]]:
    """
    计算查询与所有知识条目之间的余弦相似度
    
    返回: [(索引, 相似度分数), ...]
    """
    # 1. 归一化向量（用于余弦相似度）
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    kb_norms = embeddings_2d / np.linalg.norm(
        embeddings_2d, axis=1, keepdims=True
    )
    
    # 2. 计算余弦相似度
    similarities = np.dot(kb_norms, query_norm)
    
    # 3. 获取 top-k 最相似的索引
    top_indices = np.argsort(similarities)[-actual_k:][::-1]
    
    return [(int(idx), float(similarities[idx])) for idx in top_indices]
```

**关键点**:
- 使用 **余弦相似度** (Cosine Similarity)
- 返回 top-k 个最相似的条目
- 相似度范围: 0.0-1.0（1.0 = 完全相同）

---

### 🎯 B. 按相似度提取规则

**位置**: 第 270-328 行

```python
def retrieve_knowledge(
    self,
    problem_text: str,
    top_k: int = 5,
    similarity_threshold: float = 0.3  # ← 相似度阈值
) -> List[str]:
    """
    使用语义相似度检索相关的知识条目
    """
    # 1. 将问题文本编码为向量
    query_embedding = self.model.encode(
        problem_text,
        convert_to_numpy=True
    )
    
    # 2. 计算与所有知识条目的相似度
    similar_entries = self._compute_similarity(query_embedding, top_k=top_k)
    
    # 3. 按相似度阈值过滤
    retrieved_rules = []
    for idx, similarity in similar_entries:
        if similarity >= similarity_threshold:  # 只保留相似度 ≥ 0.3 的
            entry = self.knowledge_entries[idx]
            retrieved_rules.append(entry.rule)
            
            # 打印相似度信息
            print(f"  Similarity: {similarity:.3f}")
            print(f"     {entry.rule[:80]}...")
        else:
            print(f"  ✗ Similarity {similarity:.3f} below threshold")
            break
    
    return retrieved_rules
```

**参数说明**:
- `top_k=5`: 返回最多 5 条规则
- `similarity_threshold=0.3`: 相似度阈值（默认 0.3）
  - 0.3-0.5: 弱相关
  - 0.5-0.7: 中等相关
  - 0.7-1.0: 强相关

---

### 🎯 C. 获取相似度分数（增强版）

**位置**: 第 330-361 行

```python
def retrieve_with_scores(
    self,
    problem_text: str,
    top_k: int = 5,
    similarity_threshold: float = 0.3
) -> List[Tuple[str, float, Optional[str]]]:
    """
    检索知识并返回相似度分数
    
    返回: [(规则, 分数, 类别), ...]
    """
    query_embedding = self.model.encode(problem_text, convert_to_numpy=True)
    similar_entries = self._compute_similarity(query_embedding, top_k=top_k)
    
    results = []
    for idx, similarity in similar_entries:
        if similarity >= similarity_threshold:
            entry = self.knowledge_entries[idx]
            results.append((entry.rule, similarity, entry.category))
    
    return results
```

**用法示例**:
```python
retriever = VectorKnowledgeRetriever()

# 获取带分数的结果
results = retriever.retrieve_with_scores(
    "Calculate force on 10kg object",
    top_k=3,
    similarity_threshold=0.3
)

for rule, score, category in results:
    print(f"[{category}] Score: {score:.3f}")
    print(f"  {rule}")
```

---

### 💾 D. 添加规则（自动计算嵌入）

**位置**: 第 382-425 行

```python
def add_knowledge(
    self,
    rule: str,
    category: Optional[str] = None,
    save_to_disk: bool = True
) -> None:
    """
    添加新的知识条目并计算其嵌入
    """
    # 1. 计算新规则的向量嵌入
    embedding = self.model.encode(rule, convert_to_numpy=True)
    
    # 2. 创建新条目
    new_entry = VectorKnowledgeEntry(
        rule=rule,
        category=category,
        embedding=embedding
    )
    
    # 3. 添加到内存
    self.knowledge_entries.append(new_entry)
    
    # 4. 更新嵌入矩阵
    if self.embeddings_matrix is not None:
        self.embeddings_matrix = np.vstack([self.embeddings_matrix, embedding])
    else:
        self.embeddings_matrix = embedding.reshape(1, -1)
    
    # 5. 保存到磁盘
    if save_to_disk:
        self.save_knowledge_base()  # 保存 JSON
        self._cache_embeddings()    # 缓存向量
```

**用法示例**:
```python
retriever.add_knowledge(
    rule="Newton's Second Law: F = ma",
    category="physics",
    save_to_disk=True  # 自动保存
)
```

---

### 💾 E. 保存知识库

**位置**: 第 427-445 行

```python
def save_knowledge_base(self) -> None:
    """
    将当前知识库保存回 JSON 文件
    """
    data = [
        {
            "rule": entry.rule,
            "category": entry.category
        }
        for entry in self.knowledge_entries
    ]
    
    with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Knowledge base saved to {self.knowledge_base_path}")
```

---

## 2️⃣ **AIKnowledgeRetriever** (AI检索器)

**文件**: `engine/ai_retriever.py`

### 🔍 A. 语义相似度计算

**位置**: 第 888-930 行

```python
def _semantic_similarity(self, text1: str, text2: str) -> float:
    """
    使用嵌入计算两个文本之间的语义相似度
    
    返回: 相似度分数（0.0-1.0）
    """
    # 1. 加载模型（懒加载）
    if self.sentence_model is None:
        self._load_sentence_model()
    
    # 2. 编码两个文本
    emb1 = self.sentence_model.encode([text1], convert_to_numpy=True)
    emb2 = self.sentence_model.encode([text2], convert_to_numpy=True)
    
    # 3. 计算余弦相似度
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity(emb1, emb2)[0][0]
    
    return float(similarity)
```

---

### 💾 B. 通过相似度判断是否保存规则（去重）

**位置**: 第 935-985 行

```python
def _rule_exists_in_kb(self, rule: str, kb_data: List[Dict]) -> bool:
    """
    检查规则是否已存在（使用相似度去重）
    
    三层检查:
    1. 完全匹配（忽略大小写）
    2. 语义相似度 > 0.60（如果启用）
    3. 简单词相似度 > 0.9（降级）
    """
    rule_lower = rule.lower()
    
    for entry in kb_data:
        existing_rule = entry.get("rule", "")
        existing_lower = existing_rule.lower()
        
        # ✅ 检查1: 完全匹配
        if rule_lower == existing_lower:
            return True
        
        # ✅ 检查2: 语义相似度（使用向量）
        if self.use_semantic_dedup:
            semantic_sim = self._semantic_similarity(rule, existing_rule)
            
            # 阈值: 0.60（公式和自然语言都适用）
            if semantic_sim > 0.60:
                print(f"   🔍 Semantic duplicate detected (similarity: {semantic_sim:.2f})")
                return True  # 相似度过高，判定为重复，不保存
        
        # ✅ 检查3: 简单词相似度（降级方案）
        if self._similarity(rule_lower, existing_lower) > 0.9:
            return True
    
    return False  # 不重复，可以保存
```

**关键点**:
- **相似度阈值: 0.60**（60%相似就判定为重复）
- 如果检测到重复，**不会保存**该规则
- 三层保护：完全匹配 → 语义相似度 → 词相似度

---

### 🔍 C. 简单词相似度（降级方案）

**位置**: 第 987-1015 行

```python
def _similarity(self, s1: str, s2: str) -> float:
    """
    计算两个字符串的简单相似度（基于词集合）
    
    返回: 相似度分数（0.0-1.0）
    """
    # 分词
    words1 = set(s1.split())
    words2 = set(s2.split())
    
    # 计算交集和并集
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    # Jaccard 相似度
    return len(intersection) / len(union)
```

---

## 📊 相似度阈值对比

| 文件 | 用途 | 阈值 | 说明 |
|------|------|------|------|
| `vector_retriever.py` | **提取规则** | 0.3 (默认) | 低阈值，更宽松，检索更多规则 |
| `ai_retriever.py` | **保存去重** | 0.60 | 高阈值，更严格，避免重复保存 |

**为什么阈值不同？**
- **提取规则** (0.3): 宁可多检索，不要漏掉可能有用的规则
- **保存去重** (0.60): 宁可严格，避免知识库充满相似规则

---

## 🎯 使用场景

### 场景1: 检索规则（VectorKnowledgeRetriever）

```python
from engine import VectorKnowledgeRetriever

# 初始化
retriever = VectorKnowledgeRetriever(
    knowledge_base_path="../data/knowledge_base.json",
    model_name="all-MiniLM-L6-v2"
)

# 检索规则
problem = "Calculate the force on a 10kg object"
rules = retriever.retrieve_knowledge(
    problem_text=problem,
    top_k=5,  # 最多5条
    similarity_threshold=0.3  # 相似度 ≥ 0.3
)

# 带分数检索
results = retriever.retrieve_with_scores(problem, top_k=3)
for rule, score, category in results:
    print(f"[{category}] {score:.3f}: {rule}")
```

---

### 场景2: 保存规则并去重（AIKnowledgeRetriever）

```python
from engine import AIKnowledgeRetriever

# 初始化（启用语义去重）
retriever = AIKnowledgeRetriever(
    use_semantic_dedup=True,  # 启用语义相似度去重
    verbose=True
)

# 添加规则（自动去重）
new_rule = "Newton's Second Law: F = ma"

# 内部会调用 _rule_exists_in_kb()
# 如果相似度 > 0.60，不会保存
retriever.add_rule_to_kb(new_rule, category="physics")
```

---

## 🧪 测试相似度功能

### 测试 VectorKnowledgeRetriever

```bash
# 运行测试
python engine/vector_retriever.py

# 测试输出：
# 🔍 Encoding query: An object with mass...
# 📊 Top 5 similar knowledge entries:
#   1. [physics] Similarity: 0.856
#      Newton's Second Law: F = ma
#   2. [physics] Similarity: 0.723
#      Force equals mass times acceleration
```

### 测试语义相似度

```python
from engine import AIKnowledgeRetriever

retriever = AIKnowledgeRetriever(use_semantic_dedup=True)

# 计算相似度
sim = retriever._semantic_similarity(
    "Newton's Second Law: F = ma",
    "Force equals mass times acceleration"
)
print(f"Similarity: {sim:.3f}")  # 约 0.75-0.85
```

---

## 📝 关键配置参数

### VectorKnowledgeRetriever

```python
# 初始化参数
VectorKnowledgeRetriever(
    knowledge_base_path="data/knowledge_base.json",  # JSON文件路径
    model_name="all-MiniLM-L6-v2",                  # 嵌入模型
    cache_path="data/knowledge_embeddings.pkl",     # 缓存路径
    use_cache=True                                   # 是否使用缓存
)

# 检索参数
retrieve_knowledge(
    problem_text="...",
    top_k=5,                    # 返回最多5条
    similarity_threshold=0.3    # 相似度阈值
)
```

### AIKnowledgeRetriever

```python
# 初始化参数
AIKnowledgeRetriever(
    use_semantic_dedup=True,    # 启用语义去重
    verbose=True                 # 打印详细信息
)

# 去重参数（内部硬编码）
semantic_sim > 0.60  # 语义相似度阈值
word_sim > 0.9       # 词相似度阈值
```

---

## 🎓 相似度计算原理

### 余弦相似度 (Cosine Similarity)

```
相似度 = cos(θ) = (A · B) / (||A|| × ||B||)

其中:
- A, B 是两个向量（embeddings）
- · 表示点积
- ||A|| 表示向量长度（范数）
```

**特点**:
- 范围: [-1, 1]，但对于正向量通常是 [0, 1]
- 1.0 = 完全相同方向（语义完全相同）
- 0.0 = 正交（语义完全无关）
- 0.3 = 弱相关
- 0.6 = 中等相关
- 0.8+ = 强相关

---

## 📚 相关文档

- 向量检索升级文档: `VECTOR_RETRIEVER_UPGRADE.md`
- 向量检索快速上手: `向量检索5分钟快速上手.md`
- 主引擎代码: `main.py`
- Engine 包: `engine/__init__.py`

---

## 🎯 快速定位

**想找相似度代码？**

| 需求 | 文件 | 行号 |
|------|------|------|
| 计算余弦相似度 | `vector_retriever.py` | 217-268 |
| 按相似度提取规则 | `vector_retriever.py` | 270-328 |
| 添加规则（计算嵌入） | `vector_retriever.py` | 382-425 |
| 保存知识库 | `vector_retriever.py` | 427-445 |
| 语义相似度计算 | `ai_retriever.py` | 888-930 |
| 相似度去重 | `ai_retriever.py` | 935-985 |
| 简单词相似度 | `ai_retriever.py` | 987-1015 |

---

**总结**: 你要找的相似度代码都在这里了！🎉

