# 冗余代码与可清理项审计（Redundant Code Audit)

本报告基于当前仓库代码与引用关系，列出疑似冗余/未被调用的代码与“死代码路径”，并给出清理建议。目标是在不破坏现有功能的前提下，减小体积、降低复杂度、避免混淆。

> 说明：结论以静态检索和现有调用路径为依据；如某些文件在你本地工作流或外部脚本中使用，请按需保留。

## A. 明确未被引用的模块（可移除或移至 experimental）

- engine/scaffolder_enhanced.py:1
  - 现状：未在仓库其他代码处被导入，引用仅出现在文档中。
  - 建议：如无后续计划，移除；或移动到 `experimental/` 并注明状态。

- engine/executor_enhanced.py:1
  - 现状：未在仓库其他代码处被导入，引用仅出现在文档中。
  - 建议：同上，移除或移至 `experimental/`。

- engine/causal_visualizer.py:1
  - 现状：无外部调用；`engine/causal_graph_visualizer.py` 才是实际在 `main.py` 与 `batch_evaluator.py` 中使用的可视化工具。
  - 建议：如不需要图片可视化 demo，移除；保留 `causal_graph_visualizer.py`。

- engine/answer_type_detector.py:1
  - 现状：未被运行时代码导入使用；只在某些维护文档中提及。
  - 建议：如评估/比对不依赖此模块，移除或合并到评估工具中；否则在使用处显式接入。

## B. 死代码路径与历史遗留引用

- main.py:314, main.py:325
  - 症状：仍存在对 `code_generator` 与 `sandbox_executor` 的调用语句，但对应模块已移除；当前分支通过 `if False` 规避执行。
  - 风险：增加阅读负担，误导维护者；若误改条件可能直接运行时报错。
  - 建议：删除整段“符号执行模式”死代码；若需保留文档性描述，改为注释性链接到历史版本。

- engine/executor.py:18
  - 现状：当前系统已强制 LLM 计算模式，未走符号执行路径；该类被初始化为“兼容占位”。
  - 建议：若“符号执行”已明确不再支持，移除初始化与模块；保留说明到迁移指南。若未来可能恢复，可将其标注为 deprecated 并从默认流程剥离。

## C. 工具/脚本类文件（按需保留）

- build_vector_cache.py:1
  - 说明：用于离线构建向量检索缓存；非主流程必需。
  - 建议：若团队固定使用在线编码，可改为文档化步骤；否则保留。

- test_grpo_system.py:1
  - 说明：GRPO 测试脚本；非主流程。
  - 建议：保留（有价值的集成回归）。

## D. 有用但易混的模块（保留）

- engine/causal_graph_visualizer.py:1
  - 现状：被 `main.py:281`, `batch_evaluator.py:110` 条件使用，属于“可选可视化”。
  - 建议：保留；在 README/指南中说明何时启用（例如调试/分析时）。

- engine/vector_retriever.py:1, main.py:120-128
  - 说明：基于语义相似度的 RAG 检索组件；主流程可选使用（已具备切换能力）。
  - 建议：保留并在 CLI/配置中明确切换参数与依赖。

- engine/ai_retriever.py:1, engine/domain_keywords.py:738
  - 说明：AI 检索器使用领域关键词等工具；在“规则不足时”作为补充路径。
  - 建议：保留。

## E. 引入与导出（需修复的语法/风格问题）

- engine/__init__.py:21, engine/__init__.py:30-31
  - 问题：多条 import/导出挤在同一行（语法风险），与部分维护文档“已修复”的描述不符。
  - 建议：
    - 每个 import 独立一行：
      - `from .llm_computer import LLMComputer`
      - `from .question_augmentor import QuestionAugmentor`
      - `from .grpo_experience_manager import GRPOExperienceManager`
      - `from .grpo_trainer import TrainingFreeGRPOTrainer`
    - `__all__` 中每个符号独立一行，`]` 独占一行。

## F. GRPO 相关实现一致性检查（与文档对齐）

- 已实现（建议保留）：
  - `engine/multi_agent_scaffolder.py:46-74` 新增 `rollouts_per_generator`。
  - `engine/multi_agent_scaffolder.py:274-359` 新增 `generate_scaffold_for_grpo_training(...)`，按生成器多 rollouts → 单独融合。
  - `engine/grpo_trainer.py:72-85` 训练器内注入 `experience_manager` 与同步 `rollouts_per_generator`。
  - `engine/grpo_trainer.py:275-278` 训练器改为调用 GRPO 接口。

- 待完善（不阻断运行，但建议提升）：
  - `engine/grpo_trainer.py:295-301` 仅以 `target_variable` 代替真实答案；建议改为 `LLMComputer.compute_from_scaffold` 执行并用统一的答案比较逻辑（可复用 `evaluate_framework.py` 的实现）。
  - `engine/grpo_trainer.py:277` 的 `retrieved_knowledge=[]` 可接入真实 RAG（向量/AI）以闭环训练。

## G. 建议的清理顺序（稳妥）

1) 删：main.py 中“符号执行模式”的整段死代码（含已删除模块的调用）。
2) 移：将 `scaffolder_enhanced.py`、`executor_enhanced.py`、`causal_visualizer.py`、`answer_type_detector.py` 转移到 `experimental/` 或 `archive/`；无计划回用则删除。
3) 修：规范 `engine/__init__.py` 的 import/导出格式，消除语法风险。
4) 补：在文档中补充“可选可视化/工具脚本”的使用说明，避免误解为主流程依赖。

---

如需，我可以基于以上清单提交一个“安全清理补丁”，默认只删除死代码与未引用模块，并将潜在实验性代码迁移到 `experimental/` 目录，保证主流程与评估脚本不受影响。

