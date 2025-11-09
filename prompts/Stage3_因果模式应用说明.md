# Stage 3: 因果模式应用说明

## 📝 **更新背景**

### **之前的问题：**
Stage 3的prompt只是**识别**了三种因果模式（Chain、Fork、Collider），但没有明确说明如何**利用这些模式来主动修正DAG**。

- ❌ **只识别：** "这里有一个Chain模式"
- ❌ **不修正：** 发现跳步后，不知道该用Chain模式来补充中间节点

### **现在的改进：**
将三种因果模式从**识别工具**升级为**修正工具**！

- ✅ **识别+应用：** "这里跳步了，我要用Chain模式来补充中间节点"
- ✅ **主动重构：** 遇到混乱的DAG，用Fork/Collider模式来重新组织

---

## 🎯 **三种因果模式的"应用"场景**

### **1. Chain模式：A → B → C**

#### **定义：**
B是A和C之间的**中介变量**（mediator）

#### **何时应用：**
- ✅ **发现跳步时**：A直接到C，但中间缺少了B
- ✅ **物理过程分解**：复杂关系需要分解为多个步骤

#### **应用示例：**

##### **场景1：自由落体（跳步）**
```
❌ 原始DAG（错误）：
mass → acceleration

✅ 应用Chain模式修正：
mass → gravitational_force → acceleration
     (F = m*g)         (a = F/m)

理由：
- 质量不直接导致加速度
- 质量产生重力，重力产生加速度
- Chain模式：mass → force → acceleration
```

##### **场景2：运动学问题（跳步）**
```
❌ 原始DAG（错误）：
initial_velocity → final_position

✅ 应用Chain模式修正：
initial_velocity → displacement → final_position
                (s = v₀*t)      (x_f = x₀ + s)

理由：
- 速度不直接决定最终位置
- 速度产生位移，位移改变位置
- Chain模式：velocity → displacement → position
```

##### **场景3：能量转换（跳步）**
```
❌ 原始DAG（错误）：
height → kinetic_energy

✅ 应用Chain模式修正：
height → potential_energy → kinetic_energy
        (PE = mgh)         (KE = PE)

理由：
- 高度不直接产生动能
- 高度产生势能，势能转换为动能
- Chain模式：height → PE → KE
```

---

### **2. Fork模式：A ← B → C**

#### **定义：**
B是**公因**（common cause），同时导致A和C

#### **何时应用：**
- ✅ **一个原因导致多个结果**
- ✅ **多个独立边需要统一为Fork结构**

#### **应用示例：**

##### **场景1：加热过程**
```
❌ 原始DAG（关系不清）：
heating → temperature
heating → pressure

✅ 应用Fork模式重构：
temperature ← heating → pressure

说明：
- heating是公因
- 加热同时导致温度上升和压强增大
- Fork模式清晰表达：一因多果
```

##### **场景2：力的作用**
```
❌ 原始DAG（关系不清）：
force → acceleration_x
force → acceleration_y

✅ 应用Fork模式重构：
acceleration_x ← force → acceleration_y

说明：
- force是公因
- 力同时产生x方向和y方向的加速度
- Fork模式清晰表达：一个力，两个方向的加速度
```

##### **场景3：电流效应**
```
❌ 原始DAG（关系不清）：
current → magnetic_field
current → heat

✅ 应用Fork模式重构：
magnetic_field ← current → heat

说明：
- current是公因
- 电流同时产生磁场和热效应
- Fork模式清晰表达：电流的两种效应
```

---

### **3. Collider模式：A → B ← C**

#### **定义：**
B是**公果**（common effect），由A和C共同决定

#### **何时应用：**
- ✅ **多个原因导致一个结果**
- ✅ **需要明确表达"共同作用"**

#### **应用示例：**

##### **场景1：重力势能**
```
❌ 原始DAG（关系不清）：
height → potential_energy
mass → potential_energy

✅ 应用Collider模式重构：
height → potential_energy ← mass
         (PE = mgh)

说明：
- potential_energy是公果
- 势能同时取决于高度和质量
- Collider模式清晰表达：PE需要height和mass两个输入
```

##### **场景2：压强计算**
```
❌ 原始DAG（关系不清）：
force → pressure
area → pressure

✅ 应用Collider模式重构：
force → pressure ← area
        (P = F/A)

说明：
- pressure是公果
- 压强由力和面积共同决定
- Collider模式清晰表达：P = F/A需要两个输入
```

##### **场景3：动量计算**
```
❌ 原始DAG（关系不清）：
mass → momentum
velocity → momentum

✅ 应用Collider模式重构：
mass → momentum ← velocity
       (p = mv)

说明：
- momentum是公果
- 动量由质量和速度共同决定
- Collider模式清晰表达：p = mv需要两个输入
```

---

## 🔄 **Prompt更新对照表**

### **1. 任务顺序调整**

| **之前** | **现在** | **原因** |
|---------|---------|---------|
| 1. Detect Issues<br>2. Identify Patterns<br>3. Optimize DAG | 1. **Understand Patterns (Toolkit)**<br>2. Detect Issues<br>3. **Optimize Using Patterns** | 先理解工具，再用工具修复 |

### **2. 核心哲学**

**新增开头说明：**
```
**Core Philosophy:**
The three causal patterns (Chain, Fork, Collider) are NOT just for identification - 
they are your **active tools** for restructuring and fixing messy DAGs.
```

**翻译：**
> 三种因果模式（Chain、Fork、Collider）**不只是用来识别的**，它们是你**主动重构和修复混乱DAG的工具**。

### **3. 模式说明增强**

#### **之前：**
```
- **Chain**: A → B → C (B mediates the effect of A on C)
```

#### **现在：**
```
- **Chain**: A → B → C (B mediates the effect of A on C)
  * Use this to fix skipped steps
  * Example: `mass → force → acceleration` instead of `mass → acceleration`
```

**改进点：**
- ✅ 明确指出**何时使用**（修复跳步）
- ✅ 给出**具体例子**（mass → force → acceleration）

### **4. 优化任务说明**

#### **之前：**
```
3. **Optimize the DAG:**
   - Fix cycles by removing or reversing incorrect edges
   - Connect isolated nodes based on computation_plan dependencies
   - Add missing intermediate steps to avoid skips
```

#### **现在：**
```
3. **Optimize the DAG Using Causal Patterns:**
   - **Fix cycles**: Remove or reverse incorrect edges based on domain logic
   - **Connect isolated nodes**: Determine if they fit into a Chain, Fork, or Collider
   - **Fix skipped steps**: Insert intermediate variables to form proper Chains
   - **Clarify relationships**: Restructure as explicit Fork or Collider if needed
   - **Most Important**: Use Chain/Fork/Collider as templates to reconstruct messy DAGs
```

**改进点：**
- ✅ 标题强调"Using Causal Patterns"
- ✅ 每个任务明确指出使用哪个模式
- ✅ 新增"Most Important"：将模式作为重构模板

---

## 📚 **新增示例**

### **示例3：跳步修复（使用Chain模式）**

```
**当前DAG（错误）：**
mass → acceleration (跳步)

**识别问题：**
- Issue: Skipped step
- Missing: force

**应用模式：**
Pattern to Apply: Chain (A → B → C)

**修正后：**
mass → force → acceleration
Add to causal_graph:
- {cause: ["mass", "g"], effect: "force", rule: "F = m * g"}
- {cause: ["force", "mass"], effect: "acceleration", rule: "a = F / m"}
```

### **示例4：多效应重构（使用Fork模式）**

```
**当前DAG（关系不清）：**
heating → temperature
heating → pressure

**识别问题：**
- Issue: Unclear pattern
- Two separate edges

**应用模式：**
Pattern to Apply: Fork (A ← B → C)

**修正后：**
temperature ← heating → pressure
This clarifies: heating is the common cause of BOTH temperature and pressure
```

### **示例5：多因重构（使用Collider模式）**

```
**当前DAG（关系不清）：**
mass → weight
g → weight

**识别问题：**
- Issue: Unclear pattern
- Two causes not structured

**应用模式：**
Pattern to Apply: Collider (A → B ← C)

**修正后：**
mass → weight ← g
This clarifies: weight is the common effect of BOTH mass and g
```

---

## 📊 **输出格式更新**

### **modifications_made字段**

#### **之前：**
```json
"modifications_made": [
  "Removed edge A→B to break cycle",
  "Added edge C→D to connect isolated node D",
  "Inserted intermediate step F between mass and acceleration"
]
```

#### **现在：**
```json
"modifications_made": [
  "Removed edge A→B to break cycle",
  "Added edge C→D to connect isolated node D",
  "Applied Chain pattern: Inserted intermediate variable F (mass → force → acceleration)",
  "Applied Fork pattern: Restructured heating as common cause of temperature and pressure",
  "Applied Collider pattern: Identified weight as common effect of mass and g"
]
```

**改进点：**
- ✅ 明确说明**应用了哪个模式**
- ✅ 描述更清晰：不只是"added"，而是"Applied Chain pattern and inserted..."

### **causal_patterns字段**

#### **之前（只识别）：**
```json
"causal_patterns": {
  "chains": [{"path": ["A", "B", "C"], "interpretation": "B mediates A→C"}],
  "forks": [{"common_cause": "B", "effects": ["A", "C"]}],
  "colliders": [{"common_effect": "B", "causes": ["A", "C"]}]
}
```

#### **现在（识别+应用）：**
```json
"causal_patterns": {
  "chains": [
    {
      "path": ["A", "B", "C"], 
      "interpretation": "B mediates A→C",
      "applied": "Used to fix skipped step"
    }
  ],
  "forks": [
    {
      "common_cause": "B", 
      "effects": ["A", "C"],
      "applied": "Used to clarify B causes both A and C"
    }
  ],
  "colliders": [
    {
      "common_effect": "B", 
      "causes": ["A", "C"],
      "applied": "Used to show B depends on both A and C"
    }
  ]
}
```

**改进点：**
- ✅ 新增`"applied"`字段：说明模式**如何被使用**的
- ✅ 从"识别到的"变为"应用的"

---

## 🔍 **完整示例对比**

### **旧版输出（只识别）：**

```json
{
  "issues_detected": [
    {"type": "skipped_step", "description": "Missing force F", "severity": "high"}
  ],
  "modifications_made": [
    "Added intermediate variable 'gravitational_force'"
  ],
  "causal_patterns": {
    "chains": [{"path": ["mass", "gravitational_force", "acceleration"]}]
  }
}
```

**问题：**
- ❌ 没说明用了什么模式来修复
- ❌ `causal_patterns`只是报告，不是"应用"

---

### **新版输出（应用模式）：**

```json
{
  "issues_detected": [
    {"type": "skipped_step", "description": "Missing force F between mass and acceleration", "severity": "high"}
  ],
  "modifications_made": [
    "Applied Chain pattern: mass → force → acceleration",
    "Added intermediate variable 'gravitational_force' with rule F=mg",
    "Updated acceleration to depend on force: a=F/m"
  ],
  "causal_patterns": {
    "chains": [
      {
        "path": ["mass", "gravitational_force", "acceleration"],
        "interpretation": "Force mediates mass→acceleration",
        "applied": "Used Chain pattern to fix skipped step - added force as intermediate variable"
      }
    ]
  },
  "reasoning": "Applied Chain pattern to fix skipped step. Original DAG jumped from mass directly to acceleration, which is physically incorrect. Using the Chain pattern (mass → force → acceleration), I inserted the missing 'gravitational_force' variable."
}
```

**改进：**
- ✅ 明确说明"Applied Chain pattern"
- ✅ `causal_patterns.chains[0].applied`详细记录了如何应用
- ✅ `reasoning`解释了为什么用Chain模式

---

## ✅ **总结**

### **核心变化：**

| **维度** | **之前** | **现在** |
|---------|---------|---------|
| **定位** | 识别工具 | **修正工具** |
| **功能** | 报告"发现了Chain模式" | **应用Chain模式修复跳步** |
| **任务顺序** | 先检测问题，再识别模式 | **先理解模式，用模式修复问题** |
| **输出** | 列出发现的模式 | **说明如何应用模式** |

### **三大模式的应用场景：**

1. **Chain (A → B → C)：**
   - ✅ 修复跳步
   - ✅ 分解复杂过程
   - ✅ 补充中间变量

2. **Fork (A ← B → C)：**
   - ✅ 整理"一因多果"
   - ✅ 明确公因关系
   - ✅ 重构混乱的多边

3. **Collider (A → B ← C)：**
   - ✅ 整理"多因一果"
   - ✅ 明确公果关系
   - ✅ 表达共同作用

### **对LLM的影响：**

**之前：**
```
LLM: "我发现这里有个Chain模式。"
（只识别，不知道该怎么用）
```

**现在：**
```
LLM: "我发现这里跳步了，我要用Chain模式来补充中间节点！"
（识别+应用，主动修正）
```

---

## 🚀 **后续建议**

### **1. 增强验证逻辑**
建议在`causal_structure_optimizer.py`中增加对`applied`字段的提取和统计：

```python
def _extract_applied_patterns(self, optimization_result: Dict) -> Dict[str, int]:
    """统计应用了哪些模式来修复DAG"""
    patterns = optimization_result.get('causal_patterns', {})
    applied_count = {
        'chain': len([p for p in patterns.get('chains', []) if p.get('applied')]),
        'fork': len([p for p in patterns.get('forks', []) if p.get('applied')]),
        'collider': len([p for p in patterns.get('colliders', []) if p.get('applied')])
    }
    return applied_count
```

### **2. 日志输出优化**
```python
if applied_count['chain'] > 0:
    self._print(f"  ✓ Applied {applied_count['chain']} Chain pattern(s) to fix skipped steps")
if applied_count['fork'] > 0:
    self._print(f"  ✓ Applied {applied_count['fork']} Fork pattern(s) to clarify common causes")
if applied_count['collider'] > 0:
    self._print(f"  ✓ Applied {applied_count['collider']} Collider pattern(s) to show common effects")
```

### **3. 评估指标**
在`structure_report`中添加模式应用统计：

```python
'structure_optimization': {
    'patterns_applied': {
        'chain': 2,
        'fork': 1,
        'collider': 0
    },
    'improvements': [
        'Fixed 2 skipped steps using Chain pattern',
        'Clarified 1 common cause using Fork pattern'
    ]
}
```

---

## 📄 **相关文档**

- `LLM驱动的Stage3优化方案.md` - Stage 3的LLM驱动设计
- `enhance_dag完整流程模拟示例.md` - 包含Stage 3的完整流程示例
- `Stage3优化未生效问题说明.md` - Stage 3调试记录

---

## 🎉 **最终效果**

**之前：**
```
Stage 3: 因果结构优化
- 识别了2个Chain模式
- 识别了1个Fork模式
- 添加了metadata
```
**问题：** 只识别，没修正

**现在：**
```
Stage 3: 因果结构优化
- 应用Chain模式修复了2个跳步问题
- 应用Fork模式重构了1个公因关系
- 生成了优化后的完整DAG
```
**成功：** 识别+应用，主动修正！

🎯 **三种因果模式：从"观察员"升级为"修复专家"！**



