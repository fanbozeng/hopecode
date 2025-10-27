# Question Perspective Augmentor - 使用指南
# Question Perspective Augmentor - User Guide

## 📚 目录 (Table of Contents)

- [概述](#概述-overview)
- [核心概念](#核心概念-core-concepts)
- [快速开始](#快速开始-quick-start)
- [释义策略](#释义策略-paraphrasing-strategies)
- [一致性测试](#一致性测试-consistency-testing)
- [鲁棒性评估](#鲁棒性评估-robustness-evaluation)
- [与评估框架集成](#与评估框架集成-integration)
- [高级用法](#高级用法-advanced-usage)
- [性能考虑](#性能考虑-performance-considerations)

---

## 概述 (Overview)

### 什么是问题视角增强器？

**问题视角增强器 (Question Perspective Augmentor)** 是一个专门设计的模块，用于通过**对抗性释义 (Adversarial Paraphrasing)** 测试和增强推理系统的鲁棒性。

### 为什么需要它？

1. **检测提示脆弱性 (Prompt Brittleness)**
   - 真正理解问题的模型不应该因为措辞变化而给出不同答案
   - 从"施加力"改为"受到力的作用"不应影响结果

2. **压力测试 (Stress Testing)**
   - 系统化地生成语义等价的问题变体
   - 验证推理过程的一致性和可靠性

3. **提升鲁棒性 (Enhance Robustness)**
   - 识别系统的弱点
   - 指导改进方向

### 理论基础

基于以下前沿研究：
- **Adversarial Prompting for Black Box Foundation Models** (2023)
- **Prompt Robustness and Consistency Testing** (2024)
- **Semantic Invariance Testing for NLP Systems** (2024)

---

## 核心概念 (Core Concepts)

### 1. 对抗性释义 (Adversarial Paraphrasing)

系统性地生成问题的**语义等价变体**，保持：
- ✅ 所有物理事实不变
- ✅ 所有数值和单位不变
- ✅ 所有逻辑关系不变
- ❌ 仅改变语言表达方式

### 2. 一致性检测 (Consistency Detection)

测试模型对不同表述的同一问题是否给出一致答案：
- **高一致性** → 模型真正理解问题
- **低一致性** → 模型依赖表面特征

### 3. 鲁棒性评分 (Robustness Scoring)

综合评估：
```
Robustness Score = Consistency Score × Correctness Rate
```

- **完美鲁棒性 (1.0)**: 所有变体答案一致且正确
- **良好鲁棒性 (0.7-0.9)**: 大部分变体一致
- **脆弱性 (< 0.7)**: 对措辞敏感

---

## 快速开始 (Quick Start)

### 安装

```bash
# 确保已安装基础依赖
pip install -r requirements.txt

# 模块已包含在 engine/ 目录中
# engine/question_augmentor.py
```

### 示例 1: 生成释义

```python
from engine.question_augmentor import QuestionAugmentor

# 初始化增强器
augmentor = QuestionAugmentor(
    num_paraphrases=3,  # 生成3个释义
    temperature=0.7,     # LLM温度
    verbose=True         # 显示详细信息
)

# 原始问题
question = "一个质量为10kg的物体初始静止，施加50N的恒定力持续5秒。求最终速度。"

# 生成释义
paraphrases = augmentor.generate_paraphrases(question)

# 查看结果
for i, p in enumerate(paraphrases, 1):
    print(f"\n{i}. [{p.paraphrase_strategy}]")
    print(f"   {p.paraphrased_question}")
```

**输出示例**:
```
1. [syntactic_restructuring]
   对于一个10kg质量的静止物体，在5秒内对其施加50N的恒力，最终速度是多少？

2. [voice_conversion]
   最终速度是多少？已知物体质量10kg，初始静止，受到50N恒定力作用持续5秒。

3. [information_reordering]
   求最终速度：物体初始静止，质量10kg，持续5秒受到50N的恒定力。
```

### 示例 2: 一致性测试

```python
from engine.question_augmentor import QuestionAugmentor
from main import CausalReasoningEngine

# 初始化
augmentor = QuestionAugmentor(num_paraphrases=3, verbose=True)
engine = CausalReasoningEngine()

# 定义求解函数
def solver(question):
    return engine.solve_problem(question, include_validation=False)

# 测试一致性
result = augmentor.test_consistency(
    question=question,
    solver_func=solver,
    answer_extractor_func=lambda r: r.get('final_answer'),
    similarity_threshold=0.9
)

# 查看结果
print(f"Consistency Score: {result.consistency_score:.2%}")
print(f"Robustness Score: {result.robustness_score:.2%}")
print(f"Inconsistent Cases: {len(result.inconsistent_cases)}")
```

### 命令行使用

```bash
# 1. 简单演示：仅生成释义
python test_question_augmentor.py --demo simple

# 2. 完整演示：包括一致性测试
python test_question_augmentor.py --demo consistency

# 3. 测试自定义问题
python test_question_augmentor.py --question "Your question here"

# 4. 完整一致性测试（需要求解）
python test_question_augmentor.py --question "Your question" --consistency-test
```

---

## 释义策略 (Paraphrasing Strategies)

### 1. 句法重构 (Syntactic Restructuring)

改变句子结构，保持语义不变。

**原始**:
```
一个质量为10kg的物体初始静止，施加50N的恒定力持续5秒。求最终速度。
```

**释义**:
```
对于一个10kg质量的静止物体，在5秒内对其施加50N的恒力，最终速度是多少？
```

**特点**:
- 简单句 → 复合句
- 从句重排
- 问句形式变化

### 2. 语态转换 (Voice Conversion)

在主动和被动语态之间转换。

**原始**:
```
A force of 20 N pushes a 5 kg box.
```

**释义**:
```
A 5 kg box is pushed by a force of 20 N.
```

**特点**:
- 主动 → 被动
- 被动 → 主动
- 保持动作关系

### 3. 同义词替换 (Synonym Substitution)

用同义词替换非专业术语。

**原始**:
```
施加一个力在物体上
```

**释义**:
```
对物体作用一个力
```

**特点**:
- 保留专业术语（力、质量等）
- 保留所有数值
- 仅替换连接词和辅助词

### 4. 信息重排 (Information Reordering)

改变信息呈现顺序。

**原始**:
```
质量10kg，初速度0，力50N，时间5s，求最终速度。
```

**释义**:
```
求最终速度：时间5s，力50N，质量10kg，初速度0。
```

**特点**:
- 所有信息完整保留
- 仅改变顺序
- 测试模型的信息整合能力

### 5. 正式度变化 (Formality Change)

调整语言的正式程度。

**原始 (正式)**:
```
已知物体质量为10千克，初始速度为零，受恒力50牛顿作用5秒，求末速度。
```

**释义 (非正式)**:
```
一个10公斤的东西一开始不动，给它推50牛的力推5秒，最后跑多快？
```

**特点**:
- 学术 ↔ 口语
- 完整 ↔ 简化
- 测试模型对不同风格的适应性

### 6. 复杂度变化 (Complexity Variation)

简化或详细化表达。

**原始**:
```
物体在力的作用下加速。
```

**详细化**:
```
当外力施加在物体上时，根据牛顿第二定律，物体会产生加速度。
```

**简化**:
```
力推物体，物体加速。
```

---

## 一致性测试 (Consistency Testing)

### 工作流程

```
1. 接收原始问题
   ↓
2. 生成N个释义（N=3-5）
   ↓
3. 使用推理系统求解原始问题
   ↓
4. 使用同一系统求解所有释义
   ↓
5. 比较答案一致性
   ↓
6. 生成鲁棒性报告
```

### 一致性判断

**数值答案**:
```python
# 允许小的相对误差
relative_error = |ans1 - ans2| / max(|ans1|, |ans2|)
consistent = relative_error < 0.1  # 10%阈值
```

**文本答案**:
```python
# 字符串匹配（标准化后）
consistent = normalize(ans1) == normalize(ans2)
```

### 结果解读

| 一致性分数 | 状态 | 说明 |
|-----------|------|------|
| ≥ 0.9 | ✅ 优秀 | 系统非常鲁棒，几乎不受措辞影响 |
| 0.7 - 0.9 | ⚠️ 良好 | 系统总体稳定，少数变体有差异 |
| 0.5 - 0.7 | ⚠️ 一般 | 系统对措辞较为敏感，需改进 |
| < 0.5 | ❌ 脆弱 | 系统严重依赖特定表述 |

---

## 鲁棒性评估 (Robustness Evaluation)

### 批量评估

```bash
# 评估 GSM8K 数据集上的鲁棒性
python evaluate_with_augmentation.py \
    --dataset gsm8k \
    --limit 20 \
    --num-paraphrases 3 \
    --methods full_framework direct_llm

# 评估多个方法
python evaluate_with_augmentation.py \
    --dataset math \
    --limit 10 \
    --num-paraphrases 5 \
    --methods full_framework zero_shot_cot few_shot_cot \
    --verbose
```

### 评估指标

1. **Original Accuracy** (原始准确率)
   - 在原始问题上的正确率
   - 基础性能指标

2. **Average Consistency** (平均一致性)
   - 跨释义的答案一致性
   - 范围: 0-1

3. **Average Robustness** (平均鲁棒性)
   - 综合指标：准确 × 一致
   - 真正的鲁棒性度量

4. **Fully Robust Rate** (完全鲁棒率)
   - 100%一致且全部正确的题目比例
   - 最严格的标准

### 结果分析示例

```json
{
  "summary": {
    "full_framework": {
      "total_problems": 20,
      "original_accuracy": 0.85,
      "average_consistency": 0.92,
      "average_robustness": 0.78,
      "fully_robust_rate": 0.65
    },
    "direct_llm": {
      "total_problems": 20,
      "original_accuracy": 0.75,
      "average_consistency": 0.70,
      "average_robustness": 0.53,
      "fully_robust_rate": 0.30
    }
  }
}
```

**解读**:
- Full Framework: 85%准确，92%一致 → 高鲁棒性
- Direct LLM: 75%准确，70%一致 → 较脆弱

---

## 与评估框架集成 (Integration)

### 集成到现有评估

```python
from evaluate_framework import FrameworkEvaluator, EvaluationMethod
from engine.question_augmentor import QuestionAugmentor

class RobustEvaluator(FrameworkEvaluator):
    def __init__(self, num_paraphrases=3, **kwargs):
        super().__init__(**kwargs)
        self.augmentor = QuestionAugmentor(num_paraphrases)
    
    def evaluate_with_robustness(self, problem, method):
        # 评估原始问题
        original_result = self.evaluate_single(problem, method)
        
        # 生成并评估释义
        paraphrases = self.augmentor.generate_paraphrases(
            problem['question']
        )
        
        paraphrase_results = []
        for p in paraphrases:
            modified_problem = problem.copy()
            modified_problem['question'] = p.paraphrased_question
            result = self.evaluate_single(modified_problem, method)
            paraphrase_results.append(result)
        
        # 计算鲁棒性
        consistency = self._calc_consistency(
            original_result, paraphrase_results
        )
        
        return {
            'original': original_result,
            'paraphrases': paraphrase_results,
            'consistency': consistency
        }
```

### 添加到批量评估

```python
# 在 batch_evaluator.py 中添加鲁棒性测试选项
python batch_evaluator.py \
    --dataset gsm8k \
    --limit 50 \
    --batch-size 5 \
    --methods baselines \
    --enable-robustness-test \
    --num-paraphrases 3
```

---

## 高级用法 (Advanced Usage)

### 1. 自定义释义策略

```python
from engine.question_augmentor import QuestionAugmentor

class CustomAugmentor(QuestionAugmentor):
    PARAPHRASE_STRATEGIES = [
        "domain_specific",      # 领域特定转换
        "multilingual",         # 多语言翻译
        "notation_variation",   # 符号表示变化
    ]
    
    def _generate_domain_specific(self, question):
        # 实现领域特定的释义策略
        pass
```

### 2. 引导式生成

使用检测器引导释义生成，找到模型的"盲点"：

```python
class GuidedAugmentor(QuestionAugmentor):
    def __init__(self, detector_model, **kwargs):
        super().__init__(**kwargs)
        self.detector = detector_model
    
    def generate_adversarial_paraphrase(self, question):
        """
        生成能最大化欺骗检测器的释义
        """
        candidates = self.generate_paraphrases(question)
        
        # 评估每个候选
        scores = [
            self.detector.evaluate(c.paraphrased_question)
            for c in candidates
        ]
        
        # 选择最具对抗性的
        best_idx = np.argmax(scores)
        return candidates[best_idx]
```

### 3. 多轮迭代增强

```python
def iterative_augmentation(question, engine, rounds=3):
    """
    多轮增强，逐步提高难度
    """
    current_question = question
    history = []
    
    for round in range(rounds):
        # 生成释义
        paraphrases = augmentor.generate_paraphrases(current_question)
        
        # 找到导致不一致的释义
        for p in paraphrases:
            result = engine.solve_problem(p.paraphrased_question)
            if not consistent_with_original(result):
                # 记录并使用这个作为下一轮输入
                history.append({
                    'round': round,
                    'paraphrase': p,
                    'result': result
                })
                current_question = p.paraphrased_question
                break
    
    return history
```

### 4. 与知识检索集成

测试知识检索器对不同表述的鲁棒性：

```python
from engine.question_augmentor import QuestionAugmentor
from engine.retriever import KnowledgeRetriever

augmentor = QuestionAugmentor(num_paraphrases=5)
retriever = KnowledgeRetriever("data/knowledge_base.json")

question = "一个物体受到力的作用"
paraphrases = augmentor.generate_paraphrases(question)

# 测试检索一致性
retrieved_rules = {}
for p in [question] + [pp.paraphrased_question for pp in paraphrases]:
    rules = retriever.get_knowledge(p)
    retrieved_rules[p] = rules

# 分析：所有释义是否检索到相同规则？
consistency = analyze_retrieval_consistency(retrieved_rules)
```

---

## 性能考虑 (Performance Considerations)

### 计算成本

每个问题的增强成本：
```
Total Cost = (1 + N) × Solver_Cost
```
其中 N = 释义数量

**建议**:
- 开发/调试: N = 2-3
- 完整评估: N = 3-5
- 发布前测试: N = 5-10

### 并行化

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_augmentation_test(problems, num_workers=4):
    augmentor = QuestionAugmentor(num_paraphrases=3)
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(augmentor.test_consistency, p, solver_func)
            for p in problems
        ]
        
        results = [f.result() for f in futures]
    
    return results
```

### 缓存策略

```python
import hashlib
import json
from pathlib import Path

class CachedAugmentor(QuestionAugmentor):
    def __init__(self, cache_dir="cache/paraphrases", **kwargs):
        super().__init__(**kwargs)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_paraphrases(self, question):
        # 检查缓存
        cache_key = hashlib.md5(question.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
                return [ParaphraseResult(**p) for p in cached]
        
        # 生成并缓存
        paraphrases = super().generate_paraphrases(question)
        
        with open(cache_file, 'w') as f:
            json.dump([p.to_dict() for p in paraphrases], f)
        
        return paraphrases
```

---

## 最佳实践 (Best Practices)

### 1. 选择合适的释义数量

| 场景 | 推荐数量 | 原因 |
|------|---------|------|
| 快速验证 | 2-3 | 平衡速度和覆盖 |
| 标准评估 | 3-5 | 充分测试鲁棒性 |
| 严格测试 | 5-10 | 全面覆盖策略 |
| 研究发布 | 10+ | 最大化置信度 |

### 2. 策略选择

根据应用场景选择策略：

**物理问题**:
- 句法重构 ✅
- 语态转换 ✅
- 信息重排 ✅
- 同义词替换 ⚠️ (保留专业术语)

**数学问题**:
- 符号表示变化 ✅
- 信息重排 ✅
- 复杂度变化 ✅

**跨语言测试**:
- 翻译（中↔英）
- 保持数学符号

### 3. 结果解读

不要仅看一致性分数，要分析：
1. **哪些策略导致不一致？** → 指向特定弱点
2. **错误是系统性的还是随机的？** → 判断问题性质
3. **原始问题正确但释义错误？** → 提示脆弱性
4. **所有版本都错误？** → 知识或推理缺陷

### 4. 迭代改进

```
1. 运行鲁棒性测试
   ↓
2. 识别脆弱案例
   ↓
3. 分析失败模式
   ↓
4. 改进系统（提示/检索/推理）
   ↓
5. 重新测试
```

---

## 故障排除 (Troubleshooting)

### 问题 1: 释义质量差

**症状**: 生成的释义改变了问题含义

**解决**:
```python
# 提高提示词的约束性
augmentor = QuestionAugmentor(
    temperature=0.3,  # 降低温度
    strategies=['syntactic_restructuring', 'information_reordering']  # 限制策略
)

# 或使用更强的模型
# 在 .env 中配置 GPT-4
```

### 问题 2: 一致性检测不准确

**症状**: 明显相同的答案被判定为不一致

**解决**:
```python
# 自定义答案比较函数
def custom_answer_extractor(result):
    answer = result.get('final_answer')
    # 标准化答案格式
    answer = normalize_answer(answer)
    return answer

result = augmentor.test_consistency(
    question=question,
    solver_func=solver,
    answer_extractor_func=custom_answer_extractor,
    similarity_threshold=0.85  # 调整阈值
)
```

### 问题 3: 运行时间过长

**症状**: 测试一个问题需要很长时间

**解决**:
```python
# 1. 减少释义数量
augmentor = QuestionAugmentor(num_paraphrases=2)

# 2. 使用缓存
augmentor = CachedAugmentor()

# 3. 并行处理
from concurrent.futures import ThreadPoolExecutor
# 见上文并行化示例
```

---

## 示例工作流 (Example Workflow)

### 完整的鲁棒性测试流程

```bash
# Step 1: 快速验证
python test_question_augmentor.py --demo simple

# Step 2: 单题深度测试
python test_question_augmentor.py \
    --question "一个质量为10kg的物体..." \
    --consistency-test

# Step 3: 小批量评估
python evaluate_with_augmentation.py \
    --dataset gsm8k \
    --limit 10 \
    --num-paraphrases 3 \
    --methods full_framework

# Step 4: 分析结果
python visualize_results.py \
    evaluation_results/gsm8k_robustness_*.json

# Step 5: 完整评估
python evaluate_with_augmentation.py \
    --dataset gsm8k \
    --limit 100 \
    --num-paraphrases 5 \
    --methods baselines \
    --output results/final_robustness.json
```

---

## 参考文献 (References)

1. **Adversarial Prompting for Black Box Foundation Models** (2023)
   - 对抗性提示方法论

2. **Prompt Robustness and Consistency Testing** (2024)
   - 提示鲁棒性测试框架

3. **Semantic Invariance Testing for NLP Systems** (2024)
   - 语义不变性测试

4. **Paraphrase Generation for Robust NLP** (2023)
   - 释义生成技术

---

## 总结 (Summary)

问题视角增强器是提升因果推理系统鲁棒性的关键工具：

✅ **系统化测试**: 不依赖手工设计的测试用例
✅ **全面覆盖**: 多种释义策略覆盖不同语言变化
✅ **定量评估**: 一致性和鲁棒性分数提供客观度量
✅ **易于集成**: 无缝集成到现有评估框架
✅ **指导改进**: 识别弱点，指导系统优化

通过持续的鲁棒性测试，我们可以构建真正可靠的推理系统！

---

**更新日期**: 2025-10-19


