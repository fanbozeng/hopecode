# LLM驱动的Causal Structure Optimization 完整方案

## 🎯 **设计理念**

**用户说得对：用Prompt比写复杂逻辑简单多了！**

---

## ✅ **新实现 vs 旧实现对比**

### **旧实现（❌ 无效）：**
```python
1. 构建图 → NetworkX
2. 识别Chain/Fork/Collider → 规则检测
3. 验证因果方向 → 启发式规则
4. 检测结构问题 → 环路、孤立节点
5. "应用"优化 → 只加metadata，不改DAG！
```

**问题：**
- ❌ 写了500+行代码
- ❌ 只做分析，不做修改
- ❌ causal_graph和computation_plan完全没变
- ❌ 用了跟没用一样

### **新实现（✅ 有效）：**
```python
1. 构建图 → 快速检查（可选）
2. 调用LLM → 发送DAG + 问题
3. LLM分析 → 检测所有问题
4. LLM优化 → 直接输出修复后的完整DAG
5. 验证 → 确保结构正确
6. 返回 → 优化后的DAG + 报告
```

**优势：**
- ✅ 代码简洁（~200行）
- ✅ LLM真正修改DAG
- ✅ causal_graph和computation_plan都被优化
- ✅ 灵活，可以处理各种复杂情况

---

## 📝 **核心Prompt设计**

### **Prompt要求LLM做什么：**

#### **1. 检测问题**
```
- Cycles（环路）
- Isolated nodes（孤立节点）
- Skipped steps（跳步）
- Incorrect computation order（计算顺序错误）
- Inconsistent causal patterns（模式不一致）
```

#### **2. 识别模式**
```
- Chain: A → B → C
- Fork: A ← B → C
- Collider: A → B ← C
```

#### **3. 优化DAG**
```
- Fix cycles（修复环路）
- Connect isolated nodes（连接孤立节点）
- Add missing steps（添加缺失步骤）
- Reorder computation_plan（重排计算顺序）
- Ensure consistency（确保一致性）
```

#### **4. 输出格式**
```json
{
  "issues_detected": [...],
  "modifications_made": [...],
  "optimized_dag": {
    "target_variable": "...",
    "knowns": {...},
    "causal_graph": [...],  // 修改后的！
    "computation_plan": [...]  // 修改后的！
  },
  "causal_patterns": {...},
  "validation": {...},
  "reasoning": "..."
}
```

---

## 🔄 **完整流程**

```
输入DAG (from Stage 2)
    ↓
构建图（快速检查是否为空）
    ↓
准备Prompt
    ├─ problem_text
    └─ current_dag (JSON)
    ↓
调用LLM（temperature=0.0）
    ↓
解析响应（提取JSON）
    ↓
验证优化后的DAG
    ├─ 检查必需字段
    ├─ 检查causal_graph结构
    └─ 检查computation_plan结构
    ↓
    Valid? ──No──> 返回原始DAG + 错误报告
    ↓ Yes
生成结构报告
    ├─ issues_detected
    ├─ modifications_made
    ├─ causal_patterns
    └─ validation
    ↓
返回（优化后的DAG，报告）
```

---

## 📊 **示例场景**

### **场景1：检测到跳步**

**输入DAG：**
```json
{
  "causal_graph": [
    {"cause": ["mass"], "effect": "acceleration", "rule": "a = F/m"}
  ],
  "computation_plan": [
    {"id": "step1", "target": "acceleration", "inputs": ["mass"]}
  ]
}
```

**LLM检测：**
```
问题：Missing force F between mass and acceleration
严重性：high
```

**LLM优化：**
```json
{
  "modifications_made": [
    "Added intermediate variable 'gravitational_force' with rule F=mg",
    "Reordered computation_plan: force first, then acceleration"
  ],
  "optimized_dag": {
    "causal_graph": [
      {"cause": ["mass", "g"], "effect": "gravitational_force", "rule": "F = m * g"},
      {"cause": ["gravitational_force", "mass"], "effect": "acceleration", "rule": "a = F / m"}
    ],
    "computation_plan": [
      {"id": "step1", "target": "gravitational_force", "inputs": ["mass", "g"]},
      {"id": "step2", "target": "acceleration", "inputs": [{"ref": "step1"}, "mass"]}
    ]
  }
}
```

### **场景2：检测到环路**

**输入DAG：**
```json
{
  "causal_graph": [
    {"cause": ["A"], "effect": "B", "rule": "..."},
    {"cause": ["B"], "effect": "C", "rule": "..."},
    {"cause": ["C"], "effect": "A", "rule": "..."}  // 环！
  ]
}
```

**LLM检测：**
```
问题：Graph contains cycle: A → B → C → A
严重性：high
```

**LLM优化：**
```json
{
  "modifications_made": [
    "Removed edge C→A to break cycle (C does not actually cause A)"
  ],
  "optimized_dag": {
    "causal_graph": [
      {"cause": ["A"], "effect": "B", "rule": "..."},
      {"cause": ["B"], "effect": "C", "rule": "..."}
      // C→A被移除
    ]
  }
}
```

### **场景3：检测到孤立节点**

**输入DAG：**
```json
{
  "causal_graph": [
    {"cause": ["A"], "effect": "B", "rule": "..."}
  ],
  "computation_plan": [
    {"id": "step1", "target": "B", "inputs": ["A"]},
    {"id": "step2", "target": "C", "inputs": [{"ref": "step1"}]}  // C依赖B
  ]
}
```

**LLM检测：**
```
问题：Node C is isolated (not in causal_graph)
严重性：medium
```

**LLM优化：**
```json
{
  "modifications_made": [
    "Added edge B→C to connect isolated node C"
  ],
  "optimized_dag": {
    "causal_graph": [
      {"cause": ["A"], "effect": "B", "rule": "..."},
      {"cause": ["B"], "effect": "C", "rule": "..."}  // 新增
    ]
  }
}
```

---

## 💻 **代码实现**

### **主方法：**
```python
def optimize_causal_structure(self, dag, problem_text):
    """Use LLM to optimize DAG structure"""
    
    # 1. 检查
    if not self.causal_expert:
        return dag, {'status': 'skipped'}
    
    # 2. 准备prompt
    prompt = self.optimization_prompt.format(
        problem=problem_text,
        dag=json.dumps(dag, indent=2, ensure_ascii=False)
    )
    
    # 3. 调用LLM
    response = self.causal_expert.complete(prompt, temperature=0.0)
    
    # 4. 解析
    result = self._parse_optimization_response(response)
    optimized_dag = result.get('optimized_dag')
    
    # 5. 验证
    if not self._validate_dag_structure(optimized_dag):
        return dag, {'status': 'validation_failed'}
    
    # 6. 返回
    return optimized_dag, {
        'status': 'success',
        'issues_detected': result.get('issues_detected', []),
        'modifications_made': result.get('modifications_made', []),
        'causal_patterns': result.get('causal_patterns', {}),
        'reasoning': result.get('reasoning', '')
    }
```

### **验证方法：**
```python
def _validate_dag_structure(self, dag):
    """Validate optimized DAG has correct structure"""
    
    required_fields = ['target_variable', 'knowns', 
                       'causal_graph', 'computation_plan']
    
    # 检查必需字段
    for field in required_fields:
        if field not in dag:
            return False
    
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

## 🎨 **控制台输出示例**

### **无问题：**
```
🔗 Optimizing causal structure...
  🤖 Analyzing DAG structure with LLM...
    Calling causal expert LLM...
  ✓ No optimization needed: DAG structure is already good
```

### **有问题（修复）：**
```
🔗 Optimizing causal structure...
  🤖 Analyzing DAG structure with LLM...
    Calling causal expert LLM...
    Modifications applied:
      • Added intermediate variable 'gravitational_force' with rule F=mg
      • Reordered computation_plan: force first, then acceleration
      • Connected isolated node C with edge B→C
  ✓ Optimization complete: 3 issues detected, 3 modifications applied
```

### **验证失败：**
```
🔗 Optimizing causal structure...
  🤖 Analyzing DAG structure with LLM...
    Calling causal expert LLM...
    ⚠️  Optimized DAG has invalid structure, keeping original
      Missing required field: computation_plan
```

---

## 📈 **优势总结**

| 方面 | 旧实现（规则） | 新实现（LLM） |
|------|---------------|--------------|
| **代码量** | 500+ 行 | ~200 行 |
| **复杂度** | 高（图算法） | 低（Prompt） |
| **灵活性** | 差（需改代码） | 好（改Prompt） |
| **实际修改DAG** | ❌ 否 | ✅ 是 |
| **理解语义** | ❌ 否 | ✅ 是 |
| **处理边界情况** | ❌ 难 | ✅ 易 |
| **维护成本** | 高 | 低 |

---

## 🚀 **关键创新点**

### **1. 全量输出而非增量修改**
```python
# ❌ 旧方式：增量修改
dag_copy = deepcopy(dag)
dag_copy['causal_graph'].append(new_edge)  # 容易出错
dag_copy['computation_plan'].insert(...)  # 难以维护

# ✅ 新方式：全量输出
optimized_dag = llm.optimize(dag)  # LLM输出完整的新DAG
```

### **2. 语义理解**
```python
# ❌ 规则检测：只能识别"result"、"answer"等关键词
if "result" in source_name:
    # 可能方向错误

# ✅ LLM理解：理解物理/数学含义
"mass causes force (F=mg), force causes acceleration (a=F/m)"
```

### **3. 一次调用完成所有优化**
```python
# ❌ 旧方式：多次调用
dag = fix_cycles(dag)
dag = fix_isolated(dag)
dag = fix_skipped_steps(dag)
dag = optimize_order(dag)

# ✅ 新方式：一次完成
optimized_dag = llm_optimize(dag)  # 一次性修复所有问题
```

---

## ✅ **总结**

**旧实现：**
- 写了500+行复杂代码
- 只做分析，不做修改
- 用了跟没用一样

**新实现：**
- 用一个精心设计的Prompt
- LLM真正优化DAG
- 简单、灵活、有效

**用户说得对：不用这么复杂，直接用prompt做最好了！** 🎉

---

## 📝 **使用方式**

```python
# 初始化（需要提供causal_expert_client）
optimizer = CausalStructureOptimizer(
    causal_expert_client=llm_client,
    verbose=True
)

# 优化DAG
optimized_dag, report = optimizer.optimize_causal_structure(
    dag=current_dag,
    problem_text="A 2kg mass falls under gravity. Find acceleration."
)

# 查看报告
print(f"Issues detected: {len(report['issues_detected'])}")
print(f"Modifications: {report['modifications_made']}")
print(f"Reasoning: {report['reasoning']}")
```

**这才是Stage 3应该有的样子！** 🚀



