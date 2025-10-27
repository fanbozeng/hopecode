# Release Notes

Date: 2025-10-26

This release focuses on three themes: (1) removing unused symbolic-execution code paths to simplify operations, (2) making GRPO training faster and more configurable, and (3) improving evaluation readability and documentation. Summary below.

## Added
- train_with_grpo.py
  - New CLI flags to control concurrency
    - `--gen-exec {parallel|serial}`: execute the 3 generators in parallel or serial (default: parallel)
    - `--rollout-exec {parallel|serial}`: execute per‑generator N rollouts in parallel or serial (default: parallel)
  - Prints the effective execution modes during startup
- engine/multi_agent_scaffolder.py
  - generate_scaffold_for_grpo_training now supports optional parallel execution
    - Parallel across generators when `parallel_generators = True`
    - Parallel inside each generator when `parallel_rollouts = True`
    - Both attributes are set by the trainer script if present; safe fallback to serial
  - Keeps the original serial code path if parallel is disabled or errors occur
- Documentation and artifacts
  - `doc/cr.md`: GRPO code review against the architecture documents
  - `doc/REDUNDANT_CODE_AUDIT.md`: audit of redundant/unused modules and suggested cleanup order
  - `passage.mD`: paper‑style write‑up (Abstract, Intro, Related Work, Method, Experiments, Conclusion)

## Changed
- evaluate_framework.py
  - Enriched docstrings and inline comments for dataset loaders, evaluator, and comparison printing
  - Removed duplicated `ArgumentParser` creation, clarified CLI entry
  - Kept public API and result schema stable
- main.py
  - Forced computation to LLM mode (symbolic execution removed); prints computation mode consistently
  - Retains vector‑RAG retriever path and traditional retriever fallback

## Removed
- engine/code_generator.py (unused after removing symbolic execution)
- engine/sandbox_executor.py (unused after removing symbolic execution)
- engine/__init__.py no longer exports CodeGenerator/SandboxExecutor

## Performance and Training
- GRPO training speed‑ups via concurrency controls
  - Parallel across 3 generators reduces total wall‑clock time (subject to API rate limits)
  - Parallel inside each generator for N rollouts further accelerates per‑problem processing
- Safe fallbacks
  - If parallel branches error or attributes are missing, scaffolder falls back to the original serial flow

## Upgrade Notes
- Computation mode
  - The pipeline no longer generates/executes Python code for symbolic math. All computation uses `LLMComputer` with structured prompts
- Concurrency
  - New flags: `--gen-exec`, `--rollout-exec` in `train_with_grpo.py`
  - Ensure API provider quotas/concurrency limits are appropriate before using full parallel modes
- GRPO experience injection
  - Trainer injects experience manager and rollouts per generator into the multi‑agent scaffolder
  - If properties are missing in older scaffolder revisions, trainer ignores them safely

## Known Issues (to be addressed next)
- engine/__init__.py imports
  - Some import symbols still appear concatenated on one line; split into one import per line to avoid syntax/formatting hazards
- engine/grpo_trainer.py encoding/indentation
  - File contains mojibake/encoding artifacts and an improperly nested `except` block around the numeric fallback comparison. While training flow runs in many cases, a full pass to normalize encoding and fix try/except indentation is recommended
- Fraction strings in scaffolds
  - `_extract_json` may quote bare fractions (e.g., `1/3` → `"1/3"`). Numeric consumers (e.g., counterfactual doubling) should convert to numeric before arithmetic

## How to Use New Concurrency Options
- Parallel generators + parallel rollouts (default)
  - `python train_with_grpo.py --epochs 3 --group-size 3`
- Serial generators + parallel rollouts
  - `python train_with_grpo.py --gen-exec serial --rollout-exec parallel --epochs 3 --group-size 3`
- Parallel generators + serial rollouts
  - `python train_with_grpo.py --gen-exec parallel --rollout-exec serial --epochs 3 --group-size 3`
- Fully serial (max stability, slowest)
  - `python train_with_grpo.py --gen-exec serial --rollout-exec serial --epochs 3 --group-size 3`

## File Inventory (modified/new)
- New: `doc/cr.md`, `doc/REDUNDANT_CODE_AUDIT.md`, `passage.mD`, `release.md`
- Removed: `engine/code_generator.py`, `engine/sandbox_executor.py`
- Modified: `train_with_grpo.py`, `engine/multi_agent_scaffolder.py`, `evaluate_framework.py`, `main.py`, `engine/__init__.py` (exports cleaned)

## Next Steps
- Split and normalize problematic imports in `engine/__init__.py`
- Normalize encoding and indentation in `engine/grpo_trainer.py`; extract shared answer‑comparison helper to a utility for reuse by trainer and evaluator
- Optional: add max‑workers CLI flags to cap parallel thread pools for generators/rollouts

