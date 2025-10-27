# GRPO 迁移指南 (V1 → V2)
# GRPO Migration Guide (V1 → V2)

## 🎯 快速总结

**V1 已删除**，现在只有一个版本的 `TrainingFreeGRPOTrainer`（基于原 V2 架构）。

---

## ⚡ 如果你之前使用 V1

### 代码更改

**之前 (V1):**
```python
from engine import TrainingFreeGRPOTrainer

trainer = TrainingFreeGRPOTrainer(
    causal_engine=engine,
    experience_manager=experience_manager,
    group_size=3,  # ← 旧参数名
    num_epochs=3,
    verbose=True
)
```

**现在 (统一版本):**
```python
from engine import TrainingFreeGRPOTrainer  # 导入不变

trainer = TrainingFreeGRPOTrainer(
    causal_engine=engine,
    experience_manager=experience_manager,
    rollouts_per_generator=3,  # ← 新参数名（更清晰）
    num_epochs=3,
    verbose=True
)
```

### 唯一需要改的地方

**参数名变更：**
- ❌ `group_size=3` 
- ✅ `rollouts_per_generator=3`

**其他一切保持不变！**

---

## ⚡ 如果你之前使用 V2

### 代码更改

**之前 (V2):**
```python
from engine import TrainingFreeGRPOTrainerV2  # ← 旧类名

trainer = TrainingFreeGRPOTrainerV2(  # ← 旧类名
    causal_engine=engine,
    experience_manager=experience_manager,
    rollouts_per_generator=3,
    num_epochs=3,
    verbose=True
)
```

**现在 (统一版本):**
```python
from engine import TrainingFreeGRPOTrainer  # ← 去掉 V2 后缀

trainer = TrainingFreeGRPOTrainer(  # ← 去掉 V2 后缀
    causal_engine=engine,
    experience_manager=experience_manager,
    rollouts_per_generator=3,  # 参数不变
    num_epochs=3,
    verbose=True
)
```

### 需要改的地方

**类名变更：**
- ❌ `TrainingFreeGRPOTrainerV2`
- ✅ `TrainingFreeGRPOTrainer`

**参数保持不变！**

---

## 📋 检查清单

完成以下检查以确保迁移成功：

- [ ] 更新所有 `group_size` 为 `rollouts_per_generator`
- [ ] 移除所有 `V2` 后缀
- [ ] 确认导入使用 `TrainingFreeGRPOTrainer`
- [ ] 运行测试：`python test_grpo_system.py`
- [ ] 小规模训练测试：`python train_with_grpo.py --max-problems 5 --epochs 1`

---

## 🔍 常见问题

### Q: 我的旧检查点还能用吗？

**A:** 经验库格式没有变，可以继续使用：
```bash
python train_with_grpo.py --use-existing-experiences --epochs 2
```

### Q: 为什么要删除 V1？

**A:** V2 架构明显更优：
- ✅ 每个生成器独立学习
- ✅ 可以精确追踪各生成器表现
- ✅ 针对性改进效果更好

### Q: V1 和 V2 有什么区别？

**A:** 核心区别在经验更新策略：

| 特性 | V1 (已删除) | V2 (现在) |
|------|-------------|-----------|
| Rollout 生成 | 3个生成器各生成多个 | 3个生成器各生成多个 ✓ |
| Critic 融合 | 混合所有9个rollouts | **分别**融合每个生成器 ✓ |
| 最终答案 | 1个答案 | **3个**答案（每生成器1个）✓ |
| 经验更新 | 所有生成器共享更新 | **各自独立**更新 ✓ |
| 可追踪性 | 低 | **高** ✓ |

### Q: 训练命令有变化吗？

**A:** 没有变化！
```bash
# 这些命令都正常工作
python train_with_grpo.py
python train_with_grpo.py --epochs 5 --group-size 3
python train_with_grpo.py --datasets aime2024 --max-problems 50
```

---

## 🚀 开始使用

### 1. 验证安装
```bash
python -c "from engine import TrainingFreeGRPOTrainer; print('✓ Ready!')"
```

### 2. 运行测试
```bash
python test_grpo_system.py
```

### 3. 开始训练
```bash
python train_with_grpo.py --epochs 3 --group-size 3
```

---

## 💡 新功能建议

现在代码统一后，可以考虑这些改进：

1. **增强答案比较** - 支持分数、单位、LaTeX
2. **重试机制** - LLM 调用失败时自动重试
3. **经验去重** - 避免添加重复经验
4. **A/B 测试工具** - 对比有无经验的效果
5. **断点续训** - 训练中断后可继续

---

## 📞 需要帮助？

- 查看快速开始：`GRPO快速开始.md`
- 查看详细日志：`GRPO_CLEANUP_LOG.md`
- 运行测试脚本：`test_grpo_system.py`

---

**迁移很简单，只需改一两个地方！🎉**

