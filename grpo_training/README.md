# GRPO Training Module
# GRPO训练模块

## 📁 Directory Structure | 目录结构

```
grpo_training/
├── __init__.py                     # Package initialization | 包初始化
├── README.md                       # This file | 本文档
├── experience_extractor.py         # Universal experience extraction | 通用经验提炼
├── generator1.py                   # Generator 1 training script | Generator 1训练脚本
├── generator2.py                   # Generator 2 training script | Generator 2训练脚本
├── generator3.py                   # Generator 3 training script | Generator 3训练脚本
├── critic.py                       # Critic training script | Critic训练脚本
└── cache/                          # Training cache (auto-created) | 训练缓存（自动创建）
    ├── generator_1_rollouts.jsonl  # Generator 1 rollouts | Generator 1的rollouts
    ├── generator_2_rollouts.jsonl  # Generator 2 rollouts | Generator 2的rollouts
    ├── generator_3_rollouts.jsonl  # Generator 3 rollouts | Generator 3的rollouts
    └── critic_results.jsonl        # Critic fusion results | Critic融合结果
```

## 🚀 Quick Start | 快速开始

### 1. Configure API Keys | 配置API密钥

```bash
# Copy example config | 复制示例配置
cp data/api_keys/api_config.json.example data/api_keys/api_config.json

# Edit with your real API keys | 使用真实API密钥编辑
nano data/api_keys/api_config.json
```

### 2. Run Generators in Parallel | 并行运行Generators

Open 3 separate terminals and run:
在3个独立的终端中运行：

```bash
# Terminal 1 - Generator 1
python -m grpo_training.generator1 --dataset aime2024 --max-problems 10

# Terminal 2 - Generator 2
python -m grpo_training.generator2 --dataset aime2024 --max-problems 10

# Terminal 3 - Generator 3
python -m grpo_training.generator3 --dataset aime2024 --max-problems 10
```

### 3. Run Critic (After Generators Complete) | 运行Critic（在Generators完成后）

```bash
# Terminal 4 - Critic
python -m grpo_training.critic
```

## 📝 Command Line Arguments | 命令行参数

### Generator Scripts

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--dataset` | str | `aime2024` | Dataset: `aime2024`, `aime2025`, `physics` |
| `--max-problems` | int | `None` | Max problems to train (None = all) |
| `--rollouts` | int | `3` | Number of rollouts per problem |
| `--temperature` | float | `0.3` | LLM temperature for generation |

### Critic Script

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--temperature` | float | `0.0` | LLM temperature (0.0 = deterministic) |

## 🔧 Architecture | 架构

### Workflow | 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│              Step 1: Parallel Generator Training             │
│              步骤1：并行Generator训练                         │
└─────────────────────────────────────────────────────────────┘
                             │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    Generator 1        Generator 2        Generator 3
    (API Key 1)        (API Key 2)        (API Key 3)
         │                  │                  │
         ├─ 3 Rollouts      ├─ 3 Rollouts      ├─ 3 Rollouts
         ├─ Rewards         ├─ Rewards         ├─ Rewards
         ├─ GRPO Stats      ├─ GRPO Stats      ├─ GRPO Stats
         ├─ Experience      ├─ Experience      ├─ Experience
         │                  │                  │
         └─ Save to         └─ Save to         └─ Save to
            cache/              cache/              cache/

┌─────────────────────────────────────────────────────────────┐
│              Step 2: Critic Fusion & Training                │
│              步骤2：Critic融合和训练                          │
└─────────────────────────────────────────────────────────────┘
                             │
                        Critic Agent
                        (API Key 4)
                             │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    Fusion Task 1      Fusion Task 2      Fusion Task 3
    (Gen1's 3 DAGs)    (Gen2's 3 DAGs)    (Gen3's 3 DAGs)
         │                  │                  │
         ├─ Fused DAG       ├─ Fused DAG       ├─ Fused DAG
         ├─ Answer          ├─ Answer          ├─ Answer
         ├─ Rewards         ├─ Rewards         ├─ Rewards
         │                  │                  │
         └──────────────────┴──────────────────┘
                             │
                    GRPO Statistics (μ, σ)
                             │
                    Experience Extraction
                             │
                    Save Critic Experience
```

### GRPO Experience Extraction | GRPO经验提炼

- **Trigger Condition | 触发条件**: σ > τ (standard deviation > threshold)
- **Default Threshold | 默认阈值**: τ = 0.05
- **Experience Content | 经验内容**: ≤32 words, actionable insights

## 📊 Output Files | 输出文件

### 1. Rollouts Cache | Rollouts缓存

**Location**: `grpo_training/cache/generator_X_rollouts.jsonl`

**Format**:
```json
{
  "problem_id": "aime2024_001",
  "problem_text": "Find the value of...",
  "ground_truth": "42",
  "rollouts": [
    {
      "rollout_id": 1,
      "scaffold": "...",
      "answer": "40",
      "is_correct": false,
      "r_ans": 0.0,
      "r_logic": 0.75,
      "r_graph": 0.80,
      "r_total": 0.3875
    },
    ...
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. Critic Fusion Results | Critic融合结果

**Location**: `grpo_training/cache/critic_results.jsonl`

**Format**:
```json
{
  "problem_id": "aime2024_001",
  "problem_text": "Find the value of...",
  "ground_truth": "42",
  "generator_id": "generator_1",
  "fused_scaffold": "...",
  "final_answer": "42",
  "is_correct": true,
  "rewards": {
    "r_ans": 1.0,
    "r_logic": 0.85,
    "r_graph": 0.90,
    "r_fusion": 0.75,
    "r_total": 0.875
  },
  "timestamp": "2024-01-15T11:00:00"
}
```

### 3. Experience Libraries | 经验库

**Location**: `data/grpo_experiences/`

- `generator_1_experiences.json`
- `generator_2_experiences.json`
- `generator_3_experiences.json`
- `critic_experiences.json`

**Format**:
```json
[
  {
    "id": "G1-001",
    "content": "When dealing with modular arithmetic, ensure proper handling of remainders.",
    "category": "causal_graph",
    "source_problem": "aime2024_003",
    "created_at": "2024-01-15T10:35:00"
  },
  ...
]
```

## 🐛 Troubleshooting | 故障排除

### Problem: "API key not found for generator_X"

**Solution**: 
1. Check `data/api_keys/api_config.json` exists
2. Ensure all required keys are configured:
   - `generator_1`, `generator_2`, `generator_3`, `critic`

### Problem: "Rollouts file not found" (Critic)

**Solution**: 
1. Ensure all 3 Generator scripts have completed
2. Check `grpo_training/cache/` for rollouts files

### Problem: Import errors

**Solution**: 
```bash
# Run from project root
cd /path/to/project/root
python -m grpo_training.generator1 ...
```

## 📈 Monitoring Progress | 监控进度

All scripts use `tqdm` progress bars for real-time monitoring:
所有脚本都使用 `tqdm` 进度条实时监控：

```
generator_1: 100%|██████████| 30/30 [15:30<00:00, 31.00s/it]
  generator_1: μ=0.456, σ=0.089 → Extract (σ>τ)
    ✅ Saved: Prioritize edge case validation in complex graph structures...
```

## 🔗 Related Files | 相关文件

- `engine/api_manager.py`: API key management | API密钥管理
- `engine/reward_evaluator.py`: Reward computation | 奖励计算
- `engine/scaffolder.py`: Causal scaffolding | 因果脚手架
- `prompts/generator_experience_extraction.txt`: Generator prompt | Generator提示词
- `prompts/critic_experience_extraction.txt`: Critic prompt | Critic提示词

## 📚 Documentation | 文档

For more details, see:
详细文档请参考：

- `doc/设计方案.md`: Design specification | 设计说明
- `TRAINING_GUIDE.md`: Training guide | 训练指南
- `README.md`: Main project README | 主项目README

## ⚖️ License | 许可证

See project root LICENSE file.

