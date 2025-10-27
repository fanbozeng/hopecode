# Computation Mode Ablation Study
# 计算模式消融实验

## 📋 Overview / 概述

This document describes the **computation mode ablation study** that compares two different computation approaches in the causal reasoning framework:

本文档描述了**计算模式消融实验**，比较因果推理框架中的两种不同计算方法：

1. **Symbolic Execution** (默认方式 / Default)
   - Code Generation + Python Sandbox Execution
   - 代码生成 + Python沙箱执行

2. **LLM-based Computation** (消融实验 / Ablation Study)
   - LLM computes based on causal scaffold
   - LLM基于因果脚手架计算

---

## 🎯 Purpose / 目的

### Research Question / 研究问题

**Is symbolic execution necessary, or can LLM computation based on causal scaffolds achieve comparable accuracy?**

**符号执行是否必要，或者基于因果脚手架的LLM计算能否达到相当的准确性？**

### What This Tests / 测试内容

This ablation study tests:
此消融实验测试：

✅ **Keeps the same** / **保持不变**:
- Knowledge Retrieval (RAG) / 知识检索
- Causal Scaffolding / 因果脚手架生成
- Synthesis & Validation / 合成与验证

🔄 **Changes** / **变化**:
- **Symbolic Mode**: Code Generation → Symbolic Execution
  - **符号模式**: 代码生成 → 符号执行
- **LLM Mode**: LLM Computation (based on scaffold)
  - **LLM模式**: LLM计算（基于脚手架）

---

## 🏗️ Architecture / 架构

### Full Pipeline Comparison / 完整流程对比

```
┌────────────────────────────────────────────────────────────────┐
│                    SYMBOLIC MODE (Default)                      │
│                    符号模式（默认）                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Knowledge Retrieval       →  Retrieve relevant rules       │
│     知识检索                       检索相关规则                   │
│                                                                 │
│  2. Causal Scaffolding        →  Generate causal graph (JSON)  │
│     因果脚手架                     生成因果图（JSON）             │
│                                                                 │
│  3. Code Generation           →  Convert scaffold to Python    │
│     代码生成                       将脚手架转换为Python            │
│                                                                 │
│  4. Symbolic Execution        →  Execute code in sandbox       │
│     符号执行                       在沙箱中执行代码                │
│                                                                 │
│  5. Synthesis & Validation    →  Generate explanation          │
│     合成与验证                     生成解释                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    LLM MODE (Ablation)                          │
│                    LLM模式（消融实验）                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Knowledge Retrieval       →  Retrieve relevant rules       │
│     知识检索                       检索相关规则                   │
│                                                                 │
│  2. Causal Scaffolding        →  Generate causal graph (JSON)  │
│     因果脚手架                     生成因果图（JSON）             │
│                                                                 │
│  3. LLM Computation           →  LLM computes based on scaffold│
│     LLM计算                        LLM基于脚手架计算              │
│                                                                 │
│  4. Synthesis & Validation    →  Generate explanation          │
│     合成与验证                     生成解释                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Usage / 使用方法

### 1. Using main.py Directly / 直接使用main.py

```python
from main import CausalReasoningEngine

# Symbolic Execution Mode (Default)
# 符号执行模式（默认）
engine_symbolic = CausalReasoningEngine(
    computation_mode="symbolic"  # Default
)

# LLM Computation Mode (Ablation)
# LLM计算模式（消融实验）
engine_llm = CausalReasoningEngine(
    computation_mode="llm"  # Ablation
)

# Solve problem
# 求解问题
problem = "What is 2 + 3 * 4?"
result_symbolic = engine_symbolic.solve_problem(problem)
result_llm = engine_llm.solve_problem(problem)

print(f"Symbolic: {result_symbolic['final_answer']}")
print(f"LLM: {result_llm['final_answer']}")
```

### 2. Using Evaluation Framework / 使用评估框架

```bash
# Run ablation studies including NO_SYMBOLIC_EXECUTION
# 运行消融实验，包括NO_SYMBOLIC_EXECUTION
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 20 \
    --methods ablations
```

This will run:
这将运行：
- `NO_RETRIEVER` - No knowledge retrieval / 无知识检索
- `NO_AI_RETRIEVER` - No AI-generated rules / 无AI生成规则
- **`NO_SYMBOLIC_EXECUTION`** - **LLM computation instead of symbolic execution** / **LLM计算而非符号执行**

### 3. Direct Comparison Test / 直接对比测试

```bash
# Run comparison test script
# 运行对比测试脚本
python test_computation_modes.py
```

This script will:
此脚本将：
- Run the same problem with both modes / 使用两种模式运行同一问题
- Compare results and execution time / 比较结果和执行时间
- Show which mode is more accurate / 显示哪种模式更准确

---

## 📊 Output Examples / 输出示例

### Symbolic Mode Output / 符号模式输出

```
--- STAGE 3: CODE GENERATION (Symbolic Mode) ---
---  3: 代码生成（符号执行模式）---
✓ Code generated successfully

--- STAGE 3.5: SANDBOX EXECUTION ---
---  3.5: 沙箱执行 ---
✓ Code executed successfully
Final Answer: 14
```

### LLM Mode Output / LLM模式输出

```
--- STAGE 3: LLM-BASED COMPUTATION (LLM Mode) ---
---  3: 基于LLM的计算（LLM模式）---
✓ LLM response received
✓ Final answer computed: 14
```

---

## 📈 Evaluation Metrics / 评估指标

When comparing the two modes, consider:
比较两种模式时，考虑：

1. **Accuracy / 准确性**
   - How often does each mode produce the correct answer?
   - 每种模式多久产生一次正确答案？

2. **Consistency / 一致性**
   - Do both modes produce the same answer?
   - 两种模式是否产生相同答案？

3. **Execution Time / 执行时间**
   - Which mode is faster?
   - 哪种模式更快？

4. **Error Rate / 错误率**
   - Which mode fails more often?
   - 哪种模式更容易失败？

5. **Error Types / 错误类型**
   - What kinds of errors does each mode encounter?
   - 每种模式遇到什么类型的错误？

---

## 🔍 Expected Results / 预期结果

### Hypothesis / 假设

**Symbolic Execution** (符号执行) should be:
- More accurate for complex calculations / 对复杂计算更准确
- More reliable for multi-step problems / 对多步骤问题更可靠
- Deterministic and reproducible / 确定性和可重现性

**LLM Computation** (LLM计算) might be:
- Faster (no code generation step) / 更快（无代码生成步骤）
- More flexible for edge cases / 对边界情况更灵活
- Less reliable for numerical precision / 数值精度可能较低

---

## 📝 Implementation Details / 实现细节

### New Components / 新组件

1. **`engine/llm_computer.py`**
   - `LLMComputer` class
   - Takes causal scaffold as input
   - Generates structured prompt for LLM
   - Extracts final answer from LLM response

2. **`main.py` - Updated**
   - Added `computation_mode` parameter
   - Conditional logic to choose computation path
   - Both paths start from causal scaffold

3. **`evaluate_framework.py` - Updated**
   - `_run_without_symbolic_execution()` now uses `computation_mode='llm'`
   - Proper ablation study (not just direct LLM call)

### Key Code / 关键代码

```python
# In main.py solve_problem()
if self.computation_mode == "symbolic":
    # Original: Code Generation + Execution
    generated_code = self.code_generator.generate_code(causal_plan)
    execution_result = self.sandbox_executor.execute_code(generated_code)
    final_answer = execution_result['result']

elif self.computation_mode == "llm":
    # Ablation: LLM Computation
    computation_result = self.llm_computer.compute_from_scaffold(
        causal_scaffold=causal_plan,
        problem_text=problem_text
    )
    final_answer = computation_result['result']
```

---

## 🧪 Testing / 测试

### Quick Test / 快速测试

```bash
# Test both modes on a single problem
# 在单个问题上测试两种模式
python test_computation_modes.py
```

### Full Evaluation / 完整评估

```bash
# Evaluate on GSM8K dataset
# 在GSM8K数据集上评估
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 50 \
    --methods ablations \
    --verbose
```

### Batch Evaluation / 批量评估

```bash
# Use batch evaluator for concurrent processing
# 使用批量评估器进行并发处理
python batch_evaluator.py \
    --dataset gsm8k \
    --limit 100 \
    --methods ablations \
    --max-workers 4
```

---

## 📊 Results Analysis / 结果分析

After running evaluations, compare:
运行评估后，比较：

```python
# Example results comparison
# 示例结果比较

FULL_FRAMEWORK (Symbolic):
  Accuracy: 85.0% (17/20)
  Avg Time: 5.2s per problem

NO_SYMBOLIC_EXECUTION (LLM):
  Accuracy: 78.0% (16/20)
  Avg Time: 3.8s per problem
```

### Analysis Questions / 分析问题

1. Is the accuracy difference significant? / 准确性差异是否显著？
2. Is the time savings worth the accuracy loss? / 时间节省是否值得准确性损失？
3. For which problem types does LLM mode fail? / LLM模式在哪些问题类型上失败？
4. Can the LLM prompt be improved? / LLM提示能否改进？

---

## 🎯 Recommendations / 建议

### When to Use Symbolic Mode / 何时使用符号模式

✅ **Use Symbolic Execution when** / **在以下情况使用符号执行**:
- High numerical precision is required / 需要高数值精度
- Multi-step calculations are involved / 涉及多步计算
- Reproducibility is critical / 可重现性至关重要
- Problem involves complex formulas / 问题涉及复杂公式

### When to Use LLM Mode / 何时使用LLM模式

✅ **Use LLM Computation when** / **在以下情况使用LLM计算**:
- Speed is more important than precision / 速度比精度更重要
- Problems are relatively simple / 问题相对简单
- Code generation frequently fails / 代码生成经常失败
- For research/ablation purposes / 用于研究/消融目的

---

## 🐛 Known Issues / 已知问题

### LLM Computation Limitations / LLM计算限制

1. **Numerical Precision** / **数值精度**
   - LLM may round numbers incorrectly
   - LLM可能错误地四舍五入数字

2. **Complex Calculations** / **复杂计算**
   - May struggle with multi-step arithmetic
   - 可能难以处理多步骤算术

3. **Answer Extraction** / **答案提取**
   - Final answer extraction may fail if LLM format is unexpected
   - 如果LLM格式出乎意料，最终答案提取可能失败

---

## 📚 Related Documentation / 相关文档

- **Main Documentation**: `ENGINE_FRAMEWORK_DOCUMENTATION.md`
- **Evaluation Guide**: `doc/EVALUATION_GUIDE.md`
- **Retry Mechanism**: `RETRY_MECHANISM_GUIDE.md`
- **Batch Evaluation**: `doc/BATCH_EVALUATION_GUIDE.md`

---

## ✅ Checklist / 检查清单

- [x] Created `LLMComputer` class in `engine/llm_computer.py`
- [x] Added `computation_mode` parameter to `main.py`
- [x] Updated `NO_SYMBOLIC_EXECUTION` ablation in `evaluate_framework.py`
- [x] Created `test_computation_modes.py` for comparison testing
- [x] Created this documentation

---

## 🚀 Quick Start / 快速开始

```bash
# 1. Test the comparison script
# 1. 测试对比脚本
python test_computation_modes.py

# 2. Run ablation study
# 2. 运行消融实验
python evaluate_framework.py --dataset gsm8k --limit 20 --methods ablations

# 3. Analyze results
# 3. 分析结果
# Check evaluation_results/ directory for JSON output
# 检查 evaluation_results/ 目录中的 JSON 输出
```

---

**Last Updated**: 2025-01-15

享受消融实验！🎉 / Enjoy the ablation study! 🎉
