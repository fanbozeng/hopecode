# 完整评估指南 (Complete Evaluation Guide)

本指南教您如何使用评估框架在各种数据集上测试您的因果推理框架和基线方法。

---

## 📚 目录 (Table of Contents)

1. [快速开始](#快速开始)
2. [支持的数据集](#支持的数据集)
3. [支持的评估方法](#支持的评估方法)
4. [基本使用](#基本使用)
5. [高级使用](#高级使用)
6. [结果分析](#结果分析)
7. [常见问题](#常见问题)
8. [完整示例](#完整示例)

---

## 🚀 快速开始

### 1. 最简单的评估命令

```bash
# 在 GSM8K 上评估 20 个问题（基线方法）
python evaluate_framework.py --dataset gsm8k --limit 20 --methods baselines
```

**输出**:
- 实时进度显示
- 准确率统计
- 平均执行时间
- 结果保存到 `evaluation_results/GSM8K_comparison.json`

### 2. 交互式评估菜单

```bash
python run_evaluation.py
```

**功能**:
- 选择数据集
- 选择评估方法
- 设置问题数量
- 自动运行评估

---

## 📊 支持的数据集

### 1. GSM8K (小学数学推理)
- **路径**: `dataset/GSM8K/grade_school_math/data/test.jsonl`
- **格式**: JSONL (每行一个 JSON 对象)
- **问题数**: ~1300
- **难度**: ⭐⭐
- **语言**: 英文

**示例命令**:
```bash
python evaluate_framework.py --dataset gsm8k --limit 50 --methods baselines
```

### 2. MATH (竞赛数学)
- **路径**: `dataset/Math/test-00000-of-00001.parquet.json`
- **格式**: JSON 数组
- **问题数**: ~5000
- **难度**: ⭐⭐⭐⭐
- **语言**: 英文

**示例命令**:
```bash
python evaluate_framework.py --dataset math --limit 30 --methods baselines
```

### 3. MyData (中国数学竞赛)
- **路径**: `dataset/mydata/data/2024A.json`
- **格式**: JSON 数组
- **问题数**: ~100
- **难度**: ⭐⭐⭐⭐⭐
- **语言**: 中文

**示例命令**:
```bash
python evaluate_framework.py --dataset mydata --limit 20 --methods baselines
```

### 4. OlympiadBench (奥林匹克竞赛) 🆕

OlympiadBench 包含多个子数据集：

#### 数学竞赛数据集
| 文件名 | 语言 | 类型 | 难度 |
|--------|------|------|------|
| `OE_TO_maths_zh_CEE.json` | 中文 | 高考 | ⭐⭐⭐ |
| `OE_TO_maths_zh_COMP.json` | 中文 | 竞赛 | ⭐⭐⭐⭐⭐ |
| `OE_TO_maths_en_COMP.json` | 英文 | 竞赛 | ⭐⭐⭐⭐⭐ |
| `OE_MM_maths_zh_CEE.json` | 中文 | 高考 (多选) | ⭐⭐⭐⭐ |
| `OE_MM_maths_zh_COMP.json` | 中文 | 竞赛 (多选) | ⭐⭐⭐⭐⭐ |
| `OE_MM_maths_en_COMP.json` | 英文 | 竞赛 (多选) | ⭐⭐⭐⭐⭐ |

#### 物理竞赛数据集
| 文件名 | 语言 | 类型 | 难度 |
|--------|------|------|------|
| `OE_TO_physics_zh_CEE.json` | 中文 | 高考 | ⭐⭐⭐ |
| `OE_TO_physics_en_COMP.json` | 英文 | 竞赛 | ⭐⭐⭐⭐⭐ |
| `OE_MM_physics_zh_CEE.json` | 中文 | 高考 (多选) | ⭐⭐⭐⭐ |

**数据格式**:
```json
{
    "id": 3103,
    "subfield": "Derivative",
    "question": "问题描述...",
    "solution": ["解答步骤..."],
    "final_answer": ["最终答案"],
    "answer_type": "Interval",
    "unit": null
}
```

---

## 🔬 支持的评估方法

### 基线方法 (Baselines)

#### 1. Direct LLM (直接 LLM)
- **描述**: 直接让 LLM 回答，不使用思维链
- **优点**: 最快
- **缺点**: 准确率较低
- **代码**: `baselines/direct_llm.py`

#### 2. Zero-Shot CoT (零样本思维链)
- **描述**: 使用 "Let's think step by step" 提示
- **优点**: 无需示例，推理能力强
- **缺点**: 比直接 LLM 慢
- **参考**: Kojima et al., NeurIPS 2022
- **代码**: `baselines/zero_shot_cot.py`

#### 3. Few-Shot CoT (少样本思维链)
- **描述**: 提供示例后再求解
- **优点**: 准确率最高（基线中）
- **缺点**: 需要精心设计示例
- **参考**: Wei et al., NeurIPS 2022
- **代码**: `baselines/few_shot_cot.py`

#### 4. Full Framework (完整因果推理框架)
- **描述**: 使用完整的 4 阶段流程
- **优点**: 最高准确率，可解释性强
- **缺点**: 较慢
- **阶段**:
  1. 混合知识检索
  2. 因果脚手架
  3. 符号执行
  4. 合成验证

### 消融实验方法 (Ablations)

#### 5. No Retriever (无检索器)
- **描述**: 移除知识检索模块
- **目的**: 评估知识检索的重要性

#### 6. No AI Retriever (无 AI 检索器)
- **描述**: 仅使用传统检索，不用 AI 生成
- **目的**: 评估 AI 动态生成的价值

#### 7. No Symbolic Execution (无符号执行)
- **描述**: 使用 LLM 直接计算，不用 SymPy
- **目的**: 评估符号执行的必要性

---

## 💻 基本使用

### 命令行参数详解

```bash
python evaluate_framework.py \
    --dataset DATASET_NAME \    # 数据集名称
    --limit N \                  # 评估问题数量
    --methods METHOD_TYPE \      # 评估方法类型
    --output OUTPUT_DIR \        # 输出目录
    --verbose                    # 显示详细信息
```

### 参数说明

#### `--dataset` (必需)
选择评估数据集：
- `gsm8k`: GSM8K 数据集
- `math`: MATH 数据集
- `mydata`: MyData 数据集

#### `--limit` (可选, 默认=20)
限制评估的问题数量：
```bash
--limit 10    # 仅评估 10 个问题
--limit 100   # 评估 100 个问题
--limit 0     # 评估所有问题 (可能很慢!)
```

#### `--methods` (可选, 默认=baselines)
选择评估方法类型：
- `baselines`: 所有基线方法
- `ablations`: 所有消融实验
- `all`: 所有方法

可以组合使用：
```bash
--methods baselines ablations    # 基线 + 消融
--methods all                     # 所有方法
```

#### `--output` (可选, 默认=evaluation_results)
指定结果保存目录：
```bash
--output my_results     # 保存到 my_results/
--output ./results      # 保存到 ./results/
```

#### `--verbose` (可选)
显示详细的执行信息：
```bash
--verbose    # 显示每个步骤的详细信息
```

---

## 🎯 使用示例

### 示例 1: 快速测试（10个问题）

```bash
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 10 \
    --methods baselines
```

**预计时间**: 2-5 分钟
**用途**: 快速验证系统工作正常

### 示例 2: 标准评估（50个问题）

```bash
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 50 \
    --methods baselines ablations
```

**预计时间**: 15-30 分钟
**用途**: 获得可靠的性能评估

### 示例 3: 完整评估（所有问题）

```bash
python evaluate_framework.py \
    --dataset math \
    --limit 100 \
    --methods all \
    --output math_full_results
```

**预计时间**: 1-2 小时
**用途**: 论文实验，完整性能报告

### 示例 4: 仅测试完整框架

```bash
python evaluate_framework.py \
    --dataset mydata \
    --limit 20 \
    --methods baselines \
    --verbose
```

### 示例 5: 对比基线方法

```bash
# 运行所有基线方法
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 50 \
    --methods baselines \
    --output baseline_comparison
```

### 示例 6: 消融实验

```bash
# 运行所有消融实验
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 30 \
    --methods ablations \
    --output ablation_study
```

---

## 📈 高级使用

### 1. 批量评估多个数据集

创建脚本 `batch_eval.sh`:

```bash
#!/bin/bash

# 评估 GSM8K
python evaluate_framework.py --dataset gsm8k --limit 50 --methods baselines

# 评估 MATH
python evaluate_framework.py --dataset math --limit 50 --methods baselines

# 评估 MyData
python evaluate_framework.py --dataset mydata --limit 20 --methods baselines

echo "All evaluations completed!"
```

运行:
```bash
bash batch_eval.sh
```

### 2. 评估 OlympiadBench 数据集

首先需要添加 OlympiadBench 数据加载器（见下文），然后：

```bash
python evaluate_olympiad.py \
    --dataset OE_TO_maths_zh_CEE \
    --limit 30 \
    --methods baselines
```

### 3. 自定义评估方法

编辑 `evaluate_framework.py`，添加自定义方法：

```python
class EvaluationMethod(Enum):
    # 添加自定义方法
    MY_CUSTOM_METHOD = "my_custom_method"

# 在 evaluate_single 中添加处理逻辑
def evaluate_single(self, problem, method):
    if method == EvaluationMethod.MY_CUSTOM_METHOD:
        predicted_answer = self._run_my_custom_method(problem)
```

---

## 📊 结果分析

### 1. 查看评估结果

评估完成后，结果保存在 JSON 文件中：

```bash
cat evaluation_results/GSM8K_comparison.json
```

**结果结构**:
```json
{
  "dataset_name": "GSM8K",
  "total_problems": 50,
  "evaluation_time": "2025-10-07T...",
  "methods": {
    "direct_llm": {
      "statistics": {
        "total": 50,
        "correct": 30,
        "accuracy": 0.60,
        "avg_time": 1.2
      },
      "results": [...]
    },
    "full_framework": {
      "statistics": {
        "total": 50,
        "correct": 45,
        "accuracy": 0.90,
        "avg_time": 3.5
      },
      "results": [...]
    }
  }
}
```

### 2. 生成对比表格

```bash
python visualize_results.py evaluation_results/GSM8K_comparison.json
```

**输出**:
```
============================================================
COMPARISON TABLE / 对比表格
============================================================
Dataset: GSM8K
数据集: GSM8K

Method                         Accuracy        Avg Time
方法                           准确率          平均时间
------------------------------------------------------------
direct_llm                     60.00%          1.20s
zero_shot_cot                  75.00%          2.10s
few_shot_cot                   80.00%          2.50s
full_framework                 90.00%          3.50s
============================================================
```

### 3. 生成 LaTeX 表格（论文用）

```bash
python visualize_results.py \
    evaluation_results/GSM8K_comparison.json \
    --latex \
    --output paper_table.tex
```

**输出文件** `paper_table.tex`:
```latex
\begin{table}[h]
\centering
\begin{tabular}{lcc}
\hline
Method & Accuracy & Avg Time (s) \\
\hline
Direct LLM & 60.00\% & 1.20 \\
Zero-Shot CoT & 75.00\% & 2.10 \\
Few-Shot CoT & 80.00\% & 2.50 \\
Full Framework & 90.00\% & 3.50 \\
\hline
\end{tabular}
\caption{Performance comparison on GSM8K dataset}
\end{table}
```

### 4. 导出 CSV

```bash
python visualize_results.py \
    evaluation_results/GSM8K_comparison.json \
    --csv \
    --output results.csv
```

### 5. 对比两种方法

```bash
python visualize_results.py \
    evaluation_results/GSM8K_comparison.json \
    --compare direct_llm full_framework
```

**输出**:
```
Comparing: direct_llm vs full_framework
-----------------------------------------
Accuracy improvement: +30.00%
Time overhead: +2.30s (+191.67%)
Correct answers gained: +15 questions
```

---

## 🛠️ 常见问题

### Q1: 评估太慢怎么办？

**A**: 减少评估问题数量
```bash
--limit 10    # 快速测试
--limit 20    # 标准测试
```

### Q2: 如何只评估完整框架？

**A**: 暂时无法单独选择，但可以修改代码：
```python
# 在 main() 函数中
methods_to_run = [EvaluationMethod.FULL_FRAMEWORK]
```

### Q3: 如何添加新数据集？

**A**: 在 `evaluate_framework.py` 中添加数据加载器：
```python
@staticmethod
def load_my_dataset(file_path, limit=None):
    # 读取数据
    # 格式化为标准格式
    # 返回问题列表
    pass
```

### Q4: 评估中断怎么办？

**A**: 目前不支持断点续传，需要重新运行。建议：
- 减少 `--limit` 值
- 使用多个小批次评估

### Q5: 如何调试单个问题？

**A**: 使用 Python API：
```python
from evaluate_framework import FrameworkEvaluator, EvaluationMethod

evaluator = FrameworkEvaluator(verbose=True)
problem = {
    'id': 'test_1',
    'question': 'What is 2+2?',
    'answer': '4'
}

result = evaluator.evaluate_single(
    problem,
    EvaluationMethod.FULL_FRAMEWORK
)
print(f"Correct: {result.is_correct}")
print(f"Predicted: {result.predicted_answer}")
```

### Q6: 准确率很低怎么办？

**A**: 检查以下几点：
1. API 密钥是否正确配置
2. 数据格式是否匹配
3. 答案比较逻辑是否合适
4. 使用 `--verbose` 查看详细错误

---

## 📝 完整示例流程

### 场景：评估框架在多个数据集上的性能

#### Step 1: 配置环境
```bash
# 确保 .env 文件配置正确
cat .env
```

#### Step 2: 快速测试
```bash
# 先用少量数据测试
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 5 \
    --methods baselines \
    --verbose
```

#### Step 3: GSM8K 完整评估
```bash
python evaluate_framework.py \
    --dataset gsm8k \
    --limit 100 \
    --methods baselines ablations \
    --output gsm8k_results
```

#### Step 4: MATH 数据集评估
```bash
python evaluate_framework.py \
    --dataset math \
    --limit 50 \
    --methods baselines \
    --output math_results
```

#### Step 5: MyData 评估
```bash
python evaluate_framework.py \
    --dataset mydata \
    --limit 20 \
    --methods baselines \
    --output mydata_results
```

#### Step 6: 结果可视化
```bash
# 生成对比表格
python visualize_results.py gsm8k_results/GSM8K_comparison.json

# 生成 LaTeX 表格
python visualize_results.py \
    gsm8k_results/GSM8K_comparison.json \
    --latex --output gsm8k_table.tex

# 导出 CSV
python visualize_results.py \
    gsm8k_results/GSM8K_comparison.json \
    --csv --output gsm8k_results.csv
```

#### Step 7: 分析结果
```python
import json

# 读取结果
with open('gsm8k_results/GSM8K_comparison.json', 'r') as f:
    results = json.load(f)

# 打印统计信息
for method, data in results['methods'].items():
    stats = data['statistics']
    print(f"{method}: {stats['accuracy']*100:.1f}% "
          f"({stats['correct']}/{stats['total']})")
```

---

## 🎓 评估最佳实践

1. **从小开始**: 先用 `--limit 10` 快速测试
2. **逐步增加**: 确认无误后增加到 50、100
3. **记录结果**: 保存所有评估结果以便对比
4. **多次运行**: 对于随机性较大的方法，多次运行取平均
5. **检查错误**: 使用 `--verbose` 查看详细错误信息
6. **合理设置超时**: 复杂问题可能需要更长时间

---

## 📞 获取帮助

- **查看源码**: `evaluate_framework.py`
- **运行测试**: `python test_baselines.py`
- **查看文档**:
  - `BASELINES_GUIDE.md` - 基线方法指南
  - `HYBRID_RETRIEVAL_GUIDE.md` - 混合检索指南
  - `README.md` - 项目主文档

---

**祝评估顺利！📊**
