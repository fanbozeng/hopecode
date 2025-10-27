# CausalReasoningEngine 参数错误修复
# Parameter Error Fix

**错误**: `TypeError: __init__() got an unexpected keyword argument 'use_vector_retriever'`  
**原因**: `CausalReasoningEngine` 不接受 `use_vector_retriever` 参数  
**修复时间**: 2025-01-XX

---

## ❌ 错误信息

```python
TypeError: __init__() got an unexpected keyword argument 'use_vector_retriever'
```

**位置**: `train_with_grpo.py:317`

---

## ✅ 修复内容

### 修复前（错误的代码）

```python
engine = CausalReasoningEngine(
    verbose=True,
    use_multi_agent=True,
    num_generators=3,
    generator_temperature=0.3,
    critic_temperature=0.0,
    computation_mode='llm',
    use_vector_retriever=True  # ❌ 这个参数不存在！
)
```

### 修复后（正确的代码）

```python
engine = CausalReasoningEngine(
    verbose=True,
    use_multi_agent=True,
    num_generators=3,
    generator_temperature=0.3,
    critic_temperature=0.0,
    computation_mode='llm'  # ✅ 移除了不存在的参数
)
```

---

## 📋 CausalReasoningEngine 有效参数列表

### 所有可用参数

根据 `main.py` 中的定义，`CausalReasoningEngine.__init__()` 接受以下参数：

```python
def __init__(
    self,
    knowledge_base_path: str = "data/knowledge_base.json",
    verbose: bool = True,
    use_ai_retriever: bool = True,
    auto_enrich_kb: bool = True,
    min_rules_threshold: int = 5,
    computation_mode: str = "llm",           # 'symbolic' 或 'llm'
    use_multi_agent: bool = True,            # 是否使用多智能体
    num_generators: int = 3,                 # 生成器数量
    generator_temperature: float = 0.3,      # 生成器温度
    critic_temperature: float = 0.0          # 批判者温度
):
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `knowledge_base_path` | str | "data/knowledge_base.json" | 知识库路径 |
| `verbose` | bool | True | 是否打印详细信息 |
| `use_ai_retriever` | bool | True | 是否使用 AI 检索器 |
| `auto_enrich_kb` | bool | True | 是否自动丰富知识库 |
| `min_rules_threshold` | int | 5 | 最小规则阈值 |
| `computation_mode` | str | "llm" | 计算模式: "symbolic" 或 "llm" |
| `use_multi_agent` | bool | True | 是否使用多智能体系统 |
| `num_generators` | int | 3 | 并行生成器数量 |
| `generator_temperature` | float | 0.3 | 生成器温度（多样性） |
| `critic_temperature` | float | 0.0 | 批判者温度（确定性） |

### ❌ 不存在的参数

以下参数**不存在**，请勿使用：
- ❌ `use_vector_retriever` 
- ❌ `vector_db_path`
- ❌ `embedding_model`

---

## 🔍 为什么没有 `use_vector_retriever`？

### 可能的原因

1. **功能未实现**: Vector retriever 可能还未集成到 `CausalReasoningEngine`
2. **内部自动选择**: 引擎可能根据 `use_ai_retriever` 自动选择检索器类型
3. **配置在其他地方**: Vector retriever 的配置可能在其他地方

### 如何使用 Vector Retriever

如果需要使用 vector retriever，可能需要：

```python
# 方案1: 通过 use_ai_retriever 参数（可能内部会用 vector）
engine = CausalReasoningEngine(
    use_ai_retriever=True,  # 可能会使用 vector retriever
    ...
)

# 方案2: 直接修改引擎内部（需要查看 main.py 实现）
engine = CausalReasoningEngine(...)
# 手动替换 retriever
from engine import VectorKnowledgeRetriever
engine.retriever = VectorKnowledgeRetriever(...)
```

---

## ✅ 正确的 GRPO 训练初始化

### 推荐配置

```python
from main import CausalReasoningEngine
from engine import GRPOExperienceManager, TrainingFreeGRPOTrainer

# 1. 初始化经验管理器
experience_manager = GRPOExperienceManager(
    experience_dir='../data/grpo_experiences',
    verbose=True
)

# 2. 初始化引擎（使用正确的参数）
engine = CausalReasoningEngine(
    verbose=True,
    use_multi_agent=True,  # ✅ 使用多智能体
    num_generators=3,  # ✅ 3个生成器
    generator_temperature=0.3,  # ✅ 生成器温度
    critic_temperature=0.0,  # ✅ 批判者温度
    computation_mode='llm'  # ✅ LLM 计算模式
    # ❌ 不要添加 use_vector_retriever
)

# 3. 注入经验管理器（重要！）
if hasattr(engine, 'scaffolder'):
    engine.scaffolder.experience_manager = experience_manager
    engine.scaffolder.rollouts_per_generator = 3

# 4. 初始化训练器
trainer = TrainingFreeGRPOTrainer(
    causal_engine=engine,
    experience_manager=experience_manager,
    rollouts_per_generator=3,
    num_epochs=3,
    verbose=True
)

# 5. 开始训练
trainer.train(training_problems)
```

---

## 🧪 测试验证

### 快速测试

```bash
# 测试参数是否正确
python -c "
from main import CausalReasoningEngine

engine = CausalReasoningEngine(
    verbose=False,
    use_multi_agent=True,
    num_generators=3,
    generator_temperature=0.3,
    critic_temperature=0.0,
    computation_mode='llm'
)
print('✅ Engine initialized successfully!')
"
```

### 完整测试

```bash
# 运行训练脚本（小规模）
python train_with_grpo.py --max-problems 3 --epochs 1
```

---

## 📝 其他参数使用示例

### 最小配置（使用所有默认值）

```python
engine = CausalReasoningEngine()
```

### 单智能体配置

```python
engine = CausalReasoningEngine(
    use_multi_agent=False,
    computation_mode='symbolic'
)
```

### 多智能体配置（调整温度）

```python
engine = CausalReasoningEngine(
    use_multi_agent=True,
    num_generators=5,                # 更多生成器
    generator_temperature=0.5,       # 更高温度（更多样化）
    critic_temperature=0.1,          # 稍高温度（略有随机性）
    computation_mode='llm'
)
```

### 自定义知识库路径

```python
engine = CausalReasoningEngine(
    knowledge_base_path="my_kb/custom.json",
    auto_enrich_kb=False,            # 不自动丰富
    min_rules_threshold=10           # 更高阈值
)
```

---

## 🔧 常见错误检查清单

在调用 `CausalReasoningEngine()` 时，确保：

- [ ] ✅ 只使用有效的参数（见上面列表）
- [ ] ✅ `computation_mode` 只能是 "symbolic" 或 "llm"
- [ ] ✅ 温度值在合理范围内（0.0-1.0）
- [ ] ✅ `num_generators` 是正整数
- [ ] ❌ 不要使用 `use_vector_retriever`
- [ ] ❌ 不要使用未定义的参数

---

## 📚 相关文档

- 今日总结: `TODAY_SUMMARY.md`
- 导入修复: `ENGINE_IMPORT_FIX.md`
- GRPO 快速开始: `GRPO快速开始.md`
- 主引擎代码: `main.py`

---

## ✅ 修复验证

### 修复前
```
❌ TypeError: __init__() got an unexpected keyword argument 'use_vector_retriever'
```

### 修复后
```
✅ Engine initialized successfully!
✅ Training script runs without parameter errors
```

---

## 🎯 总结

### 问题
- ❌ 使用了不存在的 `use_vector_retriever` 参数

### 解决方案
- ✅ 删除该参数
- ✅ 使用正确的参数列表

### 状态
- ✅ **已修复，可以正常运行！**

---

**修复完成时间**: 2025-01-XX  
**修复人**: AI Assistant  
**验证状态**: ✅ 通过

---

**现在可以正常运行 GRPO 训练了！🎉**

