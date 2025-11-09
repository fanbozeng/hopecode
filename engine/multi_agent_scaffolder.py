"""
Multi-Agent Causal Scaffolding Module
多智能体因果脚手架模块

This module implements a multi-agent system for causal graph generation:
- 3 parallel LLM agents generate causal graphs independently
- 1 critic agent reviews, merges, and refines the results

此模块实现了用于因果图生成的多智能体系统：
- 3个并行LLM智能体独立生成因果图
- 1个批判者智能体审查、融合和精炼结果
"""

import json
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Import base scaffolder
from engine.scaffolder import LLMClient, CausalScaffolder


class MultiAgentScaffolder:
    """
    Multi-Agent Causal Scaffolder with parallel generation and critic fusion.
    具有并行生成和批判融合的多智能体因果脚手架器

    Architecture:
    1. Three generator agents run in parallel to produce diverse causal graphs
    2. One critic agent evaluates, merges, and refines the outputs

    架构：
    1. 三个生成器智能体并行运行以产生多样化的因果图
    2. 一个批判者智能体评估、融合和精炼输出
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        num_generators: int = 3,
        generator_temperature: float = 0.3,  # Slightly higher for diversity
        critic_temperature: float = 0.0,  # Deterministic for stability
        max_retries: int = 3,
        retry_delay: float = 2.0,
        experience_manager=None,  # 新增：GRPO经验管理器 / Added: GRPO experience manager
        rollouts_per_generator: int = 1,  # 新增：每个generator生成的rollout数量 / Added: Number of rollouts per generator (for GRPO training)
        use_separate_apis: bool = True  # 新增：是否为每个agent使用独立API / Added: Use separate API for each agent
    ):
        """
        Initialize multi-agent scaffolder.
        初始化多智能体脚手架器

        Args:
            llm_client: Shared LLM client (used only if use_separate_apis=False)
                        共享的LLM客户端（仅在use_separate_apis=False时使用）
            num_generators: Number of parallel generator agents (default: 3)
                           并行生成器智能体的数量（默认：3）
            generator_temperature: Temperature for generator agents (for diversity)
                                  生成器智能体的温度（用于多样性）
            critic_temperature: Temperature for critic agent (deterministic)
                               批判者智能体的温度（确定性）
            max_retries: Maximum retry attempts
                        最大重试次数
            retry_delay: Delay between retries
                        重试之间的延迟
            experience_manager: GRPOExperienceManager instance for injecting learned experiences
                               GRPO经验管理器实例，用于注入学到的经验
            rollouts_per_generator: Number of rollouts each generator produces (for GRPO training)
                                   每个生成器产生的rollout数量（用于GRPO训练，默认1）
            use_separate_apis: Use separate API for each generator and critic
                              为每个生成器和批判者使用独立的API
        """
        self.num_generators = num_generators
        self.generator_temperature = generator_temperature
        self.critic_temperature = critic_temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_separate_apis = use_separate_apis
        
        # GRPO Experience Manager / GRPO经验管理器
        self.experience_manager = experience_manager
        
        # GRPO: Number of rollouts per generator / GRPO：每个生成器的rollout数量
        self.rollouts_per_generator = rollouts_per_generator

        # Initialize LLM clients for each agent / 为每个智能体初始化LLM客户端
        if use_separate_apis:
            self._init_separate_clients()
        else:
            # Use shared client / 使用共享客户端
            self.llm_client = llm_client or LLMClient()
            self.generator_clients = {i: self.llm_client for i in range(1, num_generators + 1)}
            self.critic_client = self.llm_client

        # Load prompts
        self.generator_prompt = self._load_prompt("prompts/scaffolding_prompt_v3.txt")
        self.critic_prompt = self._load_prompt("prompts/critic_fusion_prompt.txt")

        # Logs
        self.generation_log = []
        self.fusion_log = []

        print(f"🤖 Multi-Agent Scaffolder initialized:")
        print(f"   - {num_generators} parallel generators (T={generator_temperature})")
        if use_separate_apis:
            print(f"   - Using separate API for each generator ✓")
        if rollouts_per_generator > 1:
            print(f"   - {rollouts_per_generator} rollouts per generator (GRPO mode)")
        print(f"   - 1 critic agent (T={critic_temperature})")
        if experience_manager:
            print(f"   - Training-Free GRPO enabled ✓")
        print(f"🤖 多智能体脚手架器已初始化：")
        print(f"   - {num_generators}个并行生成器（温度={generator_temperature}）")
        if use_separate_apis:
            print(f"   - 每个生成器使用独立API ✓")
        if rollouts_per_generator > 1:
            print(f"   - 每个生成器{rollouts_per_generator}个rollouts（GRPO模式）")
        print(f"   - 1个批判者智能体（温度={critic_temperature}）")
        if experience_manager:
            print(f"   - 训练自由GRPO已启用 ✓")
    
    def _init_separate_clients(self) -> None:
        """
        Initialize separate LLM clients for each generator and critic.
        为每个生成器和批判者初始化独立的LLM客户端
        """
        from engine.api_manager import APIKeyManager
        from engine.scaffolder import LLMClient
        
        try:
            api_manager = APIKeyManager()
            
            # Initialize generator clients / 初始化生成器客户端
            self.generator_clients = {}
            for i in range(1, self.num_generators + 1):
                role = f'generator_{i}'
                try:
                    api_key = api_manager.get_api_key(role)
                    # Create client with API key
                    client = LLMClient()
                    # Override API key
                    if hasattr(client, 'client'):
                        client.client.api_key = api_key
                    self.generator_clients[i] = client
                    print(f"   ✓ Generator {i} API configured")
                except Exception as e:
                    print(f"   ⚠️  Generator {i} API config failed: {e}, using default")
                    self.generator_clients[i] = LLMClient()
            
            # Initialize critic client / 初始化批判者客户端
            try:
                critic_key = api_manager.get_api_key('critic')
                self.critic_client = LLMClient()
                if hasattr(self.critic_client, 'client'):
                    self.critic_client.client.api_key = critic_key
                print(f"   ✓ Critic API configured")
            except Exception as e:
                print(f"   ⚠️  Critic API config failed: {e}, using default")
                self.critic_client = LLMClient()
                
        except Exception as e:
            print(f"   ⚠️  API Manager initialization failed: {e}")
            print(f"   Using default LLM client for all agents")
            # Fallback to shared client
            default_client = LLMClient()
            self.generator_clients = {i: default_client for i in range(1, self.num_generators + 1)}
            self.critic_client = default_client
    
    def _load_agent_experiences(self, agent_id: str) -> str:
        """
        Load agent's own experiences from its experience file.
        从agent自己的经验文件加载经验
        
        Args:
            agent_id: Agent identifier (e.g., 'generator_1', 'generator_2', 'critic')
            
        Returns:
            Formatted experiences string for prompt
        """
        import json
        from pathlib import Path
        
        # Get absolute path to experience file
        project_root = Path(__file__).parent.parent
        exp_file = project_root / "data" / "grpo_experiences" / f"{agent_id}_experiences.json"
        
        if not exp_file.exists():
            return "No prior experiences available."
        
        try:
            with open(exp_file, 'r', encoding='utf-8') as f:
                experiences = json.load(f)
            
            if not experiences:
                return "No prior experiences available."
            
            # Format experiences as numbered list
            experiences_str = "\n".join(
                f"{i}. {exp['content']}" for i, exp in enumerate(experiences, 1)
            )
            
            return experiences_str
            
        except Exception as e:
            print(f"  ⚠️  Failed to load experiences for {agent_id}: {e}")
            return "No prior experiences available."

    def _load_prompt(self, path: str) -> str:
        """Load prompt template from file."""
        prompt_path = Path(path)
        
        # Try relative path first
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Try absolute path from project root
        project_root = Path(__file__).parent.parent
        absolute_path = project_root / prompt_path
        
        if absolute_path.exists():
            with open(absolute_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Fallback to default only for critic prompt
        if "critic" in path:
            return self._get_default_critic_prompt()
        
        # For generator prompt, raise error (must use file)
        raise FileNotFoundError(
            f"Generator prompt template not found at:\n"
            f"  - Relative path: {prompt_path}\n"
            f"  - Absolute path: {absolute_path}\n"
            f"Please ensure '{path}' exists in project root."
        )

    def _get_default_critic_prompt(self) -> str:
        """Get default critic fusion prompt."""
        return """**ROLE:**
You are a Meta-Critic for Causal Reasoning. You receive multiple causal graph proposals from different agents and your task is to:
1. Identify strengths and weaknesses in each proposal
2. Detect inconsistencies, errors, or missing elements
3. Merge the best ideas from all proposals into one coherent, correct solution
4. Ensure the final output is logically sound and complete

**INPUT:**
You will receive:
- The original problem
- Retrieved knowledge (formulas, rules)
- THREE causal graph proposals (JSON format) from different agents

**YOUR TASK:**
Analyze all three proposals critically and generate a SINGLE REFINED JSON that:
- Preserves correct elements from all proposals
- Fixes errors or inconsistencies
- Adds missing causal links if needed
- Ensures computational plan is complete and correct

---
**ORIGINAL PROBLEM:**
{problem_text}

**RETRIEVED KNOWLEDGE (from knowledge base):**
{retrieved_knowledge}

**PRIOR EXPERIENCES (learned from previous problems):**
{prior_experiences}

**PROPOSAL 1 (Agent 1):**
```json
{proposal_1}
```

**PROPOSAL 2 (Agent 2):**
```json
{proposal_2}
```

**PROPOSAL 3 (Agent 3):**
```json
{proposal_3}
```

---

**CRITICAL ANALYSIS PROTOCOL:**

1. **Constraint Adherence Check:**
   - Do all proposals correctly identify the problem constraints?
   - Are there any violations of stated conditions?

2. **Causal Graph Comparison:**
   - Which proposal has the most complete causal graph?
   - Are there missing causal links in any proposal?
   - Are there incorrect or redundant links?

3. **Computation Plan Evaluation:**
   - Which plan is most logically ordered?
   - Are all necessary steps included?
   - Are there any computational errors?

4. **Consistency Check:**
   - Do the knowns match across proposals?
   - Is the target_variable correctly identified?
   - Are variable names consistent?

5. **Fusion Strategy:**
   - Take the most accurate constraints_and_premises
   - Merge causal graphs to include all valid causal links
   - Create a refined computation_plan with correct ordering
   - Ensure all variables are properly defined

**OUTPUT:**
Generate a SINGLE refined JSON object following the same schema as the proposals. This should be the best possible synthesis of all three inputs.

**REFINED JSON OUTPUT:**
"""

    def generate_scaffold_parallel(
        self,
        problem_text: str,
        retrieved_knowledge: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate causal scaffold using multi-agent parallel system.
        使用多智能体并行系统生成因果脚手架

        Process:
        1. Launch 3 generator agents in parallel (each loads its own experiences)
        2. Collect all proposals
        3. Send to critic for fusion (critic loads its own experiences)
        4. Return refined result

        流程：
        1. 并行启动3个生成器智能体（各自加载自己的经验）
        2. 收集所有提案
        3. 发送给批判者进行融合（批判者加载自己的经验）
        4. 返回精炼结果

        Args:
            problem_text: Problem statement
            retrieved_knowledge: List of relevant formulas/rules (from RAG)

        Returns:
            Refined causal scaffold JSON
        """
        print("\n" + "="*80)
        print("🚀 MULTI-AGENT CAUSAL SCAFFOLDING STARTED")
        print("🚀 多智能体因果脚手架生成开始")
        print("="*80 + "\n")

        # Step 1: Parallel generation by 3 agents
        print(f"📊 Phase 1: Parallel Generation ({self.num_generators} agents)")
        print(f"📊 阶段1：并行生成（{self.num_generators}个智能体）")
        print("-" * 80)

        proposals = self._parallel_generate(problem_text, retrieved_knowledge)

        if len(proposals) == 0:
            print("\n❌ No valid proposals generated by any agent.")
            print("❌ 没有智能体生成有效提案")
            return None

        print(f"\n✓ Generated {len(proposals)}/{self.num_generators} valid proposals")
        print(f"✓ 生成了 {len(proposals)}/{self.num_generators} 个有效提案")

        # Step 2: Critic fusion
        print(f"\n📊 Phase 2: Critic Fusion & Refinement")
        print(f"📊 阶段2：批判者融合与精炼")
        print("-" * 80)

        refined_scaffold = self._critic_fusion(
            problem_text,
            retrieved_knowledge,
            proposals
        )

        if refined_scaffold:
            print("\n" + "="*80)
            print("✅ MULTI-AGENT SCAFFOLDING COMPLETED")
            print("✅ 多智能体脚手架生成完成")
            print("="*80 + "\n")
        else:
            print("\n" + "="*80)
            print("❌ MULTI-AGENT SCAFFOLDING FAILED")
            print("❌ 多智能体脚手架生成失败")
            print("="*80 + "\n")

        return refined_scaffold

    def generate_scaffold_for_grpo_training(
        self,
        problem_text: str,
        retrieved_knowledge: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate scaffolds for GRPO training with multiple rollouts per generator.
        为GRPO训练生成脚手架，每个生成器产生多个rollouts
        
        Architecture (用户架构):
        Question → Generator 1 → [R1.1, R1.2, R1.3] → Critic fusion → Scaffold 1
        Question → Generator 2 → [R2.1, R2.2, R2.3] → Critic fusion → Scaffold 2
        Question → Generator 3 → [R3.1, R3.2, R3.3] → Critic fusion → Scaffold 3
        
        Returns:
            List of 3 final scaffolds (one per generator after critic fusion)
            返回3个最终脚手架（每个生成器经过critic融合后一个）
        """
        print("\n" + "="*80)
        print("🎓 GRPO TRAINING MODE: Multiple Rollouts Per Generator")
        print("🎓 GRPO训练模式：每个生成器多个Rollouts")
        print("="*80)
        print(f"   - {self.num_generators} generators")
        print(f"   - {self.rollouts_per_generator} rollouts per generator")
        print(f"   - Total rollouts: {self.num_generators * self.rollouts_per_generator}")
        print(f"   - {self.num_generators}个生成器")
        print(f"   - 每个生成器{self.rollouts_per_generator}个rollouts")
        print(f"   - 总rollouts: {self.num_generators * self.rollouts_per_generator}\n")
        
        knowledge_str = "\n".join(
            f"{i}. {rule}" for i, rule in enumerate(retrieved_knowledge, 1)
        )
        
        results = []

        # Optional: parallelize across generators if configured
        try:
            if getattr(self, 'parallel_generators', False) and self.num_generators > 1:
                def _process_generator(agent_id: int):
                    # Build rollouts for this generator (optionally in parallel)
                    rollouts_local = []
                    def _gen_one(idx: int):
                        sc = self._single_agent_generate(
                            agent_id=agent_id,
                            problem_text=problem_text,
                            knowledge_str=knowledge_str
                        )
                        if sc:
                            return {'agent_id': agent_id, 'rollout_id': idx, 'scaffold': sc}
                        return None
                    if getattr(self, 'parallel_rollouts', False) and self.rollouts_per_generator > 1:
                        with ThreadPoolExecutor(max_workers=self.rollouts_per_generator) as ex:
                            futs = {ex.submit(_gen_one, i): i for i in range(1, self.rollouts_per_generator + 1)}
                            for fut in as_completed(futs):
                                v = fut.result()
                                if v:
                                    rollouts_local.append(v)
                    else:
                        for i in range(1, self.rollouts_per_generator + 1):
                            v = _gen_one(i)
                            if v:
                                rollouts_local.append(v)
                    if not rollouts_local:
                        return None
                    fused = self._critic_fusion(
                        problem_text=problem_text,
                        retrieved_knowledge=retrieved_knowledge,
                        proposals=rollouts_local
                    )
                    if fused:
                        return {
                            'agent_id': agent_id,
                            'num_rollouts': len(rollouts_local),
                            'scaffold': fused,
                            'rollouts': rollouts_local
                        }
                    return None

                with ThreadPoolExecutor(max_workers=self.num_generators) as ex:
                    futs = {ex.submit(_process_generator, g): g for g in range(1, self.num_generators + 1)}
                    for fut in as_completed(futs):
                        res = fut.result()
                        if res:
                            results.append(res)
                # Return early if parallel branch was used
                print(f"\nParallel generators mode produced {len(results)} fused scaffolds")
                return results
        except Exception:
            # Fallback to serial loop below on any error
            pass
        
        # For each generator, generate multiple rollouts and fuse them
        # 对每个生成器，生成多个rollouts并融合
        for agent_id in range(1, self.num_generators + 1):
            print(f"\n{'─'*80}")
            print(f"🤖 Generator {agent_id}: Generating {self.rollouts_per_generator} rollouts")
            print(f"🤖 生成器 {agent_id}：生成 {self.rollouts_per_generator} 个rollouts")
            print(f"{'─'*80}")
            
            # Step 1: Generate multiple rollouts for this generator
            # 步骤1：为这个生成器生成多个rollouts
            rollouts = []
            for rollout_idx in range(1, self.rollouts_per_generator + 1):
                print(f"\n  📝 Rollout {rollout_idx}/{self.rollouts_per_generator}...")
                
                scaffold = self._single_agent_generate(
                    agent_id=agent_id,
                    problem_text=problem_text,
                    knowledge_str=knowledge_str
                )
                
                if scaffold:
                    rollouts.append({
                        'agent_id': agent_id,
                        'rollout_id': rollout_idx,
                        'scaffold': scaffold
                    })
                    print(f"    ✓ Rollout {rollout_idx} generated successfully")
                else:
                    print(f"    ✗ Rollout {rollout_idx} failed")
            
            print(f"\n  📊 Generator {agent_id} produced {len(rollouts)}/{self.rollouts_per_generator} valid rollouts")
            
            # Step 2: Critic fuses this generator's rollouts
            # 步骤2：Critic融合这个生成器的rollouts
            if len(rollouts) > 0:
                print(f"\n  🧠 Critic fusing Generator {agent_id}'s rollouts...")
                print(f"  🧠 Critic正在融合生成器 {agent_id} 的rollouts...")
                
                fused_scaffold = self._critic_fusion(
                    problem_text=problem_text,
                    retrieved_knowledge=retrieved_knowledge,
                    proposals=rollouts
                )
                
                if fused_scaffold:
                    results.append({
                        'agent_id': agent_id,
                        'num_rollouts': len(rollouts),
                        'scaffold': fused_scaffold,
                        'rollouts': rollouts  # Keep rollouts for analysis
                    })
                    print(f"    ✅ Generator {agent_id}: Fusion successful")
                else:
                    print(f"    ❌ Generator {agent_id}: Fusion failed")
            else:
                print(f"  ⚠ Generator {agent_id}: No valid rollouts, skipping fusion")
        
        print(f"\n{'='*80}")
        print(f"📊 GRPO Training Rollout Summary")
        print(f"📊 GRPO训练Rollout总结")
        print(f"{'='*80}")
        print(f"✓ Successful fusions: {len(results)}/{self.num_generators}")
        print(f"✓ 成功融合: {len(results)}/{self.num_generators}")
        
        for result in results:
            print(f"  - Generator {result['agent_id']}: {result['num_rollouts']} rollouts → 1 fused scaffold")
        
        print(f"{'='*80}\n")
        
        return results

    def _parallel_generate(
        self,
        problem_text: str,
        retrieved_knowledge: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate proposals in parallel using ThreadPoolExecutor.
        使用ThreadPoolExecutor并行生成提案
        
        Note: Each generator loads its own experiences internally.
        注意：每个生成器在内部加载自己的经验。

        Returns:
            List of valid proposals
        """
        knowledge_str = "\n".join(
            f"{i}. {rule}" for i, rule in enumerate(retrieved_knowledge, 1)
        ) if retrieved_knowledge else "No additional knowledge provided."

        proposals = []

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.num_generators) as executor:
            # Submit all generator tasks
            # Each agent will load its own experiences based on agent_id
            # 每个agent将根据agent_id加载自己的经验
            future_to_agent = {
                executor.submit(
                    self._single_agent_generate,
                    agent_id,
                    problem_text,
                    knowledge_str
                ): agent_id
                for agent_id in range(1, self.num_generators + 1)
            }

            # Collect results as they complete
            for future in as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    result = future.result()
                    if result:
                        proposals.append({
                            'agent_id': agent_id,
                            'scaffold': result,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                        print(f"  ✓ Agent {agent_id} completed successfully")
                        print(f"  ✓ 智能体 {agent_id} 成功完成")
                    else:
                        print(f"  ✗ Agent {agent_id} failed to generate valid scaffold")
                        print(f"  ✗ 智能体 {agent_id} 生成无效脚手架")
                except Exception as e:
                    print(f"  ✗ Agent {agent_id} encountered error: {e}")
                    print(f"  ✗ 智能体 {agent_id} 遇到错误: {e}")

        return proposals

    def _single_agent_generate(
        self,
        agent_id: int,
        problem_text: str,
        knowledge_str: str
    ) -> Optional[Dict[str, Any]]:
        """
        Single agent generation with retry logic.
        单个智能体生成（带重试逻辑）

        Args:
            agent_id: Agent identifier (1, 2, or 3)
            problem_text: Problem statement
            knowledge_str: Formatted knowledge string (RAG)

        Returns:
            Generated scaffold or None
        """
        print(f"\n🤖 Agent {agent_id} starting generation...")
        print(f"🤖 智能体 {agent_id} 开始生成...")

        # Load this agent's own experiences from its experience file
        # 从该agent自己的经验文件加载经验
        experiences_str = self._load_agent_experiences(f'generator_{agent_id}')

        # Construct prompt with both knowledge and experiences
        # 使用知识和经验构造提示
        prompt = self.generator_prompt.format(
            retrieved_knowledge=knowledge_str,
            prior_experiences=experiences_str,
            problem_text=problem_text
        )

        # Retry loop
        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt > 1:
                    print(f"  🔄 Agent {agent_id} retry {attempt}/{self.max_retries}")
                    time.sleep(self.retry_delay)

                # Call LLM with agent-specific client / 使用该智能体特定的客户端调用LLM
                agent_client = self.generator_clients.get(agent_id, self.generator_clients[1])
                response = agent_client.complete(
                    prompt,
                    temperature=self.generator_temperature
                )

                # Extract JSON
                scaffold = self._extract_json(response)

                if scaffold:
                    # Validate
                    if self._validate_scaffold(scaffold):
                        print(f"  ✓ Agent {agent_id} generated valid scaffold")

                        # Log generation
                        self.generation_log.append({
                            'agent_id': agent_id,
                            'attempt': attempt,
                            'success': True,
                            'target_variable': scaffold.get('target_variable')
                        })

                        return scaffold

                # Failed to parse or validate
                if attempt < self.max_retries:
                    print(f"  ⚠ Agent {agent_id} failed attempt {attempt}, retrying...")

            except Exception as e:
                print(f"  ✗ Agent {agent_id} error on attempt {attempt}: {e}")
                if attempt >= self.max_retries:
                    self.generation_log.append({
                        'agent_id': agent_id,
                        'attempt': attempt,
                        'success': False,
                        'error': str(e)
                    })

        return None

    def _critic_fusion(
        self,
        problem_text: str,
        retrieved_knowledge: List[str],
        proposals: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Critic agent fuses multiple proposals into refined output.
        批判者智能体将多个提案融合为精炼输出

        Args:
            problem_text: Original problem
            retrieved_knowledge: Knowledge base (from RAG)
            proposals: List of proposals from generator agents

        Returns:
            Refined scaffold or None
        """
        if len(proposals) == 0:
            print("⚠ No proposals to fuse")
            return None

        # If only one proposal, validate and return it
        if len(proposals) == 1:
            print("ℹ Only one proposal available, using it directly")
            return proposals[0]['scaffold']

        print(f"\n🧠 Critic analyzing {len(proposals)} proposals...")
        print(f"🧠 批判者正在分析 {len(proposals)} 个提案...")

        # Format knowledge
        knowledge_str = "\n".join(
            f"{i}. {rule}" for i, rule in enumerate(retrieved_knowledge, 1)
        ) if retrieved_knowledge else "No additional knowledge provided."
        
        # Load critic's own experiences from its experience file
        # 从critic自己的经验文件加载经验
        experiences_str = self._load_agent_experiences('critic')

        # Prepare proposals for prompt (pad with empty if less than 3)
        proposal_jsons = []
        for i in range(3):
            if i < len(proposals):
                proposal_jsons.append(
                    json.dumps(proposals[i]['scaffold'], indent=2, ensure_ascii=False)
                )
            else:
                proposal_jsons.append("{}")  # Empty placeholder

        # Construct critic prompt with knowledge and experiences
        prompt = self.critic_prompt.format(
            problem_text=problem_text,
            retrieved_knowledge=knowledge_str,
            prior_experiences=experiences_str,
            proposal_1=proposal_jsons[0],
            proposal_2=proposal_jsons[1],
            proposal_3=proposal_jsons[2]
        )

        # Retry loop for critic
        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt > 1:
                    print(f"  🔄 Critic retry {attempt}/{self.max_retries}")
                    time.sleep(self.retry_delay)

                print(f"  📝 Critic processing (attempt {attempt})...")
                print(f"  📝 批判者处理中（第 {attempt} 次尝试）...")

                # Call LLM with critic-specific client / 使用批判者特定的客户端调用LLM
                response = self.critic_client.complete(
                    prompt,
                    temperature=self.critic_temperature
                )

                print(f"  ✓ Critic response received ({len(response)} chars)")

                # Extract JSON
                refined = self._extract_json(response)

                if refined:
                    if self._validate_scaffold(refined):
                        print(f"  ✅ Critic produced valid refined scaffold")
                        print(f"  ✅ 批判者生成了有效的精炼脚手架")

                        # Print critic analysis if available
                        critic_analysis = refined.get('critic_analysis')
                        if critic_analysis:
                            print("\n" + "="*80)
                            print("🔍 CRITIC ANALYSIS (批判者分析)")
                            print("="*80)
                            print(critic_analysis)
                            print("="*80 + "\n")

                        # Log fusion
                        self.fusion_log.append({
                            'num_proposals': len(proposals),
                            'attempt': attempt,
                            'success': True,
                            'target_variable': refined.get('target_variable'),
                            'critic_analysis': critic_analysis
                        })

                        return refined

                # Failed to parse or validate
                if attempt < self.max_retries:
                    print(f"  ⚠ Critic failed attempt {attempt}, retrying...")

            except Exception as e:
                print(f"  ✗ Critic error on attempt {attempt}: {e}")
                if attempt >= self.max_retries:
                    self.fusion_log.append({
                        'num_proposals': len(proposals),
                        'attempt': attempt,
                        'success': False,
                        'error': str(e)
                    })

        print("  ❌ Critic failed to produce valid output, using best generator proposal")
        print("  ❌ 批判者未能生成有效输出，使用最佳生成器提案")

        # Fallback: return first valid proposal
        return proposals[0]['scaffold'] if len(proposals) > 0 else None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        import re

        # Try to find JSON code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON object
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None

        # Preprocess: Fix Python-style fractions to string format
        # 预处理：将Python风格的分数转换为字符串格式（保留精度）
        # Convert patterns like `: 1/3,` to `: "1/3",` to keep precision
        json_str = re.sub(r':\s*(\d+)/(\d+)(\s*[,\}])', r': "\1/\2"\3', json_str)
        json_str = re.sub(r'\[\s*(\d+)/(\d+)(\s*[,\]])', r'["\1/\2"\3', json_str)
        json_str = re.sub(r',\s*(\d+)/(\d+)(\s*[,\]\}])', r', "\1/\2"\3', json_str)

        # Parse JSON
        try:
            result = json.loads(json_str)

            # Unwrap if needed
            if isinstance(result, dict) and "problem_analysis" in result:
                result = result["problem_analysis"]

            return result
        except json.JSONDecodeError as e:
            # Enhanced error logging
            if hasattr(self, 'verbose') and self.verbose:
                print(f"  ⚠ JSON parse error: {e}")
                print(f"  First 200 chars: {json_str[:200]}")
            return None

    def _validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
        """Validate scaffold structure (internal)."""
        required_keys = ["target_variable", "knowns", "causal_graph", "computation_plan"]

        if not all(key in scaffold for key in required_keys):
            return False

        # Validate causal_graph
        for link in scaffold.get("causal_graph", []):
            if not all(key in link for key in ["cause", "effect", "rule"]):
                return False

        # Validate computation_plan
        for step in scaffold.get("computation_plan", []):
            required_step_keys = ["id", "target", "inputs", "description"]
            if not all(key in step for key in required_step_keys):
                return False

        return True

    def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
        """
        Validate scaffold structure (public API for compatibility).
        验证脚手架结构（公共API，用于兼容性）

        Args:
            scaffold: The scaffold dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        return self._validate_scaffold(scaffold)

    def get_logs(self) -> Dict[str, Any]:
        """
        Get generation and fusion logs.
        获取生成和融合日志
        """
        return {
            'generation_log': self.generation_log,
            'fusion_log': self.fusion_log
        }

    def print_summary(self):
        """Print summary of multi-agent execution."""
        print("\n" + "="*80)
        print("📊 MULTI-AGENT EXECUTION SUMMARY")
        print("📊 多智能体执行摘要")
        print("="*80)

        # Generation stats
        total_generations = len(self.generation_log)
        successful_generations = sum(1 for log in self.generation_log if log.get('success'))

        print(f"\n🤖 Generator Agents:")
        print(f"   Total attempts: {total_generations}")
        print(f"   Successful: {successful_generations}")
        print(f"   Failed: {total_generations - successful_generations}")

        print(f"\n🤖 生成器智能体:")
        print(f"   总尝试次数: {total_generations}")
        print(f"   成功: {successful_generations}")
        print(f"   失败: {total_generations - successful_generations}")

        # Fusion stats
        total_fusions = len(self.fusion_log)
        successful_fusions = sum(1 for log in self.fusion_log if log.get('success'))

        print(f"\n🧠 Critic Agent:")
        print(f"   Total fusion attempts: {total_fusions}")
        print(f"   Successful: {successful_fusions}")
        print(f"   Failed: {total_fusions - successful_fusions}")

        print(f"\n🧠 批判者智能体:")
        print(f"   总融合尝试: {total_fusions}")
        print(f"   成功: {successful_fusions}")
        print(f"   失败: {total_fusions - successful_fusions}")

        print("="*80 + "\n")


# Example usage
if __name__ == "__main__":
    # Initialize multi-agent scaffolder
    ma_scaffolder = MultiAgentScaffolder(
        num_generators=3,
        generator_temperature=0.3,
        critic_temperature=0.0
    )

    # Test problem
    problem = """
    An object with a mass of 10 kg is initially at rest.
    A constant force of 50 Newtons is applied to it for 5 seconds.
    What is its final velocity?
    """

    # Mock retrieved knowledge
    knowledge = [
        "Newton's Second Law: Force equals mass times acceleration (F=ma).",
        "Kinematic Equation: Final velocity equals initial velocity plus acceleration multiplied by time (v_f = v_i + a*t)."
    ]

    # Generate scaffold using multi-agent system
    scaffold = ma_scaffolder.generate_scaffold_parallel(problem, knowledge)

    if scaffold:
        print("\n--- REFINED SCAFFOLD ---")
        print(json.dumps(scaffold, indent=2, ensure_ascii=False))

        # Print summary
        ma_scaffolder.print_summary()
