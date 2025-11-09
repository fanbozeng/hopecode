# Domain Expert Reviewer 错误修复说明

## 🐛 **原始错误**

```
🔬 Expert reviewing DAG... ✗ Failed: 'domain'
```

这个错误信息很简洁，难以定位具体问题。

---

## 🔍 **可能的原因分析**

### **1. KeyError: 'domain'**
某个地方直接访问了字典的'domain'键：
```python
# ❌ 可能导致KeyError
some_dict['domain']  

# ✅ 应该使用
some_dict.get('domain', 'unknown')
```

### **2. 返回值类型错误**
`_parse_review_response`返回了非字典类型：
```python
# 可能返回None或其他类型
review_report = None
domain = review_report.get('problem_domain')  # → AttributeError
```

### **3. JSON解析失败**
LLM返回的格式不正确，JSON解析失败后fallback逻辑有问题

### **4. Expert Client未初始化**
`self.expert`为None，调用`self.expert.complete()`报错

---

## ✅ **已添加的修复**

### **修复1：Expert Client检查**

```python
def _review_with_expert(...):
    # 在调用前检查expert是否初始化
    if self.expert is None:
        self._print("✗ Expert client not initialized")
        return dag, self._create_error_report("Expert client not initialized")
    
    # 继续处理...
```

### **修复2：响应解析验证**

```python
# 解析响应后验证类型
review_report = self._parse_review_response(response)

if not isinstance(review_report, dict):
    self._print(f"✗ Invalid review report type: {type(review_report)}")
    return dag, self._create_error_report(f"Invalid review report type")

# 提取domain（已有默认值）
domain = review_report.get('problem_domain', 'unknown')
```

### **修复3：确保必需键存在**

```python
def _parse_review_response(self, response: str) -> Dict[str, Any]:
    ...
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            if isinstance(parsed, dict):
                # 确保必需的键存在
                if 'problem_domain' not in parsed:
                    parsed['problem_domain'] = 'unknown'
                if 'issues' not in parsed:
                    parsed['issues'] = []
                if 'corrections' not in parsed:
                    parsed['corrections'] = []
                return parsed
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"   ⚠️  JSON decode error: {e}")
    
    # Fallback
    return {
        'problem_domain': 'unknown',
        'issues': [],
        'corrections': [],
        'overall_assessment': 'Could not parse expert review'
    }
```

### **修复4：改进异常处理**

```python
except Exception as e:
    import traceback
    error_detail = f"{type(e).__name__}: {str(e)}"  # 显示异常类型
    self._print(f"✗ Failed: {error_detail}")
    if self.verbose:
        traceback.print_exc()  # 显示完整堆栈
    return dag, self._create_error_report(error_detail)
```

### **修复5：改进prompt加载**

```python
def _load_prompts(self):
    # 尝试相对路径
    if prompt_path.exists():
        # 加载...
    else:
        # 尝试绝对路径
        project_root = Path(__file__).parent.parent
        absolute_path = project_root / prompt_path
        
        if absolute_path.exists():
            # 加载...
        else:
            # 使用fallback
            self.review_prompt = self._get_default_prompt()
            if self.verbose:
                print(f"   ⚠️  Prompt file not found, using default")
```

### **修复6：安全的corrections处理**

```python
# 确保corrections是列表类型
corrections = review_report.get('corrections', [])
if not isinstance(corrections, list):
    corrections = []
reviewed_dag = self._apply_corrections(dag, corrections)
```

---

## 📊 **现在的错误信息会更详细**

### **场景1：Expert未初始化**
```
🔬 Expert reviewing DAG... ✗ Expert client not initialized
```

### **场景2：JSON解析失败**
```
🔬 Expert reviewing DAG... 
   ⚠️  JSON decode error: ...
   ⚠️  Could not parse expert review, using fallback
✓ [unknown] Found 0 issues, applied 0 corrections
```

### **场景3：其他异常**
```
🔬 Expert reviewing DAG... ✗ Failed: KeyError: 'domain'
Traceback (most recent call last):
  File "...", line X, in _review_with_expert
    ...
KeyError: 'domain'
```

### **场景4：类型错误**
```
🔬 Expert reviewing DAG... ✗ Invalid review report type: <class 'NoneType'>
```

---

## 🎯 **调试建议**

### **1. 启用verbose模式**
```python
expert_reviewer = DomainExpertReviewer(
    math_expert_client=expert_client,
    physics_expert_client=expert_client,
    verbose=True  # ← 启用详细输出
)
```

### **2. 查看错误类型**
现在错误会显示为：
```
KeyError: 'domain'
TypeError: 'NoneType' object is not subscriptable
AttributeError: 'NoneType' object has no attribute 'complete'
```

### **3. 检查LLM响应**
添加调试代码：
```python
# 在_review_with_expert中
response = self.expert.complete(prompt, temperature=0.0)
if self.verbose:
    print(f"   LLM response (first 200 chars): {response[:200]}")
```

### **4. 验证expert初始化**
```python
# 在main.py初始化时
expert_reviewer = DomainExpertReviewer(...)
if expert_reviewer.expert is None:
    print("⚠️  Warning: Expert client is None!")
```

---

## ✅ **总结**

**修复内容：**
1. ✅ 添加expert client存在性检查
2. ✅ 验证响应解析结果类型
3. ✅ 确保所有必需键存在
4. ✅ 改进异常处理（显示类型和堆栈）
5. ✅ 改进prompt加载（绝对路径fallback）
6. ✅ 安全的corrections列表处理

**错误信息改进：**
- ❌ 旧: `'domain'`
- ✅ 新: `KeyError: 'domain'` + 完整堆栈跟踪（verbose模式）

**现在重新运行应该能看到更详细的错误信息，帮助定位具体问题！** 🎉



