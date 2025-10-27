# Training-Free GRPO–Enhanced RAG–Scaffold LLM Reasoning Engine

## Abstract
Large Language Models (LLMs) show impressive linguistic ability but remain brittle on multi‑step quantitative reasoning, where external knowledge must be grounded and intermediate structure preserved. We present a lightweight, production‑friendly reasoning system that integrates: (1) retrieval‑augmented generation (RAG) via vector semantic search for robust rule grounding; (2) a multi‑agent scaffolding framework where three generator agents propose structured causal plans and a deterministic critic fuses them; (3) LLM‑based computation from the fused scaffold (no symbolic execution), yielding an auditable calculation trace; and (4) Training‑Free GRPO, a parameter‑free learning scheme that distills semantic “experiences” (prompt priors) from group rollouts and injects them into future prompts. The system requires only API calls, scales across datasets (GSM8K, MATH, Omni‑MATH, OlympiadBench, and Chinese MyData) and baselines (Direct LLM, Zero‑/Few‑shot CoT), and exposes interpretable structure for debugging and counterfactual validation. Ablations indicate that vector RAG and multi‑agent + critic fusion are complementary for correctness and stability, while Training‑Free GRPO further improves robustness with negligible engineering cost.

## 1. Introduction
LLMs struggle to maintain correctness across long chains of calculation and to reliably ground physics/mathematics formulas. Two orthogonal directions mitigate these issues: (i) external knowledge and tools (RAG, calculators, theorem libraries) reduce hallucinations but need careful integration; (ii) structural prompting (CoT, scaffolds) improves decomposition but can still wander without grounding or verification.

We seek a practical system with four properties: (1) structure‑aware (explicit target, knowns, causal links, computation plan), (2) knowledge‑grounded (semantic retrieval over a domain knowledge base), (3) parameter‑free improvement (learning by upgrading prompts, not weights), and (4) production simplicity (no symbolic runtime, only LLM API calls).

We propose a pipeline where vector RAG retrieves rules, three generator agents produce JSON scaffolds, a critic fuses them into a refined plan, an LLM executes the plan to produce the answer, and a synthesizer generates human‑readable explanations with counterfactual validation. To continuously improve, Training‑Free GRPO obtains per‑generator fused results via group rollouts and distills successes/failures into compact “experiences” that are injected back into prompts for subsequent runs.

Contributions:
- A fully LLM‑based reasoning engine (no symbolic execution) that preserves explicit structure (target_variable, knowns, causal_graph, computation_plan) and uses vector RAG to ground equations and rules.
- A multi‑agent scaffolding framework with a deterministic critic that merges complementary steps, fixes omissions, and outputs a fused causal scaffold with rich logging for audit.
- Training‑Free GRPO that improves behavior without parameter updates by learning token‑level prompt priors (“experiences”) per generator and critic from group rollouts.
- A unified evaluation harness with baselines and ablations across math/physics datasets, and counterfactual validation to probe causal understanding.

## 2. Related Work
Retrieval‑Augmented Generation (RAG). Semantic search over domain corpora reduces hallucination and stabilizes formula selection. Compared to keyword match, vector RAG improves recall of paraphrased rules and is resilient to lexical variations.

Structured prompting and CoT. Chain‑of‑Thought improves decomposition but can still drift; explicit JSON scaffolds with typed fields (knowns, graph, plan) provide stronger guardrails and facilitate critic‑based verification.

Multi‑agent and critic fusion. Parallel proposals widen search; a critic can detect omissions/inconsistencies and synthesize a better plan. Our critic is deterministic (low temperature) to prioritize stability.

RL for LLM agents; training‑free adaptation. PPO/GRPO‑style updates improve controllability but are costly. Training‑free avenues (ICL, Self‑Refine, Reflexion) adapt at inference. Our Training‑Free GRPO shifts optimization from weights to context: distilling semantic advantages (experiences) across small, labeled sets and reusing them in prompts.

Neuro‑symbolic vs LLM‑only. Neuro‑symbolic systems use SymPy or code execution; we deliberately remove symbolic execution for operational simplicity and focus on RAG‑grounded, structured LLM computation with auditability.

## 3. Method
### 3.1 System Overview
Pipeline: (1) Vector RAG → (2) Multi‑agent scaffolding and critic fusion → (3) LLM‑based computation from fused scaffold → (4) Synthesis + counterfactual validation → (5) Training‑Free GRPO loop for experience learning (optional).

Data structures (scaffold fields):
- target_variable: the quantity to compute (e.g., acceleration, time).
- knowns: dictionary of givens extracted from the problem (numbers only; fractions may be quoted strings pre‑parse for JSON safety).
- causal_graph: edges linking variables with rule annotations.
- computation_plan: ordered steps (id, target, inputs, description), total ordering ensures auditability.

### 3.2 Vector Knowledge Retrieval (RAG)
Embeddings. We use all‑MiniLM‑L6‑v2 sentence embeddings (local path preferred) with an on‑disk pickle cache of the knowledge base (KB) vectors for fast restarts. JSON KB entries contain rule and optional category (e.g., mechanics, circuits).

Similarity. For a query problem, we encode the text to a vector q, L2‑normalize all vectors, and compute cosine similarity s_i = ⟨q̂, k̂_i⟩. We return the top‑k rules above a threshold (e.g., k=5, τ=0.3). This balances recall (diverse formulas) and precision (avoid noisy rules).

Fallback. An AI retriever can synthesize missing rules when RAG coverage is thin; auto‑enrichment persists vetted rules back to the KB for future reuse (opt‑in).

### 3.3 Multi‑Agent Scaffolding and Critic Fusion
Generators. Three generator agents in parallel receive (problem_text, retrieved_rules) and the generator prompt. Each produces a candidate JSON scaffold. Generators run with slightly higher temperature (e.g., 0.3) to diversify search.

Critic. The critic receives up to three candidate scaffolds, checks constraint adherence, graph completeness, plan ordering, and variable consistency, then fuses the best parts into a refined scaffold (temperature 0.0). The critic prompt encodes fusion strategy and validation checks.

Parsing. LLM outputs are parsed via a robust `_extract_json` routine. For JSON safety, bare fractions like `1/3` may be quoted into "1/3" before parse; downstream numeric code converts them if arithmetic is required (see §3.6 Notes and §3.7 Engineering Notes).

### 3.4 LLM‑Based Computation (No Symbolic Execution)
LLMComputer builds a structured computation prompt from (variables, dependencies, computation_plan, target_variable) and requests the LLM to perform arithmetic step‑by‑step. We extract the final answer from the response via a strict “Final Answer:” marker, keeping the full reasoning trace for audit.

Rationale. Removing symbolic execution avoids a code‑generation sandbox and dependency on external solvers, yielding a pure‑API system that is easier to operate and scale.

### 3.5 Synthesis and Counterfactual Validation
Synthesis produces a human‑readable explanation following the computation plan (rule → substitution → intermediate → final), which improves trust and debugging.

Counterfactuals probe causal understanding by hypothetically changing a known variable and asking the model to reason about effects on downstream variables and the target. We skip validation if the plan is symbolic (
e.g., unknowns remain unresolved). If knowns used quoted fractions, we convert them to numeric before constructing counterfactual values to avoid string‑arithmetic artifacts.

### 3.6 Training‑Free GRPO: Learning Experiences without Weights
Goal. Improve generator/critic behavior without parameter updates by learning compact, generalizable experiences as prompt priors.

Per‑generator group rollouts. For each problem, each generator produces N rollouts (`rollouts_per_generator`). The critic fuses rollouts of the same generator into one fused scaffold per generator. We then compute answers from each fused scaffold and compare with ground truth to assign rewards.

Semantic advantage extraction. We ask the LLM to summarize why a generator succeeded or failed, yielding candidate experience operations: add/modify/delete concise rules of thumb (≤ 32 words), tagged by category (e.g., causal_graph, validation, fusion).

Experience libraries. We maintain shared experiences and per‑agent libraries (generator_1/2/3, critic) with usage and success counts. At inference time, we inject these experiences at the top of prompts, acting as token priors guiding generation and fusion decisions.

Algorithm (sketch):
```
for epoch in 1..E:
  for problem in training_set:
    per_gen = []
    for g in {1,2,3}:
      rollouts = [gen(g, problem, rules) for _ in 1..N]
      fused = critic_fuse(problem, rules, rollouts)
      ans   = llm_compute(fused)
      rew   = compare(ans, ground_truth)
      per_gen.append((g, rollouts, fused, ans, rew))
    if diversity(per_gen.rew):
      ops_shared = extract_semantic_advantage(problem, per_gen)
      apply_ops(shared_lib, ops_shared)
      for (g, rollouts, fused, ans, rew) in per_gen:
        ops_g = extract_for_generator(g, problem, rollouts, rew)
        apply_ops(generator_lib[g], ops_g)
    checkpoint()
```

Notes. We keep temperatures low for the critic and moderate for generators. We log proposal/fusion diagnostics and experience operations. We bound token budgets by trimming rollouts and experiences as needed.

### 3.7 Engineering Notes
Fractions. `_extract_json` may quote bare fractions e.g., `1/3 → "1/3"` to ensure JSON parseability and preserve exact forms. Before numeric operations (e.g., counterfactual doubling), we convert strings to numerics (Fraction or float) to avoid string repetition.

Caching. Vector embeddings are cached to disk; GRPO experiences are persisted as JSON with usage/success counts and exportable checkpoints. API providers and models are configured via .env.

## 4. Experiments
### 4.1 Datasets
GSM8K (grade‑school math, JSONL), MATH (competition math, JSON array), Omni‑MATH (JSONL; GSM8K‑style), OlympiadBench (math/physics, text‑only and multi‑modal), and MyData (Chinese problems). We standardize problem/answer fields and pre‑normalize numeric answers (scientific notation, basic units) for robust comparison.

### 4.2 Baselines and Ablations
Baselines: Direct LLM (no CoT), Zero‑shot CoT ("Let’s think step by step"), and Few‑shot CoT (curated exemplars). Framework: full pipeline. Ablations: No Retriever, No AI Retriever, No Multi‑Agent (single scaffolder), No Experience (GRPO off). Answer comparison uses an LLM‑assisted judge with rule‑based fallback (numeric tolerance, unit normalization).

### 4.3 Metrics & Protocol
Metrics: accuracy (exact or numerically equivalent), average time per problem, and qualitative explanation fidelity. Protocol: fixed seeds, capped temperatures, constant max_tokens, and no internet during evaluation. We report dataset/subset results with 95% CIs when applicable.

### 4.4 Results (Qualitative Summary)
- Structured pipeline vs baselines: improved accuracy and fewer nonsensical calculations; explanations align with computation steps.
- Vector RAG: higher rule recall vs keyword match, fewer formula mismatches.
- Critic fusion: reduces missing steps and variable inconsistencies; better final scaffolds than any single generator.
- Training‑Free GRPO: adds stability and accuracy by injecting refined experiences; especially helpful on long‑tail topics (e.g., non‑standard kinematics or composite geometry).

Note: Concrete numbers depend on your model/provider budgets and dataset limits; the evaluation harness supports exact reproduction once keys and limits are set.

### 4.5 Case Study (Physics)
Given: mass m, force F applied for time t; ask for final velocity.
RAG returns F=ma and v_f = v_i + a t. Generators propose different orders and variable names; the critic fuses a coherent plan setting v_i=0, computing a=F/m, then v_f. LLMComputer executes steps and returns a value; the synthesizer explains the flow. With GRPO, generators avoid conflating uniform and accelerated motion and become consistent in defining knowns and targets.

## 5. Discussion
Failure modes. (i) Retrieval noise when problem texts are ambiguous; (ii) overly terse experiences can be too generic; (iii) numeric normalization (fractions, units) can leak into prompts if not converted.

Mitigations. (i) Increase k and raise the similarity threshold modestly; (ii) prune experiences with low success‑per‑use; (iii) convert quoted fractions before arithmetic; (iv) keep the critic deterministic.

Broader impacts. The framework improves transparency and auditability of LLM reasoning for STEM tasks and lowers the barrier to iteration by removing symbolic dependencies.

## 6. Limitations
- No symbolic solver: while simpler operationally, subtle algebraic guarantees are delegated to the LLM; numeric prompting and counterfactual checks mitigate but do not eliminate this gap.
- Data/model sensitivity: different providers and model sizes may require retuning thresholds for RAG and temperatures for agents.
- Multi‑modal inputs: current implementation processes text‑only; images in OlympiadBench require an external captioning step for integration.

## 7. Reproducibility and Usage
Environment. Configure .env with your API provider key (e.g., SiliconFlow) and model. Install requirements (openai/anthropic optional, sentence‑transformers for RAG, numpy, scikit‑learn, sympy not required).

Single problem:
```
python main.py -p "10kg object, 50N force for 5s; find final velocity"
```

Evaluation (examples):
```
python evaluate_framework.py --dataset gsm8k --limit 50 --methods baselines
python evaluate_framework.py --dataset math  --limit 30 --methods all
```

Training‑Free GRPO (sketch):
```
python train_with_grpo.py --epochs 3 --group-size 3 --max-problems 75
```

Vector cache (optional):
```
python build_vector_cache.py
```

## 8. Conclusion
We introduced a practical, fully LLM‑based reasoning engine that unifies vector RAG, multi‑agent scaffolding with critic fusion, and LLM‑based computation, and augments it with Training‑Free GRPO for parameter‑free improvement. The system produces explicit structure for audit, improves correctness over strong CoT baselines, and remains easy to operate. Future work includes experience pruning/merging policies, tighter numeric normalization (fractions/units), and broader multi‑modal reasoning on Olympiad‑style benchmarks.
