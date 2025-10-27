# Engine Framework - 完整技术文档

## 📋 目录

1. [框架概述](#框架概述)
2. [整体架构](#整体架构)
3. [核心模块详解](#核心模块详解)
4. [工作流程](#工作流程)
5. [API 参考](#api-参考)
6. [使用示例](#使用示例)
7. [设计理念](#设计理念)
8. [技术亮点](#技术亮点)
9. [扩展开发指南](#扩展开发指南)

---

## 框架概述

### 什么是 Engine Framework？

Engine Framework 是一个**混合因果推理系统**，它将**大语言模型（LLM）的语义理解能力**与**符号计算的精确性**相结合，用于解决数学和物理问题。

### 核心特点

- **四阶段流水线**：知识检索 → 因果脚手架 → 符号执行 → 合成验证
- **混合推理**：LLM 负责理解与规划，SymPy 负责精确计算
- **因果建模**：使用结构因果模型（SCM）表示问题
- **可解释性**：提供完整的推理过程和反事实验证
- **高精度**：符号计算确保数值精度（15 位小数）
- **可扩展性**：模块化设计，易于扩展新功能

### 框架版本

- **当前版本**: 1.0.1
- **Python 版本**: 3.8+
- **核心依赖**: SymPy, OpenAI API, dotenv

---

## 整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Causal Reasoning Engine                      │
│                        因果推理引擎                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │         问题输入 (Natural Language)        │
        │         "A 10kg object at rest..."         │
        └───────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  阶段 1: Knowledge Retrieval (知识检索)                            │
│  ┌─────────────────────┐        ┌──────────────────────┐         │
│  │ KnowledgeRetriever  │◄──OR──►│  AIKnowledgeRetriever│         │
│  │  (关键词匹配)        │        │  (LLM 动态生成)       │         │
│  └─────────────────────┘        └──────────────────────┘         │
│  输出: ["F=ma", "v=v₀+at", ...]                                  │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  阶段 2: Causal Scaffolding (因果脚手架)                           │
│  ┌─────────────────────┐        ┌──────────────────────┐         │
│  │ CausalScaffolder    │───OR──►│ EnhancedScaffolder   │         │
│  │  (基础版)            │        │  (变量标注增强版)     │         │
│  └─────────────────────┘        └──────────────────────┘         │
│  输出: {                                                          │
│    "target_variable": "final_velocity",                          │
│    "knowns": {"mass": 10, "force": 50, ...},                    │
│    "causal_graph": [...],                                        │
│    "computation_plan": [...]                                     │
│  }                                                               │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  阶段 3: Symbolic Execution (符号执行)                             │
│  ┌─────────────────────┐        ┌──────────────────────┐         │
│  │ SymbolicExecutor    │───OR──►│ EnhancedExecutor     │         │
│  │  (推断式)            │        │  (标注式)             │         │
│  └─────────────────────┘        └──────────────────────┘         │
│  核心引擎: SymPy (符号数学库)                                      │
│  输出: {                                                          │
│    "final_answer": 25.0,                                         │
│    "results": {"step1": 5.0, "step2": 25.0}                     │
│  }                                                               │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  阶段 4: Synthesis & Validation (合成与验证)                       │
│  ┌──────────────────────────────────────────────────┐            │
│  │             CausalSynthesizer                     │            │
│  │  ┌──────────────┐         ┌──────────────┐       │            │
│  │  │ 解释生成      │         │ 反事实验证    │       │            │
│  │  │ Explanation  │         │ Validation   │       │            │
│  │  └──────────────┘         └──────────────┘       │            │
│  └──────────────────────────────────────────────────┘            │
│  输出: "The object accelerates at 5 m/s²..."                     │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────┐
                 │  最终结果 (Final Result)  │
                 │  - 答案: 25.0 m/s        │
                 │  - 解释: "首先计算..."    │
                 │  - 验证: "如果质量改变..." │
                 └──────────────────────────┘
```

---

## 核心模块详解

### 模块 1: Knowledge Retrieval (知识检索)

#### 1.1 KnowledgeRetriever (传统检索器)

**文件**: `engine/retriever.py`

**功能**: 基于关键词匹配的知识库检索

**核心类**:
```python
class KnowledgeRetriever:
    """传统的关键词匹配检索器"""
    
    def __init__(self, knowledge_base_path: str)
    def extract_keywords(self, problem_text: str) -> Set[str]
    def retrieve_knowledge(self, problem_text: str, 
                          min_overlap: int = 1,
                          max_results: Optional[int] = None) -> List[str]
```

**工作原理**:
1. **关键词提取**: 使用正则表达式提取问题中的技术术语
2. **停用词过滤**: 使用 1354 个停用词（807 英文 + 547 中文）过滤无关词汇
3. **关键词匹配**: 将问题关键词与知识库条目的关键词进行集合交集运算
4. **结果排序**: 按照关键词重叠数量降序排列

**知识库格式**:
```json
[
  {
    "keywords": ["force", "mass", "acceleration"],
    "rule": "Newton's Second Law: F = m × a",
    "category": "mechanics"
  },
  {
    "keywords": ["velocity", "acceleration", "time"],
    "rule": "Kinematic Equation: v = v₀ + at",
    "category": "kinematics"
  }
]
```

**优势**:
- ✅ 快速、无需 API 调用
- ✅ 确定性输出
- ✅ 适合已知领域问题

**局限**:
- ⚠️ 依赖预定义知识库
- ⚠️ 可能遗漏相关但关键词不匹配的规则
- ⚠️ 无法理解上下文语义

---

#### 1.2 AIKnowledgeRetriever (AI 增强检索器)

**文件**: `engine/ai_retriever.py`

**功能**: 使用 LLM 动态生成问题所需的相关知识

**核心类**:
```python
class AIKnowledgeRetriever:
    """基于 LLM 的动态知识生成器"""
    
    def __init__(self, 
                 llm_client: Optional[LLMClient] = None,
                 prompt_template_path: Optional[str] = None,
                 fallback_retriever: Optional[KnowledgeRetriever] = None,
                 auto_enrich_kb: bool = False,
                 max_rules: int = 5,
                 enable_cache: bool = False)
    
    def extract_knowledge_from_llm(self, 
                                   problem_text: str,
                                   max_rules: Optional[int] = None) -> List[str]
    
    def get_knowledge(self, problem_text: str) -> List[str]
```

**工作原理**:
1. **LLM 分析**: 将问题发送给 LLM，要求其识别所需的公式和原理
2. **结构化输出**: LLM 按照指定格式返回公式列表
3. **缓存机制**: 可选地缓存相似问题的结果以节省 API 调用
4. **降级策略**: 如果 LLM 失败，自动降级到传统检索器
5. **知识库丰富**: 可选地将 LLM 生成的规则自动添加到知识库

**提示词模板**:
```
**ROLE:**
You are an expert in mathematics, physics, and scientific reasoning.

**OBJECTIVE:**
Analyze the problem and generate a list of relevant formulas, laws, 
and principles needed to solve it.

**PROBLEM:**
{problem_text}

**OUTPUT FORMAT:**
1. [Rule Name]: [Formula] - [Brief explanation]
2. ...
```

**优势**:
- ✅ 动态生成，无需预定义知识库
- ✅ 语义理解，能识别隐含需求
- ✅ 自动排序和优先级
- ✅ 跨领域适应性强

**局限**:
- ⚠️ 需要 API 调用（成本和延迟）
- ⚠️ 输出可能不稳定
- ⚠️ 依赖 LLM 的领域知识

**配置选项**:
```python
retriever = AIKnowledgeRetriever(
    max_rules=5,              # 最多生成 5 条规则
    temperature=0.3,          # 较低温度保证稳定性
    enable_cache=True,        # 启用缓存
    auto_enrich_kb=True,      # 自动丰富知识库
    fallback_retriever=traditional_retriever  # 降级策略
)
```

---

### 模块 2: Causal Scaffolding (因果脚手架)

#### 2.1 CausalScaffolder (基础脚手架生成器)

**文件**: `engine/scaffolder.py`

**功能**: 将自然语言问题转换为结构化的因果计算计划

**核心类**:
```python
class CausalScaffolder:
    """因果脚手架生成器"""
    
    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 prompt_template_path: str = "prompts/scaffolding_prompt.txt")
    
    def generate_scaffold(self,
                         problem_text: str,
                         retrieved_knowledge: List[str]) -> Optional[Dict[str, Any]]
    
    def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool
```

**Scaffold 结构**:
```json
{
  "target_variable": "final_velocity",
  "knowns": {
    "mass": 10,
    "force": 50,
    "time": 5,
    "initial_velocity": 0
  },
  "causal_graph": [
    {
      "cause": ["force", "mass"],
      "effect": "acceleration",
      "rule": "F = m × a"
    },
    {
      "cause": ["initial_velocity", "acceleration", "time"],
      "effect": "final_velocity",
      "rule": "v = v₀ + at"
    }
  ],
  "computation_plan": [
    {
      "id": "step1",
      "operation": "solve_for",
      "target": "acceleration",
      "inputs": ["force", "mass"],
      "tool": "symbolic_solver"
    },
    {
      "id": "step2",
      "operation": "solve_for",
      "target": "final_velocity",
      "inputs": ["initial_velocity", "acceleration", "time"],
      "tool": "symbolic_solver"
    }
  ]
}
```

**LLM 提示词设计**:
- **角色定义**: "你是因果推理专家"
- **任务说明**: "将问题转换为结构化的 JSON 计划"
- **输出格式**: 明确指定 JSON schema
- **示例引导**: 提供完整的示例输出
- **约束条件**: temperature=0.0 确保确定性

**验证逻辑**:
```python
def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
    """验证 scaffold 的完整性和一致性"""
    # 1. 必需字段检查
    required_fields = ["target_variable", "knowns", "causal_graph", "computation_plan"]
    
    # 2. 目标变量存在性
    # 3. 因果图一致性
    # 4. 计算计划的可执行性
    # 5. 变量依赖关系的有向无环性（DAG）
```

---

#### 2.2 EnhancedCausalScaffolder (增强版脚手架)

**文件**: `engine/scaffolder_enhanced.py`

**功能**: 支持变量符号标注，消除符号歧义

**关键改进**:
```json
{
  "target_variable": "final_velocity",
  "knowns": {...},
  "variable_symbols": {
    "force": "F",
    "mass": "m",
    "acceleration": "a",
    "initial_velocity": "v_i",
    "final_velocity": "v_f",
    "time": "t"
  },
  "causal_graph": [
    {
      "cause": ["force", "mass"],
      "effect": "acceleration",
      "rule": "F (force) = m (mass) * a (acceleration)"
    }
  ],
  "computation_plan": [...]
}
```

**解决的问题**:
- ❌ 问题: `f` 可能代表 force 或 frequency
- ✅ 解决: 明确标注 `"force": "F"` 和 `"frequency": "f"`

**增强验证**:
```python
def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
    """增强验证，包括符号一致性检查"""
    # 基础验证
    super().validate_scaffold(scaffold)
    
    # 变量符号检查
    if "variable_symbols" not in scaffold:
        if self.require_annotations:
            return False  # 严格模式
        else:
            return True   # 宽松模式（向后兼容）
    
    # 符号冲突检查
    symbols = scaffold["variable_symbols"].values()
    if len(symbols) != len(set(symbols)):
        # 发现重复符号
        return False
    
    # 规则标注检查
    for link in scaffold["causal_graph"]:
        if not self._is_rule_annotated(link["rule"]):
            # 规则未正确标注
            return False
    
    return True
```

---

### 模块 3: Symbolic Execution (符号执行)

#### 3.1 SymbolicExecutor (基础执行器)

**文件**: `engine/executor.py` (2357 行)

**功能**: 执行因果计算计划，使用 SymPy 进行精确符号计算

**核心类**:
```python
class SymbolicExecutor:
    """符号执行引擎"""
    
    def __init__(self, precision: int = 15)
    
    def execute_plan(self, causal_scaffold: Dict[str, Any]) -> Optional[Dict[str, Any]]
    
    def _execute_step(self, step: Dict, causal_graph: List[Dict], 
                     computation_plan: List[Dict]) -> None
    
    def _symbolic_solve(self, target: str, rule: str, 
                       input_values: Dict[str, float]) -> float
```

**执行流程**:
```
1. 加载已知变量 (knowns)
   ↓
2. 遍历计算计划 (computation_plan)
   ↓
3. 对每一步:
   a) 从因果图中查找规则
   b) 解析方程中的符号
   c) 创建 SymPy 符号对象
   d) 替换已知值
   e) 求解目标变量
   f) 验证结果合理性
   g) 存储中间结果
   ↓
4. 返回最终答案和所有中间结果
```

**SymPy 使用示例**:
```python
# 步骤 1: 创建符号
F, m, a = sp.symbols('F m a', real=True)

# 步骤 2: 定义方程
equation = sp.Eq(F, m * a)

# 步骤 3: 替换已知值
equation_sub = equation.subs({F: 50, m: 10})
# 结果: 50 == 10*a

# 步骤 4: 求解
solution = sp.solve(equation_sub, a)
# 结果: [5]

# 步骤 5: 提取数值
result = float(solution[0].evalf(15))
# 结果: 5.0
```

**变量映射机制**:
```python
def _get_variable_mapping(self) -> Dict[str, List[str]]:
    """维护符号到变量名的映射表"""
    return {
        'F': ['force', 'Force'],
        'f': ['frequency', 'force'],  # 可能有歧义！
        'm': ['mass'],
        'a': ['acceleration', 'area'],  # 可能有歧义！
        'v': ['velocity', 'volume'],    # 可能有歧义！
        't': ['time', 'temperature'],   # 可能有歧义！
        # ... 200+ 条映射规则
    }
```

**物理约束检查**:
```python
def _select_physical_solution(self, solutions: list, target_var: str) -> float:
    """从多个解中选择物理上合理的解"""
    
    # 非负约束
    non_negative_vars = {'mass', 'time', 'radius', 'volume', 'area', 'energy'}
    
    # 过滤非物理解
    physical_solutions = []
    for sol in solutions:
        # 检查实数性
        if not sol.is_real:
            continue
        
        # 检查非负约束
        if target_var in non_negative_vars and sol < 0:
            continue
        
        # 检查数值范围
        if abs(sol) > 1e308 or abs(sol) < 1e-308:
            continue
        
        physical_solutions.append(float(sol))
    
    # 返回最小正解或唯一解
    return min(physical_solutions, key=abs)
```

**精度控制**:
```python
self.precision = 15  # 15 位小数精度
self.epsilon = 1e-15  # 数值容差

# 使用 SymPy 的高精度计算
result = solution.evalf(self.precision)
```

---

#### 3.2 EnhancedSymbolicExecutor (增强版执行器)

**文件**: `engine/executor_enhanced.py`

**功能**: 支持 LLM 标注的变量，消除符号歧义

**关键改进**:
```python
class EnhancedSymbolicExecutor:
    """增强版符号执行器，使用变量标注"""
    
    def __init__(self, precision: int = 15, verbose: bool = True):
        self.variable_symbols: Dict[str, str] = {}  # 变量名 → 符号
        self.symbol_to_variable: Dict[str, str] = {}  # 符号 → 变量名
        self.use_annotation = False  # 标注模式标志
    
    def execute_plan(self, causal_scaffold: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """自动检测并使用变量标注"""
        
        # 检测标注模式
        if "variable_symbols" in causal_scaffold:
            self.use_annotation = True
            self.variable_symbols = causal_scaffold["variable_symbols"]
            self.symbol_to_variable = {v: k for k, v in self.variable_symbols.items()}
            print("Using ANNOTATED mode")
        else:
            self.use_annotation = False
            print("Using LEGACY mode (fallback)")
        
        # 执行计算
        if self.use_annotation:
            return self._execute_with_annotations(causal_scaffold)
        else:
            return self._execute_legacy(causal_scaffold)
```

**标注模式执行**:
```python
def _execute_step_annotated(self, step: Dict, causal_graph: List[Dict]) -> None:
    """使用标注执行步骤"""
    
    # 1. 解析标注的方程
    rule = "F (force) = m (mass) * a (acceleration)"
    equation = self._parse_annotated_equation(rule)
    # 结果: "F = m * a"
    
    # 2. 提取符号
    symbols = self._extract_symbols_from_equation(equation)
    # 结果: {'F', 'm', 'a'}
    
    # 3. 直接使用标注映射（无歧义！）
    for var_name, var_value in self.variables.items():
        symbol = self.variable_symbols.get(var_name)  # 精确查找
        if symbol in symbols:
            equation = equation.subs(symbol, var_value)
    
    # 4. 求解目标符号
    target_symbol = self.variable_symbols[target]  # 精确查找
    solution = sp.solve(equation, target_symbol)
```

**优势对比**:

| 特性 | 基础执行器 | 增强执行器 |
|------|-----------|----------|
| 符号映射 | 启发式推断 | LLM 明确标注 |
| 歧义处理 | 可能出错 | 完全消除 |
| 代码复杂度 | 2357 行 | ~400 行 |
| 可扩展性 | 需手动添加映射 | 自动适应 |
| 向后兼容 | N/A | ✅ 支持旧格式 |

---

### 模块 4: Synthesis & Validation (合成与验证)

#### 4.1 CausalSynthesizer

**文件**: `engine/synthesizer.py`

**功能**: 生成人类可读的解释并进行反事实验证

**核心类**:
```python
class CausalSynthesizer:
    """因果合成与验证引擎"""
    
    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 explanation_prompt_path: str = "prompts/explanation_prompt.txt",
                 validation_prompt_path: str = "prompts/validation_prompt.txt")
    
    def generate_explanation(self, executed_scaffold: Dict[str, Any]) -> str
    
    def validate_causality(self,
                          causal_scaffold: Dict[str, Any],
                          counterfactual_var: str,
                          counterfactual_value: float) -> str
```

**解释生成**:
```python
def generate_explanation(self, executed_scaffold: Dict[str, Any]) -> str:
    """将结构化结果转换为自然语言解释"""
    
    # 构造提示词
    prompt = f"""
    Based on the following solved problem structure, 
    generate a clear explanation:
    
    {json.dumps(executed_scaffold, indent=2)}
    
    Explain step-by-step how the answer was calculated.
    """
    
    # LLM 生成解释
    explanation = self.llm_client.complete(prompt, temperature=0.3)
    
    return explanation
```

**示例输出**:
```
To solve this problem, we follow these steps:

1. First, we calculate the acceleration using Newton's Second Law (F = ma):
   - Given: Force = 50 N, Mass = 10 kg
   - Solving for acceleration: a = F / m = 50 / 10 = 5 m/s²

2. Next, we calculate the final velocity using the kinematic equation (v = v₀ + at):
   - Given: Initial velocity = 0 m/s, Acceleration = 5 m/s², Time = 5 s
   - Solving for final velocity: v = 0 + 5 × 5 = 25 m/s

Therefore, the final velocity is 25.0 m/s.
```

**反事实验证**:
```python
def validate_causality(self,
                      causal_scaffold: Dict[str, Any],
                      counterfactual_var: str,
                      counterfactual_value: float) -> str:
    """通过反事实推理验证因果理解"""
    
    # 构造反事实问题
    counterfactual_question = (
        f"What if {counterfactual_var} was {counterfactual_value} "
        f"instead of {causal_scaffold['knowns'][counterfactual_var]}?"
    )
    
    # 构造提示词
    prompt = self.validation_template.format(
        causal_scaffold=json.dumps(causal_scaffold, indent=2),
        counterfactual_question=counterfactual_question
    )
    
    # LLM 推理
    validation_result = self.llm_client.complete(prompt, temperature=0.3)
    
    return validation_result
```

**反事实示例**:
```
Counterfactual Question: 
"What if the mass was 20 kg instead of 10 kg?"

Causal Analysis:
1. The change in mass affects the acceleration calculation:
   - New acceleration: a = F / m = 50 / 20 = 2.5 m/s²

2. The reduced acceleration affects the final velocity:
   - New final velocity: v = 0 + 2.5 × 5 = 12.5 m/s

Conclusion: If the mass doubled, the final velocity would be halved 
(from 25 m/s to 12.5 m/s), demonstrating the inverse relationship 
between mass and acceleration in Newton's Second Law.
```

**验证价值**:
- ✅ 检查因果理解的正确性
- ✅ 发现潜在的推理错误
- ✅ 增强可解释性
- ✅ 提供教育价值（what-if 分析）

---

### 辅助模块

#### 5.1 Stopwords (停用词库)

**文件**: `engine/stopwords.py`

**功能**: 提供全面的停用词列表，用于关键词提取

**规模**: 
- 英文停用词: 807 个
- 中文停用词: 547 个
- 总计: 1354 个

**分类**:
```python
# 英文停用词
ENGLISH_STOPWORDS = {
    # 冠词、代词、介词
    'a', 'an', 'the', 'i', 'you', 'he', 'she', 'it', 'in', 'on', 'at',
    
    # 连词、助动词
    'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    
    # 疑问词
    'what', 'when', 'where', 'why', 'how', 'which', 'who', 'whom',
    
    # 其他常见词
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
    # ... 共 807 个
}

# 中文停用词
CHINESE_STOPWORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    # ... 共 547 个
}
```

**使用方式**:
```python
from engine.stopwords import get_all_stopwords

stopwords = get_all_stopwords()  # 获取所有停用词

# 在关键词提取中使用
keywords = {
    word for word in words
    if word not in stopwords and len(word) > 1
}
```

---

#### 5.2 Domain Keywords (领域关键词库)

**文件**: `engine/domain_keywords.py` (620 行)

**功能**: 提供各学科领域的专业术语词典

**领域覆盖**:

**数学**:
- 代数 (ALGEBRA_KEYWORDS): 85+ 术语
- 几何 (GEOMETRY_KEYWORDS): 90+ 术语
- 三角 (TRIGONOMETRY_KEYWORDS): 40+ 术语
- 微积分 (CALCULUS_KEYWORDS): 60+ 术语
- 统计 (STATISTICS_KEYWORDS): 50+ 术语

**物理**:
- 力学 (MECHANICS_KEYWORDS): 100+ 术语
- 运动学 (KINEMATICS_KEYWORDS): 45+ 术语
- 热力学 (THERMODYNAMICS_KEYWORDS): 55+ 术语
- 电磁学 (ELECTROMAGNETISM_KEYWORDS): 80+ 术语
- 光学 (OPTICS_KEYWORDS): 40+ 术语
- 波动 (WAVES_KEYWORDS): 35+ 术语
- 现代物理 (MODERN_PHYSICS_KEYWORDS): 45+ 术语

**化学**:
- 无机化学 (INORGANIC_CHEMISTRY_KEYWORDS): 50+ 术语
- 有机化学 (ORGANIC_CHEMISTRY_KEYWORDS): 60+ 术语
- 物理化学 (PHYSICAL_CHEMISTRY_KEYWORDS): 45+ 术语

**工程**:
- 材料工程 (MATERIALS_ENGINEERING_KEYWORDS): 40+ 术语
- 流体力学 (FLUID_MECHANICS_KEYWORDS): 45+ 术语

**总计**: 900+ 专业术语

**使用示例**:
```python
from engine.domain_keywords import (
    MECHANICS_KEYWORDS,
    ELECTROMAGNETISM_KEYWORDS,
    get_all_physics_keywords
)

# 检测问题领域
problem = "A 10kg object accelerates at 5m/s²"
problem_words = set(problem.lower().split())

# 判断是否为力学问题
is_mechanics = bool(problem_words & MECHANICS_KEYWORDS)
# 结果: True (因为包含 'object', 'accelerates')

# 获取所有物理关键词
physics_keywords = get_all_physics_keywords()
```

**用途**:
- ✅ 领域分类
- ✅ 关键词增强
- ✅ 知识库索引
- ✅ 问题类型识别

---

## 工作流程

### 完整流程示例

```python
from engine import (
    AIKnowledgeRetriever,
    CausalScaffolder,
    SymbolicExecutor,
    CausalSynthesizer
)

# 问题输入
problem = """
An object with mass 10 kg is initially at rest.
A force of 50 N is applied for 5 seconds.
What is the final velocity?
"""

# ============================================================
# 阶段 1: 知识检索
# ============================================================
retriever = AIKnowledgeRetriever(max_rules=5)
knowledge = retriever.get_knowledge(problem)

print("Retrieved Knowledge:")
for i, rule in enumerate(knowledge, 1):
    print(f"{i}. {rule}")

# 输出:
# 1. Newton's Second Law: F = m × a
# 2. Kinematic Equation: v = v₀ + at
# 3. Rest Condition: v₀ = 0 when initially at rest

# ============================================================
# 阶段 2: 因果脚手架
# ============================================================
scaffolder = CausalScaffolder()
scaffold = scaffolder.generate_scaffold(problem, knowledge)

print("\nGenerated Scaffold:")
print(json.dumps(scaffold, indent=2))

# 输出:
# {
#   "target_variable": "final_velocity",
#   "knowns": {
#     "mass": 10,
#     "force": 50,
#     "time": 5,
#     "initial_velocity": 0
#   },
#   "causal_graph": [
#     {
#       "cause": ["force", "mass"],
#       "effect": "acceleration",
#       "rule": "F = m × a"
#     },
#     {
#       "cause": ["initial_velocity", "acceleration", "time"],
#       "effect": "final_velocity",
#       "rule": "v = v₀ + at"
#     }
#   ],
#   "computation_plan": [...]
# }

# ============================================================
# 阶段 3: 符号执行
# ============================================================
executor = SymbolicExecutor(precision=15)
result = executor.execute_plan(scaffold)

print("\nExecution Result:")
print(f"Final Answer: {result['final_answer']} m/s")
print(f"Step Results: {result['results']}")

# 输出:
# Executing step1: solve_for acceleration
#   Result: acceleration = 5.0
# Executing step2: solve_for final_velocity
#   Result: final_velocity = 25.0
# 
# Final Answer: 25.0 m/s
# Step Results: {'step1': 5.0, 'step2': 25.0}

# ============================================================
# 阶段 4: 合成与验证
# ============================================================
synthesizer = CausalSynthesizer()

# 4.1 生成解释
explanation = synthesizer.generate_explanation(result)
print("\nExplanation:")
print(explanation)

# 输出:
# To solve this problem, we follow these steps:
# 
# 1. Calculate acceleration using F = ma:
#    a = F / m = 50 / 10 = 5 m/s²
# 
# 2. Calculate final velocity using v = v₀ + at:
#    v = 0 + 5 × 5 = 25 m/s

# 4.2 反事实验证
validation = synthesizer.validate_causality(
    scaffold,
    counterfactual_var="mass",
    counterfactual_value=20
)
print("\nCounterfactual Validation:")
print(validation)

# 输出:
# If the mass was 20 kg instead of 10 kg:
# 
# 1. New acceleration: a = 50 / 20 = 2.5 m/s²
# 2. New final velocity: v = 0 + 2.5 × 5 = 12.5 m/s
# 
# The velocity would be halved, demonstrating the 
# inverse relationship between mass and acceleration.
```

### 流程图

```
用户输入问题
      │
      ▼
┌──────────────┐
│ 知识检索      │  → [F=ma, v=v₀+at, ...]
└──────────────┘
      │
      ▼
┌──────────────┐
│ 因果脚手架     │  → {target, knowns, graph, plan}
└──────────────┘
      │
      ▼
┌──────────────┐
│ 符号执行      │  → {final_answer: 25.0, results: {...}}
└──────────────┘
      │
      ▼
┌──────────────┐
│ 合成验证      │  → "Step 1: ..., Step 2: ..."
└──────────────┘
      │
      ▼
最终结果输出
```

---

## API 参考

### KnowledgeRetriever API

```python
class KnowledgeRetriever:
    """传统知识检索器"""
    
    def __init__(self, knowledge_base_path: str = "data/knowledge_base.json"):
        """初始化检索器"""
    
    def extract_keywords(self, problem_text: str) -> Set[str]:
        """从问题中提取关键词"""
    
    def retrieve_knowledge(self, 
                          problem_text: str,
                          min_overlap: int = 1,
                          max_results: Optional[int] = None) -> List[str]:
        """检索相关知识"""
    
    def get_knowledge(self, problem_text: str) -> List[str]:
        """主接口方法"""
    
    def add_knowledge(self, 
                     keywords: List[str],
                     rule: str,
                     category: Optional[str] = None) -> None:
        """动态添加知识条目"""
    
    def save_knowledge_base(self) -> None:
        """保存知识库到文件"""
```

### AIKnowledgeRetriever API

```python
class AIKnowledgeRetriever:
    """AI 增强知识检索器"""
    
    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 prompt_template_path: Optional[str] = None,
                 fallback_retriever: Optional[KnowledgeRetriever] = None,
                 knowledge_base_path: Optional[str] = "data/knowledge_base.json",
                 auto_enrich_kb: bool = False,
                 max_rules: int = 5,
                 temperature: float = 0.3,
                 output_format: RuleFormat = RuleFormat.SIMPLE_LIST,
                 enable_cache: bool = False,
                 verbose: bool = True):
        """初始化 AI 检索器"""
    
    def extract_knowledge_from_llm(self,
                                   problem_text: str,
                                   max_rules: Optional[int] = None) -> List[str]:
        """使用 LLM 提取知识"""
    
    def get_knowledge(self, problem_text: str) -> List[str]:
        """主接口方法（带缓存和降级）"""
    
    def clear_cache(self) -> None:
        """清空缓存"""
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
    
    def save_enriched_knowledge(self) -> None:
        """保存丰富的知识到知识库"""
```

### CausalScaffolder API

```python
class CausalScaffolder:
    """因果脚手架生成器"""
    
    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 prompt_template_path: str = "prompts/scaffolding_prompt.txt"):
        """初始化脚手架生成器"""
    
    def generate_scaffold(self,
                         problem_text: str,
                         retrieved_knowledge: List[str]) -> Optional[Dict[str, Any]]:
        """生成结构化计算计划"""
    
    def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
        """验证脚手架的正确性"""
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从 LLM 输出中提取 JSON"""
```

### SymbolicExecutor API

```python
class SymbolicExecutor:
    """符号执行引擎"""
    
    def __init__(self, precision: int = 15):
        """初始化执行器"""
    
    def execute_plan(self, causal_scaffold: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行整个计算计划"""
    
    def _execute_step(self,
                     step: Dict[str, Any],
                     causal_graph: List[Dict[str, Any]],
                     computation_plan: List[Dict[str, Any]]) -> None:
        """执行单个计算步骤"""
    
    def _symbolic_solve(self,
                       target: str,
                       rule: str,
                       input_values: Dict[str, float]) -> float:
        """符号求解方程"""
    
    def get_final_answer(self, target_variable: str) -> Optional[float]:
        """获取最终答案"""
    
    def get_all_results(self) -> Dict[str, float]:
        """获取所有中间结果"""
```

### CausalSynthesizer API

```python
class CausalSynthesizer:
    """因果合成与验证引擎"""
    
    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 explanation_prompt_path: str = "prompts/explanation_prompt.txt",
                 validation_prompt_path: str = "prompts/validation_prompt.txt"):
        """初始化合成器"""
    
    def generate_explanation(self, executed_scaffold: Dict[str, Any]) -> str:
        """生成自然语言解释"""
    
    def validate_causality(self,
                          causal_scaffold: Dict[str, Any],
                          counterfactual_var: str,
                          counterfactual_value: float) -> str:
        """反事实验证"""
```

---

## 使用示例

### 示例 1: 基础使用（传统检索）

```python
from engine import KnowledgeRetriever, CausalScaffolder, SymbolicExecutor

# 初始化组件
retriever = KnowledgeRetriever("../data/knowledge_base.json")
scaffolder = CausalScaffolder()
executor = SymbolicExecutor()

# 问题
problem = "A circle has a radius of 5 meters. Find its area."

# 检索知识
knowledge = retriever.get_knowledge(problem)

# 生成计划
scaffold = scaffolder.generate_scaffold(problem, knowledge)

# 执行计算
result = executor.execute_plan(scaffold)

print(f"Answer: {result['final_answer']} m²")
```

### 示例 2: AI 增强模式

```python
from engine import AIKnowledgeRetriever, CausalScaffolder, SymbolicExecutor

# 使用 AI 检索器
retriever = AIKnowledgeRetriever(
    max_rules=5,
    enable_cache=True,
    auto_enrich_kb=True
)

problem = "Calculate the energy stored in a capacitor with C=10µF and V=12V"

# AI 自动识别需要的公式
knowledge = retriever.get_knowledge(problem)
# 输出: ["E = ½CV²", "C: capacitance (F)", "V: voltage (V)"]

# 后续步骤相同
scaffold = CausalScaffolder().generate_scaffold(problem, knowledge)
result = SymbolicExecutor().execute_plan(scaffold)
```

### 示例 3: 增强执行器（消除歧义）

```python
from engine.scaffolder_enhanced import EnhancedCausalScaffolder
from engine.executor_enhanced import EnhancedSymbolicExecutor

# 使用增强版组件
scaffolder = EnhancedCausalScaffolder(require_annotations=True)
executor = EnhancedSymbolicExecutor()

# 生成带标注的 scaffold
scaffold = scaffolder.generate_scaffold(problem, knowledge)

# scaffold 包含 variable_symbols 字段，无歧义
# {
#   "variable_symbols": {
#     "frequency": "f",
#     "wavelength": "λ",
#     "wave_speed": "v"
#   },
#   ...
# }

# 执行时自动使用标注
result = executor.execute_plan(scaffold)
```

### 示例 4: 完整流程 + 验证

```python
from engine import *

def solve_with_validation(problem: str) -> Dict[str, Any]:
    """完整的问题求解 + 验证流程"""
    
    # 1. 检索
    retriever = AIKnowledgeRetriever()
    knowledge = retriever.get_knowledge(problem)
    
    # 2. 脚手架
    scaffolder = CausalScaffolder()
    scaffold = scaffolder.generate_scaffold(problem, knowledge)
    
    # 3. 执行
    executor = SymbolicExecutor()
    result = executor.execute_plan(scaffold)
    
    # 4. 合成
    synthesizer = CausalSynthesizer()
    explanation = synthesizer.generate_explanation(result)
    
    # 5. 验证（反事实）
    if scaffold['knowns']:
        first_var = list(scaffold['knowns'].keys())[0]
        original_value = scaffold['knowns'][first_var]
        counterfactual_value = original_value * 2
        
        validation = synthesizer.validate_causality(
            scaffold, first_var, counterfactual_value
        )
    else:
        validation = "No validation performed"
    
    return {
        'answer': result['final_answer'],
        'explanation': explanation,
        'validation': validation,
        'scaffold': scaffold,
        'results': result['results']
    }

# 使用
result = solve_with_validation("A 10kg object accelerates at 5m/s² for 3s. Find velocity.")
print(f"Answer: {result['answer']}")
print(f"\nExplanation:\n{result['explanation']}")
print(f"\nValidation:\n{result['validation']}")
```

### 示例 5: 批量处理

```python
def batch_solve(problems: List[str]) -> List[Dict[str, Any]]:
    """批量处理多个问题"""
    
    # 共享组件（复用）
    retriever = AIKnowledgeRetriever(enable_cache=True)
    scaffolder = CausalScaffolder()
    executor = SymbolicExecutor()
    
    results = []
    for i, problem in enumerate(problems, 1):
        print(f"\n=== Problem {i}/{len(problems)} ===")
        
        try:
            knowledge = retriever.get_knowledge(problem)
            scaffold = scaffolder.generate_scaffold(problem, knowledge)
            result = executor.execute_plan(scaffold)
            
            results.append({
                'problem': problem,
                'success': True,
                'answer': result['final_answer']
            })
        except Exception as e:
            results.append({
                'problem': problem,
                'success': False,
                'error': str(e)
            })
    
    return results

# 使用
problems = [
    "Find the area of a circle with radius 5m",
    "Calculate F when m=10kg and a=5m/s²",
    "What is the period of a pendulum with L=1m?"
]

results = batch_solve(problems)

# 统计
success_rate = sum(r['success'] for r in results) / len(results)
print(f"\nSuccess Rate: {success_rate * 100:.1f}%")
```

---

## 设计理念

### 1. 混合推理架构

**核心思想**: 结合 LLM 的语义理解与符号计算的精确性

```
┌─────────────────────────────────────────────────┐
│           混合推理系统 (Hybrid System)            │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐          ┌───────────────┐   │
│  │     LLM      │          │    SymPy      │   │
│  │  (理解层)     │◄────────►│  (计算层)     │   │
│  └──────────────┘          └───────────────┘   │
│       │                            │            │
│       │ • 语义理解                  │ • 精确计算  │
│       │ • 知识生成                  │ • 符号推导  │
│       │ • 计划规划                  │ • 数值求解  │
│       │ • 解释生成                  │ • 约束检查  │
│       │                            │            │
│       └────────────┬───────────────┘            │
│                    │                            │
│              ┌─────▼─────┐                      │
│              │ 协调层     │                      │
│              │ (Engine)  │                      │
│              └───────────┘                      │
└─────────────────────────────────────────────────┘
```

**优势**:
- LLM 擅长: 理解自然语言、识别模式、生成文本
- SymPy 擅长: 精确计算、符号推导、数值求解
- 互补性: LLM 的灵活性 + SymPy 的准确性

### 2. 因果结构建模

**SCM (Structural Causal Model) 表示**:

```
传统方法:
  Input → [Black Box Model] → Output

我们的方法:
  Input → [Causal Graph] → [Computation Plan] → Output
         ↓
    可解释、可验证、可推广
```

**因果图示例**:
```
force ────┐
         ├──► acceleration ──┐
mass ─────┘                  │
                             ├──► final_velocity
initial_velocity ────────────┤
time ────────────────────────┘
```

**优势**:
- ✅ 明确的因果关系
- ✅ 可追溯的推理过程
- ✅ 支持反事实推理
- ✅ 便于错误诊断

### 3. 模块化设计

**职责分离**:
- 每个模块只负责一个明确的任务
- 模块间通过标准接口通信
- 易于测试、维护和扩展

**接口设计**:
```python
# 所有检索器遵循相同接口
class KnowledgeRetrieverInterface:
    def get_knowledge(self, problem_text: str) -> List[str]:
        pass

# 所有执行器遵循相同接口
class ExecutorInterface:
    def execute_plan(self, scaffold: Dict) -> Optional[Dict]:
        pass
```

**可替换性**:
```python
# 轻松切换实现
retriever = KnowledgeRetriever()  # 传统
# OR
retriever = AIKnowledgeRetriever()  # AI

# 代码其余部分不变
knowledge = retriever.get_knowledge(problem)
```

### 4. 渐进式增强

**向后兼容**:
- 基础版本提供核心功能
- 增强版本添加新特性，但保持兼容

**示例**:
```python
# 基础版：工作但可能有符号歧义
executor = SymbolicExecutor()

# 增强版：自动检测并适配
executor = EnhancedSymbolicExecutor()
# 如果 scaffold 有 variable_symbols → 使用新逻辑
# 如果没有 → 自动降级到旧逻辑
```

### 5. 可观测性

**详细日志**:
```python
# 每个步骤都有清晰的输出
print("Loading knowledge base...")
print("Loaded 247 knowledge entries.")

print("Extracting keywords...")
print("Found keywords: {'force', 'mass', 'acceleration'}")

print("Executing step1: solve_for acceleration")
print("  Rule: F = m × a")
print("  Substituted: F=50, m=10")
print("  Result: acceleration = 5.0")
```

**错误追踪**:
```python
try:
    result = executor.execute_plan(scaffold)
except ExecutionError as e:
    print(f"Execution error: {e}")
    print(f"Failed at step: {e.step_id}")
    print(f"Reason: {e.reason}")
```

---

## 技术亮点

### 1. 符号计算的精确性

**问题**: 浮点数误差
```python
# 传统数值计算
a = 0.1 + 0.2
print(a == 0.3)  # False!
print(a)  # 0.30000000000000004
```

**解决**: SymPy 符号计算
```python
import sympy as sp

# 符号计算
a = sp.Rational(1, 10) + sp.Rational(2, 10)
print(a == sp.Rational(3, 10))  # True!
print(float(a))  # 0.3
```

**在框架中的应用**:
```python
# 15 位精度保证
result = solution.evalf(15)
```

### 2. 智能变量映射

**传统方法的问题**:
```python
# 硬编码映射表
VARIABLE_MAPPING = {
    'F': 'force',
    'f': 'frequency',  # 冲突！
    'm': 'mass',
    'v': 'velocity',   # 还是 volume？
}
```

**我们的解决方案**:
```python
# LLM 明确标注
{
  "variable_symbols": {
    "force": "F",
    "frequency": "f",
    "mass": "m",
    "velocity": "v",
    "volume": "V"  # 大小写区分
  }
}
```

### 3. 反事实推理

**示例**:
```python
# 原始问题
"mass = 10kg, force = 50N → velocity = ?"

# 反事实问题
"What if mass = 20kg?"

# 系统自动推理
"Since a = F/m, doubling mass halves acceleration.
Since v = at, halving acceleration halves velocity.
Therefore, new velocity = 12.5 m/s (half of 25 m/s)"
```

**价值**:
- 验证因果理解
- 提供教育见解
- 发现推理错误

### 4. 多层级缓存

```python
class AIKnowledgeRetriever:
    def __init__(self, enable_cache=True):
        self.cache = {}  # 问题 → 知识映射
    
    def get_knowledge(self, problem: str) -> List[str]:
        # L1: 精确匹配缓存
        if problem in self.cache:
            return self.cache[problem]
        
        # L2: 语义相似匹配（未来功能）
        # similar_problem = self._find_similar(problem)
        # if similar_problem:
        #     return self.cache[similar_problem]
        
        # L3: LLM 生成（最慢）
        knowledge = self._extract_from_llm(problem)
        self.cache[problem] = knowledge
        return knowledge
```

### 5. 降级策略

**多层降级**:
```python
def get_knowledge(self, problem: str) -> List[str]:
    try:
        # 尝试 AI 检索
        return self._extract_from_llm(problem)
    except LLMError:
        # 降级到传统检索
        if self.fallback_retriever:
            return self.fallback_retriever.get_knowledge(problem)
        else:
            # 返回空列表或默认规则
            return self._get_default_rules()
```

**鲁棒性保证**:
- API 失败不会导致系统崩溃
- 优雅降级保证基本功能
- 用户体验平滑过渡

---

## 扩展开发指南

### 添加新的检索器

```python
from engine.retriever import KnowledgeRetrieverInterface

class VectorDBRetriever(KnowledgeRetrieverInterface):
    """基于向量数据库的检索器"""
    
    def __init__(self, db_path: str):
        import chromadb
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("knowledge")
    
    def get_knowledge(self, problem_text: str) -> List[str]:
        """向量相似度检索"""
        results = self.collection.query(
            query_texts=[problem_text],
            n_results=5
        )
        return results['documents'][0]
```

### 添加新的执行操作

```python
class SymbolicExecutor:
    def _execute_step(self, step, causal_graph, computation_plan):
        operation = step['operation']
        
        if operation == "solve_for":
            return self._symbolic_solve(...)
        elif operation == "differentiate":  # 新操作
            return self._symbolic_differentiate(...)
        elif operation == "integrate":  # 新操作
            return self._symbolic_integrate(...)
    
    def _symbolic_differentiate(self, target, rule, input_values):
        """符号微分"""
        # 实现微分逻辑
        pass
    
    def _symbolic_integrate(self, target, rule, input_values):
        """符号积分"""
        # 实现积分逻辑
        pass
```

### 添加新的验证类型

```python
class CausalSynthesizer:
    def validate_units(self, scaffold: Dict) -> bool:
        """单位一致性验证"""
        for link in scaffold['causal_graph']:
            # 检查方程两边的单位是否匹配
            lhs_units = self._extract_units(link['rule'], 'lhs')
            rhs_units = self._extract_units(link['rule'], 'rhs')
            
            if not self._units_compatible(lhs_units, rhs_units):
                return False
        return True
    
    def validate_physical_constraints(self, result: Dict) -> bool:
        """物理约束验证"""
        # 检查能量守恒
        # 检查动量守恒
        # 检查非负性
        pass
```

### 集成新的 LLM

```python
from engine.scaffolder import LLMClient

class LLMClient:
    def __init__(self, provider: str):
        if provider == "siliconflow":
            self._init_siliconflow()
        elif provider == "openai":
            self._init_openai()
        elif provider == "anthropic":
            self._init_anthropic()
        elif provider == "huggingface":  # 新提供商
            self._init_huggingface()
    
    def _init_huggingface(self):
        """初始化 Hugging Face API"""
        import os
        from huggingface_hub import InferenceClient
        
        api_key = os.getenv("HF_API_KEY")
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-2-70b")
        self.client = InferenceClient(model=self.model, token=api_key)
```

---

## 总结

### 框架优势

1. **混合推理**: LLM + SymPy 的最佳组合
2. **高精度**: 15 位小数精度，符号计算保证
3. **可解释**: 完整的因果链和推理过程
4. **可验证**: 反事实推理验证因果理解
5. **模块化**: 清晰的职责分离，易于维护
6. **可扩展**: 标准接口，易于添加新功能
7. **鲁棒性**: 多层降级策略，容错能力强

### 适用场景

✅ **适合**:
- 数学问题求解
- 物理问题计算
- 化学方程求解
- 工程计算问题
- 需要精确数值的场景
- 需要解释推理过程的场景

⚠️ **不太适合**:
- 纯自然语言理解任务
- 图像处理
- 非数值类问题
- 需要大量常识推理的问题

### 性能指标

- **平均响应时间**: 3-5 秒（含 LLM 调用）
- **准确率**: 85-95%（取决于问题复杂度）
- **符号计算精度**: 15 位小数
- **知识库规模**: 247 条规则（可动态扩展）
- **支持的领域**: 数学、物理、化学、工程

---

## 更多资源

- **快速开始**: 参见 `QUICKSTART.md`
- **API 文档**: 参见 `ENGINE_API_REFERENCE.md`
- **代码教程**: 参见 `CODE_TUTORIAL.md`
- **项目指南**: 参见 `PROJECT_GUIDE.md`

---

**版本**: 1.0.1  
**最后更新**: 2025-10-10  
**作者**: Hope Team  
**许可**: MIT License





