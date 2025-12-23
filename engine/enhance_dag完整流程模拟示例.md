# enhance_dag 完整流程模拟示例

## 📝 **问题描述**

> **Problem:** "一个质量为2kg的物体从静止开始自由下落，忽略空气阻力。求物体下落3秒后的速度。"

---

## 🎬 **完整流程**

```
Step1: Multi-Agent Scaffolding → 生成初始DAG (Fixed DAG)
    ↓
enhance_dag() 开始：
    ├─ Stage 1: Domain Expert Review (修正公式错误)
    ├─ Stage 2: RAG Knowledge Enhancement (补充知识)
    └─ Stage 3: Causal Structure Optimization (优化结构)
    ↓
返回 Enhanced DAG
```

---

## 📊 **阶段0：Step1输出的Initial DAG (Fixed DAG)**

这是Multi-Agent Scaffolding生成的初始DAG，**可能有错误**：

```json
{
  "target_variable": "final_velocity",
  "expected_answer_type": "Numerical",
  
  "knowns": {
    "mass": 2,
    "initial_velocity": 0,
    "acceleration": 5,  // ❌ 错误！应该用g=9.8
    "time": 3
  },
  
  "causal_graph": [
    {
      "cause": ["initial_velocity", "acceleration", "time"],
      "effect": "final_velocity",
      "rule": "v = v0 + a * t"  // ❌ 公式对，但a的值错了
    }
  ],
  
  "computation_plan": [
    {
      "id": "step1",
      "target": "final_velocity",
      "inputs": ["initial_velocity", "acceleration", "time"],
      "description": "计算最终速度：v = v0 + a*t = 0 + 5*3 = 15 m/s"  // ❌ 应该是29.4 m/s
    }
  ],
  
  "problem_model": "物体在恒定加速度下的运动",
  "chosen_strategy": "使用运动学方程 v = v0 + at"
}
```

**问题：**
- ❌ 使用了错误的加速度值 a=5，应该用重力加速度 g=9.8
- ❌ 结果错误：15 m/s（正确应该是 29.4 m/s）

---

## 🚀 **Pipeline启动**

```
════════════════════════════════════════════════════════
🚀 Starting DAG Enhancement Pipeline
🚀 开始DAG增强流水线
════════════════════════════════════════════════════════
```

---

## 📋 **Stage 1/3: Domain Expert Review（领域专家审查）**

### **输入：**
Initial DAG（上面的错误DAG）

### **过程：**
```
────────────────────────────────────────────────────────
📋 Stage 1/3: Domain Expert Review
📋 阶段1/3：领域专家审查
────────────────────────────────────────────────────────
🔬 Expert reviewing DAG...
  🤖 Calling expert LLM...
```

### **LLM专家分析：**

```json
{
  "problem_domain": "physics",
  
  "issues": [
    {
      "node": "final_velocity",
      "issue": "Used arbitrary acceleration a=5 instead of gravitational acceleration g=9.8 m/s²",
      "severity": "high",
      "category": "physics_violation"
    },
    {
      "node": "acceleration",
      "issue": "For free fall, must use g (gravitational acceleration), not generic 'a'",
      "severity": "high",
      "category": "formula_error"
    }
  ],
  
  "corrections": [
    {
      "node": "acceleration",
      "original": "acceleration = 5 m/s²",
      "corrected": "g = 9.8 m/s² (gravitational acceleration)",
      "reason": "Free fall motion is caused by gravity, must use g = 9.8 m/s² for Earth's surface"
    }
  ],
  
  "corrected_dag": {
    "target_variable": "final_velocity",
    "expected_answer_type": "Numerical",
    
    "knowns": {
      "mass": 2,
      "initial_velocity": 0,
      "g": 9.8,  // ✅ 修正：使用正确的重力加速度
      "time": 3
    },
    
    "causal_graph": [
      {
        "cause": ["initial_velocity", "g", "time"],
        "effect": "final_velocity",
        "rule": "v = v0 + g * t"  // ✅ 修正：使用g而不是a
      }
    ],
    
    "computation_plan": [
      {
        "id": "step1",
        "target": "final_velocity",
        "inputs": ["initial_velocity", "g", "time"],
        "description": "计算最终速度：v = v0 + g*t = 0 + 9.8*3 = 29.4 m/s"  // ✅ 正确！
      }
    ],
    
    "problem_model": "自由落体运动（只受重力作用）",
    "chosen_strategy": "使用自由落体运动学方程 v = v0 + gt"
  },
  
  "overall_assessment": "Critical error: Used arbitrary acceleration instead of gravitational acceleration. Corrected to use g = 9.8 m/s². The formula v = v0 + gt is now correct."
}
```

### **输出：**
```
  ✓ [physics] Found 2 issues, applied 2 corrections
    • Corrected: acceleration=5 → g=9.8
    • Corrected: rule "v = v0 + a*t" → "v = v0 + g*t"
    • Corrected: computation result 15 m/s → 29.4 m/s
```

### **Stage 1输出的DAG（Reviewed DAG）：**
```json
{
  "knowns": {"g": 9.8, ...},  // ✅ 已修正
  "causal_graph": [{"rule": "v = v0 + g * t"}],  // ✅ 已修正
  "computation_plan": [{"description": "v = 29.4 m/s"}]  // ✅ 已修正
}
```

---

## 📋 **Stage 2/3: RAG Knowledge Enhancement（RAG知识增强）**

### **输入：**
Reviewed DAG（Stage 1修正后的DAG）

### **过程：**
```
────────────────────────────────────────────────────────
📋 Stage 2/3: RAG Knowledge Enhancement
📋 阶段2/3：RAG知识增强
────────────────────────────────────────────────────────
🔍 RAG Knowledge Enhancer analyzing DAG...
  Identifying knowledge gaps...
```

### **LLM分析知识缺口：**

```json
{
  "knowledge_gaps": [
    {
      "gap": "缺少位移计算",
      "reason": "问题只问速度，但完整的自由落体分析应包括位移",
      "suggested_formula": "s = v0*t + 0.5*g*t²"
    },
    {
      "gap": "缺少能量分析",
      "reason": "可以通过动能变化验证结果",
      "suggested_formula": "ΔEk = 0.5*m*v² - 0.5*m*v0²"
    }
  ],
  
  "retrieved_knowledge": [
    "自由落体运动公式：v = v0 + gt",
    "位移公式：s = v0*t + 0.5*g*t²",
    "动能公式：Ek = 0.5*m*v²",
    "重力势能变化：ΔEp = -mg*s（向下为正）"
  ]
}
```

### **增强策略：**
```
  Strategy: add_context
  Adding knowledge as metadata (not modifying core DAG for this problem)
```

### **输出：**
```
  ✓ RAG enhancement completed
    • Added 4 reference formulas to metadata
    • Identified 2 potential knowledge extensions
    • Core DAG unchanged (target_variable only asks for velocity)
```

### **Stage 2输出的DAG（Knowledge-Enhanced DAG）：**
```json
{
  "target_variable": "final_velocity",
  "knowns": {"g": 9.8, ...},
  "causal_graph": [{"rule": "v = v0 + g * t"}],
  "computation_plan": [...],
  
  "enhancement_metadata": {  // ✅ 新增：知识增强元数据
    "rag_enhanced": true,
    "retrieved_knowledge": [
      "自由落体运动公式：v = v0 + gt",
      "位移公式：s = v0*t + 0.5*g*t²",
      "动能公式：Ek = 0.5*m*v²"
    ],
    "knowledge_gaps_identified": [
      "可扩展：计算位移",
      "可扩展：能量分析"
    ]
  }
}
```

**注意：** Stage 2主要添加了参考知识到metadata，核心DAG没变（因为问题只要求速度）。

---

## 📋 **Stage 3/3: Causal Structure Optimization（因果结构优化）**

### **输入：**
Knowledge-Enhanced DAG（Stage 2增强后的DAG）

### **过程：**
```
────────────────────────────────────────────────────────
📋 Stage 3/3: Causal Structure Optimization
📋 阶段3/3：因果结构优化
────────────────────────────────────────────────────────
🔗 Optimizing causal structure...
  🤖 Analyzing DAG structure with LLM...
    Calling causal expert LLM...
```

### **LLM结构分析：**

```json
{
  "issues_detected": [
    {
      "type": "missing_intermediate",
      "description": "Missing explicit gravity node as common cause",
      "severity": "low"
    }
  ],
  
  "modifications_made": [
    "No critical structural issues found",
    "DAG is already well-structured for this simple problem",
    "Computation order is correct: knowns → final_velocity"
  ],
  
  "optimized_dag": {
    "target_variable": "final_velocity",
    "expected_answer_type": "Numerical",
    
    "knowns": {
      "mass": 2,
      "initial_velocity": 0,
      "g": 9.8,
      "time": 3
    },
    
    "causal_graph": [
      {
        "cause": ["initial_velocity", "g", "time"],
        "effect": "final_velocity",
        "rule": "v = v0 + g * t"
      }
    ],
    
    "computation_plan": [
      {
        "id": "step1",
        "target": "final_velocity",
        "inputs": ["initial_velocity", "g", "time"],
        "description": "计算最终速度：v = v0 + g*t = 0 + 9.8*3 = 29.4 m/s"
      }
    ],
    
    "problem_model": "自由落体运动（只受重力作用）",
    "chosen_strategy": "使用自由落体运动学方程 v = v0 + gt",
    
    "enhancement_metadata": {
      "rag_enhanced": true,
      "structure_optimized": true,  // ✅ 新增
      "causal_patterns": {  // ✅ 新增
        "chains": [],
        "forks": [
          {
            "common_cause": "g",
            "effects": ["final_velocity"],
            "interpretation": "重力加速度g是速度变化的根本原因"
          }
        ],
        "colliders": []
      }
    }
  },
  
  "causal_patterns": {
    "chains": [],
    "forks": [
      {
        "common_cause": "g",
        "effects": ["final_velocity"],
        "interpretation": "Gravity g is the common cause driving the motion"
      }
    ],
    "colliders": []
  },
  
  "validation": {
    "is_dag": true,
    "is_connected": true,
    "computation_order_valid": true
  },
  
  "reasoning": "The DAG structure is simple and correct. No cycles or isolated nodes. Computation order is valid. The causal relationship is clear: gravity causes acceleration, which affects velocity over time."
}
```

### **输出：**
```
  ✓ No optimization needed: DAG structure is already good
    • Validated: is_dag = true
    • Validated: is_connected = true
    • Validated: computation_order_valid = true
    • Identified: 1 fork pattern (g as common cause)
```

### **Stage 3输出的DAG（Optimized DAG）：**
```json
{
  "target_variable": "final_velocity",
  "knowns": {"g": 9.8, ...},
  "causal_graph": [{"rule": "v = v0 + g * t"}],
  "computation_plan": [...],
  
  "enhancement_metadata": {
    "rag_enhanced": true,
    "structure_optimized": true,
    "causal_patterns": {
      "forks": [{"common_cause": "g", "effects": ["final_velocity"]}]
    },
    "structural_issues": []  // ✅ 无结构问题
  }
}
```

---

## ✅ **Pipeline完成**

```
════════════════════════════════════════════════════════
✅ DAG Enhancement Pipeline Completed
✅ DAG增强流水线完成
════════════════════════════════════════════════════════

Summary / 总结:
  • Stage 1: ✓ 2 corrections applied (fixed g value and formula)
  • Stage 2: ✓ 4 knowledge items added
  • Stage 3: ✓ Structure validated, no issues
  
Total enhancement time: 2.3s
════════════════════════════════════════════════════════
```

---

## 📊 **最终输出：Enhanced DAG**

```json
{
  "target_variable": "final_velocity",
  "expected_answer_type": "Numerical",
  
  "knowns": {
    "mass": 2,
    "initial_velocity": 0,
    "g": 9.8,  // ✅ Stage 1修正
    "time": 3
  },
  
  "causal_graph": [
    {
      "cause": ["initial_velocity", "g", "time"],
      "effect": "final_velocity",
      "rule": "v = v0 + g * t"  // ✅ Stage 1修正
    }
  ],
  
  "computation_plan": [
    {
      "id": "step1",
      "target": "final_velocity",
      "inputs": ["initial_velocity", "g", "time"],
      "description": "计算最终速度：v = v0 + g*t = 0 + 9.8*3 = 29.4 m/s"  // ✅ Stage 1修正
    }
  ],
  
  "problem_model": "自由落体运动（只受重力作用）",
  "chosen_strategy": "使用自由落体运动学方程 v = v0 + gt",
  
  "enhancement_metadata": {
    "rag_enhanced": true,  // ✅ Stage 2添加
    "retrieved_knowledge": [
      "自由落体运动公式：v = v0 + gt",
      "位移公式：s = v0*t + 0.5*g*t²",
      "动能公式：Ek = 0.5*m*v²"
    ],
    "structure_optimized": true,  // ✅ Stage 3添加
    "causal_patterns": {
      "forks": [{"common_cause": "g", "effects": ["final_velocity"]}]
    },
    "structural_issues": []
  }
}
```

---

## 📈 **Enhancement Report**

```json
{
  "pipeline_status": "success",
  "stages_run": ["expert_review", "rag_enhancement", "structure_optimization"],
  
  "expert_review": {
    "status": "success",
    "problem_domain": "physics",
    "num_issues": 2,
    "num_corrections": 2,
    "issues": [
      {"severity": "high", "issue": "Used a=5 instead of g=9.8"},
      {"severity": "high", "issue": "Wrong acceleration type"}
    ]
  },
  
  "rag_enhancement": {
    "status": "success",
    "knowledge_items_added": 4,
    "knowledge_gaps_identified": 2
  },
  
  "structure_optimization": {
    "status": "success",
    "modifications_made": 0,
    "causal_patterns": {
      "num_chains": 0,
      "num_forks": 1,
      "num_colliders": 0
    },
    "validation": {
      "is_dag": true,
      "is_connected": true
    }
  },
  
  "summary": {
    "total_corrections": 2,
    "total_enhancements": 6,
    "final_status": "enhanced_and_validated"
  }
}
```

---

## 🎯 **关键变化对比**

| 字段 | Initial DAG (错误) | Enhanced DAG (正确) |
|------|-------------------|-------------------|
| **knowns.acceleration** | 5 (❌) | - |
| **knowns.g** | - | 9.8 (✅) |
| **causal_graph[0].cause** | ["...", "acceleration", ...] (❌) | ["...", "g", ...] (✅) |
| **causal_graph[0].rule** | "v = v0 + a * t" (❌) | "v = v0 + g * t" (✅) |
| **computation result** | 15 m/s (❌) | 29.4 m/s (✅) |
| **metadata** | - | 包含知识和结构信息 (✅) |

---

## 📝 **流程总结**

```
Initial DAG (from Step1)
    ↓ ❌ 错误：用了a=5
    
Stage 1: Domain Expert Review
    ↓ ✅ 修正：改用g=9.8，修改rule和计算
    
Stage 2: RAG Knowledge Enhancement  
    ↓ ✅ 增强：添加参考知识到metadata
    
Stage 3: Causal Structure Optimization
    ↓ ✅ 验证：确认结构正确，添加模式分析
    
Enhanced DAG (ready for Step3)
    ✅ 公式正确
    ✅ 计算正确
    ✅ 知识完整
    ✅ 结构优化
```

---

## 🚀 **Step3使用Enhanced DAG计算最终答案**

```python
# Step3: LLM-Based Computation
llm_computer.compute_from_scaffold(
    causal_scaffold=enhanced_dag,
    problem_text="..."
)

# 基于修正后的DAG计算：
# v = v0 + g*t = 0 + 9.8*3 = 29.4 m/s

# 输出：
{
  "result": "29.4",
  "unit": "m/s",
  "reasoning": "使用自由落体运动学方程v = v0 + gt，代入v0=0, g=9.8, t=3，得到v=29.4 m/s"
}
```

**最终答案：29.4 m/s** ✅

---

## ✅ **完整流程价值**

### **没有Enhancement Pipeline（❌）：**
```
Step1 → 错误DAG (a=5) → Step3 → 错误答案 (15 m/s)
```

### **有Enhancement Pipeline（✅）：**
```
Step1 → 错误DAG (a=5)
    ↓ Stage 1: 修正错误 (g=9.8)
    ↓ Stage 2: 补充知识
    ↓ Stage 3: 验证结构
    → 正确DAG (g=9.8) → Step3 → 正确答案 (29.4 m/s)
```

**Enhancement Pipeline确保了DAG的正确性、完整性和结构合理性！** 🎉



