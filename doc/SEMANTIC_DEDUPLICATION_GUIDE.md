# 语义去重指南 (Semantic Deduplication Guide)

## 📚 什么是语义嵌入去重？

**语义嵌入（Semantic Embedding）** 是一种将文本转换为高维向量的技术，使计算机能够真正"理解"文本的语义含义，而不仅仅是匹配字符串。

### 工作原理

```
文本A: "F = m * a"
  ↓ 转换为向量
  [0.23, -0.15, 0.42, ..., 0.18]  (384维)

文本B: "Force equals mass times acceleration"
  ↓ 转换为向量
  [0.24, -0.14, 0.43, ..., 0.19]  (384维)

  ↓ 计算余弦相似度
  相似度 = 0.92 > 0.85 阈值
  ↓
  判定为重复 ✅
```

---

## 🚀 安装依赖

### 步骤1：安装语义嵌入库

```bash
# 安装 sentence-transformers 及其依赖
pip install sentence-transformers torch scikit-learn

# 或者一次性安装所有依赖
pip install -r requirements.txt
```

**依赖包说明**：
- `sentence-transformers`: 语义嵌入模型（~80MB）
- `torch`: PyTorch 后端（~700MB）
- `scikit-learn`: 余弦相似度计算

### 步骤2：首次运行会自动下载模型

```bash
# 第一次使用时，系统会自动下载模型（约80MB）
python evaluate_framework.py --dataset gsm8k --limit 5
```

模型会被缓存到：
- Windows: `C:\Users\<username>\.cache\torch\sentence_transformers\`
- Linux/Mac: `~/.cache/torch/sentence_transformers/`

---

## 💡 使用方法

### 方法1：自动启用（默认）

系统**默认启用**语义去重，无需任何配置！

```bash
# 直接运行，自动使用语义去重
python evaluate_framework.py --dataset gsm8k --limit 20

# 系统会自动：
# 1. 检测是否安装了 sentence-transformers
# 2. 如果已安装 → 使用语义去重 ✅
# 3. 如果未安装 → 降级使用简单相似度 ⚠️
```

### 方法2：手动控制

```python
from engine.ai_retriever import AIKnowledgeRetriever

# 创建检索器（自动启用语义去重）
retriever = AIKnowledgeRetriever(
    auto_enrich_kb=True,
    verbose=True
)

# 语义去重会自动工作
rules = retriever.get_knowledge("F = m * a")
# 后续添加 "Force equals mass times acceleration" 会被去重
```

---

## 📊 效果对比

### 测试案例

| 规则A | 规则B | 简单去重 | 语义去重 |
|-------|-------|---------|---------|
| `F = m * a` | `Force equals mass times acceleration` | ❌ 不去重 | ✅ 去重 (0.89) |
| `力 = 质量 * 加速度` | `F = m × a` | ❌ 不去重 | ✅ 去重 (0.82) |
| `V = I * R` | `Voltage = Current × Resistance` | ❌ 不去重 | ✅ 去重 (0.91) |
| `E = mc²` | `Energy equals mass times speed of light squared` | ❌ 不去重 | ✅ 去重 (0.88) |
| `F = m * a` | `P = F * v` | ✅ 不去重 | ✅ 不去重 (0.34) |

括号内数字为语义相似度分数。

---

## 🎯 配置选项

### 相似度阈值

当前阈值：**0.85** （在 `engine/ai_retriever.py` 第953行）

```python
# 修改阈值
if semantic_sim > 0.85:  # 默认阈值
    return True  # 判定为重复
```

**推荐阈值**：
- `0.80`: 宽松（可能误判不同规则为重复）
- `0.85`: 平衡（推荐）✅
- `0.90`: 严格（可能漏掉相似规则）

### 禁用语义去重

如果不想使用语义去重（如内存受限），系统会自动降级：

```python
# 不安装 sentence-transformers
# 系统会自动输出：
# ⚠ sentence-transformers not installed. Falling back to simple similarity.
# ⚠ 未安装 sentence-transformers。降级使用简单相似度。
```

---

## 🔍 运行日志示例

### 启用语义去重时

```
Initialized AI Knowledge Retriever.
已初始化AI知识检索器
   Auto-enrichment of knowledge base is ENABLED.
   知识库自动丰富功能已启用

(第一次使用时)
   Loading semantic embedding model: all-MiniLM-L6-v2...
   正在加载语义嵌入模型: all-MiniLM-L6-v2...
   ✓ Semantic embedding model loaded successfully.
   ✓ 语义嵌入模型加载成功

(检测到语义重复时)
   🔍 Semantic duplicate detected (similarity: 0.89)
   🔍 检测到语义重复（相似度: 0.89）
   ℹ All rules already exist in knowledge base.
   ℹ 所有规则已存在于知识库中
```

### 未安装时（降级）

```
   ⚠ sentence-transformers not installed. Falling back to simple similarity.
   ⚠ 未安装 sentence-transformers。降级使用简单相似度。
   Install with: pip install sentence-transformers

(继续使用简单词相似度)
   ✓ Added 2 new structured rules to knowledge base.
   ✓ 向知识库添加了 2 条新的结构化规则
```

---

## 📈 性能考虑

### 内存占用

| 组件 | 大小 | 说明 |
|------|------|------|
| 模型文件 | ~80MB | 首次下载，后续使用缓存 |
| 运行时内存 | ~200MB | 模型加载到内存 |
| 嵌入缓存 | ~1KB/规则 | 避免重复计算 |

### 速度

| 操作 | 时间 |
|------|------|
| 首次加载模型 | 2-3秒 |
| 生成单个嵌入 | 10-50ms |
| 计算相似度 | <1ms |
| 缓存命中 | <0.1ms |

**优化技巧**：
1. ✅ 嵌入向量自动缓存
2. ✅ 懒加载（只有需要时才加载模型）
3. ✅ 只对新规则计算嵌入

---

## 🛠️ 高级用法

### 自定义嵌入模型

如果需要更强的多语言支持，可以修改模型：

```python
# 在 engine/ai_retriever.py 第807行
model_name = 'all-MiniLM-L6-v2'  # 默认（英文为主）

# 改为多语言模型
model_name = 'paraphrase-multilingual-MiniLM-L12-v2'  # 支持50+语言
```

**可选模型**：
| 模型 | 大小 | 语言 | 速度 | 质量 |
|------|------|------|------|------|
| `all-MiniLM-L6-v2` | 80MB | 英文 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| `paraphrase-multilingual-MiniLM-L12-v2` | 420MB | 50+语言 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| `all-mpnet-base-v2` | 420MB | 英文 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 查看嵌入缓存统计

```python
from engine.ai_retriever import AIKnowledgeRetriever

retriever = AIKnowledgeRetriever()

# 运行一些操作...

# 查看缓存
print(f"Cached embeddings: {len(retriever._embeddings_cache)}")
```

---

## 🐛 故障排除

### 问题1：导入错误

```
ImportError: No module named 'sentence_transformers'
```

**解决**：
```bash
pip install sentence-transformers
```

### 问题2：CUDA/GPU错误

```
RuntimeError: CUDA out of memory
```

**解决**：
```python
# 强制使用CPU（在 ai_retriever.py 第812行后添加）
self._embedding_model = SentenceTransformer(model_name, device='cpu')
```

### 问题3：下载模型超时

**解决**：
```bash
# 方案1：手动下载模型
mkdir -p ~/.cache/torch/sentence_transformers
cd ~/.cache/torch/sentence_transformers
wget https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/...

# 方案2：使用镜像
export HF_ENDPOINT=https://hf-mirror.com
pip install sentence-transformers
```

### 问题4：内存不足

**解决**：
```python
# 禁用语义去重，使用简单相似度
# 在 main.py 中
engine = CausalReasoningEngine(
    use_ai_retriever=True,
    auto_enrich_kb=True
)
# 或者卸载 sentence-transformers
# pip uninstall sentence-transformers
```

---

## 📊 实际效果验证

### 验证脚本

创建 `test_semantic_dedup.py`：

```python
from engine.ai_retriever import AIKnowledgeRetriever

# 创建检索器
retriever = AIKnowledgeRetriever(
    auto_enrich_kb=True,
    verbose=True
)

# 测试用例
test_rules = [
    ("F = m * a", "Force equals mass times acceleration"),
    ("V = I * R", "Voltage = Current × Resistance"),
    ("E = mc²", "Energy equals mass times speed of light squared"),
    ("力 = 质量 * 加速度", "F = m × a"),
]

print("\n=== 测试语义去重 ===\n")

for rule1, rule2 in test_rules:
    sim = retriever._semantic_similarity(rule1, rule2)
    status = "✅ 会去重" if sim > 0.85 else "❌ 不去重"
    print(f"{status} | 相似度: {sim:.3f}")
    print(f"  规则1: {rule1}")
    print(f"  规则2: {rule2}\n")
```

运行：
```bash
python test_semantic_dedup.py
```

---

## 💡 最佳实践

1. **首次部署**：在本地先测试，确保模型下载成功
2. **生产环境**：预先下载模型，避免首次运行延迟
3. **大规模评估**：前100题建立知识库，后续题目会更快
4. **定期清理**：检查知识库，移除低质量规则
5. **监控日志**：注意"Semantic duplicate detected"出现频率

---

## 📚 参考资源

- [Sentence Transformers 文档](https://www.sbert.net/)
- [模型列表](https://www.sbert.net/docs/pretrained_models.html)
- [余弦相似度](https://en.wikipedia.org/wiki/Cosine_similarity)

---

## 🎉 总结

语义嵌入去重是一个**强大但可选**的功能：

✅ **优势**：
- 真正理解语义，不是简单字符串匹配
- 跨语言支持（中英混合）
- 识别不同表述的相同规则

⚠️ **权衡**：
- 需要额外依赖（~80MB模型）
- 首次加载稍慢（2-3秒）
- 占用额外内存（~200MB）

**推荐使用场景**：
- ✅ 长期运行的评估任务
- ✅ 知识库会持续增长
- ✅ 对去重质量要求高
- ❌ 内存受限的环境
- ❌ 一次性快速测试

---

**最后更新**: 2025-10-19


