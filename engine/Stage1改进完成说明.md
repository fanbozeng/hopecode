# Stage 1: Domain Expert Review 改进完成

## ✅ **改进目标**

让Stage 1真正修复DAG，而不是只改`description`字段！

---

## 🔧 **改进内容**

### **1. 更新Prompt模板（prompts/expert_review_prompt.txt）**

#### **新增`corrected_dag`字段：**

```json
{
  "problem_domain": "math" | "physics" | "mixed",
  "issues": [...],
  "corrections": [...],
  "corrected_dag": {  // ← 新增！LLM输出修正后的完整DAG
    "target_variable": "...",
    "knowns": {...},  // 修正后的
    "causal_graph": [...],  // 修正后的
    "computation_plan": [...]  // 修正后的
  },
  "overall_assessment": "..."
}
```

#### **添加了清晰的示例：**

**示例1：物理错误（F=ma改为F=mg）**
```json
{
  "issues": ["Used 'a' instead of 'g'"],
  "corrected_dag": {
    "knowns": {"mass": 2, "g": 9.8},  // 改了！
    "causal_graph": [
      {"cause": ["mass", "g"], "effect": "F", "rule": "F = m * g"}  // 改了！
    ],
    "computation_plan": [
      {"inputs": ["mass", "g"], "description": "F = mg"}  // 改了！
    ]
  }
}
```

**示例2：数学错误（x=4改为x=3）**
- 展示了如何修正computation_plan中的值

**示例3：无错误（corrected_dag与输入相同）**
- 告诉LLM如果没错误就返回原始DAG

---

### **2. 更新代码实现（engine/domain_expert_reviewer.py）**

#### **旧实现（❌ 只改description）：**

```python
def _apply_corrections(self, dag, corrections):
    reviewed_dag = dag.copy()
    for correction in corrections:
        # 只改description
        step['description'] = corrected
    return reviewed_dag
```

#### **新实现（✅ 使用LLM返回的完整DAG）：**

```python
# Get corrected DAG from expert review
corrected_dag = review_report.get('corrected_dag')

if corrected_dag:
    # Validate structure
    if not self._validate_dag_structure(corrected_dag):
        return dag, review_report  # 验证失败，保留原始
    
    # Use corrected DAG
    reviewed_dag = corrected_dag  # ← 直接使用LLM返回的DAG
else:
    # Fallback
    reviewed_dag = dag
```

#### **新增验证方法：**

```python
def _validate_dag_structure(self, dag):
    """验证corrected_dag的结构是否正确"""
    
    # 检查必需字段
    required_fields = ['target_variable', 'knowns', 
                       'causal_graph', 'computation_plan']
    
    # 检查causal_graph结构
    for link in dag['causal_graph']:
        if 'cause' not in link or 'effect' not in link or 'rule' not in link:
            return False
    
    # 检查computation_plan结构
    for step in dag['computation_plan']:
        if 'id' not in step or 'target' not in step or 'inputs' not in step:
            return False
    
    return True
```

---

## 📊 **改进前后对比**

### **改进前（❌ 无效）：**

```
输入DAG:
  knowns: {"mass": 2, "a": 5}
  causal_graph: [{"rule": "F = m * a"}]
  computation_plan: [{"inputs": ["mass", "a"]}]

专家发现：应该用g=9.8，不是a=5

代码"修正"后:
  knowns: {"mass": 2, "a": 5}  ← 没变
  causal_graph: [{"rule": "F = m * a"}]  ← 没变
  computation_plan: [
    {"inputs": ["mass", "a"], "description": "F = mg = 19.6"}  ← 只有这个变了
  ]

问题：description说F=mg，但实际还是F=ma！
```

### **改进后（✅ 有效）：**

```
输入DAG:
  knowns: {"mass": 2, "a": 5}
  causal_graph: [{"rule": "F = m * a"}]
  computation_plan: [{"inputs": ["mass", "a"]}]

专家发现：应该用g=9.8，不是a=5

LLM返回corrected_dag:
  knowns: {"mass": 2, "g": 9.8}  ← 改了！
  causal_graph: [{"rule": "F = m * g"}]  ← 改了！
  computation_plan: [
    {"inputs": ["mass", "g"], "description": "F = mg = 19.6"}  ← 都改了！
  ]

结果：DAG的核心逻辑被真正修复！
```

---

## 🎯 **与Stage 3的一致性**

现在Stage 1和Stage 3都使用相同的策略：

| 阶段 | 策略 | 代码量 | 效果 |
|------|------|--------|------|
| **Stage 1 (新)** | LLM直接输出corrected_dag | ~200行 | ✅ 真正修复 |
| **Stage 3 (新)** | LLM直接输出optimized_dag | ~200行 | ✅ 真正优化 |

**都是：**
1. 精心设计的Prompt
2. LLM返回完整的修正/优化后DAG
3. 验证结构
4. 直接使用

---

## 📈 **现在的完整Pipeline**

```
Step1: Multi-Agent Scaffolding
  ↓ 生成初始DAG

Stage 1: Domain Expert Review (改进后)
  ↓ LLM修正公式错误 → 返回corrected_dag ✅ 真正修改了
  
Stage 2: RAG Knowledge Enhancement
  ↓ 注入新知识 (待检查)
  
Stage 3: Causal Structure Optimization (已改进)
  ↓ LLM优化结构 → 返回optimized_dag ✅ 真正优化了
  
Step3: LLM-Based Computation
  使用最终DAG计算答案
```

---

## 🎉 **现在的效果**

### **场景1：发现错误**

```
🔬 Expert reviewing DAG...
  Calling expert LLM...
  Issues detected:
    • [high] Used general acceleration 'a' instead of 'g'
    • [high] Acceleration value 5 m/s² is incorrect
  Corrections applied:
    • knowns: a=5 → g=9.8
    • causal_graph: F=ma → F=mg
    • computation_plan: inputs=[mass, a] → [mass, g]
✓ [physics] Found 2 issues, applied 2 corrections
```

**DAG被真正修复！**

### **场景2：没有错误**

```
🔬 Expert reviewing DAG...
  Calling expert LLM...
✓ [physics] No issues found, DAG is correct
```

**返回原始DAG（corrected_dag与输入相同）**

### **场景3：验证失败**

```
🔬 Expert reviewing DAG...
  Calling expert LLM...
✗ [physics] Corrected DAG has invalid structure, keeping original
  Missing required field: computation_plan
```

**安全fallback到原始DAG**

---

## ✅ **总结**

### **改进前：**
- ❌ 只改了`step['description']`
- ❌ `causal_graph`的`rule`没变
- ❌ `computation_plan`的`inputs`没变
- ❌ `knowns`没变
- ❌ **用了跟没用一样**

### **改进后：**
- ✅ LLM返回完整的`corrected_dag`
- ✅ `causal_graph`被真正修正
- ✅ `computation_plan`被真正修正
- ✅ `knowns`被真正修正
- ✅ **真正修复了DAG的错误！**

### **与Stage 3一致：**
- ✅ 都用LLM直接输出完整DAG
- ✅ 都有结构验证
- ✅ 都有安全fallback
- ✅ 代码简洁（~200行）

**现在Stage 1真正有用了！** 🎉

---

## 🚀 **使用方式**

```python
# 初始化（需要提供expert_client）
reviewer = DomainExpertReviewer(
    math_expert_client=expert_client,
    physics_expert_client=expert_client,
    verbose=True
)

# 审查并修正DAG
reviewed_dag, report = reviewer.review_dag(
    dag=current_dag,
    problem_text="A 2kg mass falls under gravity. Find force."
)

# 查看修正情况
print(f"Issues: {len(report['issues'])}")
print(f"Corrections: {len(report['corrections'])}")
print(f"Domain: {report['problem_domain']}")

# reviewed_dag现在是真正修正后的DAG！
```

**Stage 1现在和Stage 3一样强大了！** 🚀



