# Dataset Structure Analysis
# 数据集结构分析

## Overview / 概览

本文档分析项目中使用的数学推理数据集的结构。

---

## 1. GSM8K (Grade School Math 8K)

### File Format / 文件格式
- **Type**: JSONL (JSON Lines)
- **Path**: `dataset/GSM8K/grade_school_math/data/test.jsonl`

### Structure / 结构
```json
{
  "question": "Janet's ducks lay 16 eggs per day...",
  "answer": "Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs a day.\n#### 18"
}
```

### Key Fields / 关键字段
- `question`: 问题文本
- `answer`: 答案，格式为 `解析过程 #### 最终答案`

### Characteristics / 特点
- ✅ 纯文本
- ✅ 小学数学
- ✅ 每行一个 JSON 对象

---

## 2. MATH Dataset

### File Format / 文件格式
- **Type**: JSON array
- **Path**: `dataset/Math/test-00000-of-00001.parquet.json`

### Structure / 结构
```json
[
  {
    "problem": "What is the value of $x$...",
    "answer": "42",
    "solution": "Step 1: ...",
    "subject": "Algebra",
    "level": "Level 3",
    "unique_id": "math_001"
  }
]
```

### Key Fields / 关键字段
- `problem`: 问题文本
- `answer`: 最终答案
- `solution`: 详细解答过程
- `subject`: 学科分类
- `level`: 难度级别

### Characteristics / 特点
- ✅ 纯文本
- ✅ 高中/大学数学
- ✅ 包含 LaTeX 公式

---

## 3. Omni-MATH

### File Format / 文件格式
- **Type**: JSONL (JSON Lines)
- **Path**: `dataset/Omni-MATH/archive/main_test.jsonl`

### Structure / 结构
```json
{
  "question": "Janet's ducks lay 16 eggs per day...",
  "answer": "Janet sells 16 - 3 - 4 = <<16-3-4=9>>9 duck eggs a day.\n#### 18"
}
```

### Key Fields / 关键字段
- `question`: 问题文本
- `answer`: 答案，格式与 GSM8K 相同

### Available Files / 可用文件
- `main_test.jsonl`: 主测试集
- `main_train.jsonl`: 主训练集
- `socratic_test.jsonl`: Socratic 测试集
- `socratic_train.jsonl`: Socratic 训练集

### Characteristics / 特点
- ✅ 纯文本
- ✅ 格式与 GSM8K 类似
- ✅ 包含多个子集

---

## 4. OlympiadBench Dataset ⭐

### File Format / 文件格式
- **Type**: JSON array
- **Path**: `dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/*.json`

### Structure / 结构
```json
[
  {
    "id": 1735,
    "subfield": "Geometry",
    "context": null,
    "question": "Three circular arcs... <img_3408> Fig. 1",
    "solution": ["Step 1...", "Step 2..."],
    "final_answer": null,
    "is_multiple_answer": true,
    "unit": null,
    "answer_type": null,
    "error": null
  }
]
```

### Key Fields / 关键字段
- `id`: 问题 ID
- `subfield`: 子领域（Geometry, Combinatorics, Number Theory, Algebra）
- `context`: 上下文信息（通常为 null）
- `question`: 问题文本（**可能包含图片标记**）
- `solution`: 解答步骤（数组）
- `final_answer`: 最终答案（可能为 null）
- `is_multiple_answer`: 是否多答案
- `unit`: 单位
- `answer_type`: 答案类型
- `error`: 错误信息

### 🖼️ Multi-Modal Support / 多模态支持

**Image Markers in Question Text:**
```
"question": "... <img_3408> ... <img_3692> ..."
```

图片标记格式：`<img_数字>`

### File Naming Convention / 文件命名规则

```
{Problem_Type}_{Modality}_{Subject}_{Language}_{Exam}.json
```

#### Problem Types / 问题类型
- `TP` = Theorem Proving (定理证明)
- `OE` = Open-Ended (开放式)

#### Modalities / 模态类型
- `TO` = **Text-Only** (纯文本，无图片)
- `MM` = **Multi-Modal** (多模态，包含图片)

#### Subjects / 学科
- `maths` = Mathematics (数学)
- `physics` = Physics (物理)

#### Languages / 语言
- `en` = English (英语)
- `zh` = Chinese (中文)

#### Exam Types / 考试类型
- `COMP` = Competition (竞赛)
- `CEE` = College Entrance Exam (高考)

### Available Files / 可用文件

| File | Description |
|------|-------------|
| `TP_TO_maths_en_COMP.json` | 数学竞赛-定理证明-纯文本-英语 |
| `TP_MM_maths_en_COMP.json` | 数学竞赛-定理证明-多模态-英语 ⭐ |
| `TP_TO_physics_en_COMP.json` | 物理竞赛-定理证明-纯文本-英语 |
| `TP_MM_physics_en_COMP.json` | 物理竞赛-定理证明-多模态-英语 ⭐ |
| `TP_TO_maths_zh_COMP.json` | 数学竞赛-定理证明-纯文本-中文 |
| `TP_MM_maths_zh_COMP.json` | 数学竞赛-定理证明-多模态-中文 ⭐ |
| `TP_TO_maths_zh_CEE.json` | 数学高考-定理证明-纯文本-中文 |
| `TP_MM_maths_zh_CEE.json` | 数学高考-定理证明-多模态-中文 ⭐ |
| `OE_TO_maths_en_COMP.json` | 数学竞赛-开放式-纯文本-英语 |
| `OE_MM_maths_en_COMP.json` | 数学竞赛-开放式-多模态-英语 ⭐ |
| `OE_TO_maths_zh_COMP.json` | 数学竞赛-开放式-纯文本-中文 |
| `OE_MM_maths_zh_COMP.json` | 数学竞赛-开放式-多模态-中文 ⭐ |
| `OE_TO_maths_zh_CEE.json` | 数学高考-开放式-纯文本-中文 |
| `OE_MM_maths_zh_CEE.json` | 数学高考-开放式-多模态-中文 ⭐ |
| `OE_TO_physics_en_COMP.json` | 物理竞赛-开放式-纯文本-英语 |
| `OE_MM_physics_en_COMP.json` | 物理竞赛-开放式-多模态-英语 ⭐ |
| `OE_TO_physics_zh_CEE.json` | 物理高考-开放式-纯文本-中文 |
| `OE_MM_physics_zh_CEE.json` | 物理高考-开放式-多模态-中文 ⭐ |

⭐ = Contains images / 包含图片

### Characteristics / 特点
- ⭐ **多模态支持**：部分文件包含图片
- 📚 **高难度**：奥林匹克竞赛级别
- 🌐 **多语言**：英语和中文
- 📐 **多学科**：数学、物理
- 🎯 **多题型**：定理证明、开放式问题

### Image Handling / 图片处理

对于多模态问题：
1. **Detection**: 检查 `question` 中是否包含 `<img_` 标记
2. **Extraction**: 提取所有图片标记（如 `<img_3408>`）
3. **Storage**: 记录图片列表供后续处理
4. **Fallback**: 如果无法处理图片，标记为 `has_images=True`

---

## 5. MyData (Custom Dataset)

### File Format / 文件格式
- **Type**: JSON array
- **Path**: `dataset/mydata/data/2024A.json`

### Structure / 结构
```json
[
  {
    "id": "001",
    "question": "...",
    "final_answer": ["42"],
    "solution": ["Step 1", "Step 2"],
    "subfield": "Algebra",
    "context": "..."
  }
]
```

### Key Fields / 关键字段
- `id`: 问题 ID
- `question`: 问题文本
- `final_answer`: 最终答案（数组）
- `solution`: 解答步骤（数组）
- `subfield`: 子领域
- `context`: 上下文

### Characteristics / 特点
- ✅ 自定义格式
- ✅ 答案为数组格式

---

## Summary Table / 汇总表

| Dataset | Format | Modality | Difficulty | Language | Image Support |
|---------|--------|----------|-----------|----------|---------------|
| GSM8K | JSONL | Text | Elementary | EN | ❌ |
| MATH | JSON | Text | High School | EN | ❌ |
| Omni-MATH | JSONL | Text | Mixed | EN | ❌ |
| OlympiadBench | JSON | **Multi-Modal** | **Olympiad** | EN/ZH | ⭐ **YES** |
| MyData | JSON | Text | Custom | ZH | ❌ |

---

## Usage Examples / 使用示例

### Loading Datasets

```python
from evaluate_framework import DatasetLoader

loader = DatasetLoader()

# GSM8K
problems_gsm8k = loader.load_gsm8k("dataset/GSM8K/grade_school_math/data/test.jsonl", limit=10)

# MATH
problems_math = loader.load_math("dataset/Math/test-00000-of-00001.parquet.json", limit=10)

# Omni-MATH (NEW!)
problems_omnimath = loader.load_omnimath("dataset/Omni-MATH/archive/main_test.jsonl", limit=10)

# OlympiadBench (NEW! Multi-Modal)
# Text-only
problems_olympiad_to = loader.load_olympiadbench(
    "dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/TP_TO_maths_en_COMP.json",
    limit=10
)

# Multi-modal
problems_olympiad_mm = loader.load_olympiadbench(
    "dataset/OlympiadBench_Dataset/OlympiadBench_Dataset/data/TP_MM_maths_en_COMP.json",
    limit=10
)

# Check if problem has images
for p in problems_olympiad_mm:
    if p.get('has_images'):
        print(f"Problem {p['id']} has images: {p['image_ids']}")
```

---

## Notes for Multi-Modal Processing / 多模态处理注意事项

### Current Limitation / 当前限制
- 图片仅作为标记存储，不进行实际图像处理
- LLM 评估时图片信息会在问题文本中以标记形式保留

### Future Enhancement / 未来增强
- 实际图片文件的加载和编码
- 支持视觉语言模型（VLM）
- 图片特征提取

---

**Last Updated**: 2025-01-15
