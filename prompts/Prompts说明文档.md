# 因果推理系统 Prompt 说明文档

本文档整理了系统中使用的所有Prompt及其作用，按照推理流程的顺序组织。

---

## 📋 目录

1. [Step1: 因果图生成阶段](#step1-因果图生成阶段)
   - 1.1 生成器Prompt (scaffolding_prompt_v3.txt)
   - 1.2 批判者融合Prompt (critic_fusion_prompt.txt)

2. [Step2: DAG增强阶段](#step2-dag增强阶段)
   - 2.1 领域专家审查Prompt (expert_review_prompt.txt)
   - 2.2 知识缺口识别Prompt (knowledge_gap_identification_prompt.txt)
   - 2.3 因果结构优化Prompt (causal_structure_optimization_prompt.txt)

3. [Step3: 计算与验证阶段](#step3-计算与验证阶段)
   - 3.1 逻辑评分Prompt (logic_scoring_prompt.txt)
   - 3.2 答案对比Prompt (answer_comparison_prompt.txt)

4. [辅助模块](#辅助模块)
   - 4.1 知识提取Prompt (knowledge_extraction_prompt.txt) [RAG]
   - 4.2 生成器经验提取Prompt (generator_experience_extraction.txt) [GRPO]
   - 4.3 批判者经验提取Prompt (critic_experience_extraction.txt) [GRPO]

---

## Step1: 因果图生成阶段

### 1.1 生成器Prompt (scaffolding_prompt_v3.txt)

**功能：** 将自然语言问题解构为结构化的因果DAG（有向无环图）

**角色定位：**
- Fields奖数学家 + 诺贝尔物理学家
- 超逻辑、严谨的因果推理引擎
- 不做假设，先验证；不急于计算，先构建正确模型

**核心流程 - 7步推理协议：**

1. **约束与前提识别**
   - 提取所有约束、条件、定义
   - 包括变量域（如"正整数"、"非零"）
   - 包括关系（如"不同"、"垂直"）、边界条件

2. **目标识别**
   - 明确最终问题是什么？
   - 要求的输出形式（数值、符号表达式、方程等）

3. **场景建模**
   - **物理问题：** 有哪些对象？运动阶段？坐标系？守恒定律？
   - **数学问题：** 涉及的数学结构？关键定理？

4. **策略选择**
   - 基于模型选择高层求解策略
   - 例如："应用中国剩余定理"、"使用功能定理"
   - 说明为什么该策略尊重约束

5. **变量提取与分类**
   - **具体值：** 标记为数值已知量
   - **符号参数：** 标记为符号（值为null）
   - **中间变量：** 待计算
   - **最终目标：** 目标变量

6. **因果路径映射**
   - 制定连接变量的数学方程
   - 确保每个方程都是已知定律或定理的直接应用

7. **计算计划与自我批判**
   - 创建逐步求解计划
   - 自问："该计划是否违反任何约束？"
   - "是否误解了任何符号？"
   - "是否有不合理的逻辑跳跃？"

**输出JSON结构：**
```json
{
  "constraints_and_premises": ["约束列表"],
  "problem_model": "物理/数学场景描述",
  "chosen_strategy": "求解方法",
  "target_variable": "目标变量",
  "expected_answer_type": "Numerical|Expression|Interval|Tuple|Mixed",
  "knowns": {"变量名": 值或null},
  "causal_graph": [
    {
      "cause": ["输入变量"],
      "effect": "输出变量",
      "rule": "Python语法公式 (如 'F = m * a')"
    }
  ],
  "computation_plan": [
    {
      "id": "step1",
      "target": "要计算的变量",
      "inputs": ["变量1", "变量2"],
      "description": "该步骤的作用"
    }
  ]
}
```

**关键错误示例：**
- **错误1 - 前提违背：** 问题说"a和b是不同的正整数"，但假设a=0或a=b
- **错误2 - 符号误解：** 将"N ≡ a (mod k)"理解为"N是k的倍数"，正确应为"N除以k余a"

**使用场景：** 3个并行生成器分别调用此Prompt生成不同的因果图方案

---

### 1.2 批判者融合Prompt (critic_fusion_prompt.txt)

**功能：** 接收多个生成器的提案，融合为一个最优方案

**角色定位：**
- 元批判者（Meta-Critic）和融合代理
- 结构因果模型专家
- 数学家的分析严谨性 + 工程师的系统化思维

**核心任务：**
1. **批判性分析：** 评估每个提案的正确性、完整性、逻辑连贯性
2. **错误检测：** 识别错误、不一致或约束违背
3. **最佳实践提取：** 从每个提案中找到最强的元素
4. **智能融合：** 将所有提案的见解合并为最优方案
5. **精炼：** 确保最终输出逻辑合理、完整、可执行

**7步批判性思考协议：**

1. **约束验证**
   - 从原始问题提取所有约束
   - 检查每个提案是否遵守这些约束
   - 标记违规（如错误的变量域、遗漏条件）

2. **因果图比较**
   - 比较所有提案的因果图
   - 识别任一提案中缺失的因果链接
   - 检测不正确或冗余的因果关系
   - 确定哪个提案的图最完整和准确

3. **已知变量验证**
   - 验证所有提案是否正确提取了已知值
   - 检查变量命名的一致性
   - 确保没有遗漏关键的已知量

4. **目标变量评估**
   - 确认每个提案中目标变量识别正确
   - 对于多值输出，检查目标是否正确结构化（如元组、范围）

5. **计算计划评估**
   - 评估每个提案中步骤的逻辑顺序
   - 检查完整性（是否包含所有必要的中间步骤？）
   - 识别最高效、最清晰的计算计划

6. **一致性检查**
   - 确保变量名在因果图和计算计划中一致
   - 验证每个计算步骤引用有效的输入
   - 检查所有步骤是否通向目标变量

7. **融合策略**
   - 选择最佳的约束和前提（最完整的）
   - 合并因果图：包含所有有效的因果链接，删除重复
   - 创建精炼的计算计划：最优排序，所有必要步骤
   - 确保最终JSON自洽且可执行

**融合指南：**
- **保持正确性：** 不引入新错误
- **最大化完整性：** 包含所有必要的变量和步骤
- **确保清晰性：** 使用清晰、一致的变量名
- **优化结构：** 逻辑排序步骤，删除冗余
- **处理分歧：** 选择物理/数学上最合理的选项

**输出结构：**
```json
{
  "problem_analysis": {
    "critic_analysis": "详细说明发现的问题和所做更改",
    "constraints_and_premises": [...],
    "problem_model": "...",
    "chosen_strategy": "...",
    "target_variable": "...",
    "expected_answer_type": "...",
    "knowns": {...},
    "causal_graph": [...],
    "computation_plan": [...]
  }
}
```

**使用场景：** 批判者接收3个生成器的提案，融合为最终的因果DAG

---

## Step2: DAG增强阶段

### 2.1 领域专家审查Prompt (expert_review_prompt.txt)

**功能：** 从数学/物理专家视角审查因果DAG的正确性

**角色定位：**
- 数学或物理领域的专家审查员
- 自动识别问题是数学、物理还是混合问题
- 批判性审查DAG中的公式、定理和物理定律应用

**审查重点：**
1. **自动识别问题领域**（数学/物理/混合）
2. **验证公式、定理和物理定律的正确应用**
3. **检查逻辑有效性和单位一致性**
4. **识别错误并提供具体修正**

**审查指南：**
- 从领域专家视角彻底而批判地审查
- 识别实际错误，而非风格偏好
- 提供具体修正和清晰解释
- 按严重性分类：高（错误答案）、中（误导）、低（小问题）
- 如果DAG正确，明确说明

**输出JSON结构：**
```json
{
  "problem_domain": "math|physics|mixed",
  "issues": [
    {
      "node": "节点名称或边描述",
      "issue": "问题的详细描述",
      "severity": "high|medium|low",
      "category": "formula_error|logic_error|unit_error|physics_violation|missing_step|other"
    }
  ],
  "corrections": [
    {
      "node": "节点名称",
      "original": "原始错误内容",
      "corrected": "修正后内容",
      "reason": "为什么需要此修正及遵循的原理"
    }
  ],
  "overall_assessment": "审查总结：整体质量、发现的主要问题、推理链是否合理"
}
```

**示例场景：**
- **物理错误：** 自由落体问题用了F=ma=2×5=10N，应该用F=mg=2×9.8=19.6N
- **数学错误：** 求解(x-3)=0得到x=4，应为x=3
- **正确情况：** 上抛运动用v=v₀-gt求时间，公式正确，计算准确

**使用场景：** 统一专家（Math+Physics）审查DAG，识别和修正公式、定理错误

---

### 2.2 知识缺口识别Prompt (knowledge_gap_identification_prompt.txt)

**功能：** 分析因果DAG，识别缺失的公式、定理或物理定律

**角色定位：**
- 数学和物理专家
- 识别完整推理所需的知识缺口
- 检测不完整的推理链

**分析任务：**
1. **识别缺失的公式、定理或物理定律**
2. **检测需要额外知识的不完整推理链**
3. **找出应该明确表达的隐含假设**
4. **建议相关领域知识来增强DAG**

**分析指南：**
- 寻找跳过必要中间公式的推理步骤
- 识别出现但没有明确定义的变量或量
- 检查缺失的物理原理或数学定理
- 考虑是否表达了所有必要的领域知识

**输出JSON结构：**
```json
{
  "knowledge_gaps": [
    {
      "gap_type": "formula|theorem|principle|constant",
      "description": "缺少什么知识以及为什么需要",
      "relevance": "此缺口如何影响推理",
      "priority": "high|medium|low"
    }
  ],
  "incomplete_chains": [
    {
      "from_node": "起始节点或概念",
      "to_node": "结束节点或概念",
      "missing_steps": "缺失的中间推理描述",
      "needed_knowledge": "填补此缺口所需的知识"
    }
  ],
  "suggestions": [
    {
      "knowledge_item": "具体公式、定理或原理",
      "application": "如何在此问题上下文中应用",
      "confidence": 0.0-1.0
    }
  ]
}
```

**示例场景：**
- **缺失公式：** 从加速度直接跳到最终答案，缺少速度计算（v=v₀+at）
- **缺失常数：** 未明确说明重力加速度g=9.8 m/s²
- **不完整链：** 从质量到动能，缺少速度计算（需要v²=v₀²+2ad和KE=½mv²）

**使用场景：** 在RAG知识增强前，识别DAG中的知识缺口，指导知识检索

---

### 2.3 因果结构优化Prompt (causal_structure_optimization_prompt.txt)

**功能：** 分析DAG结构，识别因果模式，验证因果方向

**角色定位：**
- 因果推断专家
- 专门分析有向无环图（DAG）和因果关系
- 验证因果方向和结构有效性

**分析任务：**

1. **识别三种基本因果结构：**
   - **链（中介）：** A → B → C（B中介A对C的影响）
   - **叉（共同原因）：** A ← B → C（B是A和C的共同原因）
   - **对撞（共同效应）：** A → B ← C（B由A和C共同导致）

2. **验证因果方向：**
   - 箭头方向是否基于因果逻辑正确？
   - 是否存在潜在的反向因果问题？
   - 因果关系在问题上下文中是否合理？

3. **检查结构问题：**
   - 循环（DAG必须无环）
   - 缺失边（未建模的因果关系）
   - 冗余边（可通过链解释）
   - 混淆因素（未测量的共同原因）

4. **建议结构优化**

**因果推理原则：**
- 因果从原因流向结果，不反向
- 时间优先：原因必须先于结果
- 机制：应有合理的因果机制
- 无虚假路径：相关性应反映真实因果关系

**输出JSON结构：**
```json
{
  "patterns": {
    "chains": [
      {
        "path": ["node1", "node2", "node3"],
        "interpretation": "node2中介node1对node3的影响"
      }
    ],
    "forks": [
      {
        "common_cause": "node_B",
        "effects": ["node_A", "node_C"],
        "interpretation": "node_B是创建A和C相关性的共同原因"
      }
    ],
    "colliders": [
      {
        "common_effect": "node_B",
        "causes": ["node_A", "node_C"],
        "interpretation": "node_B由node_A和node_C共同决定"
      }
    ]
  },
  "direction_validations": [
    {
      "edge": "A → B",
      "status": "valid|questionable|incorrect",
      "confidence": 0.0-1.0,
      "reasoning": "为什么这个方向合理或不合理的解释"
    }
  ],
  "structural_issues": [
    {
      "type": "cycle|missing_edge|redundant_edge|confounder",
      "description": "问题的详细描述",
      "severity": "high|medium|low",
      "suggestion": "如何修复此问题"
    }
  ],
  "optimization_suggestions": [
    {
      "action": "add_edge|remove_edge|reverse_edge|add_node",
      "details": "建议更改的具体细节",
      "rationale": "为什么此优化改进因果模型"
    }
  ],
  "overall_assessment": "因果结构质量总结和关键建议"
}
```

**示例场景：**
- **链结构：** mass → weight → kinetic_energy（质量通过重量影响动能）
- **叉结构：** temperature → {pressure, volume}（理想气体定律）
- **对撞：** {gravity, friction} → net_force（净力是重力和摩擦的结合）
- **方向错误：** mass → velocity（应该通过force和acceleration中介）
- **循环错误：** force → acceleration → velocity → force（需要移除velocity → force）

**使用场景：** 应用因果推断模式（Chain/Fork/Collider）优化DAG结构

---

## Step3: 计算与验证阶段

### 3.1 逻辑评分Prompt (logic_scoring_prompt.txt)

**功能：** 评估推理轨迹的质量，提供客观评分

**角色定位：**
- 严谨的数学推理评估者
- 基于实际内容提供客观评分
- 使用5个维度评估推理质量

**评分维度（5个维度，各占20%）：**

1. **逻辑连贯性 (coherence)**
   - 每一步是否从前一步正确推导？
   - 推理是否自然流畅？
   - 是否有不合理的跳跃？

2. **关键步骤完整性 (completeness)**
   - 是否包含必要的中间步骤？
   - 读者能否跟随推导？
   - 关键中间值是否显示？

3. **验证与自查 (verification)**
   - 是否进行了约束检查？
   - 是否验证边界条件？
   - 是否执行了合理性检查？

4. **无明显错误 (no_errors)**
   - 计算是否正确？
   - 数学事实是否准确？
   - 是否有符号错误、算术错误或逻辑谬误？

5. **工具一致性 (tool_consistency)**
   - 工具输出是否与推理一致？
   - 求解器是否正确解释工具结果？
   - 工具输出是否正确整合到推理中？

**评分要求：**
1. 仔细阅读推理轨迹的每一步
2. 基于实际内容提供0.00-1.00的评分（使用完整范围，2位小数）
3. 总分是5个维度的算术平均值（等权重）
4. 在"errors"中列出发现的具体问题（如果没有问题则为空数组）
5. **关键：每个轨迹都不同 - 评分必须反映实际质量，使用从0.00到1.00的完整范围**

**输出JSON结构：**
```json
{
  "score": 0.75,  // 总分 = 5个维度平均
  "breakdown": {
    "coherence": 0.85,
    "completeness": 0.70,
    "verification": 0.65,
    "no_errors": 0.90,
    "tool_consistency": 0.65
  },
  "errors": [
    "步骤3: 从方程(1)跳到结论，未显示求解过程",
    "步骤5: 未验证x=2满足约束x>0"
  ]
}
```

**评分示例：**
- **高质量（0.85-0.95）：** 逻辑清晰，步骤完整，有验证，无错误
- **中等质量（0.50-0.70）：** 有跳步，缺少验证，个别错误
- **低质量（0.20-0.40）：** 逻辑混乱，多处错误，缺少关键步骤

**使用场景：** 在Step3中评估LLM生成的推理轨迹质量，用于GRPO奖励计算

---

### 3.2 答案对比Prompt (answer_comparison_prompt.txt)

**功能：** 判断两个答案是否语义等价

**角色定位：**
- 科学答案验证专家
- 上下文感知的答案对比
- 处理格式、单位、科学记数法等差异

**核心规则：**

1. **上下文感知**
   - 阅读问题理解询问内容（速度、力、能量等）
   - 基于问题上下文判断答案是否等价

2. **数值等价性**
   - 科学记数法：2×10⁵ = 2e5 = 200000
   - 分数/小数：1/2 = 0.5
   - LaTeX/格式：$30$ = 30 = ['$30$']

3. **单位处理（物理问题关键）**
   - 数值匹配 且 单位在上下文中正确 → YES
   - 预期"30" vs 预测"30 m/s"（速度问题）→ YES ✓
   - 预期"30" vs 预测"30 kg"（速度问题）→ NO ✗（单位类型错误）
   - 单位转换：1km=1000m, 1kW=1000W, 1h=3600s

4. **严格匹配**
   - "2" ≠ "12"（不进行子串匹配）
   - 必须完整数值相等

**对比任务：**
考虑以下因素判断答案是否等价：
1. 问题询问的内容（使用上下文）
2. 数值等价性（处理科学记数法、格式）
3. 单位适当性（如果存在）

**输出格式：**
```
YES 或 NO
然后简要解释原因
```

**示例：**
- **YES：** 预期"0.5"，预测"1/2" → 数值等价
- **YES：** 预期"30"，预测"30 m/s"（速度问题）→ 单位正确
- **NO：** 预期"30"，预测"30 kg"（速度问题）→ 单位类型错误
- **YES：** 预期"2e5"，预测"200000" → 科学记数法等价

**使用场景：** 在Step3中比较LLM计算结果与标准答案，用于奖励计算

---

## 辅助模块

### 4.1 知识提取Prompt (knowledge_extraction_prompt.txt)

**功能：** 从问题中提取相关的公式、定律、原理（用于RAG）

**角色定位：**
- 数学、物理和科学推理专家
- 仅识别相关知识，不求解问题
- 提取领域知识列表

**目标：**
提取可能适用于问题的领域知识（公式、定律等）全面列表，不执行计算或求解问题。

**指令：**
1. 仔细阅读问题，识别领域（如力学、热力学、几何、代数）
2. 仅提取可能相关的物理定律、数学公式、原理或规则 - **不计算值、推导结果或列出求解步骤**
3. 对于每个规则，提供：
   - 相关关键词列表（小写，特定术语如"force"、"velocity"）
   - 规则描述（包括名称和数学公式或表达式）
   - 规则类别（如"mechanics"、"algebra"、"geometry"）
4. 列出最多{max_rules}个最相关的规则
5. 按相关性排序（最基础或直接适用的优先）
6. 数学记号精确（如用×表示乘法，正确的下标如v_i表示初速度）
7. 在规则描述中包含一般单位和变量定义，但避免代入问题特定值
8. **严格避免求解问题或提及问题中的数值**
9. 当问题跨两个领域时，包含数学和物理原理（如代数技巧和物理定律）
10. 输出格式为JSON对象列表，每个有"keywords"、"rule"、"category"字段

**输出JSON结构：**
```json
[
  {
    "keywords": ["force", "mass", "acceleration"],
    "rule": "Newton's Second Law: F = m × a - 关联净力(F, N)、质量(m, kg)和加速度(a, m/s²)；用于动力学连接力与运动",
    "category": "mechanics"
  },
  {
    "keywords": ["velocity", "acceleration", "time"],
    "rule": "Kinematic Equation: v = u + a × t - 描述末速度(v)与初速度(u)、加速度(a)、时间(t)的关系；适用于匀加速运动",
    "category": "kinematics"
  }
]
```

**示例场景：**
- 问题："10kg物体受50N力作用5秒，求末速度"
- 提取：牛顿第二定律(F=ma)、运动学方程(v=u+at)、初速度为零(u=0)、代数求解(a=F/m)等

**使用场景：** 在Step2.5 RAG知识增强阶段，从向量数据库检索相关知识前，先从问题提取关键词

---

### 4.2 生成器经验提取Prompt (generator_experience_extraction.txt)

**功能：** 分析生成器的多次rollout差异，提取经验教训（用于Training-Free GRPO）

**角色定位：**
- 生成器{generator_id}的经验分析师
- 分析为什么rollout产生不同结果
- 提取可操作的经验改进未来性能

**上下文：**
- 生成器刚完成{num_rollouts}个不同的因果图rollout
- 每个rollout产生不同答案和不同奖励分数
- 任务：分析为什么rollout不同，提取可操作经验

**GRPO统计：**
- 均值(μ)、标准差(σ)、范围
- **检测到高方差（σ > τ=0.05）** → 触发经验提取

**任务：**
1. **分析方差：** 为什么3个rollout有如此不同的奖励？哪个rollout表现差，为什么？
2. **识别根本原因：** 生成器在因果图构建或推理中犯了什么错误？
3. **提取可操作经验：** 生成器应该学习什么以避免未来类似错误？
4. **保持简洁：** 经验内容必须≤32词

**输出JSON结构：**
```json
{
  "operations": [
    {
      "action": "add",
      "content": "简洁、可操作的经验（≤32词）",
      "category": "causal_graph|validation|problem_solving",
      "reason": "为什么这有助于生成器X"
    }
  ],
  "analysis": "方差和根本原因的简要解释"
}
```

**指南：**
- 专注于因果图构建错误（错误变量、缺失链接、不正确关系）
- 具体说明哪里出错以及如何修复
- 避免泛泛建议如"更仔细"
- 经验应直接适用于类似问题

**示例场景：**
- 3个rollout：答案分别为10N、19.6N、15N，奖励差异大
- 分析：rollout1和3错误使用a而非g计算重力
- 经验："对于重力问题，总是使用F=mg，其中g=9.8 m/s²，而非通用F=ma"

**使用场景：** 在GRPO训练阶段，当某生成器的多个rollout方差大时，提取经验注入该生成器

---

### 4.3 批判者经验提取Prompt (critic_experience_extraction.txt)

**功能：** 分析批判者的多次融合差异，提取融合策略经验（用于Training-Free GRPO）

**角色定位：**
- 批判者代理的经验分析师
- 分析批判者的融合性能
- 提取改进融合策略的经验

**上下文：**
- 批判者刚完成3次融合任务：分别融合Generator 1、2、3的rollouts
- 同一问题，每次融合产生不同结果和不同质量分数
- 任务：分析批判者融合性能，提取改进融合策略的经验

**GRPO统计：**
- 均值(μ)、标准差(σ)、范围
- **检测到高方差（σ > τ=0.05）** → 触发经验提取

**任务：**
1. **分析融合质量方差：** 为什么3次融合产生如此不同的结果？哪次融合失败，为什么？
2. **识别融合策略问题：** 批判者是否选择了正确的rollout信任？是否正确合并了冲突信息？
3. **提取融合策略经验：** 批判者应该学习什么来改进融合质量？
4. **保持简洁：** 经验内容必须≤32词

**输出JSON结构：**
```json
{
  "operations": [
    {
      "action": "add",
      "content": "简洁、可操作的融合策略（≤32词）",
      "category": "fusion_strategy|validation|conflict_resolution",
      "reason": "为什么这改进融合质量"
    }
  ],
  "analysis": "融合问题和改进的简要解释"
}
```

**指南：**
- 专注于融合策略（如何选择最佳rollout、如何合并冲突提案、如何处理低质量输入）
- 具体说明哪个融合决策错误以及如何改进
- 考虑r_fusion分数（衡量融合有效性）
- 经验应帮助批判者在类似场景做出更好融合决策

**示例场景：**
- Fusion 1（Gen1）→ 正确，Fusion 2（Gen2）→ 错误，Fusion 3（Gen3）→ 正确
- 分析：Fusion 2选择了错误的rollout，忽略了高质量提案
- 经验："融合时优先选择逻辑评分高(r_logic>0.8)且causal_graph完整的rollout"

**使用场景：** 在GRPO训练阶段，当批判者的多次融合方差大时，提取经验注入批判者

---

## 📈 Prompt使用流程图

```
问题输入
    ↓
[RAG知识检索] ← knowledge_extraction_prompt.txt
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step1: 因果图生成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
[3个并行生成器] ← scaffolding_prompt_v3.txt
   Gen1  Gen2  Gen3
    ↓     ↓     ↓
    └─────┼─────┘
          ↓
  [批判者融合] ← critic_fusion_prompt.txt
          ↓
    初始DAG
          ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step2: DAG增强
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ↓
 [领域专家审查] ← expert_review_prompt.txt
          ↓
[知识缺口识别] ← knowledge_gap_identification_prompt.txt
          ↓
  [RAG知识注入]
          ↓
[因果结构优化] ← causal_structure_optimization_prompt.txt
          ↓
    增强DAG
          ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step3: 计算与验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ↓
  [LLM计算答案]
          ↓
   [逻辑评分] ← logic_scoring_prompt.txt
          ↓
   [答案对比] ← answer_comparison_prompt.txt
          ↓
      最终答案
          ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRPO经验学习（Training-Free）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ↓
[生成器经验提取] ← generator_experience_extraction.txt
          ↓
[批判者经验提取] ← critic_experience_extraction.txt
          ↓
   经验注入Agent
```

---

## 🔑 关键设计特点

### 1. **多智能体协作**
- **3个并行生成器** + **1个批判者**融合
- 每个agent有独立API，避免速率限制
- 批判者智能融合不同视角

### 2. **分层增强流程**
- **Step1：** 初步生成（快速、多样）
- **Step2：** 多维度增强（专家审查、知识注入、结构优化）
- **Step3：** 计算验证（逻辑评分、答案对比）

### 3. **Training-Free GRPO**
- 无需梯度训练
- 通过经验提取和注入改进agent
- 关注高方差情况（σ > 0.05）

### 4. **因果推理核心**
- 强调因果图构建（不仅是公式堆砌）
- 验证因果方向和结构
- 识别三种基本模式（Chain/Fork/Collider）

### 5. **严格约束和验证**
- 7步推理协议确保逻辑严谨
- 多层验证（专家审查、逻辑评分、答案对比）
- 避免常见错误（前提违背、符号误解等）

---

## 📝 使用建议

1. **调试时：** 先看scaffolding_prompt_v3.txt和critic_fusion_prompt.txt（核心生成）
2. **效果不好时：** 检查expert_review_prompt.txt和knowledge_gap_identification_prompt.txt（增强环节）
3. **答案错误时：** 看logic_scoring_prompt.txt和answer_comparison_prompt.txt（验证环节）
4. **持续改进：** 利用generator_experience_extraction.txt和critic_experience_extraction.txt（GRPO学习）

---

**文档版本：** v1.0  
**最后更新：** 2025-11-08  
**适用系统：** 基于因果推理的多智能体数学/物理问题求解系统

