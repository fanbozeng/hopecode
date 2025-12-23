# Domain Expert Reviewer - KeyError 'domain' 完整修复说明

## 🐛 **问题根源**

```
🔬 Expert reviewing DAG... ✗ Failed: 'domain'
```

### **错误原因：**
Prompt模板与代码参数不匹配！

---

## 🔍 **详细分析**

### **旧版Prompt模板（prompts/expert_review_prompt.txt）需要6个占位符：**

```python
You are an expert reviewer specialized in {domain}.          # ← 占位符1
Your Expertise: {domain_description}                          # ← 占位符2
Problem: {problem}                                            # ← 占位符3 ✓
Causal DAG: {dag}                                             # ← 占位符4 ✓
Review Focus: {review_focus}                                  # ← 占位符5
Common Errors: {common_errors}                                # ← 占位符6
```

### **但代码只提供了2个参数：**

```python
# engine/domain_expert_reviewer.py: line 166
prompt = self.review_prompt.format(
    problem=problem_text,      # ✓ 提供了
    dag=json.dumps(dag, ...)   # ✓ 提供了
    # domain=?                 # ✗ 缺失！
    # domain_description=?     # ✗ 缺失！
    # review_focus=?           # ✗ 缺失！
    # common_errors=?          # ✗ 缺失！
)
```

### **结果：**

Python的`str.format()`方法遇到未提供的占位符`{domain}`时：
```python
>>> "Hello {domain}".format()
KeyError: 'domain'
```

---

## ✅ **修复方案**

### **选择：更新Prompt模板**

因为当前系统设计是使用**"统一专家"**（同时处理数学和物理），而不是按领域分配专家，所以旧的prompt模板设计不适用。

### **新Prompt模板（只需2个占位符）：**

```
You are a rigorous expert in both mathematics and physics.

**Problem:**
{problem}

**Causal DAG:**
{dag}

**Review Tasks:**
1. Automatically identify if this is math, physics, or mixed
2. Verify formulas and laws
3. Check logical validity
4. Identify errors

**Output Format (JSON):**
{
  "problem_domain": "math" | "physics" | "mixed",
  "issues": [...],
  "corrections": [...],
  "overall_assessment": "..."
}
```

---

## 📊 **修复前后对比**

### **修复前：**

```
旧Prompt模板需要:
- {domain}              ← 错误！未提供
- {domain_description}  ← 错误！未提供
- {problem}             ✓
- {dag}                 ✓
- {review_focus}        ← 错误！未提供
- {common_errors}       ← 错误！未提供

代码调用:
prompt = template.format(problem=..., dag=...)

结果:
KeyError: 'domain'
```

### **修复后：**

```
新Prompt模板需要:
- {problem}             ✓ 匹配
- {dag}                 ✓ 匹配

代码调用:
prompt = template.format(problem=..., dag=...)

结果:
✓ 成功！
```

---

## 🧪 **测试验证**

### **测试脚本结果：**

```bash
1. Testing JSON serialization...
✓ JSON serialization OK

2. Testing prompt formatting...
✓ Prompt formatting OK

3. Testing DAG structure...
✓ target_variable: <class 'str'>
✓ knowns: <class 'dict'>
✓ causal_graph: <class 'list'>
✓ computation_plan: <class 'list'>

4. Simulating review report parsing...
✓ domain extraction OK: 'physics'

5. Testing with actual DomainExpertReviewer...
✓ Loaded expert review prompt from prompts\expert_review_prompt.txt
✓ DomainExpertReviewer initialized
✓ Prompt format with actual template OK

All tests completed! ✓
```

---

## 🎯 **根本原因总结**

### **为什么会出现这个问题？**

1. **Prompt文件是旧版本**
   - 设计时考虑的是"多个领域专家"（math expert, physics expert分别调用）
   - 需要显式指定`{domain}`

2. **代码已经更新为"统一专家"**
   - 使用单个LLM同时处理math和physics
   - LLM自己识别问题类型（返回`problem_domain`）

3. **Prompt文件没有同步更新**
   - 导致参数不匹配

### **教训：**
- ✅ Prompt模板和代码必须保持同步
- ✅ 修改设计时要更新所有相关文件
- ✅ 添加单元测试来验证prompt格式化

---

## 📝 **相关文件**

### **修改的文件：**
1. **`prompts/expert_review_prompt.txt`** - 完全重写，移除了4个多余的占位符
2. **`engine/domain_expert_reviewer.py`** - 已有的代码是正确的，无需修改

### **Fallback Prompt（代码中）：**
代码中的fallback prompt一直是正确的，只用了`{problem}`和`{dag}`两个占位符：

```python
# engine/domain_expert_reviewer.py: line 116
def _get_default_prompt(self) -> str:
    return """You are a rigorous expert in both mathematics and physics.
    
**Problem:**
{problem}

**Causal DAG:**
{dag}

...
"""
```

---

## ✅ **总结**

**问题：** `KeyError: 'domain'`

**原因：** Prompt模板需要6个占位符，代码只提供2个

**修复：** 更新prompt文件，使其与"统一专家"设计一致（只需2个占位符）

**结果：** ✅ 所有测试通过，问题完全解决

**现在可以正常使用DomainExpertReviewer了！** 🎉



