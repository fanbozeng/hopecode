# 各Agent独立经验库设计说明

## 🎯 **核心设计理念**

每个agent（3个generator + 1个critic）维护**各自独立的经验库**，在生成时根据自己的ID动态加载自己的经验。

---

## ❌ **旧设计的问题**

```python
# main.py: 统一传入经验
causal_plan = self.scaffolder.generate_scaffold_parallel(
    problem_text=problem_text,
    retrieved_knowledge=[],
    experiences=[]  # ❌ 所有agent共享同样的空经验
)
```

**问题：**
- ❌ 3个generator应该各自有不同的经验，而不是共享
- ❌ Critic也应该有自己专门的融合经验
- ❌ 无法针对性地为每个agent提供定制化经验

---

## ✅ **新设计（独立经验库）**

### **经验文件结构：**

```
data/grpo_experiences/
├── generator_1_experiences.json   ← Generator 1的专属经验
├── generator_2_experiences.json   ← Generator 2的专属经验
├── generator_3_experiences.json   ← Generator 3的专属经验
└── critic_experiences.json        ← Critic的专属经验
```

### **数据流：**

```
main.py:
  ↓ (不再传递experiences参数)
  
generate_scaffold_parallel():
  ├─ _parallel_generate()
  │   ↓
  │   Generator 1:
  │   └─ _single_agent_generate(agent_id=1)
  │       ↓ _load_agent_experiences('generator_1')
  │       ├─ 加载 generator_1_experiences.json
  │       └─ 使用Generator 1的专属经验生成DAG
  │
  │   Generator 2:
  │   └─ _single_agent_generate(agent_id=2)
  │       ↓ _load_agent_experiences('generator_2')
  │       ├─ 加载 generator_2_experiences.json
  │       └─ 使用Generator 2的专属经验生成DAG
  │
  │   Generator 3:
  │   └─ _single_agent_generate(agent_id=3)
  │       ↓ _load_agent_experiences('generator_3')
  │       ├─ 加载 generator_3_experiences.json
  │       └─ 使用Generator 3的专属经验生成DAG
  │
  └─ _critic_fusion()
      ↓ _load_agent_experiences('critic')
      ├─ 加载 critic_experiences.json
      └─ 使用Critic的专属经验融合3个DAG
```

---

## 🔧 **实现细节**

### **1. 新增方法：`_load_agent_experiences`**

```python
def _load_agent_experiences(self, agent_id: str) -> str:
    """
    从agent自己的经验文件加载经验
    
    Args:
        agent_id: 'generator_1', 'generator_2', 'generator_3', 或 'critic'
    
    Returns:
        格式化的经验字符串
    """
    # 加载 data/grpo_experiences/{agent_id}_experiences.json
    exp_file = f"data/grpo_experiences/{agent_id}_experiences.json"
    
    if file exists:
        # 读取并格式化为编号列表
        return "1. 经验1\n2. 经验2\n..."
    else:
        return "No prior experiences available."
```

### **2. Generator使用经验**

```python
def _single_agent_generate(self, agent_id: int, problem_text: str, knowledge_str: str):
    # 根据agent_id加载对应的经验
    experiences_str = self._load_agent_experiences(f'generator_{agent_id}')
    
    # Generator 1 → generator_1_experiences.json
    # Generator 2 → generator_2_experiences.json
    # Generator 3 → generator_3_experiences.json
    
    prompt = self.generator_prompt.format(
        retrieved_knowledge=knowledge_str,
        prior_experiences=experiences_str,  # ← 该generator的专属经验
        problem_text=problem_text
    )
```

### **3. Critic使用经验**

```python
def _critic_fusion(self, problem_text: str, retrieved_knowledge: List[str], proposals):
    # 加载critic自己的经验
    experiences_str = self._load_agent_experiences('critic')
    
    # Critic → critic_experiences.json
    
    prompt = self.critic_prompt.format(
        problem_text=problem_text,
        retrieved_knowledge=knowledge_str,
        prior_experiences=experiences_str,  # ← Critic的专属经验
        proposal_1=proposals[0],
        proposal_2=proposals[1],
        proposal_3=proposals[2]
    )
```

---

## 📊 **完整示例场景**

### **训练后的经验库状态：**

```json
// generator_1_experiences.json
[
  {
    "id": "G1-001",
    "content": "对数方程问题，先统一底数，再展开求解"
  },
  {
    "id": "G1-002",
    "content": "注意x,y,z的对称性，利用对称简化计算"
  }
]

// generator_2_experiences.json
[
  {
    "id": "G2-001",
    "content": "三个对数方程相加，可以消除部分未知数"
  },
  {
    "id": "G2-002",
    "content": "先求出log_2(xyz)的值，再求其他量"
  }
]

// generator_3_experiences.json
[
  {
    "id": "G3-001",
    "content": "对数问题要检查定义域，x,y,z必须为正"
  }
]

// critic_experiences.json
[
  {
    "id": "C-001",
    "content": "如果3个proposal答案一致，选择推理过程最清晰的"
  },
  {
    "id": "C-002",
    "content": "融合时优先保留数学公式正确性，再考虑计算效率"
  }
]
```

### **Production推理时：**

```
Problem: 对数方程问题...

Phase 1: Parallel Generation
├─ Generator 1:
│   加载经验: "1. 对数方程问题，先统一底数..."
│   生成DAG → Proposal 1
│
├─ Generator 2:
│   加载经验: "1. 三个对数方程相加..."
│   生成DAG → Proposal 2
│
└─ Generator 3:
    加载经验: "1. 对数问题要检查定义域..."
    生成DAG → Proposal 3

Phase 2: Critic Fusion
    加载经验: "1. 如果3个proposal答案一致..."
    融合Proposals 1,2,3 → Final DAG
```

---

## 🎯 **优势**

### **1. 个性化学习**
- ✅ 每个generator有自己的"学习路径"
- ✅ Generator 1可能擅长某类问题，Generator 2擅长另一类
- ✅ 经验多样化，ensemble效果更好

### **2. 独立进化**
```
Generator 1: 专注于数学严谨性
Generator 2: 专注于计算效率
Generator 3: 专注于边界条件检查
Critic: 专注于融合策略
```

### **3. 容错性**
- ✅ 某个generator的经验文件损坏，不影响其他generator
- ✅ 如果文件不存在，自动fallback到"No prior experiences"

### **4. 可扩展性**
```python
# 未来可以轻松添加更多generator
Generator 4 → generator_4_experiences.json
Generator 5 → generator_5_experiences.json
```

---

## 🔄 **与训练脚本的配合**

### **训练时（generator1.py等）：**

```python
# 单个generator训练
for problem in problems:
    # 1. 加载当前经验
    experiences = load_experiences('generator_1')
    
    # 2. 使用经验生成rollouts
    scaffold = scaffolder.generate_scaffold(
        problem_text=problem,
        retrieved_knowledge=[],
        experiences=experiences  # ← 使用自己的经验
    )
    
    # 3. GRPO分析 → 更新经验库
    extract_experience(generator_id='generator_1', ...)
    # → 更新 generator_1_experiences.json
```

### **Production使用（main.py）：**

```python
# 多智能体推理
causal_plan = self.scaffolder.generate_scaffold_parallel(
    problem_text=problem_text,
    retrieved_knowledge=[]
    # ← 不需要传experiences，各agent内部自动加载
)

# 内部流程：
# Generator 1 → 自动加载 generator_1_experiences.json
# Generator 2 → 自动加载 generator_2_experiences.json
# Generator 3 → 自动加载 generator_3_experiences.json
# Critic → 自动加载 critic_experiences.json
```

---

## ✅ **总结**

**核心变化：**
1. ❌ 移除了从外部传入统一的 `experiences` 参数
2. ✅ 每个agent内部根据自己的ID加载对应的经验文件
3. ✅ 实现了真正的"个性化agent"
4. ✅ 符合multi-agent系统的设计原则

**文件结构：**
- 每个agent一个独立的JSON文件
- 通过 `_load_agent_experiences(agent_id)` 方法加载
- 如果文件不存在，fallback到默认提示

**这才是真正的Multi-Agent + GRPO设计！** 🎉



