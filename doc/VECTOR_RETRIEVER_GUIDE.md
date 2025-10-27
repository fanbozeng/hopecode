# Vector-based RAG Retriever Guide
# 基于向量的RAG检索器指南

## 📌 Overview / 概述

The new **Vector-based Knowledge Retriever** implements true semantic similarity search using sentence embeddings, replacing the simple keyword matching approach.

新的**基于向量的知识检索器**使用句子嵌入实现真正的语义相似度搜索，取代了简单的关键词匹配方法。

### Key Improvements / 主要改进

| Feature | Keyword-based (Old) | Vector-based (New) |
|---------|--------------------|--------------------|
| **Matching Method** | Exact keyword overlap | Semantic similarity |
| **Accuracy** | Misses semantically related content | Finds conceptually similar content |
| **Language Understanding** | Limited to exact words | Understands context and meaning |
| **Example** | "force" only matches "force" | "force" matches "acceleration", "motion", "dynamics" |

---

## 🚀 Quick Start / 快速开始

### 1. Install Dependencies / 安装依赖

```bash
pip install sentence-transformers
```

### 2. Use in Your Code / 在代码中使用

#### Option A: Using CausalReasoningEngine (Recommended)

```python
from main import CausalReasoningEngine

# Initialize with vector retriever
engine = CausalReasoningEngine(
    use_vector_retriever=True,  # Enable vector-based retrieval
    vector_model_name="all-MiniLM-L6-v2",  # Local model path or HuggingFace model name
    use_ai_retriever=True,  # Optional: Enable AI fallback
    verbose=True
)

# Solve a problem
result = engine.solve_problem("Your problem text here...")
```

#### Option B: Using VectorKnowledgeRetriever Directly

```python
from engine.vector_retriever import VectorKnowledgeRetriever

# Initialize retriever
retriever = VectorKnowledgeRetriever(
    knowledge_base_path="data/knowledge_base.json",
    model_name="all-MiniLM-L6-v2",
    cache_path="data/knowledge_embeddings.pkl",
    use_cache=True
)

# Retrieve knowledge
problem = "An object with mass 10 kg accelerates at 5 m/s²..."
relevant_rules = retriever.get_knowledge(problem)

# Or get with similarity scores
results = retriever.retrieve_with_scores(
    problem,
    top_k=5,
    similarity_threshold=0.3
)

for rule, score, category in results:
    print(f"[{category}] Score: {score:.3f}")
    print(f"  {rule}")
```

---

## 🔧 Configuration / 配置

### Parameters / 参数

#### VectorKnowledgeRetriever.__init__()

```python
VectorKnowledgeRetriever(
    knowledge_base_path: str = "data/knowledge_base.json",  # Path to knowledge base
    model_name: str = "all-MiniLM-L6-v2",  # Sentence transformer model
    cache_path: Optional[str] = "data/knowledge_embeddings.pkl",  # Cache embeddings
    use_cache: bool = True  # Use cached embeddings if available
)
```

#### retrieve_knowledge()

```python
retriever.retrieve_knowledge(
    problem_text: str,  # Problem statement
    top_k: int = 5,  # Maximum number of results
    similarity_threshold: float = 0.3  # Minimum similarity score (0-1)
)
```

### Recommended Settings / 推荐设置

| Scenario | top_k | similarity_threshold |
|----------|-------|---------------------|
| **Specific domain** (physics, math) | 3-5 | 0.3-0.4 |
| **Broad search** | 8-10 | 0.2-0.3 |
| **Strict relevance** | 3 | 0.4-0.5 |

---

## 📊 Performance Comparison / 性能对比

### Example: Physics Problem

**Problem:** "A ball is dropped from a height. What is its velocity after 2 seconds?"

#### Keyword-based Results:
- Found: 2 rules (containing "velocity", "height")
- Missed: Equations using "v", "u", "g" notation

#### Vector-based Results:
- Found: 5 rules including:
  - Kinematic equations (even with different notation)
  - Newton's laws (conceptually related)
  - Free fall motion principles
  - Energy conservation (related concept)

---

## 🧠 How It Works / 工作原理

### 1. Embedding Generation / 嵌入生成

```
Knowledge Base Entry: "Force equals mass times acceleration (F=ma)"
                      ↓
Sentence Transformer Model (all-MiniLM-L6-v2)
                      ↓
Vector Embedding: [0.12, -0.34, 0.56, ..., 0.89]  (384 dimensions)
```

### 2. Semantic Search / 语义搜索

```
Query: "What force is needed to accelerate a 10kg object?"
       ↓
Encode to vector: [0.15, -0.32, 0.58, ..., 0.87]
       ↓
Compute Cosine Similarity with all knowledge vectors
       ↓
Rank by similarity & filter by threshold
       ↓
Return: Top-k most similar rules
```

### 3. Caching Mechanism / 缓存机制

- **First run**: Computes embeddings for all knowledge base entries (~10-30 seconds)
- **Subsequent runs**: Loads from cache (~1 second)
- **Cache invalidation**: Automatically recomputes if knowledge base changes

---

## 🔍 Testing / 测试

### Run the test script:

```bash
python test_vector_retriever.py
```

This will compare keyword-based vs vector-based retrieval on several test problems.

### Sample Output:

```
==================================================
 Problem: Physics - Newton's Laws
==================================================

📝 Problem Text:
An object with a mass of 10 kg is initially at rest...

------------------------------------------------
🔹 Method 1: Traditional Keyword Matching
------------------------------------------------

✓ Retrieved 2 rules:
  1. Newton's Second Law: Force equals mass times acceleration...
  2. Kinematic Equation: Final velocity equals initial velocity...

------------------------------------------------
🔹 Method 2: Vector-based Semantic Search
------------------------------------------------

✓ Retrieved 5 rules:
  1. [Physics] Similarity: 0.782
     Newton's Second Law: Force equals mass times acceleration...
  2. [Physics] Similarity: 0.654
     Kinematic Equation: v_f = v_i + a*t...
  3. [Physics] Similarity: 0.521
     Impulse-Momentum Theorem: Change in momentum equals impulse...
  4. [Physics] Similarity: 0.487
     Work-Energy Theorem: Work done equals change in kinetic energy...
  5. [Dynamics] Similarity: 0.423
     Net force causes acceleration: ΣF = ma...
```

---

## 💡 Best Practices / 最佳实践

### 1. Knowledge Base Design / 知识库设计

**✅ Good:**
```json
{
  "rule": "Newton's Second Law states that the acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass. Formula: F = ma, where F is force (N), m is mass (kg), and a is acceleration (m/s²).",
  "category": "Physics-Dynamics"
}
```

**❌ Bad:**
```json
{
  "rule": "F=ma",
  "category": "Physics"
}
```

**Why?** More detailed descriptions provide richer semantic content for better embedding quality.

### 2. Model Selection / 模型选择

| Model | Dimensions | Speed | Accuracy | Use Case |
|-------|-----------|-------|----------|----------|
| **all-MiniLM-L6-v2** | 384 | Fast | Good | Recommended for most cases |
| all-mpnet-base-v2 | 768 | Medium | Better | Higher accuracy needed |
| paraphrase-multilingual | 384 | Fast | Good | Multi-language support |

### 3. Threshold Tuning / 阈值调优

```python
# Too low (0.1-0.2): Gets many irrelevant results
retriever.retrieve_knowledge(problem, similarity_threshold=0.1)  # ❌

# Good balance (0.3-0.4): Relevant results
retriever.retrieve_knowledge(problem, similarity_threshold=0.3)  # ✅

# Too high (0.6+): Misses relevant results
retriever.retrieve_knowledge(problem, similarity_threshold=0.6)  # ⚠️
```

---

## 🛠️ Maintenance / 维护

### Adding New Knowledge / 添加新知识

```python
retriever = VectorKnowledgeRetriever("data/knowledge_base.json")

# Add new entry (automatically computes embedding)
retriever.add_knowledge(
    rule="New physics principle: ...",
    category="Physics",
    save_to_disk=True  # Saves to JSON and updates cache
)
```

### Rebuilding Cache / 重建缓存

```python
# Delete old cache
import os
if os.path.exists("data/knowledge_embeddings.pkl"):
    os.remove("data/knowledge_embeddings.pkl")

# Reinitialize (will recompute all embeddings)
retriever = VectorKnowledgeRetriever(
    "data/knowledge_base.json",
    use_cache=False  # Force recomputation
)
```

---

## 🐛 Troubleshooting / 故障排除

### Issue 1: "ModuleNotFoundError: No module named 'sentence_transformers'"

**Solution:**
```bash
pip install sentence-transformers
```

### Issue 2: "Model download is slow"

**Solution:** Use local model (already in `all-MiniLM-L6-v2/`)
```python
retriever = VectorKnowledgeRetriever(
    model_name="all-MiniLM-L6-v2"  # Will use local directory
)
```

### Issue 3: "No results returned"

**Possible causes:**
1. **Similarity threshold too high** → Lower it to 0.2-0.3
2. **Knowledge base empty** → Check `data/knowledge_base.json`
3. **Cache corrupted** → Delete `data/knowledge_embeddings.pkl` and retry

### Issue 4: "Cache size mismatch"

**Solution:** This happens when knowledge base is updated but cache is not. The system will automatically recompute embeddings.

---

## 📈 Performance Metrics / 性能指标

### Initialization Time / 初始化时间

| Knowledge Base Size | First Run (compute) | Cached Run |
|---------------------|--------------------|----|
| 100 entries | ~10 seconds | ~1 second |
| 500 entries | ~30 seconds | ~1 second |
| 1000 entries | ~60 seconds | ~2 seconds |

### Query Time / 查询时间

- **Encoding query**: ~50ms
- **Similarity computation**: ~5ms (100 entries) to ~50ms (1000 entries)
- **Total per query**: ~55-100ms

---

## 🔗 Integration with Training-Free GRPO / 与训练自由GRPO集成

The vector retriever can be combined with Training-Free GRPO for experience-enhanced retrieval:

```python
from engine.experience_manager import ExperienceManager
from engine.vector_retriever import VectorKnowledgeRetriever

# Initialize both systems
retriever = VectorKnowledgeRetriever("data/knowledge_base.json")
exp_manager = ExperienceManager("data/experiences.json")

# Retrieve knowledge + experiences
problem = "..."
knowledge_rules = retriever.get_knowledge(problem)
experiences = exp_manager.get_experiences_for_agent(agent_id=1)

# Combine for scaffolding
combined_context = f"""
**Retrieved Knowledge:**
{chr(10).join(knowledge_rules)}

**Learned Experiences:**
{experiences}
"""
```

---

## 📚 References / 参考资料

1. **Sentence Transformers**: https://www.sbert.net/
2. **all-MiniLM-L6-v2 Model**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
3. **Training-Free GRPO Paper**: arXiv:2510.08191

---

## 🎯 Summary / 总结

| Aspect | Impact |
|--------|--------|
| **Accuracy** | 🔼 Improved semantic understanding |
| **Recall** | 🔼 Finds more relevant knowledge |
| **Flexibility** | 🔼 Works with paraphrased queries |
| **Speed** | ➡️ Similar (with caching) |
| **Maintenance** | ➡️ Similar effort |

**Recommendation**: Use vector-based retriever for production. It provides significantly better semantic matching with minimal overhead.

**推荐**: 生产环境使用向量检索器。它提供明显更好的语义匹配，开销很小。


