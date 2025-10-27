# GRPO 相关代码 Code Review（基于架构文档）

本文对目前仓库中 GRPO 相关实现进行代码审查，并对照文档《GRPO新架构说明.md》《训练自由GRPO使用指南.md》给出偏差点、证据与修复建议。审查重点文件：

- engine/multi_agent_scaffolder.py
- engine/grpo_trainer.py
- engine/grpo_experience_manager.py
- engine/__init__.py
- main.py

## 总体结论

- 文档定义的“每个 Generator 生成多次 rollouts、Critic 对该 Generator 的 rollouts 独立融合、分别评估与更新经验库”的新架构未在代码中实现。当前仍是“三个并行生成器各产出一个 proposal → 批判者一次性融合为单个结果”的旧流程。
- GRPO 训练器与引擎对接存在两个明显错误：`solve_problem` 入参类型不符（传了 dict 而非字符串）、结果字段名错误（读取了不存在的 `scaffold` 键）。
- engine/__init__.py 存在合并多条 import/导出到同一行的语法问题，极易导致初始化阶段报错。
- 经验注入路径未闭环：Scaffolder 支持注入经验，但默认初始化路径未将 `GRPOExperienceManager` 注入，导致经验始终不生效。
- 若按文档开启 GRPO 训练，目前在“多 rollouts/按 Generator 融合/经验更新”的关键路径上将无法达到预期。

## 关键偏差与证据

### 1) 按 Generator 的多 rollouts 与独立融合：未实现

- 文档：每个 Generator 先生成 `rollouts_per_generator` 次 rollouts，随后 Critic 对该 Generator 的 rollouts 融合一次，得到 3 个融合结果（每个 Generator 一个），之后分别评估与更新对应经验库。
- 代码：当前只有 `generate_scaffold_parallel(...)`（engine/multi_agent_scaffolder.py:192），调用 `_parallel_generate`（264）各 Generator 各产出一个 proposal，随后 `_critic_fusion`（407）一次性融合所有 proposal，返回单结果。没有“按 Generator 多 rollouts → 单独融合”的 GRPO 模式接口。

结论：需要新增 `rollouts_per_generator` 参数与 `generate_scaffold_for_grpo_training(...)` 接口，按文档语义产出每个 Generator 的多 rollouts 与其融合后的 scaffold。

### 2) 训练器与引擎对接错误（入参与字段）

- 入参类型错误：engine/grpo_trainer.py:357 调用 `self.engine.solve_problem(problem_data)`，而引擎方法签名期望的是问题字符串。应当传 `problem_data['problem']`。
- 字段名错误：engine/grpo_trainer.py:371 读取 `result.get('scaffold', {})`，但主引擎输出的关键键为 `causal_scaffold`（生成后）与 `executed_scaffold`（执行增强后），不存在 `scaffold` 键名。

结论：这两处会导致训练流程“空转/报错”，需更正为字符串入参与正确的字段键名。

### 3) 经验注入路径未闭环

- Scaffolder 内部已支持经验注入（engine/multi_agent_scaffolder.py:338、437 使用 `experience_manager.get_experiences_for_agent(...)`）。
- 但默认引擎初始化（main.py:152）未传入 `experience_manager`，训练器也未确保注入，导致生成器/批判者提示中不会出现任何已学经验。

结论：应在 Trainer 初始化时确保 `self.engine.scaffolder.experience_manager = experience_manager`，或在构造 Scaffolder 时传入。

### 4) engine/__init__.py 语法问题

- 合并多条 import/导出到同一行（engine/__init__.py:21、30）会导致 Python 语法错误或覆盖。典型示例：

  - engine/__init__.py:21 包含多条 `from .<module> import <symbol>` 串在一行。
  - engine/__init__.py:30-31 的 `__all__` 也被挤在同一行，符号之间无逗号分隔/换行不规范。

结论：需拆分为多行，逐条 import/导出，避免初始化时报错（这也是“评估时报错一堆”的高概率根因之一）。

### 5) 结果比对方式脆弱（与评估框架不一致）

- engine/grpo_trainer.py:404 起 `_compare_answers` 仅做字符串/浮点相等判断，无法覆盖单位、科学计数法、格式差异等常见情况。
- evaluate_framework.py 中已有较为稳健的“LLM 判定 + 规则回退”方案（见 `evaluate_framework.py:762` 一段）。

结论：建议抽取评估框架的比较逻辑为公共工具，Trainer 复用，保证口径一致。

### 6) 日志编码显示“�?”

- 多数模块日志存在 `�?` 字符（编码不一致/不可见字符），影响可读性与排障效率（multi_agent_scaffolder、grpo_trainer 等多处）。

结论：统一 UTF-8，无 BOM，清理不可见字符；或统一英文日志。

## 逐文件问题与建议

### engine/multi_agent_scaffolder.py

- 已有：并行 3 个生成器 + 1 批判者的“单次融合”流程；经验注入接口；生成/融合日志。
- 缺失：GRPO 训练模式所需的：
  - `rollouts_per_generator: int`（默认 3）
  - `generate_scaffold_for_grpo_training(problem_text, retrieved_knowledge)`：
    - 对每个 generator：循环 `rollouts_per_generator` 调用 `_single_agent_generate(...)` 产生多 rollouts；
    - 将该 generator 的 rollouts 输入 `_critic_fusion(...)`，仅融合该 generator 的 rollouts；
    - 返回列表元素结构：`{ agent_id, rollouts: List[scaffold], fused_scaffold: Dict, num_rollouts }`。
- 建议：
  - 在类初始化中新增 `rollouts_per_generator`；
  - 新增上述方法，不破坏现有 `generate_scaffold_parallel` 的行为；
  - 将 `generation_log` 细化为可按 generator/attempt 聚合，便于 GRPO 统计。

### engine/grpo_trainer.py

- 入参与字段：
  - 357 行：`self.engine.solve_problem(problem_data)` → `self.engine.solve_problem(problem_data['problem'], include_validation=False, problem_id=..., method_name=...)`
  - 371 行：`result.get('scaffold', {})` → 优先使用 `result.get('executed_scaffold') or result.get('causal_scaffold')`
- 多 rollouts：
  - 目前 `_generate_group_rollouts` 只产出 1 条“final”，非 GRPO 语义。
  - 建议：调用 `engine.scaffolder.generate_scaffold_for_grpo_training(...)`，拿到每个 generator 的 `{rollouts, fused_scaffold}`，随后：
    - 用 `LLMComputer.compute_from_scaffold(fused_scaffold, problem_text)` 计算答案与 reward；
    - 写入 `{ agent_id, rollouts, fused_scaffold, answer, reward }`；
    - 分别调用 `_apply_experience_operations(..., agent_type=f'generator_{agent_id}')` 更新经验；
    - 最后基于三者表现更新 critic 经验（例如合并成功率、常见错误等）。
- 答案比较：
  - 用公共工具替换 `_compare_answers` 简化版，或直接复用 evaluate 框架逻辑。
- 注入经验：
  - 在 `__init__` 或 `train()` 开始处确保：`self.engine.scaffolder.experience_manager = self.experience_manager`。
- 稳健性：
  - `_parse_experience_operations`：优先解析 ```json fenced block```；失败再回退“最大 JSON 子串”；加上失败详情日志。

### engine/grpo_experience_manager.py

- 结构设计合理，JSON 序列化清晰。
- 建议：
  - `get_experiences_for_agent(..., format_as_prompt=True)` 的 Prompt 可增加“如何使用/限制”的简短英文 bullet，避免无约束地拼贴导致提示冗长。
  - 添加简单的去重/合并策略（按 `content` 相似度或完全相同合并）。

### engine/__init__.py

- 语法错误：多条 import、`__all__` 条目被挤在同一行（21、30-31），应逐条拆分。
- 确保 `VectorKnowledgeRetriever`、`GRPOExperienceManager`、`TrainingFreeGRPOTrainer` 等导出在多行，结尾 `]` 独占一行。

### main.py

- 如需在推理/评估阶段体验 GRPO 效果，应通过 CLI 或外部参数注入经验管理器：
  - 初始化 `experience_manager = GRPOExperienceManager(...)`；
  - `engine = CausalReasoningEngine(..., use_multi_agent=True)` 后执行注入：
    - `engine.scaffolder.experience_manager = experience_manager`
- 当前并未提供 CLI 参数控制以上行为，若需要评估对比（有/无经验），建议在评估脚本侧注入。

## 优先级修复清单（建议顺序）

1) 修复致命错误：
- 拆分 engine/__init__.py 的多行 import 与 `__all__`，保证正常导入。
- 更正 grpo_trainer 中 `solve_problem` 入参与 `scaffold` 字段名。

2) 实现 GRPO 训练模式最小闭环：
- 在 MultiAgentScaffolder 新增 `rollouts_per_generator` 与 `generate_scaffold_for_grpo_training(...)`；
- 在 Trainer 中按 Generator 聚合：计算答案/奖励 → 更新对应经验 → 更新 critic 经验；
- 在 Trainer 初始化时确保注入 `experience_manager`。

3) 提升正确性与一致性：
- 将答案比较逻辑抽取为公共工具（复用 evaluate 框架）；
- 统一日志编码与消息文本；
- 为 GRPO 训练新增最小的回归用例（见下）。

## API / 数据结构建议（与文档对齐）

### MultiAgentScaffolder

```python
class MultiAgentScaffolder:
    def __init__(..., rollouts_per_generator: int = 3, ...):
        self.rollouts_per_generator = rollouts_per_generator

    def generate_scaffold_for_grpo_training(
        self,
        problem_text: str,
        retrieved_knowledge: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Returns: [
          {
            'agent_id': int,
            'rollouts': List[Dict],       # 原始单次脚手架
            'fused_scaffold': Dict,       # 该 generator 的融合结果
            'num_rollouts': int
          }, ...  # 3 个元素
        ]
        """
```

### Trainer 中每个 generator 的评估结果

```python
{
  'agent_id': 1,
  'rollouts': [...],
  'fused_scaffold': {...},
  'answer': '...',
  'reward': True/False
}
```

## 验收建议 / 回归测试

- 单题烟雾测试：构造一个有确定答案的物理/数学题；验证：
  - `generate_scaffold_for_grpo_training` 返回 3 个 generator 结果；每个包含 `num_rollouts==rollouts_per_generator`；
  - Trainer 能对 3 个生成结果分别计算答案/奖励；
  - 经验库 JSON 在对应 `generator_1/2/3` 中新增或修改条目；
  - Critic 经验库有更新；
  - 训练日志中可见“逐 generator 融合/评估/更新”的完整链路。

## 可选优化

- 经验库去重/合并：根据 `content` 相似度合并重复项，提升密度与可读性。
- 经验成功率与使用频率驱动的排序/裁剪：推理时优先注入高质量经验。
- 训练时速率控制与失败重试（LLM API）：在 GRPO 多 rollouts 中尤为重要。
- 将评估框架的“使用经验 vs 不使用经验”对比脚本化，便于量化收益。

## 与《GRPO新架构说明.md》的对齐清单

- [ ] MultiAgentScaffolder：实现 `rollouts_per_generator` 与 `generate_scaffold_for_grpo_training`（文档已定义）
- [ ] Trainer：调用 GRPO 接口、按 Generator 评估/更新经验（文档定义的 `_evaluate_generator_results` / `_update_experiences_per_generator` 思路）
- [ ] main / 训练脚本：设置 `rollouts_per_generator = group_size`，并注入 `experience_manager`
- [ ] 结果存储与日志：输出逐 Generator 的融合结果、答案与奖励（与文档示例一致）

---

如需，我可以在上述清单基础上提交一版“最小改动补丁”，先让 GRPO 训练模式跑通，并附带一个简短的训练/验证示例脚本。

