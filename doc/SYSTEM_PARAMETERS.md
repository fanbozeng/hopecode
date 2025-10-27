# 🎛️ 系统关键参数与阈值配置指南

## 📋 目录

1. [参数总览](#参数总览)
2. [LLM调用参数](#llm调用参数)
3. [知识检索参数](#知识检索参数)
4. [符号执行参数](#符号执行参数)
5. [结果验证参数](#结果验证参数)
6. [性能控制参数](#性能控制参数)
7. [答案比较参数](#答案比较参数)
8. [推荐配置](#推荐配置)

---

## 🎯 参数总览

### 核心参数速查表

| 参数类别 | 关键参数 | 默认值 | 影响 |
|---------|---------|--------|------|
| LLM调用 | temperature | 0.0-0.3 | 确定性 vs 创造性 |
| 知识检索 | min_overlap | 1 | 检索精度 |
| 知识检索 | max_rules | 5 | 知识数量 |
| 符号执行 | numerical_tolerance | 1e-6 | 数值精度 |
| 答案比较 | answer_tolerance | 1e-6 | 答案判定 |
| 性能控制 | enable_cache | True | 速度 vs 准确性 |

---

## 🤖 LLM调用参数

### 1. Temperature (温度参数)

**位置**: `scaffolder.py`, `synthesizer.py`

```python
# 在 scaffolder.py 第270行
response = self.llm_client.complete(prompt, temperature=0.0)

# 在 synthesizer.py 第160行和第245行
explanation = self.llm_client.complete(prompt, temperature=0.3)
```

**作用**: 控制LLM输出的随机性

| 值 | 效果 | 适用场景 |
|---|------|----------|
| **0.0** | 完全确定性，每次输出相同 | ✅ 生成计划 (scaffolding) |
| **0.1-0.3** | 轻微变化，更自然 | ✅ 生成解释 (explanation) |
| **0.5-0.7** | 较大变化，有创意 | ⚠️ 不推荐用于数学问题 |
| **0.8-1.0** | 高度随机，很有创意 | ❌ 不适合本系统 |

**推荐配置**:
```python
SCAFFOLDING_TEMPERATURE = 0.0  # 计划生成必须确定
EXPLANATION_TEMPERATURE = 0.3  # 解释可以稍有变化
VALIDATION_TEMPERATURE = 0.3   # 验证可以稍有变化
```

**影响**:
- ✅ **太低(0.0)**: 输出机械，但准确
- ⚠️ **太高(>0.5)**: 输出创意，但可能偏离

---

### 2. Max Tokens (最大令牌数)

**位置**: LLM客户端配置

```python
# 默认值（在API调用中）
max_tokens = 4096  # Anthropic默认
```

**作用**: 限制LLM单次输出的最大长度

**推荐配置**:
```python
SCAFFOLDING_MAX_TOKENS = 2048   # 计划通常较短
EXPLANATION_MAX_TOKENS = 1024   # 解释中等长度
VALIDATION_MAX_TOKENS = 1024    # 验证中等长度
```

**影响**:
- ❌ **太低(<512)**: 可能截断重要信息
- ✅ **适中(1024-2048)**: 平衡成本和质量
- ⚠️ **太高(>4096)**: 增加成本，不一定有用

---

### 3. Model Selection (模型选择)

**位置**: `.env` 文件

```env
# SiliconFlow模型选择
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct  # 默认

# 其他选项:
# Qwen/Qwen2-7B-Instruct    - 更快，更便宜，质量稍低
# Qwen/Qwen2.5-72B-Instruct - 平衡性能和成本 ⭐推荐
# deepseek-ai/DeepSeek-V3   - 高质量，稍贵
```

**性能对比**:

| 模型 | 速度 | 成本 | 准确率 | 推荐场景 |
|------|-----|------|--------|----------|
| Qwen2-7B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 快速测试 |
| Qwen2.5-72B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 生产环境 ⭐ |
| DeepSeek-V3 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 高要求任务 |

---

## 📚 知识检索参数

### 1. Min Overlap (最小重叠数)

**位置**: `retriever.py` 第169行

```python
def retrieve_knowledge(
    self,
    problem_text: str,
    min_overlap: int = 1,  # ⭐ 关键参数
    max_results: Optional[int] = None
) -> List[str]:
```

**作用**: 问题关键词与知识库关键词的最小匹配数

| 值 | 效果 | 优缺点 |
|---|------|--------|
| **1** | 匹配很宽松 | ✅ 不漏重要知识<br>⚠️ 可能检索到不相关的 |
| **2** | 适中 | ✅ 较好的平衡 ⭐推荐 |
| **3+** | 严格匹配 | ✅ 精确<br>❌ 可能遗漏相关知识 |

**推荐配置**:
```python
# 传统检索器
MIN_OVERLAP_DEFAULT = 1    # 宽松，适合复杂问题
MIN_OVERLAP_STRICT = 2     # 严格，适合简单问题
```

**影响**:
```python
# 示例：问题包含 ["force", "mass", "object"]

min_overlap = 1:
  ✓ 匹配: ["force", "mass", "acceleration"]  # 2个重叠
  ✓ 匹配: ["mass", "volume", "density"]      # 1个重叠
  ✓ 匹配: ["force", "distance", "work"]      # 1个重叠

min_overlap = 2:
  ✓ 匹配: ["force", "mass", "acceleration"]  # 2个重叠
  ✗ 不匹配: ["mass", "volume", "density"]    # 只有1个重叠
  ✗ 不匹配: ["force", "distance", "work"]    # 只有1个重叠
```

---

### 2. Max Results (最大结果数)

**位置**: `retriever.py` 第171行

```python
max_results: Optional[int] = None
```

**作用**: 限制返回的知识条目数量

**推荐配置**:
```python
MAX_RESULTS_TRADITIONAL = None  # 不限制，返回所有匹配的
MAX_RESULTS_AI = 5             # AI检索限制为5条（避免过载）
```

**影响**:
- ✅ **不限制(None)**: 获取所有相关知识，但可能信息过载
- ✅ **限制(3-5)**: 聚焦最相关的，提高LLM理解质量 ⭐推荐

---

### 3. AI检索器专用参数

**位置**: `ai_retriever.py`

```python
class AIKnowledgeRetriever:
    def __init__(
        self,
        knowledge_base_path: str = "data/knowledge_base.json",
        use_traditional_fallback: bool = True,  # ⭐ 是否使用传统备选
        auto_enrich_kb: bool = False,           # ⭐ 是否自动丰富知识库
        max_rules: int = 5,                     # ⭐ 最大规则数
        enable_cache: bool = True,              # ⭐ 是否启用缓存
        llm_client: Optional[LLMClient] = None,
        traditional_retriever: Optional[KnowledgeRetriever] = None,
        prompt_template_path: Optional[str] = None
    ):
```

#### 3.1 use_traditional_fallback

**作用**: AI检索失败时是否使用传统检索作为备选

```python
use_traditional_fallback = True   # ✅ 推荐：提高鲁棒性
use_traditional_fallback = False  # ⚠️ 仅当确信AI检索足够时
```

#### 3.2 auto_enrich_kb

**作用**: 是否自动将AI提取的新知识添加到知识库

```python
auto_enrich_kb = True   # ✅ 推荐：知识库持续成长
auto_enrich_kb = False  # ⭐ 推荐：保持知识库稳定（避免噪声）
```

**影响**:
- ✅ **启用**: 知识库自动扩展，覆盖更多问题
- ⚠️ **启用**: 可能引入低质量或重复的知识
- ✅ **禁用**: 知识库保持干净，可控 ⭐推荐

#### 3.3 max_rules

**作用**: AI检索时要求LLM提取的最大规则数

```python
max_rules = 3   # 少量，适合简单问题
max_rules = 5   # ⭐ 推荐：平衡覆盖和质量
max_rules = 10  # 大量，可能信息过载
```

**推荐**: **5条** - 足够覆盖多步骤问题

#### 3.4 enable_cache

**作用**: 是否缓存相同问题的检索结果

```python
enable_cache = True   # ✅ 推荐：提速，节省API调用
enable_cache = False  # 仅调试时使用
```

**影响**:
- ✅ 启用后，相同问题不会重复调用LLM
- ⚠️ 但问题稍有变化也会被视为新问题

---

## ⚙️ 符号执行参数

### 1. Numerical Tolerance (数值容差)

**位置**: `executor.py` (隐式使用)

虽然代码中未显式定义，但在SymPy求解和浮点数转换中存在：

```python
# 建议添加到 SymbolicExecutor 类
NUMERICAL_TOLERANCE = 1e-6  # 数值精度阈值
```

**作用**: 判断两个浮点数是否相等的容差

```python
# 示例
abs(5.0000001 - 5.0) < 1e-6  # True，视为相等
abs(5.00001 - 5.0) < 1e-6    # False，不相等
```

**推荐配置**:
```python
HIGH_PRECISION = 1e-10   # 高精度科学计算
STANDARD = 1e-6          # ⭐ 标准精度（推荐）
LOW_PRECISION = 1e-3     # 低精度，用于粗略比较
```

---

### 2. Variable Mapping (变量映射)

**位置**: `executor.py` 新增的 `_get_variable_mapping` 方法

这是一个**硬编码的映射表**，定义了变量名的同义词：

```python
mapping = {
    'F': 'force',
    'f': 'force',
    'm': 'mass',
    'a': 'acceleration',
    'v': 'velocity',
    'v_f': 'final_velocity',
    'v_i': 'initial_velocity',
    # ... 等等
}
```

**作用**: 解决变量名不一致问题（如 `acceleration` vs `a`）

**调优建议**:
- ✅ 根据你的领域添加专业术语映射
- ⚠️ 避免一对多映射（一个缩写对应多个全名）
- ✅ 定期审查和清理映射表

---

## ✅ 结果验证参数

### 1. Include Validation (是否包含验证)

**位置**: `main.py`, `synthesizer.py`

```python
results = engine.solve_problem(
    problem_text,
    include_validation=True  # ⭐ 是否进行反事实验证
)
```

**作用**: 控制是否生成反事实验证（What-if分析）

**性能影响**:
```
include_validation = False:
  - 速度快（少1次LLM调用）
  - 成本低
  - ⭐ 推荐用于批量评估

include_validation = True:
  - 提供因果验证
  - 增加可信度
  - ⭐ 推荐用于关键任务
```

---

### 2. Counterfactual Question Generation (反事实问题生成)

**位置**: `synthesizer.py` 第220-227行

```python
if not variable_to_change or new_value is None:
    # 自动生成
    knowns = executed_scaffold.get("knowns", {})
    if knowns:
        variable_to_change = list(knowns.keys())[0]
        original_value = knowns[variable_to_change]
        new_value = original_value * 2  # ⭐ 默认变为2倍
```

**关键参数**: `new_value = original_value * 2`

**调优建议**:
```python
# 可以改为其他倍数或变化
new_value = original_value * 1.5  # 增加50%
new_value = original_value / 2    # 减半
new_value = original_value + 10   # 增加固定值
```

---

## 📊 答案比较参数

### 答案匹配容差

**位置**: `evaluate_framework.py` 第439-479行

```python
def _compare_answers(self, expected: str, predicted: Any) -> bool:
    # 数值比较阈值
    if abs(expected_num - predicted_num) < 1e-6:  # ⭐ 关键阈值
        return True
```

**关键参数**: `1e-6` (0.000001)

**推荐配置**:

| 场景 | 阈值 | 说明 |
|-----|------|------|
| 高精度科学计算 | `1e-10` | 极高精度要求 |
| **标准数学问题** | `1e-6` | ⭐ 推荐默认值 |
| 物理问题（有效数字） | `1e-3` | 考虑测量误差 |
| 整数答案 | `0.1` | 允许轻微舍入误差 |

**示例**:
```python
expected = 3.14159265
predicted = 3.14159264

abs(expected - predicted) = 1e-8

1e-6 阈值: ✅ 匹配（1e-8 < 1e-6）
1e-10 阈值: ❌ 不匹配（1e-8 > 1e-10）
```

---

## ⚡ 性能控制参数

### 1. Verbose Mode (详细输出模式)

**位置**: 所有主要类的 `__init__` 方法

```python
engine = CausalReasoningEngine(verbose=True)  # ⭐ 控制输出详细程度
```

**影响**:
- `verbose=True`: 打印所有中间步骤，适合调试
- `verbose=False`: 仅打印关键信息，适合生产环境

**性能影响**: 
- 输出本身对性能影响很小
- 但大量输出会影响日志文件大小

---

### 2. Timeout (超时设置)

**当前状态**: ❌ 未实现

**建议添加**:
```python
# 在 LLMClient 中
class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        timeout: int = 60  # ⭐ 建议添加超时参数
    ):
        self.timeout = timeout
    
    def complete(self, prompt: str, temperature: float = 0.0) -> str:
        # 添加超时控制
        response = self.client.chat.completions.create(
            ...,
            timeout=self.timeout
        )
```

**推荐值**:
```python
QUICK_TIMEOUT = 30      # 简单问题
STANDARD_TIMEOUT = 60   # ⭐ 标准问题
LONG_TIMEOUT = 120      # 复杂问题
```

---

### 3. Batch Size (批处理大小)

**位置**: `evaluate_framework.py`

```python
parser.add_argument(
    '--limit',
    type=int,
    default=20,  # ⭐ 默认评估20个问题
    help='Limit number of problems'
)
```

**调优建议**:
```python
# 快速测试
--limit 5

# 标准评估
--limit 20-50

# 完整评估
--limit 100+
```

---

## 🎯 推荐配置

### 配置1: 快速测试环境

```python
# .env
SILICONFLOW_MODEL=Qwen/Qwen2-7B-Instruct  # 快速小模型

# 代码配置
SCAFFOLDING_TEMPERATURE = 0.0
EXPLANATION_TEMPERATURE = 0.3
MIN_OVERLAP = 1
MAX_RULES = 3
enable_cache = True
include_validation = False
TIMEOUT = 30
```

**特点**:
- ⚡ 速度快
- 💰 成本低
- ⚠️ 准确性稍低

---

### 配置2: 生产环境 ⭐推荐

```python
# .env
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct

# 代码配置
SCAFFOLDING_TEMPERATURE = 0.0
EXPLANATION_TEMPERATURE = 0.3
MIN_OVERLAP = 1
MAX_RULES = 5
enable_cache = True
include_validation = True
NUMERICAL_TOLERANCE = 1e-6
ANSWER_TOLERANCE = 1e-6
TIMEOUT = 60
use_traditional_fallback = True
auto_enrich_kb = False
```

**特点**:
- ✅ 平衡性能和成本
- ✅ 高准确性
- ✅ 有缓存和备选机制

---

### 配置3: 高精度环境

```python
# .env
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3

# 代码配置
SCAFFOLDING_TEMPERATURE = 0.0
EXPLANATION_TEMPERATURE = 0.2  # 更确定
MIN_OVERLAP = 2  # 更严格
MAX_RULES = 7
enable_cache = False  # 每次都重新计算
include_validation = True
NUMERICAL_TOLERANCE = 1e-10  # 高精度
ANSWER_TOLERANCE = 1e-8
TIMEOUT = 120
```

**特点**:
- 🎯 最高准确性
- 💰 成本较高
- 🐢 速度较慢

---

## 📊 参数影响矩阵

| 参数 ↓ 指标 → | 准确性 | 速度 | 成本 | 鲁棒性 |
|--------------|--------|------|------|--------|
| **temperature ↑** | ↓ | → | → | ↓ |
| **min_overlap ↑** | ↑ | ↑ | → | ↓ |
| **max_rules ↑** | ↑ | ↓ | ↑ | ↑ |
| **tolerance ↑** | ↓ | → | → | ↑ |
| **enable_cache** | → | ↑↑ | ↓ | → |
| **include_validation** | ↑ | ↓ | ↑ | ↑ |
| **use_fallback** | ↑ | ↓ | → | ↑↑ |
| **auto_enrich** | ↑/↓ | ↓ | → | ↓ |

**图例**:
- ↑ 提高
- ↓ 降低
- → 无影响
- ↑↑ 显著提高
- ↑/↓ 不确定（可能提高也可能降低）

---

## 🔧 参数调优建议

### 1. 如何选择 temperature？

```python
# 决策树
if task == "生成计划":
    temperature = 0.0  # 必须确定
elif task == "生成解释":
    if need_creativity:
        temperature = 0.5
    else:
        temperature = 0.3  # ⭐ 推荐
elif task == "验证":
    temperature = 0.3
```

### 2. 如何选择 min_overlap？

```python
if problem_is_complex:
    min_overlap = 1  # 宽松，避免遗漏
elif knowledge_base_is_large:
    min_overlap = 2  # 严格，减少噪声
else:
    min_overlap = 1  # ⭐ 默认
```

### 3. 如何选择 max_rules？

```python
max_rules = min(
    estimated_steps * 2,  # 每步需要1-2条规则
    10  # 上限
)

# 示例
single_step_problem: max_rules = 3
multi_step_problem: max_rules = 5-7  # ⭐ 推荐
very_complex: max_rules = 10
```

### 4. 如何选择 tolerance？

```python
if problem_type == "理论计算":
    tolerance = 1e-10  # 高精度
elif problem_type == "物理实验":
    tolerance = 1e-3   # 考虑测量误差
else:
    tolerance = 1e-6   # ⭐ 标准
```

---

## 📝 配置检查清单

在部署前，检查以下配置：

### 必选配置 ✅

- [ ] API密钥已配置（`.env`文件）
- [ ] LLM模型已选择
- [ ] temperature参数已设置
- [ ] 知识库路径正确

### 推荐配置 ⭐

- [ ] min_overlap = 1
- [ ] max_rules = 5
- [ ] enable_cache = True
- [ ] numerical_tolerance = 1e-6
- [ ] answer_tolerance = 1e-6
- [ ] timeout = 60

### 可选配置 🔧

- [ ] auto_enrich_kb（根据需求）
- [ ] include_validation（生产环境建议True）
- [ ] verbose（调试时True，生产环境False）

---

## 💡 常见问题

### Q1: 为什么我的系统总是检索不到知识？

**A**: 检查 `min_overlap` 是否设置过高
```python
# 降低阈值
min_overlap = 1  # 而不是 2 或 3
```

### Q2: 为什么答案总是被判定为错误？

**A**: 检查 `answer_tolerance` 是否过严格
```python
# 增加容差
tolerance = 1e-3  # 而不是 1e-10
```

### Q3: 如何提高系统速度？

**A**: 优化这些参数
```python
enable_cache = True
include_validation = False
max_rules = 3
使用更快的模型（Qwen2-7B）
```

### Q4: 如何提高准确性？

**A**: 优化这些参数
```python
temperature = 0.0
max_rules = 7
include_validation = True
use_traditional_fallback = True
使用更好的模型（DeepSeek-V3）
```

---

## 📚 总结

### 最重要的5个参数

1. **temperature** (0.0-0.3) - 控制确定性
2. **min_overlap** (1-2) - 控制检索精度
3. **max_rules** (3-7) - 控制知识数量
4. **tolerance** (1e-6) - 控制答案判定
5. **enable_cache** (True) - 控制性能

### 快速优化指南

```python
# 🚀 追求速度
temperature = 0.0
max_rules = 3
enable_cache = True
include_validation = False

# 🎯 追求准确性
temperature = 0.0
max_rules = 7
enable_cache = False
include_validation = True
use_traditional_fallback = True

# 💰 追求成本效率
使用小模型 (Qwen2-7B)
enable_cache = True
max_rules = 3
include_validation = False
```

---

**创建时间**: 2024年10月
**版本**: 1.0
**用途**: 系统参数配置指南

_记住：没有完美的配置，只有最适合你场景的配置！_ 🎯

