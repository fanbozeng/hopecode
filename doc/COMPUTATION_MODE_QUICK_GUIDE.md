# 🚀 Computation Mode Quick Guide
# 🚀 计算模式快速指南

## 📌 TL;DR / 快速总结

你现在有**两种计算方式**可以选择：

1. **`computation_mode="symbolic"`** （默认）
   - 代码生成 + 符号执行
   - 更准确，适合复杂计算

2. **`computation_mode="llm"`** （消融实验）
   - LLM基于因果图直接计算
   - 更快，但可能精度较低

---

## ⚡ Quick Examples / 快速示例

### 1. 直接使用 / Direct Usage

```python
from main import CausalReasoningEngine

# 方式1: 符号执行（默认）
engine = CausalReasoningEngine(computation_mode="symbolic")

# 方式2: LLM计算（消融实验）
engine = CausalReasoningEngine(computation_mode="llm")

# 求解问题
result = engine.solve_problem("Janet's ducks lay 16 eggs...")
print(result['final_answer'])
```

### 2. 评估对比 / Evaluation Comparison

```bash
# 运行消融实验（包括NO_SYMBOLIC_EXECUTION）
python evaluate_framework.py --dataset gsm8k --limit 20 --methods ablations
```

### 3. 直接测试对比 / Direct Comparison Test

```bash
# 同时测试两种模式
python test_computation_modes.py
```

---

## 📊 什么时候用哪种？/ When to Use Which?

| 场景 / Scenario | 使用模式 / Use Mode | 原因 / Reason |
|----------------|-------------------|---------------|
| 需要高精度数值计算 / High precision needed | `symbolic` | 符号执行更准确 / Symbolic is more accurate |
| 多步骤复杂计算 / Multi-step calculations | `symbolic` | 代码执行可靠 / Code execution is reliable |
| 快速原型测试 / Quick prototyping | `llm` | 速度更快 / Faster |
| 消融研究对比 / Ablation study | `llm` | 研究目的 / Research purpose |
| 符号求解器经常出错 / Symbolic solver errors often | `llm` | 作为备选方案 / As fallback |

---

## 🔧 新增文件 / New Files

1. **`engine/llm_computer.py`** - LLM计算器类
2. **`test_computation_modes.py`** - 对比测试脚本
3. **`COMPUTATION_MODE_ABLATION.md`** - 详细文档
4. **`COMPUTATION_MODE_QUICK_GUIDE.md`** - 快速指南（本文件）

---

## 🎯 核心改动 / Core Changes

### main.py

```python
# 新增参数
def __init__(
    self,
    ...,
    computation_mode: str = "symbolic"  # 新增！
):
    ...

# 在solve_problem中选择计算方式
if self.computation_mode == "symbolic":
    # 原来的流程：代码生成 + 执行
    generated_code = self.code_generator.generate_code(causal_plan)
    execution_result = self.sandbox_executor.execute_code(generated_code)

elif self.computation_mode == "llm":
    # 新流程：LLM基于因果图计算
    computation_result = self.llm_computer.compute_from_scaffold(causal_plan, problem_text)
```

### evaluate_framework.py

```python
def _run_without_symbolic_execution(self, problem: str) -> Any:
    # 旧方法：直接调用LLM（不使用因果图）❌
    # 新方法：使用computation_mode='llm'（基于因果图）✅
    engine = CausalReasoningEngine(
        computation_mode="llm"  # 关键改动！
    )
    results = engine.solve_problem(problem)
    return results.get('final_answer')
```

---

## 📈 预期效果 / Expected Results

根据你的问题描述，符号求解器经常出错，所以：

✅ **符号模式**可能会有：
- 代码生成失败
- 沙箱执行错误
- 但如果成功，答案准确

✅ **LLM模式**可能会有：
- 更高的成功率（因为跳过代码生成）
- 但数值精度可能较低
- 适合作为备选方案

---

## 🧪 测试命令 / Test Commands

```bash
# 1. 单个问题对比测试
python test_computation_modes.py

# 2. GSM8K数据集消融实验（20题）
python evaluate_framework.py --dataset gsm8k --limit 20 --methods ablations

# 3. 完整评估（包括所有基线+消融）
python evaluate_framework.py --dataset gsm8k --limit 50 --methods all

# 4. 详细输出查看过程
python evaluate_framework.py --dataset gsm8k --limit 5 --methods ablations --verbose
```

---

## 💡 使用建议 / Tips

1. **先测试单个问题**
   ```bash
   python test_computation_modes.py
   ```

2. **观察两种模式的输出差异**
   - 符号模式：看代码生成 + 执行过程
   - LLM模式：看LLM如何基于因果图计算

3. **在小数据集上评估**
   ```bash
   python evaluate_framework.py --dataset gsm8k --limit 10 --methods ablations
   ```

4. **分析结果**
   - 检查 `evaluation_results/` 目录
   - 对比 `full_framework` vs `no_symbolic_execution` 的准确率

---

## ❓ FAQ / 常见问题

**Q: 为什么不直接替换掉符号执行器？**
A: 因为这是**消融实验**，我们需要**对比两种方法的效果**，所以两种都保留，让你可以选择。

**Q: 哪个更好？**
A: 取决于你的需求：
- 符号执行：更准确，但可能失败
- LLM计算：更稳定，但可能不够精确

**Q: 可以动态切换吗？**
A: 可以！你可以在初始化时指定 `computation_mode`，或者在评估中对比两种方法。

**Q: LLM模式还用因果图吗？**
A: 是的！LLM模式仍然生成因果图，然后让LLM基于因果图计算，这是关键区别。

---

## 🔗 相关文档 / Related Docs

- **详细文档**: `COMPUTATION_MODE_ABLATION.md`
- **引擎文档**: `ENGINE_FRAMEWORK_DOCUMENTATION.md`
- **评估指南**: `doc/EVALUATION_GUIDE.md`

---

**享受新功能！🎉 / Enjoy the new feature! 🎉**
