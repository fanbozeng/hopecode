# Causal Evaluation Guide (Step3)
# 因果评估指南（Step3）

## 📋 概述 / Overview

这是 **Step3: Causal Evaluation** 模块，实现了 **Counterfactual Faithfulness (CF)** 评估。

This is the **Step3: Causal Evaluation** module, implementing **Counterfactual Faithfulness (CF)** evaluation.

---

## 🎯 核心思想 / Core Idea

### CF 评估公式 / CF Evaluation Formula

```
CF = (Causal Intervention + Abductive Reasoning + Logic Quality + Graph Quality) / 4
```

**四个组件，各占 1/4：**

1. **因果干预质量** (Causal Intervention Score)
   - 使用 do 算子评估节点重要性
   - 不计算具体数值，只评估影响程度
   
2. **溯因推理质量** (Abductive Reasoning Score)  🆕
   - 由果溯因，测试推理链的可逆性
   - 移除原因节点，检查推理是否仍成立
   
3. **逻辑推理质量** (Logic Quality)
   - 推理步骤的合理性和连贯性
   - 借鉴自 RewardEvaluator
   
4. **DAG 图质量** (Graph Quality)
   - 图结构的正确性（无环、连通性、因果关系）
   - 借鉴自 RewardEvaluator

---

## 🔧 1. 因果干预评估 (Causal Intervention)

### 核心思想

对 DAG 中的**每个非结果节点**提问：

> **"If we perform causal intervention do(X | other_vars), what is the impact on the final result?"**
> 
> **"如果我们对节点 X 执行因果干预 do(X | 其他变量)，对最终结果的影响有多大？"**

### 评分机制

#### 步骤 1: 分配分数池

```python
总分池 = 100 分
N = 非结果节点数量
每个节点最大分数 = 100 / N
```

**示例：**
- 10 个非结果节点 → 每个节点最多 10 分
- 5 个非结果节点 → 每个节点最多 20 分

#### 步骤 2: LLM 评估每个节点

对每个节点，LLM 评估：
1. **节点的因果路径**：从该节点到结果节点的路径
2. **干预效果**：do(节点) 会发生什么？
3. **影响程度**：critical / meaningful / peripheral

#### 步骤 3: 打分

LLM 给出 **0 到 max_score_per_node** 的分数：

- **高影响** (score ≈ max_score): 节点是关键的，移除它会破坏推理链
- **中等影响** (score ≈ max_score/2): 节点有贡献但有替代方案
- **低影响** (score ≈ 0): 节点是边缘的或冗余的

#### 步骤 4: 归一化

```python
intervention_score = Σ(node_scores) / 100
# 结果：0-1 之间
```

---

## 🔄 2. 溯因推理评估 (Abductive Reasoning) 🆕

### 核心思想

**溯因推理（Abductive Reasoning）**：由果溯因，从结果反推原因

> **"Given the result and most inputs, can we verify or infer the missing cause?"**
> 
> **"给定结果和大部分输入，能否验证或推断出缺失的原因？"**

### 评分机制

#### 步骤 1: 识别原因节点

```python
cause_nodes = dag['knowns'].keys()  # 从 knowns 中提取原因节点
```

**示例：** 如果 `knowns = {"F": 10, "m": 2}`，则原因节点为 `["F", "m"]`

#### 步骤 2: 对每个原因节点进行溯因测试

对每个原因节点：
1. **移除该节点**
2. **给定信息：**
   - 结果节点的值
   - 其他所有原因节点
3. **提问 LLM：** "推理链在这种情况下是否仍然成立？"

#### 步骤 3: 二元评分

LLM 判断：
- **成立（Holds）** → 分数 = **1**
  - 可以从结果和其他原因推断出被移除的原因
  - 推理链可以被验证
- **不成立（Doesn't Hold）** → 分数 = **0**
  - 无法推断被移除的原因
  - 推理链断裂，无法验证

#### 步骤 4: 计算平均分

```python
abductive_score = Σ(scores) / N
# N = 原因节点数量
# 结果：0-1 之间
```

---

### 溯因推理示例

#### 问题

"Calculate acceleration given F=10N and m=2kg using a=F/m"

#### DAG

```json
{
  "target_variable": "acceleration",
  "knowns": {"F": 10, "m": 2},
  "causal_graph": [
    {"cause": ["F", "m"], "effect": "acceleration", "rule": "a = F/m"}
  ]
}
```

#### 溯因测试过程

**原因节点：** `F`, `m` （共 2 个）

---

##### 测试 1: 移除 F

**给定信息：**
- 结果：acceleration = 5 m/s²
- 其他原因：m = 2 kg

**LLM 分析：**
- 使用公式 a = F/m
- 已知 a=5, m=2
- 可以反推 F = a × m = 5 × 2 = 10N ✓
- **推理链成立！**

**评分：** 1

---

##### 测试 2: 移除 m

**给定信息：**
- 结果：acceleration = 5 m/s²
- 其他原因：F = 10 N

**LLM 分析：**
- 使用公式 a = F/m
- 已知 a=5, F=10
- 可以反推 m = F / a = 10 / 5 = 2 kg ✓
- **推理链成立！**

**评分：** 1

---

#### 总分

```
abductive_score = (1 + 1) / 2 = 1.0
```

**结论：** 推理链完全可逆，溯因推理分数满分（1.0）

---

### 什么时候返回 0？

#### 示例：不可逆的推理链

**问题：** "Predict outcome based on complex function"

**DAG：**
```json
{
  "knowns": {"A": 5, "B": 3, "C": 2},
  "causal_graph": [
    {"cause": ["A", "B", "C"], "effect": "outcome", 
     "rule": "outcome = complex_nonlinear_function(A, B, C)"}
  ]
}
```

**测试：** 移除 B

**给定：** outcome=100, A=5, C=2

**LLM 分析：**
- 函数是复杂的非线性函数，不可代数反解
- 多个 B 值可能导致相同的 outcome
- **无法从 outcome 和 A, C 推断 B**
- **推理链不成立！**

**评分：** 0

---

## 📐 数学示例 / Mathematical Example

### 问题

"Calculate acceleration given F=10N and m=2kg using a=F/m"

### DAG

```json
{
  "target_variable": "acceleration",
  "knowns": {"F": 10, "m": 2},
  "causal_graph": [
    {"cause": ["F", "m"], "effect": "acceleration", "rule": "a = F/m"}
  ]
}
```

### 评估过程

**非结果节点：** `F`, `m` （共 2 个）

**每个节点最大分数：** 100 / 2 = 50 分

#### 节点 1: F (force)

**LLM 分析：**
- **因果路径：** F → acceleration（直接）
- **干预效果：** 移除 F，无法计算 a
- **影响程度：** Critical（关键）
- **分数：** 48 / 50

#### 节点 2: m (mass)

**LLM 分析：**
- **因果路径：** m → acceleration（直接）
- **干预效果：** 移除 m，无法计算 a  
- **影响程度：** Critical（关键）
- **分数：** 49 / 50

#### 总分

```
intervention_score = (48 + 49) / 100 = 0.97
```

**结论：** 两个节点都是关键的，因果干预质量很高 (0.97)

---

## 💻 使用方法 / Usage

### 基本使用

```python
from causal_evaluation import CausalFaithfulnessEvaluator
from engine.scaffolder import LLMClient

# 1. 初始化
llm_client = LLMClient()
cf_evaluator = CausalFaithfulnessEvaluator(llm_client=llm_client, verbose=True)

# 2. 准备 DAG 和问题
dag = {
    "target_variable": "acceleration",
    "knowns": {"F": 10, "m": 2},
    "causal_graph": [
        {"cause": ["F", "m"], "effect": "acceleration", "rule": "a = F/m"}
    ],
    "computation_plan": [
        {"id": "step1", "target": "acceleration", "inputs": ["F", "m"], 
         "description": "Calculate a = F/m = 10/2 = 5 m/s²"}
    ]
}

problem_text = "Calculate acceleration given F=10N and m=2kg"
reasoning_trajectory = "Using Newton's second law a=F/m, we get a = 10/2 = 5 m/s²"

# 3. 评估单个问题
cf_score, report = cf_evaluator.evaluate_cf(
    dag, 
    problem_text, 
    reasoning_trajectory
)

print(f"CF Score: {cf_score:.4f}")
print(f"Intervention: {report['components']['causal_intervention']['score']:.4f}")
print(f"Abductive:    {report['components']['abductive_reasoning']['score']:.4f}")
print(f"Logic:        {report['components']['logic_quality']['score']:.4f}")
print(f"Graph:        {report['components']['graph_quality']['score']:.4f}")
```

### 批量评估

```python
# 准备多个问题
problems = [
    {
        'dag': dag1,
        'problem_text': "Problem 1...",
        'reasoning_trajectory': "Step 1, Step 2..."
    },
    {
        'dag': dag2,
        'problem_text': "Problem 2...",
        'reasoning_trajectory': "Step 1, Step 2..."
    },
    # ... more problems
]

# 批量评估
batch_results = cf_evaluator.evaluate_cf_batch(problems)

print(f"Average CF: {batch_results['average_cf']:.4f}")
print(f"Min CF:     {batch_results['summary']['min']:.4f}")
print(f"Max CF:     {batch_results['summary']['max']:.4f}")
```

---

## 📊 输出格式 / Output Format

### 单个问题的 CF 报告

```json
{
  "cf_score": 0.88,
  "components": {
    "causal_intervention": {
      "score": 0.97,
      "weight": 0.25,
      "details": {
        "status": "success",
        "total_nodes": 3,
        "non_target_nodes": 2,
        "max_score_per_node": 50.0,
        "total_score": 97.0,
        "normalized_score": 0.97,
        "node_evaluations": [
          {
            "node": "F",
            "score": 48.0,
            "max_score": 50.0,
            "report": {
              "impact_level": "high",
              "score": 48.0,
              "reasoning": "...",
              "causal_path": "F → acceleration",
              "intervention_effect": "...",
              "alternative_paths": "No"
            }
          },
          {
            "node": "m",
            "score": 49.0,
            "max_score": 50.0,
            "report": {
              "impact_level": "high",
              "score": 49.0,
              "reasoning": "...",
              "causal_path": "m → acceleration",
              "intervention_effect": "...",
              "alternative_paths": "No"
            }
          }
        ]
      }
    },
    "abductive_reasoning": {
      "score": 1.0,
      "weight": 0.25,
      "details": {
        "status": "success",
        "total_cause_nodes": 2,
        "passed_tests": 2,
        "abductive_score": 1.0,
        "node_tests": [
          {
            "removed_node": "F",
            "holds": true,
            "score": 1.0,
            "report": {
              "holds": true,
              "reasoning": "Can infer F from a and m...",
              "inference_possible": true
            }
          },
          {
            "removed_node": "m",
            "holds": true,
            "score": 1.0,
            "report": {
              "holds": true,
              "reasoning": "Can infer m from a and F...",
              "inference_possible": true
            }
          }
        ]
      }
    },
    "logic_quality": {
      "score": 0.85,
      "weight": 0.25
    },
    "graph_quality": {
      "score": 0.73,
      "weight": 0.25
    }
  }
}
```

### 批量评估报告

```json
{
  "average_cf": 0.82,
  "individual_scores": [0.85, 0.78, 0.83, ...],
  "total_problems": 10,
  "summary": {
    "min": 0.65,
    "max": 0.92,
    "avg": 0.82
  },
  "detailed_reports": [...]
}
```

---

## 🔍 深入理解 do 算子 / Understanding do-Operator

### 什么是 do(X)？

在因果推理中，**do(X)** 表示**主动干预**：
- 不是观察 X 的自然值
- 而是**强制设置** X 为某个值
- 切断所有指向 X 的因果边

### 示例：吸烟与肺癌

**观察 (Observation)：** P(cancer | smoking)
- "在吸烟的人中，肺癌的概率是多少？"
- 可能受到混淆因素影响（如基因）

**干预 (Intervention)：** P(cancer | do(smoking))
- "如果我们**强制**某人吸烟（忽略其他因素），肺癌的概率是多少？"
- 这是真正的因果效应

### 在我们的评估中

我们问 LLM：
> "If we intervene on node X (do(X)), what happens to the result?"

这让 LLM 思考：
1. X 在因果链中的角色
2. 移除或改变 X 的后果
3. 是否有绕过 X 的替代路径

**不需要计算具体数值**，只需要评估**因果影响的大小**。

---

## 📈 评分解释 / Score Interpretation

### CF Score 范围

- **0.9 - 1.0**: 优秀 (Excellent)
  - 所有节点都关键且被正确使用
  - 逻辑推理清晰完整
  - DAG 结构合理无误
  
- **0.7 - 0.9**: 良好 (Good)
  - 大部分节点有意义
  - 推理基本正确，可能有小瑕疵
  - DAG 结构基本合理
  
- **0.5 - 0.7**: 一般 (Fair)
  - 部分节点冗余或缺失
  - 推理有明显缺陷但总体方向对
  - DAG 结构有改进空间
  
- **< 0.5**: 较差 (Poor)
  - 很多节点无用或关键节点缺失
  - 推理逻辑混乱
  - DAG 结构有严重问题

---

## 🔧 高级用法 / Advanced Usage

### 1. 只评估因果干预

```python
from causal_evaluation import CausalInterventionEvaluator

intervention_evaluator = CausalInterventionEvaluator(llm_client, verbose=True)
intervention_score, report = intervention_evaluator.evaluate_intervention(dag, problem_text)
```

### 2. 自定义权重

如果你想调整三个组件的权重：

```python
# 修改 CausalFaithfulnessEvaluator 中的计算
# 当前是 (a + b + c) / 3 (均等权重)
# 你可以改为加权：
cf_score = (
    w1 * intervention_score + 
    w2 * logic_score + 
    w3 * graph_score
) / (w1 + w2 + w3)
```

### 3. 与 baseline 对比

```python
# 评估你的方法
our_cf = cf_evaluator.evaluate_cf_batch(our_dags)['average_cf']

# 评估 baseline (zero-shot, CoT, etc.)
baseline_cf = cf_evaluator.evaluate_cf_batch(baseline_dags)['average_cf']

# 对比
improvement = our_cf - baseline_cf
print(f"CF Improvement: {improvement:+.4f}")
```

---

## 🧪 测试示例 / Test Example

运行内置的测试示例：

```bash
python causal_evaluation.py
```

这会运行一个简单的物理问题示例，展示完整的评估流程。

---

## 📂 文件结构 / File Structure

```
hope_code/
├── causal_evaluation.py              # 主评估模块
├── prompts/
│   └── causal_intervention_prompt.txt # do算子评估prompt
├── engine/
│   └── reward_evaluator.py           # 逻辑和图质量评估（已存在）
└── CAUSAL_EVALUATION_GUIDE.md        # 本文档
```

---

## 🔗 与 Pipeline 的集成 / Integration with Pipeline

### 在完整 pipeline 中使用

```python
from causal_evaluation import CausalFaithfulnessEvaluator
from main import CausalReasoningEngine

# 1. 运行推理引擎
engine = CausalReasoningEngine()
result = engine.solve_problem(problem_text)

# 2. 提取 DAG 和推理轨迹
dag = result['enhanced_dag']  # 从 Step2 输出
reasoning_trajectory = result.get('reasoning_trajectory', '')

# 3. 评估 CF
cf_evaluator = CausalFaithfulnessEvaluator(llm_client=engine.llm_client)
cf_score, report = cf_evaluator.evaluate_cf(dag, problem_text, reasoning_trajectory)

# 4. 添加到结果中
result['cf_score'] = cf_score
result['cf_report'] = report
```

---

## ⚙️ 配置选项 / Configuration Options

### CausalInterventionEvaluator

```python
CausalInterventionEvaluator(
    llm_client=None,  # LLM 客户端（必需）
    verbose=True      # 是否打印详细信息
)
```

### CausalFaithfulnessEvaluator

```python
CausalFaithfulnessEvaluator(
    llm_client=None,  # LLM 客户端（必需）
    verbose=True      # 是否打印详细信息
)
```

---

## 🐛 常见问题 / FAQ

### Q1: 为什么不让 LLM 计算具体数值？

**A:** 我们关注的是**因果结构**而非数值计算。让 LLM 思考"影响大小"而非"具体结果"，避免了：
- 计算错误影响评估
- 混淆因果重要性与数值大小

### Q2: 如果没有推理轨迹怎么办？

**A:** Logic Quality 会使用默认分数 0.5。CF 仍然可以基于 Intervention 和 Graph 计算：
```python
cf_score, report = cf_evaluator.evaluate_cf(
    dag, 
    problem_text,
    reasoning_trajectory=""  # 空字符串
)
# Logic 会自动使用 0.5
```

### Q3: 评估很慢怎么办？

**A:** 因果干预评估需要为每个节点调用一次 LLM，所以：
- 节点数 = 10 → 至少 10 次 LLM 调用
- 可以考虑：
  1. 并行调用 LLM（如果 API 支持）
  2. 缓存常见节点的评估结果
  3. 采样评估（只评估一部分节点）

### Q4: CF 分数低意味着什么？

**A:** CF 分数低可能表示：
1. **DAG 质量问题**：节点冗余、缺失关键节点、结构混乱
2. **推理质量问题**：逻辑不连贯、步骤跳跃
3. **因果链不清晰**：节点之间的因果关系模糊

通过查看 `detailed_report`，可以定位具体问题。

---

## 📚 相关文献 / Related Work

- **Pearl, J. (2009).** *Causality: Models, Reasoning, and Inference*
  - do-calculus 的理论基础
  
- **Counterfactual Reasoning** in NLP/AI:
  - "Does the model truly understand causality or just correlation?"
  
- **Abductive Reasoning**:
  - 从结果推断原因（与我们评估节点重要性相关）

---

## 🎓 总结 / Summary

**Step3 Causal Evaluation** 提供了：

✅ **全面的 CF 评估**：干预 + 逻辑 + 图质量  
✅ **do 算子评估**：真正的因果推理，而非数值计算  
✅ **灵活的接口**：单个/批量评估，易于集成  
✅ **详细的报告**：每个节点的详细分析  
✅ **通用性**：适用于 zero-shot, few-shot, 任何生成 DAG 的方法  

**下一步：**
- 在评估框架中使用此模块
- 对比不同方法的 CF 分数
- 分析 CF 与最终答案准确率的相关性

---

**文档版本：** v1.0  
**日期：** 2025-11-08  
**作者：** Causal Reasoning Team



## 📋 概述 / Overview

这是 **Step3: Causal Evaluation** 模块，实现了 **Counterfactual Faithfulness (CF)** 评估。

This is the **Step3: Causal Evaluation** module, implementing **Counterfactual Faithfulness (CF)** evaluation.

---

## 🎯 核心思想 / Core Idea

### CF 评估公式 / CF Evaluation Formula

```
CF = (Causal Intervention + Abductive Reasoning + Logic Quality + Graph Quality) / 4
```

**四个组件，各占 1/4：**

1. **因果干预质量** (Causal Intervention Score)
   - 使用 do 算子评估节点重要性
   - 不计算具体数值，只评估影响程度
   
2. **溯因推理质量** (Abductive Reasoning Score)  🆕
   - 由果溯因，测试推理链的可逆性
   - 移除原因节点，检查推理是否仍成立
   
3. **逻辑推理质量** (Logic Quality)
   - 推理步骤的合理性和连贯性
   - 借鉴自 RewardEvaluator
   
4. **DAG 图质量** (Graph Quality)
   - 图结构的正确性（无环、连通性、因果关系）
   - 借鉴自 RewardEvaluator

---

## 🔧 1. 因果干预评估 (Causal Intervention)

### 核心思想

对 DAG 中的**每个非结果节点**提问：

> **"If we perform causal intervention do(X | other_vars), what is the impact on the final result?"**
> 
> **"如果我们对节点 X 执行因果干预 do(X | 其他变量)，对最终结果的影响有多大？"**

### 评分机制

#### 步骤 1: 分配分数池

```python
总分池 = 100 分
N = 非结果节点数量
每个节点最大分数 = 100 / N
```

**示例：**
- 10 个非结果节点 → 每个节点最多 10 分
- 5 个非结果节点 → 每个节点最多 20 分

#### 步骤 2: LLM 评估每个节点

对每个节点，LLM 评估：
1. **节点的因果路径**：从该节点到结果节点的路径
2. **干预效果**：do(节点) 会发生什么？
3. **影响程度**：critical / meaningful / peripheral

#### 步骤 3: 打分

LLM 给出 **0 到 max_score_per_node** 的分数：

- **高影响** (score ≈ max_score): 节点是关键的，移除它会破坏推理链
- **中等影响** (score ≈ max_score/2): 节点有贡献但有替代方案
- **低影响** (score ≈ 0): 节点是边缘的或冗余的

#### 步骤 4: 归一化

```python
intervention_score = Σ(node_scores) / 100
# 结果：0-1 之间
```

---

## 🔄 2. 溯因推理评估 (Abductive Reasoning) 🆕

### 核心思想

**溯因推理（Abductive Reasoning）**：由果溯因，从结果反推原因

> **"Given the result and most inputs, can we verify or infer the missing cause?"**
> 
> **"给定结果和大部分输入，能否验证或推断出缺失的原因？"**

### 评分机制

#### 步骤 1: 识别原因节点

```python
cause_nodes = dag['knowns'].keys()  # 从 knowns 中提取原因节点
```

**示例：** 如果 `knowns = {"F": 10, "m": 2}`，则原因节点为 `["F", "m"]`

#### 步骤 2: 对每个原因节点进行溯因测试

对每个原因节点：
1. **移除该节点**
2. **给定信息：**
   - 结果节点的值
   - 其他所有原因节点
3. **提问 LLM：** "推理链在这种情况下是否仍然成立？"

#### 步骤 3: 二元评分

LLM 判断：
- **成立（Holds）** → 分数 = **1**
  - 可以从结果和其他原因推断出被移除的原因
  - 推理链可以被验证
- **不成立（Doesn't Hold）** → 分数 = **0**
  - 无法推断被移除的原因
  - 推理链断裂，无法验证

#### 步骤 4: 计算平均分

```python
abductive_score = Σ(scores) / N
# N = 原因节点数量
# 结果：0-1 之间
```

---

### 溯因推理示例

#### 问题

"Calculate acceleration given F=10N and m=2kg using a=F/m"

#### DAG

```json
{
  "target_variable": "acceleration",
  "knowns": {"F": 10, "m": 2},
  "causal_graph": [
    {"cause": ["F", "m"], "effect": "acceleration", "rule": "a = F/m"}
  ]
}
```

#### 溯因测试过程

**原因节点：** `F`, `m` （共 2 个）

---

##### 测试 1: 移除 F

**给定信息：**
- 结果：acceleration = 5 m/s²
- 其他原因：m = 2 kg

**LLM 分析：**
- 使用公式 a = F/m
- 已知 a=5, m=2
- 可以反推 F = a × m = 5 × 2 = 10N ✓
- **推理链成立！**

**评分：** 1

---

##### 测试 2: 移除 m

**给定信息：**
- 结果：acceleration = 5 m/s²
- 其他原因：F = 10 N

**LLM 分析：**
- 使用公式 a = F/m
- 已知 a=5, F=10
- 可以反推 m = F / a = 10 / 5 = 2 kg ✓
- **推理链成立！**

**评分：** 1

---

#### 总分

```
abductive_score = (1 + 1) / 2 = 1.0
```

**结论：** 推理链完全可逆，溯因推理分数满分（1.0）

---

### 什么时候返回 0？

#### 示例：不可逆的推理链

**问题：** "Predict outcome based on complex function"

**DAG：**
```json
{
  "knowns": {"A": 5, "B": 3, "C": 2},
  "causal_graph": [
    {"cause": ["A", "B", "C"], "effect": "outcome", 
     "rule": "outcome = complex_nonlinear_function(A, B, C)"}
  ]
}
```

**测试：** 移除 B

**给定：** outcome=100, A=5, C=2

**LLM 分析：**
- 函数是复杂的非线性函数，不可代数反解
- 多个 B 值可能导致相同的 outcome
- **无法从 outcome 和 A, C 推断 B**
- **推理链不成立！**

**评分：** 0

---

## 📐 数学示例 / Mathematical Example

### 问题

"Calculate acceleration given F=10N and m=2kg using a=F/m"

### DAG

```json
{
  "target_variable": "acceleration",
  "knowns": {"F": 10, "m": 2},
  "causal_graph": [
    {"cause": ["F", "m"], "effect": "acceleration", "rule": "a = F/m"}
  ]
}
```

### 评估过程

**非结果节点：** `F`, `m` （共 2 个）

**每个节点最大分数：** 100 / 2 = 50 分

#### 节点 1: F (force)

**LLM 分析：**
- **因果路径：** F → acceleration（直接）
- **干预效果：** 移除 F，无法计算 a
- **影响程度：** Critical（关键）
- **分数：** 48 / 50

#### 节点 2: m (mass)

**LLM 分析：**
- **因果路径：** m → acceleration（直接）
- **干预效果：** 移除 m，无法计算 a  
- **影响程度：** Critical（关键）
- **分数：** 49 / 50

#### 总分

```
intervention_score = (48 + 49) / 100 = 0.97
```

**结论：** 两个节点都是关键的，因果干预质量很高 (0.97)

---

## 💻 使用方法 / Usage

### 基本使用

```python
from causal_evaluation import CausalFaithfulnessEvaluator
from engine.scaffolder import LLMClient

# 1. 初始化
llm_client = LLMClient()
cf_evaluator = CausalFaithfulnessEvaluator(llm_client=llm_client, verbose=True)

# 2. 准备 DAG 和问题
dag = {
    "target_variable": "acceleration",
    "knowns": {"F": 10, "m": 2},
    "causal_graph": [
        {"cause": ["F", "m"], "effect": "acceleration", "rule": "a = F/m"}
    ],
    "computation_plan": [
        {"id": "step1", "target": "acceleration", "inputs": ["F", "m"], 
         "description": "Calculate a = F/m = 10/2 = 5 m/s²"}
    ]
}

problem_text = "Calculate acceleration given F=10N and m=2kg"
reasoning_trajectory = "Using Newton's second law a=F/m, we get a = 10/2 = 5 m/s²"

# 3. 评估单个问题
cf_score, report = cf_evaluator.evaluate_cf(
    dag, 
    problem_text, 
    reasoning_trajectory
)

print(f"CF Score: {cf_score:.4f}")
print(f"Intervention: {report['components']['causal_intervention']['score']:.4f}")
print(f"Abductive:    {report['components']['abductive_reasoning']['score']:.4f}")
print(f"Logic:        {report['components']['logic_quality']['score']:.4f}")
print(f"Graph:        {report['components']['graph_quality']['score']:.4f}")
```

### 批量评估

```python
# 准备多个问题
problems = [
    {
        'dag': dag1,
        'problem_text': "Problem 1...",
        'reasoning_trajectory': "Step 1, Step 2..."
    },
    {
        'dag': dag2,
        'problem_text': "Problem 2...",
        'reasoning_trajectory': "Step 1, Step 2..."
    },
    # ... more problems
]

# 批量评估
batch_results = cf_evaluator.evaluate_cf_batch(problems)

print(f"Average CF: {batch_results['average_cf']:.4f}")
print(f"Min CF:     {batch_results['summary']['min']:.4f}")
print(f"Max CF:     {batch_results['summary']['max']:.4f}")
```

---

## 📊 输出格式 / Output Format

### 单个问题的 CF 报告

```json
{
  "cf_score": 0.88,
  "components": {
    "causal_intervention": {
      "score": 0.97,
      "weight": 0.25,
      "details": {
        "status": "success",
        "total_nodes": 3,
        "non_target_nodes": 2,
        "max_score_per_node": 50.0,
        "total_score": 97.0,
        "normalized_score": 0.97,
        "node_evaluations": [
          {
            "node": "F",
            "score": 48.0,
            "max_score": 50.0,
            "report": {
              "impact_level": "high",
              "score": 48.0,
              "reasoning": "...",
              "causal_path": "F → acceleration",
              "intervention_effect": "...",
              "alternative_paths": "No"
            }
          },
          {
            "node": "m",
            "score": 49.0,
            "max_score": 50.0,
            "report": {
              "impact_level": "high",
              "score": 49.0,
              "reasoning": "...",
              "causal_path": "m → acceleration",
              "intervention_effect": "...",
              "alternative_paths": "No"
            }
          }
        ]
      }
    },
    "abductive_reasoning": {
      "score": 1.0,
      "weight": 0.25,
      "details": {
        "status": "success",
        "total_cause_nodes": 2,
        "passed_tests": 2,
        "abductive_score": 1.0,
        "node_tests": [
          {
            "removed_node": "F",
            "holds": true,
            "score": 1.0,
            "report": {
              "holds": true,
              "reasoning": "Can infer F from a and m...",
              "inference_possible": true
            }
          },
          {
            "removed_node": "m",
            "holds": true,
            "score": 1.0,
            "report": {
              "holds": true,
              "reasoning": "Can infer m from a and F...",
              "inference_possible": true
            }
          }
        ]
      }
    },
    "logic_quality": {
      "score": 0.85,
      "weight": 0.25
    },
    "graph_quality": {
      "score": 0.73,
      "weight": 0.25
    }
  }
}
```

### 批量评估报告

```json
{
  "average_cf": 0.82,
  "individual_scores": [0.85, 0.78, 0.83, ...],
  "total_problems": 10,
  "summary": {
    "min": 0.65,
    "max": 0.92,
    "avg": 0.82
  },
  "detailed_reports": [...]
}
```

---

## 🔍 深入理解 do 算子 / Understanding do-Operator

### 什么是 do(X)？

在因果推理中，**do(X)** 表示**主动干预**：
- 不是观察 X 的自然值
- 而是**强制设置** X 为某个值
- 切断所有指向 X 的因果边

### 示例：吸烟与肺癌

**观察 (Observation)：** P(cancer | smoking)
- "在吸烟的人中，肺癌的概率是多少？"
- 可能受到混淆因素影响（如基因）

**干预 (Intervention)：** P(cancer | do(smoking))
- "如果我们**强制**某人吸烟（忽略其他因素），肺癌的概率是多少？"
- 这是真正的因果效应

### 在我们的评估中

我们问 LLM：
> "If we intervene on node X (do(X)), what happens to the result?"

这让 LLM 思考：
1. X 在因果链中的角色
2. 移除或改变 X 的后果
3. 是否有绕过 X 的替代路径

**不需要计算具体数值**，只需要评估**因果影响的大小**。

---

## 📈 评分解释 / Score Interpretation

### CF Score 范围

- **0.9 - 1.0**: 优秀 (Excellent)
  - 所有节点都关键且被正确使用
  - 逻辑推理清晰完整
  - DAG 结构合理无误
  
- **0.7 - 0.9**: 良好 (Good)
  - 大部分节点有意义
  - 推理基本正确，可能有小瑕疵
  - DAG 结构基本合理
  
- **0.5 - 0.7**: 一般 (Fair)
  - 部分节点冗余或缺失
  - 推理有明显缺陷但总体方向对
  - DAG 结构有改进空间
  
- **< 0.5**: 较差 (Poor)
  - 很多节点无用或关键节点缺失
  - 推理逻辑混乱
  - DAG 结构有严重问题

---

## 🔧 高级用法 / Advanced Usage

### 1. 只评估因果干预

```python
from causal_evaluation import CausalInterventionEvaluator

intervention_evaluator = CausalInterventionEvaluator(llm_client, verbose=True)
intervention_score, report = intervention_evaluator.evaluate_intervention(dag, problem_text)
```

### 2. 自定义权重

如果你想调整三个组件的权重：

```python
# 修改 CausalFaithfulnessEvaluator 中的计算
# 当前是 (a + b + c) / 3 (均等权重)
# 你可以改为加权：
cf_score = (
    w1 * intervention_score + 
    w2 * logic_score + 
    w3 * graph_score
) / (w1 + w2 + w3)
```

### 3. 与 baseline 对比

```python
# 评估你的方法
our_cf = cf_evaluator.evaluate_cf_batch(our_dags)['average_cf']

# 评估 baseline (zero-shot, CoT, etc.)
baseline_cf = cf_evaluator.evaluate_cf_batch(baseline_dags)['average_cf']

# 对比
improvement = our_cf - baseline_cf
print(f"CF Improvement: {improvement:+.4f}")
```

---

## 🧪 测试示例 / Test Example

运行内置的测试示例：

```bash
python causal_evaluation.py
```

这会运行一个简单的物理问题示例，展示完整的评估流程。

---

## 📂 文件结构 / File Structure

```
hope_code/
├── causal_evaluation.py              # 主评估模块
├── prompts/
│   └── causal_intervention_prompt.txt # do算子评估prompt
├── engine/
│   └── reward_evaluator.py           # 逻辑和图质量评估（已存在）
└── CAUSAL_EVALUATION_GUIDE.md        # 本文档
```

---

## 🔗 与 Pipeline 的集成 / Integration with Pipeline

### 在完整 pipeline 中使用

```python
from causal_evaluation import CausalFaithfulnessEvaluator
from main import CausalReasoningEngine

# 1. 运行推理引擎
engine = CausalReasoningEngine()
result = engine.solve_problem(problem_text)

# 2. 提取 DAG 和推理轨迹
dag = result['enhanced_dag']  # 从 Step2 输出
reasoning_trajectory = result.get('reasoning_trajectory', '')

# 3. 评估 CF
cf_evaluator = CausalFaithfulnessEvaluator(llm_client=engine.llm_client)
cf_score, report = cf_evaluator.evaluate_cf(dag, problem_text, reasoning_trajectory)

# 4. 添加到结果中
result['cf_score'] = cf_score
result['cf_report'] = report
```

---

## ⚙️ 配置选项 / Configuration Options

### CausalInterventionEvaluator

```python
CausalInterventionEvaluator(
    llm_client=None,  # LLM 客户端（必需）
    verbose=True      # 是否打印详细信息
)
```

### CausalFaithfulnessEvaluator

```python
CausalFaithfulnessEvaluator(
    llm_client=None,  # LLM 客户端（必需）
    verbose=True      # 是否打印详细信息
)
```

---

## 🐛 常见问题 / FAQ

### Q1: 为什么不让 LLM 计算具体数值？

**A:** 我们关注的是**因果结构**而非数值计算。让 LLM 思考"影响大小"而非"具体结果"，避免了：
- 计算错误影响评估
- 混淆因果重要性与数值大小

### Q2: 如果没有推理轨迹怎么办？

**A:** Logic Quality 会使用默认分数 0.5。CF 仍然可以基于 Intervention 和 Graph 计算：
```python
cf_score, report = cf_evaluator.evaluate_cf(
    dag, 
    problem_text,
    reasoning_trajectory=""  # 空字符串
)
# Logic 会自动使用 0.5
```

### Q3: 评估很慢怎么办？

**A:** 因果干预评估需要为每个节点调用一次 LLM，所以：
- 节点数 = 10 → 至少 10 次 LLM 调用
- 可以考虑：
  1. 并行调用 LLM（如果 API 支持）
  2. 缓存常见节点的评估结果
  3. 采样评估（只评估一部分节点）

### Q4: CF 分数低意味着什么？

**A:** CF 分数低可能表示：
1. **DAG 质量问题**：节点冗余、缺失关键节点、结构混乱
2. **推理质量问题**：逻辑不连贯、步骤跳跃
3. **因果链不清晰**：节点之间的因果关系模糊

通过查看 `detailed_report`，可以定位具体问题。

---

## 📚 相关文献 / Related Work

- **Pearl, J. (2009).** *Causality: Models, Reasoning, and Inference*
  - do-calculus 的理论基础
  
- **Counterfactual Reasoning** in NLP/AI:
  - "Does the model truly understand causality or just correlation?"
  
- **Abductive Reasoning**:
  - 从结果推断原因（与我们评估节点重要性相关）

---

## 🎓 总结 / Summary

**Step3 Causal Evaluation** 提供了：

✅ **全面的 CF 评估**：干预 + 逻辑 + 图质量  
✅ **do 算子评估**：真正的因果推理，而非数值计算  
✅ **灵活的接口**：单个/批量评估，易于集成  
✅ **详细的报告**：每个节点的详细分析  
✅ **通用性**：适用于 zero-shot, few-shot, 任何生成 DAG 的方法  

**下一步：**
- 在评估框架中使用此模块
- 对比不同方法的 CF 分数
- 分析 CF 与最终答案准确率的相关性

---

**文档版本：** v1.0  
**日期：** 2025-11-08  
**作者：** Causal Reasoning Team






