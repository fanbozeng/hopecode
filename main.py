"""
Main Orchestrator for Causal Reasoning Engine
主要因果推理引擎编排器

Pipeline Architecture (based on design diagram):
流水线架构（基于设计图）：

Step1: Multi-Agent Generator for DAG of SCM
    - 3 parallel generators independently create causal DAGs
    - 1 critic agent fuses and refines the proposals
    - Output: Fixed DAG
    第1步：多智能体生成器生成SCM的DAG
    - 3个并行生成器独立创建因果DAG
    - 1个批判者智能体融合并精炼提案
    - 输出：Fixed DAG

Step2: Post-Enhancement of the DAG
    - Domain Expert Review (Math/Physics experts)
    - RAG Knowledge Enhancement (knowledge gap filling)
    - Causal Structure Optimization (chain/fork/collider patterns)
    - Output: Enhanced DAG
    第2步：DAG后增强
    - 领域专家审查（数学/物理专家）
    - RAG知识增强（填补知识缺口）
    - 因果结构优化（链/叉/对撞结构模式）
    - 输出：Enhanced DAG

Step3: LLM-Based Computation
    - LLM computes the final answer based on Enhanced DAG
    - Output: Final Answer + Reasoning
    第3步：基于LLM的计算
    - LLM基于Enhanced DAG计算最终答案
    - 输出：最终答案 + 推理过程
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Import engine components /
from engine import (
    KnowledgeRetriever,
    AIKnowledgeRetriever,
    VectorKnowledgeRetriever,
    CausalScaffolder,
    LLMComputer,  # LLM-based computation / 基于LLM的计算
    # Step2 Enhancement modules
    DomainExpertReviewer,
    RAGKnowledgeEnhancer,
    CausalStructureOptimizer,
    DAGEnhancementPipeline,
    ProblemType
)
# Import multi-agent scaffolder / 导入多智能体脚手架器
from engine.multi_agent_scaffolder import MultiAgentScaffolder


class CausalReasoningEngine:
    """
    Main orchestrator for the causal reasoning pipeline.
    主要因果推理流水线编排器
    
    Coordinates three main steps:
    协调三个主要步骤：
    - Step1: Multi-agent generator creates Fixed DAG
    - Step2: Post-enhancement pipeline improves DAG
    - Step3: LLM-based computation produces final answer
    
    - 第1步：多智能体生成器创建Fixed DAG
    - 第2步：后增强流水线改进DAG
    - 第3步：基于LLM的计算产生最终答案
    """

    def __init__(
        self,
        knowledge_base_path: str = "data/knowledge_base.json", #知识库的位置
        verbose: bool = True, # 是否打印详细进度信息
        use_ai_retriever: bool = True,  # 是否使用AI检索器作为回退
        auto_enrich_kb: bool = True, # 是否自动保存AI生成的规则到知识库
        min_rules_threshold: int = 5, # 最小规则数
        use_multi_agent: bool = True,  # 默认使用多智能体系统
        num_generators: int = 3,  # 新增：生成器数量
        generator_temperature: float = 0.3,  # 新增：生成器温度
        critic_temperature: float = 0.0,  # 新增：批判者温度
        use_vector_retriever: bool = False,  # 新增：向量检索（语义相似度RAG）
        use_grpo_experience: bool = True,  # 新增：是否加载GRPO经验（用于消融实验）
        # Step2 Enhancement options / Step2增强选项
        enable_step2_enhancement: bool = True,  # 是否启用Step2增强
        use_expert_review: bool = True,  # 是否使用专家审查
        use_rag_enhancement: bool = True,  # 是否使用RAG知识增强
        use_structure_optimization: bool = True  # 是否使用结构优化
    ):
        """
        Initialize the causal reasoning engine.
        初始化因果推理引擎

        Args:
            knowledge_base_path: Path to knowledge base JSON file
                                 知识库JSON文件路径
            verbose: Print detailed progress information
                    打印详细进度信息
            use_ai_retriever: Use AI retriever for knowledge generation
                             使用AI检索器生成知识
            auto_enrich_kb: Automatically save AI-generated rules
                           自动保存AI生成的规则
            min_rules_threshold: Minimum rules threshold
                                最小规则阈值
            use_multi_agent: Use multi-agent scaffolder (3 generators + 1 critic)
                            使用多智能体脚手架器（3个生成器 + 1个批判者）
            num_generators: Number of parallel generator agents
                           并行生成器数量
            generator_temperature: Temperature for generator agents (for diversity)
                                  生成器温度（用于多样性）
            critic_temperature: Temperature for critic agent (for stability)
                               批判者温度（用于稳定性）
            use_vector_retriever: Use vector-based semantic retrieval
                                 使用基于向量的语义检索
            enable_step2_enhancement: Enable Step2 DAG enhancement
                                     启用第2步DAG增强
            use_expert_review: Use domain expert review
                              使用领域专家审查
            use_rag_enhancement: Use RAG knowledge enhancement
                                使用RAG知识增强
            use_structure_optimization: Use causal structure optimization
                                       使用因果结构优化
        """
        self.verbose = verbose
        self.use_ai_retriever = use_ai_retriever
        self.auto_enrich_kb = auto_enrich_kb
        self.min_rules_threshold = min_rules_threshold
        self.knowledge_base_path = knowledge_base_path
        self.use_multi_agent = use_multi_agent
        self.use_grpo_experience = use_grpo_experience  # 新增：存储是否使用GRPO经验
        self.use_vector_retriever = use_vector_retriever
        
        # Step2 Enhancement options / Step2增强选项
        self.enable_step2_enhancement = enable_step2_enhancement
        self.use_expert_review = use_expert_review
        self.use_rag_enhancement = use_rag_enhancement
        self.use_structure_optimization = use_structure_optimization

        # Initialize components / 初始化组件
        self._print("Initializing Causal Reasoning Engine...")
        self._print("初始化因果推理引擎...")

        try:
            # Knowledge retriever selection（RAG检索器选择）
            if self.use_vector_retriever:
                # True RAG: semantic similarity  这个就是从我本地加载这个编码器 转化成384维度
                self.retriever = VectorKnowledgeRetriever(
                    knowledge_base_path=knowledge_base_path,
                    model_name="all-MiniLM-L6-v2",
                    cache_path="data/knowledge_embeddings.pkl",
                    use_cache=True,
                )
                self._print(" 🔍 Using VectorKnowledgeRetriever (semantic RAG)")
                self._print(" 🔍 使用向量检索（语义相似度RAG）")
            else:
                # Keyword-based retriever
                self.retriever = KnowledgeRetriever(knowledge_base_path)

            # AI-enhanced retriever / AI 
            if use_ai_retriever:
                self.ai_retriever = AIKnowledgeRetriever(
                    knowledge_base_path=knowledge_base_path,
                    auto_enrich_kb=auto_enrich_kb,
                    max_rules=5, #TODO 这个地方跟前面那个字段要区分一下
                    enable_cache=True
                )
                self._print(" AI Knowledge Retriever enabled")
                self._print(" AI ")
            else:
                self.ai_retriever = None

            # Other components /
            # 新增：根据选项初始化单智能体或多智能体脚手架器
            if use_multi_agent:# 这个地方就是加载因果多智能体系统 其实就是加载对应的prompt
                # 如果启用GRPO经验，加载经验管理器
                experience_manager = None
                if use_grpo_experience:
                    try:
                        from engine import GRPOExperienceManager
                        experience_manager = GRPOExperienceManager(
                            experience_dir="data/grpo_experiences",
                            verbose=False
                        )
                        self._print(" ✓ GRPO Experience loaded")
                        self._print(" ✓ GRPO经验已加载")
                    except Exception as e:
                        self._print(f" ⚠️  Failed to load GRPO experiences: {e}")
                        self._print(f" ⚠️  GRPO经验加载失败：{e}")
                
                self.scaffolder = MultiAgentScaffolder(
                    num_generators=num_generators,
                    generator_temperature=generator_temperature,
                    critic_temperature=critic_temperature,
                    experience_manager=experience_manager,  # 传递经验管理器（可能为None）
                    use_separate_apis=True  # Use separate API for each generator and critic
                )
                self._print(f" 🤖 Using Multi-Agent Scaffolder ({num_generators} generators + 1 critic)")
                self._print(f" 🤖 使用多智能体脚手架器（{num_generators}个生成器 + 1个批判者）")
            else:
                self.scaffolder = CausalScaffolder()  # 生成因果图
                self._print(" 🤖 Using Single-Agent Scaffolder")
                self._print(" 🤖 使用单智能体脚手架器")

            # Initialize LLM Computer / 初始化LLM计算器
            self.llm_computer = LLMComputer(verbose=verbose)
            self._print(" ⚙️ LLM Computer initialized")
            self._print(" ⚙️ LLM计算器已初始化")
            
            # Initialize Step2 Enhancement Pipeline / 初始化Step2增强流水线
            self._initialize_step2_enhancement()

            self._print("✅ All components initialized successfully.")
            self._print("✅ 所有组件初始化成功\n")
        except Exception as e:
            self._print(f"❌ Error during initialization: {e}")
            raise

    def _print(self, message: str) -> None:
        """Print message if verbose mode enabled / 如果启用详细模式则打印消息"""
        if self.verbose:
            print(message)
    
    def _initialize_step2_enhancement(self) -> None:
        """
        Initialize Step2 DAG Enhancement Pipeline.
        初始化Step2 DAG增强流水线
        
        This method sets up:
        1. Domain Expert Reviewer (Math & Physics experts)
        2. RAG Knowledge Enhancer  
        3. Causal Structure Optimizer
        4. DAG Enhancement Pipeline (orchestrator)
        """
        if not self.enable_step2_enhancement:
            self._print(" ⏭️  Step2 Enhancement disabled")
            self._print(" ⏭️  Step2增强已禁用")
            self.enhancement_pipeline = None
            return
        
        self._print("\n 🔧 Initializing Step2 Enhancement Pipeline...")
        self._print(" 🔧 初始化Step2增强流水线...")
        
        try:
            # Load API configuration for experts
            from engine.api_manager import APIKeyManager
            api_manager = APIKeyManager()
            
            # Initialize unified expert LLM client (handles both math and physics)
            expert_client = None
            causal_expert_client = None
            
            if self.use_expert_review:
                try:
                    # Try to get expert API key (use math_expert as unified expert)
                    expert_key = api_manager.get_api_key('math_expert')
                    
                    # Create LLM client for unified expert
                    from engine.scaffolder import LLMClient
                    if expert_key:
                        expert_client = LLMClient()  # Unified expert (Math+Physics)
                    
                    self._print("   ✓ Unified expert client initialized (Math+Physics)")
                except Exception as e:
                    self._print(f"   ⚠️  Expert client initialization skipped: {e}")
            
            # Initialize causal expert client
            if self.use_structure_optimization:
                try:
                    causal_key = api_manager.get_api_key('causal_knowledge')
                    if causal_key:
                        from engine.scaffolder import LLMClient
                        causal_expert_client = LLMClient()
                        # Set API key
                        if hasattr(causal_expert_client, 'client'):
                            causal_expert_client.client.api_key = causal_key
                        self._print("   ✓ Causal expert client initialized")
                    else:
                        self._print("   ⚠️  No 'causal_knowledge' API key found, structure optimization will be skipped")
                        self._print("   ⚠️  Tip: Add CAUSAL_KNOWLEDGE_API=your_key to .env file")
                except Exception as e:
                    self._print(f"   ⚠️  Causal expert client initialization failed: {e}")
            
            # Initialize Stage 1: Domain Expert Reviewer (Unified Math+Physics Expert)
            expert_reviewer = None
            if self.use_expert_review:
                expert_reviewer = DomainExpertReviewer(
                    math_expert_client=expert_client,
                    physics_expert_client=expert_client,  # Same client for both
                    verbose=self.verbose
                )
                self._print("   ✓ Domain Expert Reviewer ready (Unified Math+Physics)")
            
            # Initialize Stage 2: RAG Knowledge Enhancer
            rag_enhancer = None
            if self.use_rag_enhancement:
                rag_enhancer = RAGKnowledgeEnhancer(
                    ai_retriever=self.ai_retriever if hasattr(self, 'ai_retriever') else None,
                    vector_retriever=self.retriever if self.use_vector_retriever else None,
                    verbose=self.verbose
                )
                self._print("   ✓ RAG Knowledge Enhancer ready")
            
            # Initialize Stage 3: Causal Structure Optimizer
            structure_optimizer = None
            if self.use_structure_optimization:
                structure_optimizer = CausalStructureOptimizer(
                    causal_expert_client=causal_expert_client,
                    verbose=self.verbose
                )
                self._print("   ✓ Causal Structure Optimizer ready")
            
            # Initialize Pipeline Orchestrator
            self.enhancement_pipeline = DAGEnhancementPipeline(
                expert_reviewer=expert_reviewer,
                rag_enhancer=rag_enhancer,
                structure_optimizer=structure_optimizer,
                verbose=self.verbose
            )
            
            self._print(" ✅ Step2 Enhancement Pipeline initialized successfully")
            self._print(" ✅ Step2增强流水线初始化成功\n")
            
        except Exception as e:
            self._print(f" ⚠️  Step2 Enhancement initialization failed: {e}")
            self._print(f" ⚠️  Step2增强初始化失败: {e}")
            self.enhancement_pipeline = None

    def solve_problem(
        self,
        problem_text: str,
        include_validation: bool = True,
        save_output: Optional[str] = None,
        problem_id: Optional[str] = None,
        method_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solve a problem using the causal reasoning pipeline.
        使用因果推理流水线解决问题

        Execution Flow:
        执行流程：
        
        Step1: Multi-Agent Causal Scaffolding
            - 3 generators create diverse causal DAGs in parallel
            - Critic fuses proposals into Fixed DAG
            - 3个生成器并行创建多样化的因果DAG
            - 批判者将提案融合为Fixed DAG
        
        Step2: DAG Enhancement
            - Domain expert reviews reasoning chains
            - RAG retrieves and fills knowledge gaps
            - Causal structure optimizer applies patterns
            - Result: Enhanced DAG
            - 领域专家审查推理链
            - RAG检索并填补知识缺口
            - 因果结构优化器应用模式
            - 结果：Enhanced DAG
        
        Step3: LLM-Based Computation
            - LLM computes final answer from Enhanced DAG
            - LLM从Enhanced DAG计算最终答案

        Args:
            problem_text: Problem statement in natural language
                         自然语言问题陈述
            include_validation: Include validation (reserved)
                               包含验证（保留）
            save_output: Path to save output JSON
                        保存输出JSON的路径
            problem_id: Problem identifier
                       问题标识符
            method_name: Method name
                        方法名称

        Returns:
            Dictionary with results and outputs
            结果和输出的字典
        """
        self._print("STARTING CAUSAL REASONING PIPELINE")
        results = {
            "problem": problem_text,
            "success": False,
            "error": None
        }

        try:
            # Step1: Multi-Agent Causal Scaffolding / 第1步：多智能体因果脚手架
            self._print("\n--- STEP 1: MULTI-AGENT CAUSAL SCAFFOLDING ---")
            self._print("--- 第1步：多智能体因果脚手架 ---")

            if self.use_multi_agent:
                # Multi-agent: each generator loads its own experiences internally
                # 多智能体：每个generator内部加载自己的经验
                causal_plan = self.scaffolder.generate_scaffold_parallel(
                    problem_text=problem_text,
                    retrieved_knowledge=[]  # RAG knowledge (currently disabled)
                )
            else:
                # Single agent mode: no retrieved knowledge or experiences (for now)
                # 单智能体模式：暂无检索知识或经验
                causal_plan = self.scaffolder.generate_scaffold(
                    problem_text=problem_text,
                    retrieved_knowledge=[],
                    experiences=[]
                )
            
            
            if not causal_plan:
                results["error"] = "Failed to generate causal scaffold"
                return results

            if not self.scaffolder.validate_scaffold(causal_plan):
                results["error"] = "Invalid scaffold structure"
                return results

            results["causal_scaffold"] = causal_plan
            
            # Step2: DAG Enhancement / 第2步：DAG增强
            if self.enable_step2_enhancement and hasattr(self, 'enhancement_pipeline') and self.enhancement_pipeline:
                self._print("\n--- STEP 2: DAG ENHANCEMENT ---")
                self._print("--- 第2步：DAG增强 ---")
                
                try:
                    enhanced_dag, enhancement_report = self.enhancement_pipeline.enhance_dag(
                        fixed_dag=causal_plan,
                        problem_text=problem_text
                    )
                    
                    # Use enhanced DAG for subsequent stages
                    causal_plan = enhanced_dag
                    results["enhanced_dag"] = enhanced_dag
                    results["enhancement_report"] = enhancement_report
                    
                    self._print(f"   ✅ DAG Enhancement completed (Quality: {enhancement_report.get('summary', {}).get('quality_score', 0):.2f})")
                    
                except Exception as e:
                    self._print(f"   ⚠️  DAG Enhancement failed: {e}")
                    self._print("   Continuing with original DAG...")
                    results["enhancement_error"] = str(e)
            else:
                self._print("\n--- STEP 2: DAG ENHANCEMENT (Skipped) ---")
                self._print("--- 第2步：DAG增强（已跳过）---")

            # Step3: LLM-Based Computation / 第3步：基于LLM的计算
            self._print("\n--- STEP 3: LLM-BASED COMPUTATION ---")
            self._print("--- 第3步：基于LLM的计算 ---")

            computation_result = self.llm_computer.compute_from_scaffold(
                causal_scaffold=causal_plan,
                problem_text=problem_text
            )

            if not computation_result['success']:
                results["error"] = f"Failed during LLM computation: {computation_result.get('error', 'Unknown error')}"
                results["computation_result"] = computation_result
                return results

            # Store computation results / 存储计算结果
            results["final_answer"] = computation_result['result']
            results["computation_result"] = computation_result
            results["reasoning"] = computation_result.get('reasoning', '')

            # Finalization / 最终化
            results["success"] = True

            if save_output:
                self._save_results(results, save_output)

        except Exception as e:
            self._print("\n" + "="*70)
            self._print("❌ ERROR DURING PIPELINE EXECUTION")
            self._print("❌ 流水线执行错误")
            self._print("="*70)
            self._print(f"\nError: {e}")

            import traceback
            tb = traceback.format_exc()
            results["error"] = str(e)
            results["traceback"] = tb
            self._print(tb)
            self._print("="*70)

        return results

    def _save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """
        Save results to JSON file.
        保存结果到JSON文件
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self._print(f"\nResults saved to: {output_file}")

    def display_results(self, results: Dict[str, Any]) -> None:
        """
        Display results in formatted output.
        格式化显示结果
        """
        print("\n" + "=" * 70)
        print("FINAL RESULTS / 最终结果")
        print("=" * 70)

        if not results.get("success"):
            print(f"\n❌ Error: {results.get('error')}")
            if results.get("traceback"):
                print(results.get("traceback"))
            return

        print(f"\nProblem / 问题:")
        print(f"   {results['problem']}")

        print(f"\nFinal Answer / 最终答案:")
        print(f"   {results.get('final_answer')}")

        print("\n" + "=" * 70)


def main():
    """
    Command-line entry point.
    命令行入口点
    """
    parser = argparse.ArgumentParser(
        description="Causal Reasoning Engine / 因果推理引擎"
    )

    parser.add_argument("-p", "--problem", type=str, help="Problem text")
    parser.add_argument("-f", "--file", type=str, help="Problem file path")
    parser.add_argument("-o", "--output", type=str, help="Output JSON path")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("--kb", type=str, default="data/knowledge_base.json", help="Knowledge base path")
    parser.add_argument("--multi-agent", action="store_true", help="Use multi-agent scaffolder")
    parser.add_argument("--num-generators", type=int, default=3, help="Number of generators")
    parser.add_argument("--generator-temp", type=float, default=0.3, help="Generator temperature")
    parser.add_argument("--critic-temp", type=float, default=0.0, help="Critic temperature")

    args = parser.parse_args()

    if args.problem:
        problem_text = args.problem
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            problem_text = f.read()
    else:
        print("Enter problem (Ctrl+D or Ctrl+Z to finish):")
        problem_text = sys.stdin.read()

    engine = CausalReasoningEngine(
        knowledge_base_path=args.kb,
        verbose=not args.quiet,
        use_multi_agent=args.multi_agent,
        num_generators=args.num_generators,
        generator_temperature=args.generator_temp,
        critic_temperature=args.critic_temp
    )

    results = engine.solve_problem(problem_text, save_output=args.output)
    engine.display_results(results)
    sys.exit(0 if results.get("success") else 1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Running demo...\n")
        demo_problem = """
         "将电动势为3.0 V的电源接入电路中,测得电源两极间的电压为2.4 V,当电路中有6 C的电荷流过时,求：\n外电路中有多少电能转化为其他形式的能；
        """
        engine = CausalReasoningEngine()
        results = engine.solve_problem(demo_problem)
        engine.display_results(results)
    else:
        main()
