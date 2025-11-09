# Prompt格式转义问题修复说明

## 🐛 **问题描述**

### **错误信息：**
```
KeyError: 'cause'

  File "engine/causal_structure_optimizer.py", line 202, in _llm_optimize_structure
    prompt = self.optimization_prompt.format(
```

### **错误原因：**

在`prompts/causal_structure_optimization_prompt.txt`的示例代码中，使用了：

```
Add to causal_graph:
- {cause: ["mass", "g"], effect: "force", rule: "F = m * g"}
- {cause: ["force", "mass"], effect: "acceleration", rule: "a = F / m"}
```

**问题：** Python的`str.format()`方法会将`{cause}`、`{effect}`等识别为**占位符**，尝试在format时替换，但代码中并没有提供这些参数，导致`KeyError`。

---

## ✅ **解决方案**

### **修复方法：**

在prompt文件中，所有**不应该被format替换的大括号**都需要用**双大括号`{{}}`转义**。

#### **修复前（错误）：**
```
- {cause: ["mass", "g"], effect: "force", rule: "F = m * g"}
```

#### **修复后（正确）：**
```
- {{cause: ["mass", "g"], effect: "force", rule: "F = m * g"}}
```

---

## 📋 **转义规则总结**

### **1. 真正的占位符（不需要转义）**

这些是代码中会提供的参数，**保持单大括号**：

```python
# causal_structure_optimization_prompt.txt
**Problem:**
{problem}  # ✅ 正确：这是真正的占位符

**Current Causal DAG:**
{dag}  # ✅ 正确：这是真正的占位符
```

对应代码：
```python
prompt = self.optimization_prompt.format(
    problem=problem_text,  # 提供了problem参数
    dag=json.dumps(dag, indent=2, ensure_ascii=False)  # 提供了dag参数
)
```

---

### **2. 示例/文档中的大括号（需要转义）**

这些是用来展示JSON格式或示例代码的，**使用双大括号转义**：

```python
# 在prompt中展示JSON结构示例
{{
  "issues_detected": [...],  # ✅ 正确：双大括号转义
  "modifications_made": [...],
  "optimized_dag": {{...}}  # ✅ 正确：双大括号转义
}}
```

```python
# 在prompt中展示causal_graph示例
- {{cause: ["mass", "g"], effect: "force", rule: "F = m * g"}}  # ✅ 正确
- {{cause: ["force", "mass"], effect: "acceleration", rule: "a = F / m"}}  # ✅ 正确
```

---

## 🔍 **如何检查Prompt文件**

### **检查步骤：**

1. **识别所有大括号**
   - 在prompt文件中搜索`{`

2. **判断是否为占位符**
   - 如果是`{problem}`、`{dag}`等代码中会提供的参数 → **单大括号**
   - 如果是示例、JSON结构、文档说明 → **双大括号转义**

3. **测试验证**
   - 运行代码，检查是否有`KeyError`

---

## 📊 **其他Prompt文件检查**

### **需要检查的文件：**

#### **1. `expert_review_prompt.txt`** ✅

```python
# 正确的占位符
**Problem:**
{problem}

**Causal DAG:**
{dag}

# 正确的转义示例
{{
  "problem_domain": "math" | "physics" | "mixed",
  "issues": [
    {{"node": "...", "issue": "...", "severity": "high/medium/low"}}
  ]
}}
```

#### **2. `scaffolding_prompt_v3.txt`** ✅

```python
# 正确的占位符
{retrieved_knowledge}
{prior_experiences}
{problem_text}

# 正确的转义示例
{{
  "target_variable": "...",
  "knowns": {{...}},
  "causal_graph": [
    {{"cause": ["..."], "effect": "...", "rule": "..."}}
  ]
}}
```

#### **3. `knowledge_gap_identification_prompt.txt`** ✅

```python
# 正确的占位符
{problem}
{dag}

# 正确的转义示例
{{
  "knowledge_gaps": [
    {{"gap_type": "formula", "description": "...", "priority": "high"}}
  ]
}}
```

---

## ⚠️ **常见错误**

### **错误1：忘记转义示例中的大括号**

```python
# ❌ 错误
Add to causal_graph:
- {cause: ["mass", "g"], effect: "force"}

# ✅ 正确
Add to causal_graph:
- {{cause: ["mass", "g"], effect: "force"}}
```

### **错误2：过度转义真正的占位符**

```python
# ❌ 错误（真正的占位符不应该转义）
**Problem:**
{{problem}}

# ✅ 正确
**Problem:**
{problem}
```

### **错误3：只转义了外层大括号**

```python
# ❌ 错误（内层的field名称也需要转义）
{{
  "causal_graph": [
    {cause: ["..."], effect: "..."}  # ← 这里的{cause会报错
  ]
}}

# ✅ 正确（所有大括号都转义）
{{
  "causal_graph": [
    {{cause: ["..."], effect: "..."}}
  ]
}}
```

---

## 🛠️ **修复Checklist**

针对每个prompt文件：

- [ ] 1. 确认所有真正的占位符（`{problem}`, `{dag}`等）使用**单大括号**
- [ ] 2. 确认所有示例代码使用**双大括号转义**
- [ ] 3. 确认JSON结构示例的所有层级都正确转义
- [ ] 4. 测试运行，确保没有`KeyError`

---

## 📝 **修复记录**

### **本次修复：**

**文件：** `prompts/causal_structure_optimization_prompt.txt`

**修复位置：** 第75-76行

**修复内容：**
```diff
- - {cause: ["mass", "g"], effect: "force", rule: "F = m * g"}
- - {cause: ["force", "mass"], effect: "acceleration", rule: "a = F / m"}
+ - {{cause: ["mass", "g"], effect: "force", rule: "F = m * g"}}
+ - {{cause: ["force", "mass"], effect: "acceleration", rule: "a = F / m"}}
```

**测试状态：** ✅ 修复后应该可以正常运行

---

## 🎯 **总结**

### **核心规则：**

| 类型 | 示例 | 格式 | 原因 |
|------|------|------|------|
| **真正的占位符** | `{problem}`, `{dag}` | 单大括号 `{...}` | 代码会提供值 |
| **示例/文档** | `{cause: [...]}` | 双大括号 `{{...}}` | 只是展示，不是占位符 |

### **记忆口诀：**

> **"代码会给，单括号；只是例子，双转义"**

### **验证方法：**

```python
# 如果你看到这个错误：
KeyError: 'xxx'

# 检查步骤：
1. 找到报错的prompt文件
2. 在文件中搜索 `{xxx`
3. 如果这个 xxx 不是代码中提供的参数，就需要转义为 {{xxx
```

---

## 🚀 **预防措施**

### **新建Prompt文件时：**

1. **先写占位符列表**
   ```
   # 占位符：
   - {problem}
   - {dag}
   ```

2. **所有其他大括号都用双括号**
   ```
   # 所有JSON示例、代码示例都用 {{...}}
   ```

3. **写完后检查**
   ```python
   # 简单测试
   prompt_template = open('prompt.txt').read()
   try:
       prompt_template.format(problem="test", dag="test")
       print("✅ Prompt格式正确")
   except KeyError as e:
       print(f"❌ 需要转义：{e}")
   ```

---

## 📚 **参考文档**

- Python官方文档：[Format String Syntax](https://docs.python.org/3/library/string.html#format-string-syntax)
- 转义规则：`{{` → `{`, `}}` → `}`



