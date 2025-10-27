# Batch Parallel Evaluation Guide
# 批量并行评估指南

## 概述 / Overview

**批量并行评估器**提供类似深度学习 `batch_size` 的功能，允许一次性并发处理多个样例，大幅提升评估速度。

The **Batch Parallel Evaluator** provides batch processing similar to deep learning's `batch_size`, allowing concurrent processing of multiple problems to significantly speed up evaluation.

---

## 核心特性 / Key Features

### ✅ 不修改原代码 / No Original Code Changes
- 完全独立的模块，导入并包装现有的 `evaluate_framework.py`
- Completely independent module that imports and wraps existing `evaluate_framework.py`

### ⚡ 并发处理 / Concurrent Processing
- 使用 `ThreadPoolExecutor` 实现真正的并发
- Uses `ThreadPoolExecutor` for true concurrency

### 🎯 类似深度学习的 batch_size / Deep Learning Style batch_size
- `batch_size=3` 表示同时处理 3 个问题
- `batch_size=3` means processing 3 problems concurrently

### 📊 完全兼容原有输出格式 / Fully Compatible Output Format
- 结果格式与原始评估器完全相同
- Output format identical to original evaluator

---

## 快速开始 / Quick Start

### 1. 基础使用 / Basic Usage

```bash
# 顺序处理（原始方法）- 一次处理 1 个问题
# Sequential processing (original) - 1 problem at a time
python evaluate_framework.py --dataset gsm8k --limit 10 --methods baselines

# 批量处理 - 一次处理 3 个问题（并发）
# Batch processing - 3 problems at a time (concurrent)
python batch_evaluator.py --dataset gsm8k --limit 10 --batch-size 3 --methods baselines
```

### 2. 运行演示 / Run Demo

```bash
# 交互式演示，比较不同模式的性能
# Interactive demo comparing different modes
python demo_batch.py
```

---

## 命令行参数 / Command Line Arguments

### 基础参数（与原版相同）/ Basic Arguments (Same as Original)

| 参数 / Argument | 说明 / Description | 示例 / Example |
|----------------|-------------------|---------------|
| `--dataset` | 数据集选择 / Dataset | `gsm8k`, `math`, `mydata` |
| `--limit` | 问题数量限制 / Problem limit | `20` |
| `--methods` | 评估方法 / Methods | `baselines`, `ablations`, `all` |
| `--output` | 输出目录 / Output directory | `evaluation_results` |
| `--verbose` | 详细输出 / Verbose output | flag |

### 新增参数（批量处理专用）/ New Arguments (Batch Processing Only)

| 参数 / Argument | 说明 / Description | 默认值 / Default |
|----------------|-------------------|-----------------|
| `--batch-size` | 并发处理的问题数量<br>Number of concurrent problems | `3` |
| `--max-workers` | 最大工作线程数<br>Max worker threads | 等于 batch_size<br>Equal to batch_size |

---

## 使用示例 / Usage Examples

### 示例 1: 小规模快速测试 / Small Scale Quick Test

```bash
# 使用 batch_size=3 处理 10 个问题
# Process 10 problems with batch_size=3
python batch_evaluator.py \
    --dataset gsm8k \
    --limit 10 \
    --batch-size 3 \
    --methods baselines
```

### 示例 2: 大规模评估 / Large Scale Evaluation

```bash
# 使用 batch_size=5 处理 50 个问题
# Process 50 problems with batch_size=5
python batch_evaluator.py \
    --dataset gsm8k \
    --limit 50 \
    --batch-size 5 \
    --methods all
```

### 示例 3: 自定义工作线程数 / Custom Worker Threads

```bash
# batch_size=3 但使用 5 个工作线程
# batch_size=3 but use 5 worker threads
python batch_evaluator.py \
    --dataset gsm8k \
    --limit 20 \
    --batch-size 3 \
    --max-workers 5 \
    --methods baselines
```

### 示例 4: MATH 数据集 / MATH Dataset

```bash
# 在 MATH 数据集上评估，batch_size=4
# Evaluate on MATH dataset with batch_size=4
python batch_evaluator.py \
    --dataset math \
    --limit 20 \
    --batch-size 4 \
    --methods baselines
```

---

## 性能对比 / Performance Comparison

### 理论加速比 / Theoretical Speedup

假设每个问题处理时间为 T：
Assuming processing time per problem is T:

| batch_size | 理论耗时 / Theoretical Time | 加速比 / Speedup |
|------------|---------------------------|-----------------|
| 1 (sequential) | 10T | 1x |
| 3 (batch) | 4T (3+3+3+1) | ~2.5x |
| 5 (batch) | 2T (5+5) | ~5x |
| 10 (batch) | T (10) | ~10x |

### 实际效果因素 / Real-world Factors

实际加速比取决于：
Actual speedup depends on:

1. **API 限流 / API Rate Limits**
   - 如果 API 有并发限制，batch_size 不能无限增大
   - If API has concurrency limits, batch_size cannot be arbitrarily large

2. **网络延迟 / Network Latency**
   - 高延迟环境下批量处理效果更明显
   - Batch processing is more effective in high-latency environments

3. **问题复杂度 / Problem Complexity**
   - 复杂问题处理时间长，批量处理收益更大
   - Complex problems benefit more from batch processing

---

## 工作原理 / How It Works

### 架构设计 / Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  batch_evaluator.py                     │
│                  (新模块 / New Module)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │    BatchParallelEvaluator                      │    │
│  │    (批量并行评估器)                              │    │
│  │                                                 │    │
│  │  ┌─────────────────────────────────────────┐  │    │
│  │  │  ThreadPoolExecutor (线程池)            │  │    │
│  │  │                                          │  │    │
│  │  │  Thread 1  Thread 2  Thread 3  ...      │  │    │
│  │  │     ↓         ↓         ↓               │  │    │
│  │  └──────┼─────────┼─────────┼───────────────┘  │    │
│  │         │         │         │                  │    │
│  │         ↓         ↓         ↓                  │    │
│  │  ┌─────────────────────────────────────────┐  │    │
│  │  │   FrameworkEvaluator.evaluate_single()  │  │    │
│  │  │   (原始评估器 / Original Evaluator)      │  │    │
│  │  └─────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────┐
│              evaluate_framework.py                      │
│              (原始代码，不修改 / Original Code)           │
└─────────────────────────────────────────────────────────┘
```

### 处理流程 / Processing Flow

```python
# 假设 batch_size=3, 总共 10 个问题
# Assume batch_size=3, 10 problems total

Batch 1: [Problem 1, Problem 2, Problem 3] -> 并发处理 / Process concurrently
         ↓
Batch 2: [Problem 4, Problem 5, Problem 6] -> 并发处理 / Process concurrently
         ↓
Batch 3: [Problem 7, Problem 8, Problem 9] -> 并发处理 / Process concurrently
         ↓
Batch 4: [Problem 10]                      -> 处理最后一个 / Process last one
```

---

## 最佳实践 / Best Practices

### 1. 选择合适的 batch_size / Choose Appropriate batch_size

```bash
# 小规模测试 (< 20 题)
# Small scale (< 20 problems)
--batch-size 3

# 中等规模 (20-50 题)
# Medium scale (20-50 problems)
--batch-size 5

# 大规模 (> 50 题)
# Large scale (> 50 problems)
--batch-size 10
```

### 2. 考虑 API 限制 / Consider API Limits

```bash
# 如果 API 限制每秒 5 个请求
# If API limits to 5 requests per second
--batch-size 5 --max-workers 5
```

### 3. 监控资源使用 / Monitor Resource Usage

```bash
# 使用 --verbose 查看详细进度
# Use --verbose to see detailed progress
python batch_evaluator.py \
    --dataset gsm8k \
    --limit 20 \
    --batch-size 5 \
    --verbose
```

---

## 输出格式 / Output Format

### 控制台输出 / Console Output

```
================================================================================
Batch Parallel Evaluator Initialized
批量并行评估器已初始化
  Batch Size: 5
  批量大小: 5
  Max Workers: 5
  最大工作线程: 5
================================================================================

================================================================================
Batch Evaluating GSM8K with 4 methods on 20 problems
批量评估 GSM8K，4 个方法，20 个问题
Batch Size: 5
批量大小: 5
================================================================================

--------------------------------------------------------------------------------
Method: direct_llm
方法: direct_llm
--------------------------------------------------------------------------------

  Batch 1/4 (Problems 1-5)
  批次 1/4（问题 1-5）
[1/5] ✓ gsm8k_0 (2.31s)
[2/5] ✓ gsm8k_1 (2.45s)
[3/5] ✗ gsm8k_2 (2.12s)
[4/5] ✓ gsm8k_3 (2.67s)
[5/5] ✓ gsm8k_4 (2.89s)
  Batch completed in 2.89s
  批次完成，耗时 2.89s

  ...

  ✓ Accuracy: 75.00% (15/20)
  ✓ 准确率: 75.00% (15/20)
  ⏱ Total Time: 45.67s (Avg: 2.28s per problem)
  ⏱ 总时间: 45.67s（平均: 2.28s 每题）
```

### JSON 输出 / JSON Output

结果保存格式与原始评估器完全相同，但增加了 `batch_config` 字段：
Output format is identical to original evaluator, with added `batch_config` field:

```json
{
  "dataset_name": "GSM8K",
  "total_problems": 20,
  "evaluation_time": "2025-01-15T10:30:00",
  "batch_config": {
    "batch_size": 5,
    "max_workers": 5
  },
  "methods": {
    "direct_llm": {
      "statistics": {
        "total": 20,
        "correct": 15,
        "wrong": 3,
        "errors": 2,
        "accuracy": 0.75,
        "total_time": 45.67,
        "avg_time": 2.28
      },
      "results": [...]
    }
  }
}
```

---

## 常见问题 / FAQ

### Q1: batch_size 应该设置多大？
**A:** 建议从 3-5 开始，根据 API 限制和实际效果调整。

### Q2: 会修改原有代码吗？
**A:** 不会！`batch_evaluator.py` 是完全独立的模块，只导入不修改。

### Q3: 结果格式和原版一样吗？
**A:** 完全一样，只是增加了 `batch_config` 字段记录批量配置。

### Q4: 如何知道最优的 batch_size？
**A:** 运行 `demo_batch.py` 选择模式 4，自动对比不同 batch_size 的性能。

### Q5: API 有速率限制怎么办？
**A:** 使用 `--max-workers` 限制并发线程数，例如 `--batch-size 10 --max-workers 3`。

---

## 技术细节 / Technical Details

### 线程安全 / Thread Safety

- 每个线程调用独立的 `evaluate_single()` 方法
- LLM 客户端使用锁机制确保线程安全
- Each thread calls independent `evaluate_single()` method
- LLM client uses locks to ensure thread safety

### 错误处理 / Error Handling

- 单个问题失败不影响整个批次
- 自动创建错误结果记录
- Single problem failure doesn't affect entire batch
- Automatically creates error result records

### 内存管理 / Memory Management

- 预分配结果列表，避免动态扩展
- 批次处理完成后立即释放资源
- Pre-allocate result list to avoid dynamic expansion
- Release resources immediately after batch completion

---

## 代码结构 / Code Structure

```
hope_code/
├── evaluate_framework.py      # 原始评估器（不修改）
│                               # Original evaluator (no changes)
├── batch_evaluator.py          # 批量并行评估器（新增）
│                               # Batch parallel evaluator (new)
├── demo_batch.py               # 快速演示脚本（新增）
│                               # Quick demo script (new)
└── BATCH_EVALUATION_GUIDE.md   # 本文档（新增）
                                # This guide (new)
```

---

## 总结 / Summary

### ✅ 优势 / Advantages

1. **无侵入性** - 不修改任何原有代码
2. **显著提速** - 理论加速比可达 batch_size 倍
3. **易于使用** - 命令行接口与原版完全相同
4. **完全兼容** - 输出格式与原版一致

### 🎯 适用场景 / Use Cases

- 大规模评估（> 50 题）
- API 延迟较高的环境
- 需要快速获得评估结果
- 对比实验（多个方法 × 多个数据集）

### 🚀 下一步 / Next Steps

```bash
# 1. 运行演示
python demo_batch.py

# 2. 小规模测试
python batch_evaluator.py --dataset gsm8k --limit 10 --batch-size 3

# 3. 正式评估
python batch_evaluator.py --dataset gsm8k --limit 50 --batch-size 5 --methods all
```

---

**Enjoy faster evaluations! 享受更快的评估！** 🚀
