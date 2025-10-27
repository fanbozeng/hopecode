# Training-Free GRPO 快速开始

## 🚀 5分钟快速上手

### 第1步：准备物理问题（2分钟）

```bash
# 复制示例文件
cp dataset/physics_problems_example.json dataset/physics_problems.json

# 编辑文件，添加你的30道物理题
# 格式：{"problem": "问题", "answer": "答案", "subject": "physics"}
```

### 第2步：开始训练（2分钟启动）

```bash
python train_with_grpo.py
```

就这么简单！系统会：
- ✅ 自动加载 AIME2024 + AIME2025 + 物理问题
- ✅ 训练3个epochs（约2-3小时）
- ✅ 保存经验到 `data/grpo_experiences/`

### 第3步：查看结果（1分钟）

```bash
# 查看学到的经验
cat data/grpo_experiences/shared_experiences.json

# 查看训练统计
# 在训练结束时会自动显示
```

---

## 🎯 核心概念（3句话理解）

1. **不更新模型参数**：训练只更新外部"经验库"（JSON文件）
2. **少量数据即可**：50-100个问题就能看到效果
3. **成本极低**：~$20-30（传统RL需要~$10,000）

---

## 📊 你的框架如何使用

### Before（无经验）
```python
engine = CausalReasoningEngine(use_multi_agent=True)
result = engine.solve_problem(problem)  # 准确率: 60%
```

### After（有经验）
```python
from engine import GRPOExperienceManager

# 加载训练好的经验
exp_manager = GRPOExperienceManager()

# 注入到引擎
engine = CausalReasoningEngine(use_multi_agent=True)
engine.scaffolder.experience_manager = exp_manager

result = engine.solve_problem(problem)  # 准确率: 70%+ ⬆️
```

---

## 🛠️ 常用命令

```bash
# 基础训练（推荐）
python train_with_grpo.py

# 只用AIME数据训练（无物理题）
python train_with_grpo.py --datasets aime2024 aime2025

# 快速测试（30个问题，2 epochs）
python train_with_grpo.py --max-problems 30 --epochs 2

# 继续训练现有经验
python train_with_grpo.py --use-existing-experiences --epochs 2

# 自定义保存路径
python train_with_grpo.py --experience-dir my_experiences
```

---

## 📁 生成的文件

```
data/grpo_experiences/
├── shared_experiences.json          # 共享经验
├── generator_1_experiences.json     # 生成器1的经验
├── generator_2_experiences.json     # 生成器2的经验
├── generator_3_experiences.json     # 生成器3的经验
└── critic_experiences.json          # 批判者的经验

checkpoints/grpo/
├── epoch_1.json                     # 每个epoch的检查点
├── epoch_2.json
└── epoch_3.json
```

---

## 🔧 快速调试

### 问题1：找不到数据集
```
错误: AIME 2024 dataset not found
解决: 确认文件存在 dataset/AIME_2024/aime_2024_problems.json
```

### 问题2：训练太慢
```
解决: 减少问题数量和epochs
python train_with_grpo.py --max-problems 30 --epochs 2
```

### 问题3：API调用失败
```
解决: 检查 .env 文件中的 API key
OPENAI_API_KEY=your_key_here
```

---

## 📈 预期效果

| 指标 | 训练前 | 训练后 | 提升 |
|------|--------|--------|------|
| **准确率** | 60% | 70% | +10% |
| **因果图质量** | 中等 | 优秀 | ⬆️ |
| **推理一致性** | 一般 | 良好 | ⬆️ |
| **训练成本** | N/A | ~$25 | 极低 |

---

## 🎓 下一步

1. **查看详细文档**：`doc/训练自由GRPO使用指南.md`
2. **调整配置**：修改 epochs、group_size 等参数
3. **评估性能**：在测试集上对比有/无经验的效果
4. **持续优化**：根据反馈继续训练

---

## 💡 核心优势

✅ **零参数更新**：模型保持冻结  
✅ **数据高效**：50个问题即可见效  
✅ **成本极低**：比传统RL便宜300倍  
✅ **即插即用**：加载JSON即可使用  
✅ **跨域泛化**：一套经验多个任务  

---

**就是这么简单！🎉**

详细文档：`doc/训练自由GRPO使用指南.md`


