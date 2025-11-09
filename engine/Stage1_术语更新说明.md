# Stage 1 术语和描述更新说明

## 📝 **更新背景**

Stage 1 的功能已经从**纯粹的审查**升级为**审查+主动修正**，因此所有相关的prompt、代码注释和文档都需要更新术语，准确反映其当前功能。

---

## 🔄 **核心变化**

### **之前：只审查**
- 角色：审查员 (Reviewer)
- 动作：发现问题、指出错误
- 输出：审查报告（描述性的修正建议）
- 后续：需要其他代码解析报告并手动修改DAG

### **现在：审查+修正**
- 角色：审查员 + 修正专家 (Reviewer & Corrector)
- 动作：发现问题、主动修正、生成修正后的DAG
- 输出：审查报告 + **完整的修正后DAG**
- 后续：直接使用LLM返回的`corrected_dag`，无需手动处理

---

## 📄 **更新的文件列表**

### **1. `prompts/expert_review_prompt.txt`**

#### **更新内容：**

**第1行：任务定义**
```diff
- You are a rigorous expert in both mathematics and physics. Your task is to critically review the following causal DAG for correctness.
+ You are a rigorous expert in both mathematics and physics. Your task is to **review and actively correct** the following causal DAG.
```

**第9行：任务列表标题**
```diff
- **Review Tasks:**
+ **Your Tasks:**
```

**第14行：新增第5项任务**
```diff
  1. Automatically identify if this is a math, physics, or mixed problem
  2. Verify formulas, theorems, and physical laws are correctly applied
  3. Check logical validity and unit consistency (for physics problems)
  4. Identify errors and provide specific corrections
+ 5. **Generate a corrected DAG** with all fixes applied (this is the most important output!)
```

**第77-79行：强调corrected_dag的重要性**
```diff
- **Important:** 
- - If no errors found, `corrected_dag` should be identical to the input DAG
- - If errors found, `corrected_dag` should have all corrections applied to the appropriate fields (knowns, causal_graph, computation_plan)

+ **Critical Requirements:** 
+ - **Always** provide `corrected_dag` - this is the primary output!
+ - If no errors found: `corrected_dag` = input DAG (unchanged)
+ - If errors found: `corrected_dag` = fully corrected DAG with all fixes applied to knowns, causal_graph, computation_plan, etc.
+ - The `corrected_dag` should be **complete and ready to use** - not just descriptions of changes
```

---

### **2. `engine/domain_expert_reviewer.py`**

#### **更新内容：**

**第1-6行：模块说明**
```diff
  """
  Domain Expert Reviewer Module
- 领域专家审查模块
+ 领域专家审查与修正模块
  
- This module provides domain-specific expert review for DAG validation.
- 本模块为DAG验证提供特定领域的专家审查。
+ This module provides domain-specific expert review and correction for DAG structures.
+ 本模块为DAG结构提供特定领域的专家审查与修正。
+ 
+ Key Functionality:
+ - Reviews DAGs for mathematical and physical correctness
+ - Identifies errors and violations of domain principles
+ - Actively corrects the DAG by generating a fixed version
+ - Returns a complete, corrected DAG ready for use
+ 
+ 主要功能：
+ - 审查DAG的数学和物理正确性
+ - 识别错误和违反领域原则的问题
+ - 主动修正DAG，生成修复后的版本
+ - 返回完整的、可直接使用的修正后DAG
  """
```

**第25-36行：类docstring**
```diff
  class DomainExpertReviewer:
      """
-     Domain Expert Reviewer for DAG validation and refinement.
-     领域专家审查器，用于DAG验证和精炼
+     Domain Expert Reviewer for DAG validation, correction, and enhancement.
+     领域专家审查器，用于DAG验证、修正和增强
      
      This class leverages domain experts (mathematicians/physicists) to:
      1. Validate formulas and theorems used in the DAG
      2. Check reasoning chain correctness
-     3. Identify and fix logical errors
+     3. Identify logical errors and violations
+     4. Actively correct the DAG by generating a fixed version
+     5. Return a complete, corrected DAG ready for downstream use
      
      本类利用领域专家（数学家/物理学家）来：
      1. 验证DAG中使用的公式和定理
      2. 检查推理链正确性
-     3. 识别并修复逻辑错误
+     3. 识别逻辑错误和违规问题
+     4. 主动修正DAG，生成修复后的版本
+     5. 返回完整的、可供下游使用的修正后DAG
      """
```

**第150行：review_dag方法的docstring**
```diff
      def review_dag(...) -> Tuple[Dict[str, Any], Dict[str, Any]]:
          """
-         Review DAG with unified expert (handles math, physics, and mixed problems).
-         使用统一专家审查DAG（处理数学、物理和混合问题）
+         Review and correct DAG with unified expert (handles math, physics, and mixed problems).
+         使用统一专家审查并修正DAG（处理数学、物理和混合问题）
+         
+         This method:
+         1. Sends the DAG to an expert LLM for review
+         2. Receives identified issues and corrections
+         3. Gets a fully corrected DAG with all fixes applied
+         4. Returns the corrected DAG for downstream use
+         
+         此方法：
+         1. 将DAG发送给专家LLM进行审查
+         2. 接收识别出的问题和修正方案
+         3. 获取已应用所有修复的完整修正后DAG
+         4. 返回修正后的DAG供下游使用
          
          Args:
              dag: The DAG structure to review
```

**第114-141行：fallback prompt**
```diff
      def _get_default_prompt(self) -> str:
-         """Default unified expert review prompt (fallback)"""
-         return """You are a rigorous expert in both mathematics and physics. Review the following causal DAG for correctness.
+         """Default unified expert review and correction prompt (fallback)"""
+         return """You are a rigorous expert in both mathematics and physics. Your task is to **review and actively correct** the following causal DAG.
          
          **Problem:**
          {problem}
          
          **Causal DAG:**
          {dag}
          
-         **Review Tasks:**
+         **Your Tasks:**
          1. Automatically identify if this is math, physics, or mixed problem
          2. Verify formulas, theorems, and physical laws are correctly applied
          3. Check logical validity and unit consistency
          4. Identify errors and provide specific corrections
+         5. **Generate a corrected DAG** with all fixes applied (this is the most important output!)
          
          **Output JSON Format:**
          {{
            "problem_domain": "math" | "physics" | "mixed",
            "issues": [...],
            "corrections": [...],
+           "corrected_dag": {{
+             "target_variable": "...",
+             "knowns": {{...}},
+             "causal_graph": [...],
+             "computation_plan": [...]
+           }},
            "overall_assessment": "summary"
          }}
+         
+         **Critical:** Always provide `corrected_dag` - if no errors, return the input DAG unchanged; if errors exist, return the fully corrected DAG.
          """
```

---

### **3. `engine/dag_enhancement_pipeline.py`**

#### **更新内容：**

**第1-14行：模块说明**
```diff
  """
  DAG Enhancement Pipeline Module
  DAG增强流水线模块
  
  This module orchestrates the three-stage DAG enhancement process:
- Stage 1: Domain Expert Review
- Stage 2: RAG Knowledge Enhancement  
- Stage 3: Causal Structure Optimization
+ Stage 1: Domain Expert Review & Correction (actively fixes math/physics errors)
+ Stage 2: RAG Knowledge Enhancement (injects relevant domain knowledge)
+ Stage 3: Causal Structure Optimization (optimizes DAG structure using causal principles)
  
  本模块协调三阶段DAG增强流程：
- 阶段1：领域专家审查
- 阶段2：RAG知识增强
- 阶段3：因果结构优化
+ 阶段1：领域专家审查与修正（主动修复数学/物理错误）
+ 阶段2：RAG知识增强（注入相关领域知识）
+ 阶段3：因果结构优化（使用因果原理优化DAG结构）
  """
```

**第108-120行：Stage 1代码注释**
```diff
-             # Stage 1: Domain Expert Review
+             # Stage 1: Domain Expert Review & Correction
+             # 阶段1：领域专家审查与修正
+             # Actively fixes math/physics errors and returns a corrected DAG
+             # 主动修复数学/物理错误并返回修正后的DAG
              if 'expert' not in skip_stages and self.expert_reviewer:
-                 self._print("\n📋 Stage 1/3: Domain Expert Review")
+                 self._print("\n📋 Stage 1/3: Domain Expert Review & Correction")
                  self._print("-" * 60)
                  current_dag, expert_report = self.expert_reviewer.review_dag(
                      current_dag, problem_text, problem_type
                  )
                  enhancement_report['expert_review'] = expert_report
                  enhancement_report['stages_run'].append('expert_review')
              else:
-                 self._print("\n⏭️  Stage 1/3: Expert Review (Skipped)")
+                 self._print("\n⏭️  Stage 1/3: Expert Review & Correction (Skipped)")
                  enhancement_report['expert_review'] = {'status': 'skipped'}
```

---

## ✅ **更新验证清单**

- ✅ **Prompt文件** - 任务描述更新为"review and actively correct"
- ✅ **Prompt文件** - 强调`corrected_dag`是主要输出
- ✅ **模块docstring** - 从"审查模块"改为"审查与修正模块"
- ✅ **类docstring** - 明确列出5个功能，包括"主动修正"和"返回完整DAG"
- ✅ **方法docstring** - 详细说明4个步骤，强调返回修正后的DAG
- ✅ **Fallback prompt** - 与主prompt保持一致
- ✅ **Pipeline注释** - 所有Stage 1引用都更新为"Review & Correction"
- ✅ **中英文对照** - 所有中文注释同步更新

---

## 🎯 **关键术语对照表**

| **英文术语** | **中文术语** | **使用场景** |
|------------|------------|------------|
| Review | 审查 | 发现问题、诊断 |
| Correct / Correction | 修正 | 修复问题、生成修正后的版本 |
| Review & Correction | 审查与修正 | Stage 1的完整功能描述 |
| Actively correct | 主动修正 | 强调不只是建议，而是实际生成修正后的DAG |
| Corrected DAG | 修正后的DAG | LLM返回的已修复的完整DAG |
| Ready to use | 可直接使用 | 强调不需要手动处理，可以直接用于下游 |

---

## 📊 **影响范围**

### **直接影响：**
1. **LLM行为：** Prompt更新会让LLM更清楚地理解任务是"生成修正后的DAG"
2. **代码可读性：** 注释和文档更准确地反映实际功能
3. **用户理解：** 终端输出显示"Review & Correction"，用户明白这个阶段不只是检查

### **间接影响：**
1. **维护性：** 代码意图更清晰，后续维护更容易
2. **扩展性：** 如果未来要添加新的修正功能，现有术语已经为此做好准备
3. **一致性：** 所有文件的术语统一，避免混淆

---

## 🚀 **后续建议**

### **1. 日志输出优化**
建议在`domain_expert_reviewer.py`中增强日志输出：
```python
if corrected_dag:
    self._print(f"✓ [{domain}] DAG corrected: {len(corrections)} fixes applied")
else:
    self._print(f"✓ [{domain}] No corrections needed, DAG is correct")
```

### **2. 统计信息**
建议在`enhancement_report`中添加修正统计：
```python
'expert_review': {
    'domain': 'physics',
    'issues_found': 2,
    'corrections_applied': 1,
    'dag_modified': True,
    ...
}
```

### **3. 错误处理**
建议增强对`corrected_dag`缺失的处理：
```python
if not corrected_dag:
    self._print("⚠️  No corrected_dag returned, using original DAG")
    return dag, review_report
```

---

## 📚 **相关文档**

- `Stage1改进完成说明.md` - Stage 1功能升级的详细说明
- `Stage1_JSON字段详解.md` - Expert Review输出JSON的字段说明
- `enhance_dag完整流程模拟示例.md` - 包含Stage 1的完整流程示例

---

## ✨ **总结**

本次更新确保了**术语的准确性和一致性**：
- ✅ Prompt清楚地指示LLM要"主动修正"
- ✅ 代码注释准确反映"审查+修正"的双重功能
- ✅ 所有文件的术语统一为"Review & Correction"
- ✅ 中英文对照清晰

**核心变化：** 从"Reviewer"（审查员）→ "Reviewer & Corrector"（审查员+修正专家）

**主要输出：** 从"Review Report"（审查报告）→ **"Corrected DAG"**（修正后的DAG）



