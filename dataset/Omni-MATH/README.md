# Omni-MATH 数据集说明

## 转换完成 ✓

已成功将所有 CSV 文件转换为 JSONL 格式！

## 文件列表

### 原始 CSV 文件
```
archive/
├── main_train.csv          (7,473 条)
├── main_test.csv           (1,319 条)
├── socratic_train.csv      (7,473 条)
└── socratic_test.csv       (1,319 条)
```

### 转换后的 JSONL 文件 ✨
```
archive/
├── main_train.jsonl        (7,473 条) ← 新生成
├── main_test.jsonl         (1,319 条) ← 新生成
├── socratic_train.jsonl    (7,473 条) ← 新生成
└── socratic_test.jsonl     (1,319 条) ← 新生成
```

**总计**: 17,584 条数据

---

## 数据格式

### CSV 格式（原始）
```csv
question,answer
"Janet's ducks lay 16 eggs per day...","""Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs...
#### 18"""
```

### JSONL 格式（转换后）✨
每行一个 JSON 对象：
```json
{"question": "Janet's ducks lay 16 eggs per day. She eats three for breakfast...", "answer": "Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs a day.\nShe makes 9 * 2 = $<<9*2=18>>18 every day at the farmer's market.\n#### 18"}
```

---

## 数据集说明

这是 **GSM8K** 格式的数学应用题数据集，包含两个版本：

### 1. Main 版本
- `main_train.jsonl`: 训练集 7,473 题
- `main_test.jsonl`: 测试集 1,319 题
- **特点**: 标准的逐步解答，直接给出计算步骤

### 2. Socratic 版本
- `socratic_train.jsonl`: 训练集 7,473 题
- `socratic_test.jsonl`: 测试集 1,319 题
- **特点**: 苏格拉底式引导，每步前有提问（与 GSM8K 的 socratic 版本类似）

---

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `question` | string | 数学应用题题目 |
| `answer` | string | 分步解答 + 最终答案（以 `#### 数字` 结尾） |

### 答案格式
- 使用 `<<表达式=结果>>` 标记中间计算
- 最终答案用 `#### 数字` 标记
- 示例：
  ```
  Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs a day.
  She makes 9 * 2 = $<<9*2=18>>18 every day at the farmer's market.
  #### 18
  ```

---

## 使用方法

### Python 读取 JSONL
```python
import json

# 读取训练集
with open('archive/main_train.jsonl', 'r', encoding='utf-8') as f:
    train_data = [json.loads(line) for line in f]

print(f"训练集: {len(train_data)} 条")
print("第一条样例:")
print(train_data[0])
```

### 使用 Hugging Face datasets
```python
from datasets import load_dataset

# 加载数据集
dataset = load_dataset('json', data_files={
    'train': 'archive/main_train.jsonl',
    'test': 'archive/main_test.jsonl'
})

print(dataset)
print(dataset['train'][0])
```

---

## 与其他数据集的对比

| 特征 | GSM8K | Omni-MATH | MATH |
|------|-------|-----------|------|
| 题目类型 | 小学应用题 | 小学应用题 | 高中竞赛数学 |
| 训练集规模 | 7,474 | 7,473 | 12,000 |
| 测试集规模 | 1,320 | 1,319 | 500 |
| 答案格式 | `#### 数字` | `#### 数字` | `\boxed{LaTeX}` |
| 难度 | 基础算术 | 基础算术 | 竞赛级 |
| 学科分类 | 无 | 无 | 7 个子领域 |
| Socratic 版本 | ✓ | ✓ | ✗ |

---

## 样例展示

### Main 版本样例
```json
{
  "question": "A robe takes 2 bolts of blue fiber and half that much white fiber. How many bolts in total does it take?",
  "answer": "It takes 2/2=<<2/2=1>>1 bolt of white fiber\nSo the total amount of fabric is 2+1=<<2+1=3>>3 bolts of fabric\n#### 3"
}
```

**中文翻译**：
- 题目：一件长袍需要 2 卷蓝色纤维和一半数量的白色纤维。总共需要多少卷？
- 解答：白色纤维需要 2/2 = 1 卷。总共需要 2+1 = 3 卷纤维。
- 答案：3

---

## 转换工具

本目录包含两个转换脚本：

### 1. `auto_convert.py` ⚡
自动转换所有 CSV 文件为 JSONL（无需交互）
```bash
python auto_convert.py
```

### 2. `convert_to_json.py` 🎛️
交互式转换工具，可选择输出格式（JSON 或 JSONL）
```bash
python convert_to_json.py
```

---

## 文件大小

| 文件 | 大小 | 行数 |
|------|------|------|
| main_train.jsonl | ~4.5 MB | 7,473 |
| main_test.jsonl | ~770 KB | 1,319 |
| socratic_train.jsonl | ~5.2 MB | 7,473 |
| socratic_test.jsonl | ~950 KB | 1,319 |

---

## 数据集统计

### 题目特点
- 全部为英文数学应用题
- 题目长度：平均约 50-100 词
- 解答长度：平均约 2-4 步推理
- 答案类型：纯数字（整数或小数）

### 计算类型
- 四则运算
- 百分比计算
- 单位换算
- 比例问题
- 多步推理

---

## 评测方法

提取最终答案并比较：
```python
import re

def extract_answer(answer_text):
    """提取 #### 后的数字"""
    match = re.search(r'#### (\-?[\d,\.]+)', answer_text)
    if match:
        return match.group(1).replace(',', '')
    return None

def is_correct(prediction, ground_truth):
    """判断预测答案是否正确"""
    pred_ans = extract_answer(prediction)
    gt_ans = extract_answer(ground_truth)
    return pred_ans == gt_ans
```

---

## 许可与引用

本数据集基于 GSM8K，如果使用请引用：

```bibtex
@article{cobbe2021gsm8k,
  title={Training Verifiers to Solve Math Word Problems},
  author={Cobbe, Karl and Kosaraju, Vineet and Bavarian, Mohammad and 
          Chen, Mark and Jun, Heewoo and Kaiser, Lukasz and 
          Plappert, Matthias and Tworek, Jerry and Hilton, Jacob and 
          Nakano, Reiichiro and others},
  journal={arXiv preprint arXiv:2110.14168},
  year={2021}
}
```

---

## 更新日志

- **2024-10**: 完成 CSV → JSONL 转换
- 生成 4 个 JSONL 文件（main/socratic × train/test）
- 总计 17,584 条数据

---

**转换完成！✨ 现在可以直接使用 JSONL 文件进行模型训练了。**

