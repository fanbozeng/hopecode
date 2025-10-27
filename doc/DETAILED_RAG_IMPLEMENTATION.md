# RAG系统详细实现文档

## 1. 概述

RAG（Retrieval-Augmented Generation，检索增强生成）是本因果推理引擎的核心组件之一，负责在问题求解过程中提供相关的领域知识，包括物理定律、数学公式等，为后续的因果推理奠定基础。

本系统采用了混合式RAG策略，结合了传统的基于关键词匹配的检索和基于AI的动态知识生成，以提高知识检索的准确性和覆盖范围。

## 2. 系统架构

RAG系统由两个主要组件构成：

1. **传统知识检索器**（[KnowledgeRetriever](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py#L38-L272)）：基于关键词匹配的传统检索方法
2. **AI知识检索器**（[AIKnowledgeRetriever](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L51-L1035)）：基于大语言模型的动态知识生成方法

系统采用混合策略，首先尝试使用传统检索器查找知识，如果结果不足则调用AI检索器动态生成知识。

## 3. 传统知识检索器（KnowledgeRetriever）

### 3.1 核心功能

传统知识检索器位于 [engine/retriever.py](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py) 文件中，主要功能包括：

1. 从问题文本中提取关键词
2. 在知识库中查找匹配的条目
3. 根据关键词重叠度排序并返回相关知识

### 3.2 核心方法

- [extract_keywords()](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py#L128-L166)：从问题文本中提取关键词
- [retrieve_knowledge()](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py#L168-L222)：根据关键词检索相关知识
- [get_knowledge()](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py#L224-L237)：获取知识的主接口
- [add_knowledge()](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py#L239-L260)：动态添加新的知识条目
- [save_knowledge_base()](file:///D:/论文/大模型因果推理/hope_code/engine/retriever.py#L262-L271)：将当前知识库保存回JSON文件

### 3.3 工作原理

1. 使用正则表达式和词边界检测从问题描述中提取有意义的技术术语
2. 利用全面的停用词数据库（1354个词：807个英文 + 547个中文）过滤掉停用词和单个字符
3. 在知识库中查找所有至少共享指定数量关键词的知识条目
4. 按关键词重叠数对匹配结果进行排序

### 3.4 使用示例

```python
from engine import KnowledgeRetriever

# 初始化检索器
retriever = KnowledgeRetriever("data/knowledge_base.json")

# 检索知识
rules = retriever.get_knowledge("一个质量为10kg的物体受到50N的力，求加速度")
```

## 4. AI知识检索器（AIKnowledgeRetriever）

### 4.1 核心功能

AI知识检索器位于 [engine/ai_retriever.py](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py) 文件中，主要功能包括：

1. 使用大语言模型分析问题陈述并动态生成上下文相关的公式、定律和原理
2. 支持多种输出格式（纯文本列表、结构化JSON）
3. 提供缓存机制避免重复调用LLM
4. 支持自动将生成的知识添加到知识库中实现持续学习

### 4.2 核心方法

- [extract_knowledge()](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L269-L339)：使用AI提取相关知识
- [_parse_rules()](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L341-L467)：解析LLM响应并提取规则
- [_save_rules_to_kb()](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L616-L706)：将生成的规则保存到知识库
- [get_knowledge()](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L241-L252)：获取知识的主接口（与KnowledgeRetriever兼容）
- [clear_cache()](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L502-L512)：清除缓存的规则
- [get_cache_stats()](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L514-L528)：获取缓存统计信息

### 4.3 工作原理

1. 将问题文本与提示词模板结合生成完整的提示
2. 调用大语言模型生成相关知识
3. 解析模型输出并返回结构化知识
4. 支持多种解析策略（JSON格式、编号列表、逐行解析）
5. 提供降级机制，当AI提取失败时可使用传统检索器

### 4.4 提示词模板

AI检索器使用专门设计的提示词模板（[prompts/knowledge_extraction_prompt.txt](file:///D:/论文/大模型因果推理/hope_code/prompts/knowledge_extraction_prompt.txt)）来指导LLM生成结构化的知识。模板要求LLM：

1. 识别问题领域
2. 提取相关公式和定律
3. 以指定的JSON格式输出，包含关键词、规则描述和分类

### 4.5 使用示例

```python
from engine import AIKnowledgeRetriever

# 初始化AI检索器
ai_retriever = AIKnowledgeRetriever(
    auto_enrich_kb=True,     # 自动丰富知识库
    max_rules=5,             # 最大生成规则数
    temperature=0.3,         # LLM采样温度
    enable_cache=True        # 启用缓存
)

# 提取知识
ai_rules = ai_retriever.get_knowledge("一个质量为10kg的物体受到50N的力，求加速度")
```

## 5. 混合RAG策略

系统采用混合策略结合两种检索器的优点：

```python
# 在 main.py 中的实现示例
# Step 1: 尝试传统检索
relevant_rules = self.retriever.get_knowledge(problem_text)

# Step 2: 如果规则不足，使用AI生成
if self.use_ai_retriever and len(relevant_rules) < self.min_rules_threshold:
    ai_generated_rules = self.ai_retriever.get_knowledge(problem_text)
    relevant_rules.extend(ai_generated_rules)
```

### 5.1 策略优势

1. **快速响应**：对于知识库中已有的问题，直接返回结果
2. **智能补充**：对于新类型问题，AI动态生成相关知识
3. **持续学习**：AI生成的知识可以自动添加到知识库中

## 6. 知识库结构

知识库存储在 [data/knowledge_base.json](file:///D:/论文/大模型因果推理/hope_code/data/knowledge_base.json) 中，每条知识包含以下字段：

```json
{
  "keywords": ["关键词1", "关键词2", "..."],
  "rule": "规则描述: 公式 - 应用说明",
  "category": "领域分类",
  "source": "来源"
}
```

### 6.1 示例条目

```json
{
  "keywords": ["force", "mass", "acceleration"],
  "rule": "牛顿第二定律: F = m × a - 描述了作用力（F，单位为牛顿N）、质量（m，单位为千克kg）和加速度（a，单位为米每二次方秒m/s²）之间的关系；用于动力学中连接力和运动",
  "category": "力学",
  "source": "ai_retriever"
}
```

## 7. 高级功能

### 7.1 缓存机制

AI检索器支持结果缓存，避免对相同问题重复调用LLM：

```python
ai_retriever = AIKnowledgeRetriever(enable_cache=True)
```

### 7.2 语义去重

系统使用语义嵌入技术检测和避免重复知识的添加：

```python
# 使用语义相似度检测重复
semantic_similarity = self._semantic_similarity(rule1, rule2)
if semantic_similarity > 0.85:
    # 认为是重复规则
```

### 7.3 知识库自动丰富

AI检索器支持自动将生成的知识添加到知识库中，实现系统的持续学习能力：

```python
# 启用自动丰富功能
ai_retriever = AIKnowledgeRetriever(auto_enrich_kb=True)

# 生成的知识将自动保存到知识库
rules = ai_retriever.get_knowledge("复杂问题描述")
```

## 8. 性能优化

### 8.1 嵌入模型

系统使用 `all-MiniLM-L6-v2` 模型进行语义相似度计算，该模型轻量级但效果良好，适合短文本处理。

### 8.2 降级策略

当AI检索失败时，系统可以降级使用传统检索器确保服务可用性。

## 9. 最佳实践

### 9.1 配置建议

1. 合理设置最大规则数（[max_rules](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L83-L83)），平衡完整性和性能
2. 适当调整温度参数（[temperature](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L85-L85)），控制生成的创造性
3. 启用缓存机制提高重复查询的响应速度

### 9.2 使用建议

1. 优先使用混合策略，结合传统检索和AI生成的优势
2. 定期审查AI生成的知识条目，确保质量和准确性
3. 启用自动丰富功能，持续优化知识库

## 10. 故障排除

### 10.1 常见问题

1. **LLM调用失败**：检查LLM客户端配置和网络连接
2. **知识库文件缺失**：确认 [data/knowledge_base.json](file:///D:/论文/大模型因果推理/hope_code/data/knowledge_base.json) 文件存在且格式正确
3. **解析失败**：检查LLM输出格式是否符合预期

### 10.2 调试技巧

1. 启用详细日志（[verbose](file:///D:/论文/大模型因果推理/hope_code/engine/ai_retriever.py#L89-L89) 参数）查看执行过程
2. 检查缓存状态了解查询历史
3. 查看知识库丰富历史了解系统学习情况

## 11. 总结

本系统中的RAG实现通过结合传统检索和AI生成的方式，实现了高效、准确、可扩展的知识检索功能。它不仅能够快速响应已知问题，还能通过AI生成处理新类型问题，并通过自动丰富机制持续优化知识库，为因果推理引擎提供了强大的知识支持。