# ⚡ 因果推理引擎 - 快速参考卡

## 🎯 一分钟了解项目

### 这是什么？
一个**混合AI系统**，让大模型+符号计算联手解决数学物理问题

### 为什么需要它？
| 问题 | 传统LLM | 本系统 |
|------|---------|--------|
| 计算精度 | ❌ 容易出错 | ✅ SymPy保证精确 |
| 多步推理 | ❌ 容易断链 | ✅ JSON结构化 |
| 领域知识 | ❌ 可能幻觉 | ✅ RAG检索真实公式 |
| 可解释性 | ❌ 黑盒 | ✅ 因果图+反事实验证 |

---

## 📂 项目结构速览

```
hope_code/
│
├── 🎮 入口文件
│   ├── main.py              ← 主程序，从这里开始！
│   ├── example_usage.py     ← 6个实战示例
│   └── test_components.py   ← 单元测试
│
├── 🧠 核心引擎 (engine/)
│   ├── retriever.py         ← 阶段1: 知识检索 (300行)
│   ├── scaffolder.py        ← 阶段2: 生成计划 (397行)
│   ├── executor.py          ← 阶段3: 符号计算 (504行)
│   ├── synthesizer.py       ← 阶段4: 生成解释 (392行)
│   └── ai_retriever.py      ← 高级检索器 (531行)
│
├── 📚 数据资源
│   ├── data/knowledge_base.json  ← 50+条物理数学公式
│   ├── prompts/                  ← LLM提示词模板
│   └── dataset/                  ← 测试数据集
│
└── 📖 文档
    ├── README.md            ← 完整文档
    ├── QUICKSTART.md        ← 5分钟快速开始
    ├── PROJECT_GUIDE.md     ← 详细指南(你正在读的)
    ├── AI_RETRIEVER_GUIDE.md ← AI检索器说明
    └── idea.md              ← 原始设计思想
```

---

## 🚀 三种使用方式

### 方式1: 命令行（最简单）

```bash
# 直接问问题
python main.py -p "10kg物体受50N力，求加速度"

# 从文件读取
python main.py -f my_problem.txt

# 保存结果
python main.py -p "你的问题" -o result.json

# 快速模式（跳过验证）
python main.py -p "你的问题" --no-validation -q
```

### 方式2: Python脚本（推荐）

```python
from main import CausalReasoningEngine

# 1. 初始化引擎
engine = CausalReasoningEngine()

# 2. 求解问题
results = engine.solve_problem("你的问题")

# 3. 查看结果
engine.display_results(results)

# 4. 提取数据
answer = results['final_answer']
explanation = results['explanation']
```

### 方式3: 交互式示例（最有趣）

```bash
# 运行示例菜单
python example_usage.py

# 然后选择：
# 1-6: 预设示例（力学、电学、数学等）
# 7: 输入自己的问题
# 8: 运行所有示例
```

---

## 🔍 四阶段处理流程

```
你的问题: "10kg物体受50N力，求加速度"
         ↓
┌────────────────────────────────┐
│ 阶段1: 知识检索 (retriever.py)  │
├────────────────────────────────┤
│ ✓ 提取关键词: force, mass      │
│ ✓ 检索公式: F = m * a          │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│ 阶段2: 生成计划 (scaffolder.py) │
├────────────────────────────────┤
│ ✓ LLM生成JSON格式计划:          │
│   {                            │
│     knowns: {F:50, m:10},      │
│     target: "a",               │
│     plan: [...]                │
│   }                            │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│ 阶段3: 符号执行 (executor.py)   │
├────────────────────────────────┤
│ ✓ SymPy计算: F = m * a         │
│ ✓ 代入: 50 = 10 * a            │
│ ✓ 求解: a = 5.0                │
└────────────────────────────────┘
         ↓
┌────────────────────────────────┐
│ 阶段4: 生成解释 (synthesizer.py)│
├────────────────────────────────┤
│ ✓ 人类可读解释                  │
│ ✓ 反事实验证                    │
└────────────────────────────────┘
         ↓
    答案: 5.0 m/s²
```

---

## 🔧 配置API密钥

### Step 1: 选择提供商

| 提供商 | 优势 | 获取地址 |
|--------|------|----------|
| **硅基流动** | 🌟国内快、便宜 | https://cloud.siliconflow.cn/ |
| OpenAI | 性能最好 | https://platform.openai.com/ |
| Anthropic | Claude最强 | https://console.anthropic.com/ |

### Step 2: 创建 .env 文件

```env
# .env
DEFAULT_PROVIDER=siliconflow
SILICONFLOW_API_KEY=你的密钥
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct
```

### Step 3: 测试

```bash
python main.py
```

---

## 💡 代码示例库

### 示例1: 基础使用

```python
from main import CausalReasoningEngine

engine = CausalReasoningEngine()
results = engine.solve_problem("半径5米的圆，求面积")
print(results['final_answer'])  # 78.53981633974483
```

### 示例2: 批量处理

```python
problems = [
    "质量2kg，速度10m/s，求动能",
    "电压12V，电阻3Ω，求电流",
    "密度：质量100kg，体积5m³"
]

for p in problems:
    result = engine.solve_problem(p, include_validation=False)
    print(f"{p} → {result['final_answer']}")
```

### 示例3: 保存结果

```python
results = engine.solve_problem(
    "复杂问题...",
    save_output="output/result_2024.json"
)

# 结果包含：
# - problem: 原始问题
# - retrieved_knowledge: 检索到的公式
# - causal_scaffold: 生成的计划
# - executed_scaffold: 执行后的结果
# - final_answer: 最终答案
# - explanation: 人类可读解释
# - validation: 反事实验证（可选）
```

### 示例4: 扩展知识库

```python
from engine import KnowledgeRetriever

# 加载知识库
retriever = KnowledgeRetriever("data/knowledge_base.json")

# 添加新公式
retriever.add_knowledge(
    keywords=["momentum", "impulse", "force", "time"],
    rule="Impulse: J = F * Δt = Δp",
    category="mechanics"
)

# 保存
retriever.save_knowledge_base()
```

---

## 📊 支持的问题类型

### ✅ 已支持

| 类型 | 示例 | 涉及公式 |
|------|------|----------|
| **力学** | 力、质量、加速度 | F=ma |
| **运动学** | 速度、时间、位移 | v=v₀+at |
| **能量** | 动能、势能 | E=½mv² |
| **电学** | 电压、电流、电阻 | V=IR |
| **几何** | 圆、球、柱体 | A=πr² |
| **热学** | 热量、温度 | Q=mcΔT |
| **光学** | 折射、透镜 | n₁sinθ₁=n₂sinθ₂ |

### 🔜 可扩展

- 微积分问题
- 概率统计
- 化学方程式
- 更多...（只需添加公式到知识库）

---

## 🐛 故障排查

### 问题1: API调用失败

```
Error calling LLM: Connection error
```

**检查清单：**
- [ ] `.env` 文件存在且在项目根目录
- [ ] API密钥正确（无多余空格）
- [ ] 网络连接正常
- [ ] API账户有余额

**快速修复：**
```bash
# 检查配置
Get-Content .env

# 测试网络
ping api.siliconflow.cn
```

### 问题2: 模块导入错误

```
ModuleNotFoundError: No module named 'openai'
```

**快速修复：**
```bash
pip install -r requirements.txt
# 或
pip install openai sympy python-dotenv
```

### 问题3: 符号执行失败

```
No solution found for X
```

**原因：**
- 变量名不匹配（公式用`a`，LLM生成的用`acceleration`）
- 公式格式错误

**已修复！** 现在系统会自动映射变量名

### 问题4: 知识检索为空

```
No relevant knowledge found
```

**解决：**
- 使用英文问题（关键词提取更准确）
- 或添加更多中文关键词到知识库

---

## 📈 性能优化

### 加速技巧

```bash
# 1. 跳过验证（节省1次LLM调用）
python main.py -p "问题" --no-validation

# 2. 静默模式（减少输出）
python main.py -p "问题" -q

# 3. 批量处理时复用引擎
engine = CausalReasoningEngine()  # 只初始化一次
for problem in problems:
    engine.solve_problem(problem)  # 复用
```

### 成本优化

```python
# 使用更便宜的模型
# .env
SILICONFLOW_MODEL=Qwen/Qwen2-7B-Instruct  # 更便宜
# 或
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct  # 更准确
```

---

## 🎓 学习路径

### 第1天：快速上手
1. ✅ 配置API密钥
2. ✅ 运行 `python main.py`
3. ✅ 运行 `python example_usage.py`
4. ✅ 尝试自己的问题

### 第2天：理解架构
1. 📖 阅读 `PROJECT_GUIDE.md`
2. 👀 查看 `main.py` 主流程
3. 🔍 查看 `engine/retriever.py` 最简单的模块
4. 🎨 查看 `data/knowledge_base.json` 知识库

### 第3天：动手实践
1. 📝 修改提示词 (`prompts/`)
2. ➕ 添加新公式到知识库
3. 🧪 测试自己的问题集
4. 📊 分析输出结果

### 第4天：深入代码
1. 🏗️ 阅读 `scaffolder.py` - LLM调用
2. ⚙️ 阅读 `executor.py` - SymPy计算
3. 📝 阅读 `synthesizer.py` - 结果生成
4. 🔧 尝试修改和扩展

---

## 🔗 快速链接

- 📘 **完整文档**: [README.md](README.md)
- 🚀 **5分钟开始**: [QUICKSTART.md](QUICKSTART.md)
- 📚 **详细指南**: [PROJECT_GUIDE.md](PROJECT_GUIDE.md)
- 💡 **设计思想**: [idea.md](idea.md)
- 🔬 **AI检索器**: [AI_RETRIEVER_GUIDE.md](AI_RETRIEVER_GUIDE.md)

---

## 📞 获取帮助

```bash
# 查看帮助
python main.py --help

# 查看版本信息
python main.py --version  # (如果实现了)

# 运行测试
python test_components.py
```

---

## 🎉 快速开始命令

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API（编辑.env文件）
notepad .env

# 3. 运行演示
python main.py

# 4. 运行示例
python example_usage.py

# 5. 测试自己的问题
python main.py -p "你的问题"
```

---

**记住：遇到问题先看这个文档！** 📖

**祝你使用愉快！** 🎊

