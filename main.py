"""
Main Orchestrator for Causal Reasoning Engine


This is the central script that orchestrates the entire four-stage pipeline:
1. Knowledge Retrieval (RAG)
2. Causal Scaffolding
3. Symbolic Execution
4. Synthesis & Validation


1.  (RAG)
2.
3.
4.
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
    SymbolicExecutor,
    CausalSynthesizer,
    LLMComputer  # Added: LLM-based computation option / 新增：基于LLM的计算选项
)
# Import multi-agent scaffolder / 导入多智能体脚手架器
from engine.multi_agent_scaffolder import MultiAgentScaffolder


class CausalReasoningEngine:
    """
    Main orchestrator for the causal reasoning pipeline.
    

    This class manages the entire problem-solving process by coordinating
    all four components of the system.

    
    """

    def __init__(
        self,
        knowledge_base_path: str = "data/knowledge_base.json",
        verbose: bool = True,
        use_ai_retriever: bool = True,
        auto_enrich_kb: bool = True,
        min_rules_threshold: int = 5,
        # computation_mode: str = "symbolic"  # Added: 'symbolic' or 'llm' / 新增：'symbolic'或'llm'
        computation_mode: str = "llm",
        use_multi_agent: bool = True,  # 新增：默认使用多智能体系统
        num_generators: int = 3,  # 新增：生成器数量
        generator_temperature: float = 0.3,  # 新增：生成器温度
        critic_temperature: float = 0.0,  # 新增：批判者温度
        use_vector_retriever: bool = False  # 新增：向量检索（语义相似度RAG）
    ):
        """
        Initialize the causal reasoning engine.


        Args:
            knowledge_base_path: Path to the knowledge base JSON file
                                  JSON
            verbose: Whether to print detailed progress information

            use_ai_retriever: Whether to use AI retriever as fallback
                               AI
            auto_enrich_kb: Whether to automatically save AI-generated rules to KB
                             AI
            min_rules_threshold: Minimum number of rules before triggering AI generation
                                  AI
            computation_mode: Computation method - 'symbolic' or 'llm'
                             计算方法 - 'symbolic'（符号执行）或'llm'（LLM计算）
                             - 'symbolic': Use code generation + symbolic execution (default)
                                          使用代码生成 + 符号执行（默认）
                             - 'llm': Use LLM-based computation (for ablation study)
                                     使用基于LLM的计算（用于消融实验）
            use_multi_agent: Whether to use multi-agent scaffolder (3 generators + 1 critic)
                            是否使用多智能体脚手架器（3个生成器 + 1个批判者）
            num_generators: Number of parallel generator agents (default: 3)
                           并行生成器智能体数量（默认：3）
            generator_temperature: Temperature for generator agents (default: 0.3)
                                  生成器智能体温度（默认：0.3）
            critic_temperature: Temperature for critic agent (default: 0.0)
                               批判者智能体温度（默认：0.0）
        """
        self.verbose = verbose
        self.use_ai_retriever = use_ai_retriever
        self.auto_enrich_kb = auto_enrich_kb
        self.min_rules_threshold = min_rules_threshold
        self.knowledge_base_path = knowledge_base_path
        self.computation_mode = computation_mode  # Added: Store computation mode / 新增：存储计算模式
        self.use_multi_agent = use_multi_agent  # 新增：存储多智能体选项
        self.use_vector_retriever = use_vector_retriever  # 新增：是否使用向量检索

        # Enforce LLM-only computation (symbolic mode removed)
        if self.computation_mode != "llm":
            self._print("⚠️ Symbolic mode is no longer supported. Falling back to LLM mode.")
        self.computation_mode = "llm"

        # Initialize all components /
        self._print("Initializing Causal Reasoning Engine...")
        self._print("...")

        try:
            # Knowledge retriever selection（RAG检索器选择）
            if self.use_vector_retriever:
                # True RAG: semantic similarity
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
                    max_rules=5,
                    enable_cache=True
                )
                self._print(" AI Knowledge Retriever enabled")
                self._print(" AI ")
            else:
                self.ai_retriever = None

            # Other components /
            # 新增：根据选项初始化单智能体或多智能体脚手架器
            if use_multi_agent:
                self.scaffolder = MultiAgentScaffolder(
                    num_generators=num_generators,
                    generator_temperature=generator_temperature,
                    critic_temperature=critic_temperature
                )
                self._print(f" 🤖 Using Multi-Agent Scaffolder ({num_generators} generators + 1 critic)")
                self._print(f" 🤖 使用多智能体脚手架器（{num_generators}个生成器 + 1个批判者）")
            else:
                self.scaffolder = CausalScaffolder()  # 生成因果图
                self._print(" 🤖 Using Single-Agent Scaffolder")
                self._print(" 🤖 使用单智能体脚手架器")

            self.executor = SymbolicExecutor()  # Keep for backward compatibility
            # (removed) code generator not used
            # (removed) sandbox executor not used
            self.synthesizer = CausalSynthesizer() #反事实验证

            # Added: Initialize LLM Computer for ablation study / 新增：初始化LLM计算器用于消融实验
            self.llm_computer = LLMComputer(verbose=verbose)
            self._print(" ⚙️ Computation Mode: LLM-based")
            self._print(" ⚙️ 计算模式: 基于LLM")

            # Print computation mode / 打印计算模式（LLM-only）
            self._print(" ⚙️ Computation Mode: LLM-based")
            self._print(" ⚙️ 计算模式: 基于LLM")

            self._print("All components initialized successfully.")
            self._print("")
        except Exception as e:
            self._print(f"Error during initialization: {e}")
            self._print(f": {e}")
            raise

    def _print(self, message: str) -> None:
        """
        Print message if verbose mode is enabled.
        

        Args:
            message: Message to print
                     
        """
        if self.verbose:
            print(message)

    def solve_problem(
        self,
        problem_text: str,
        include_validation: bool = True,
        save_output: Optional[str] = None,
        problem_id: Optional[str] = None,
        method_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solve a problem using the full causal reasoning pipeline.


        This method executes all four stages and returns comprehensive results.


        Args:
            problem_text: The problem statement in natural language

            include_validation: Whether to include counterfactual validation

            save_output: Optional path to save the output JSON
                          JSON
            problem_id: Optional problem identifier for visualization naming

            method_name: Optional method name for visualization organization


        Returns:
            Dictionary containing all results and outputs

        """
        self._print("\n" + "=" * 70)
        self._print("STARTING CAUSAL REASONING PIPELINE")
        self._print("")
        self._print("=" * 70 + "\n")

        results = {
            "problem": problem_text,
            "success": False,
            "error": None
        }

        try:
            # Stage 1: Knowledge Retrieval (Hybrid Strategy) /  1: 
            self._print("\n--- STAGE 1: KNOWLEDGE RETRIEVAL (HYBRID) ---")
            self._print("---  1: ---")

            # Step 1: Try traditional retrieval first /  1: 
            self._print("   Step 1: Traditional knowledge base retrieval...")
            self._print("    1: ...")
            relevant_rules = self.retriever.get_knowledge(problem_text)

            if relevant_rules:
                self._print(f"   Found {len(relevant_rules)} rules from knowledge base")
                self._print(f"    {len(relevant_rules)} ")
                results["retrieval_method"] = "traditional"

            # Step 2: If insufficient rules found, use AI generation /  2:  AI 
            if self.use_ai_retriever and len(relevant_rules) < self.min_rules_threshold:
                self._print(f"   Step 2: Insufficient rules (< {self.min_rules_threshold}), using AI generation...")
                self._print(f"    2: < {self.min_rules_threshold} AI ...")

                try:
                    # Generate rules using AI /  AI 
                    ai_generated_rules = self.ai_retriever.get_knowledge(problem_text)

                    if ai_generated_rules:
                        self._print(f"   AI generated {len(ai_generated_rules)} new rules")
                        self._print(f"   AI  {len(ai_generated_rules)} ")

                        # Combine traditional + AI generated rules /  AI 
                        relevant_rules.extend(ai_generated_rules)
                        results["retrieval_method"] = "hybrid"
                        results["ai_generated_rules"] = ai_generated_rules

                        if self.auto_enrich_kb:
                            self._print("   New rules saved to knowledge base for future use")
                            self._print("   ")
                    else:
                        self._print("   AI generation returned no rules")
                        self._print("   AI ")

                except Exception as e:
                    self._print(f"   AI retrieval failed: {e}")
                    self._print(f"   AI : {e}")
                    self._print("   Continuing with traditional retrieval results...")
                    self._print("   ...")

            if not relevant_rules:
                self._print("   Warning: No relevant knowledge found. Proceeding without domain knowledge.")
                self._print("   : ")
                results["retrieval_method"] = "none"

            results["retrieved_knowledge"] = relevant_rules
            self._print(f"   Total rules retrieved: {len(relevant_rules)}")
            self._print(f"   : {len(relevant_rules)}")

            # Stage 2: Causal Scaffolding /  2:
            self._print("\n--- STAGE 2: CAUSAL SCAFFOLDING ---")
            self._print("---  2:  ---")

            # 新增：根据scaffolder类型调用不同的方法
            if self.use_multi_agent:
                causal_plan = self.scaffolder.generate_scaffold_parallel(problem_text, relevant_rules)
            else:
                causal_plan = self.scaffolder.generate_scaffold(problem_text, relevant_rules)
            # ===== Visualization with organized folder structure =====
            from engine.causal_graph_visualizer import visualize_causal_graph
            from pathlib import Path

            # Determine visualization path based on method and problem_id
            if method_name and problem_id:
                # Use method-based folder and problem_id naming
                viz_dir = Path("visualization_output") / method_name
                viz_dir.mkdir(parents=True, exist_ok=True)
                viz_path = viz_dir / f"{problem_id}.png"
            else:
                # Fallback to hash-based naming for standalone usage
                viz_path = f"visualization_output/graph_{hash(problem_text) % 10000}.png"

            visualize_causal_graph(causal_plan, str(viz_path))
            # ====================
            print(causal_plan)
            if not causal_plan:
                results["error"] = "Failed to generate causal scaffold"
                return results

            # Validate scaffold structure / 
            if not self.scaffolder.validate_scaffold(causal_plan):
                results["error"] = "Invalid scaffold structure"
                return results

            results["causal_scaffold"] = causal_plan

            # Stage 3: Computation (Choose mode: symbolic or llm) / 阶段3: 计算（选择模式：符号执行或LLM）
            # Added: Conditional computation based on mode / 新增：根据模式选择计算方式
            if False:  # symbolic mode removed
                # Original pipeline: Code Generation + Symbolic Execution / 原始流程：代码生成 + 符号执行
                self._print("\n--- STAGE 3: CODE GENERATION (Symbolic Mode) ---")
                self._print("---  3: 代码生成（符号执行模式）---")
                generated_code = self.code_generator.generate_code(causal_plan)

                if not generated_code:
                    results["error"] = "Failed to generate code from causal scaffold"
                    return results

                results["generated_code"] = generated_code

                # Stage 3.5: Sandbox Execution /  3.5: 沙箱执行
                self._print("\n--- STAGE 3.5: SANDBOX EXECUTION ---")
                self._print("---  3.5: 沙箱执行 ---")
                execution_result = self.sandbox_executor.execute_code(generated_code, causal_plan)

                if not execution_result['success']:
                    results["error"] = f"Failed during sandbox execution: {execution_result['error']}"
                    results["execution_result"] = execution_result
                    return results

                # Enhance scaffold with execution results / 用执行结果增强脚手架
                executed_plan = causal_plan.copy()
                executed_plan["generated_code"] = generated_code
                executed_plan["execution_result"] = execution_result
                executed_plan["final_answer"] = execution_result['result']

                results["executed_scaffold"] = executed_plan
                results["final_answer"] = execution_result['result']
                results["execution_result"] = execution_result
                results["computation_mode"] = "symbolic"

            elif self.computation_mode == "llm":
                # Alternative pipeline: LLM-based Computation / 替代流程：基于LLM的计算
                self._print("\n--- STAGE 3: LLM-BASED COMPUTATION (LLM Mode) ---")
                self._print("---  3: 基于LLM的计算（LLM模式）---")

                computation_result = self.llm_computer.compute_from_scaffold(
                    causal_scaffold=causal_plan,
                    problem_text=problem_text
                )

                if not computation_result['success']:
                    results["error"] = f"Failed during LLM computation: {computation_result.get('error', 'Unknown error')}"
                    results["computation_result"] = computation_result
                    return results

                # Enhance scaffold with computation results / 用计算结果增强脚手架
                executed_plan = causal_plan.copy()
                executed_plan["computation_result"] = computation_result
                executed_plan["final_answer"] = computation_result['result']
                executed_plan["reasoning"] = computation_result.get('reasoning', '')

                results["executed_scaffold"] = executed_plan
                results["final_answer"] = computation_result['result']
                results["computation_result"] = computation_result
                results["computation_mode"] = "llm"

            else:
                results["error"] = f"Invalid computation_mode: {self.computation_mode}. Must be 'symbolic' or 'llm'."
                return results

            # Stage 4: Synthesis & Validation /  4: 
            self._print("\n--- STAGE 4: SYNTHESIS & VALIDATION ---")
            self._print("---  4:  ---")

            # Generate explanation / 
            explanation = self.synthesizer.generate_explanation(executed_plan)
            results["explanation"] = explanation

            # Run counterfactual validation if requested / 
            if include_validation:
                validation = self.synthesizer.run_counterfactual_check(executed_plan)
                results["validation"] = validation

            # Mark as successful / 
            results["success"] = True

            # Save output if path provided / 
            if save_output:
                self._save_results(results, save_output)

        except Exception as e:
            self._print("\n" + "="*70)
            self._print("❌ ERROR DURING PIPELINE EXECUTION")
            self._print("❌ ")
            self._print("="*70)
            self._print(f"\nError: {e}")
            self._print(f": {e}")

            import traceback
            tb = traceback.format_exc()
            results["error"] = str(e)
            results["traceback"] = tb

            self._print("\nFull Traceback:")
            self._print("")
            self._print(tb)
            self._print("="*70)

        return results

    def _save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """
        Save results to a JSON file.
         JSON 

        Args:
            results: The results dictionary
                     
            output_path: Path to save the JSON file
                          JSON 
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self._print(f"\nResults saved to: {output_file}")
        self._print(f": {output_file}")

    def display_results(self, results: Dict[str, Any]) -> None:
        """
        Display results in a formatted, human-readable way.
        

        Args:
            results: The results dictionary from solve_problem
                      solve_problem 
        """
        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("")
        print("=" * 70)

        if not results.get("success"):
            print(f"\n❌ Error: {results.get('error')}")
            print(f"❌ : {results.get('error')}")

            if results.get("traceback"):
                print("\nFull Traceback:")
                print("")
                print(results.get("traceback"))
            return

        print(f"\n Problem / :")
        print(f"   {results['problem']}")

        print(f"\n Final Answer / :")
        print(f"   {results.get('final_answer')}")

        print(f"\n Explanation / :")
        print(results.get('explanation', 'N/A'))

        if 'validation' in results:
            print(f"\n Counterfactual Validation / :")
            print(results.get('validation'))

        print("\n" + "=" * 70)


def main():
    """
    Main entry point for command-line usage.
    
    """
    parser = argparse.ArgumentParser(
        description="Causal Reasoning Engine for solving math and physics problems\n"
                    ""
    )

    parser.add_argument(
        "-p", "--problem",
        type=str,
        help="Problem text to solve / "
    )

    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Path to file containing problem text / "
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to save output JSON /  JSON "
    )

    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip counterfactual validation / "
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output / "
    )

    parser.add_argument(
        "--kb",
        type=str,
        default="data/knowledge_base.json",
        help="Path to knowledge base JSON /  JSON "
    )

    parser.add_argument(
        "--no-ai-retriever",
        action="store_true",
        help="Disable AI knowledge retriever /  AI "
    )

    parser.add_argument(
        "--no-auto-enrich",
        action="store_true",
        help="Don't automatically save AI-generated rules to KB /  AI "
    )

    parser.add_argument(
        "--min-rules",
        type=int,
        default=2,
        help="Minimum rules threshold before using AI generation /  AI "
    )

    # 新增：多智能体相关参数
    parser.add_argument(
        "--multi-agent",
        action="store_true",
        help="Use multi-agent scaffolder (3 generators + 1 critic) / 使用多智能体脚手架器（3个生成器 + 1个批判者）"
    )

    parser.add_argument(
        "--num-generators",
        type=int,
        default=3,
        help="Number of parallel generator agents (default: 3) / 并行生成器数量（默认：3）"
    )

    parser.add_argument(
        "--generator-temp",
        type=float,
        default=0.3,
        help="Temperature for generator agents (default: 0.3) / 生成器温度（默认：0.3）"
    )

    parser.add_argument(
        "--critic-temp",
        type=float,
        default=0.0,
        help="Temperature for critic agent (default: 0.0) / 批判者温度（默认：0.0）"
    )

    args = parser.parse_args()

    # Get problem text / 
    if args.problem:
        problem_text = args.problem
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            problem_text = f.read()
    else:
        # Interactive mode / 
        print("Enter your problem (press Ctrl+D or Ctrl+Z when done):")
        print(" Ctrl+D  Ctrl+Z:")
        problem_text = sys.stdin.read()

    # Initialize engine /
    engine = CausalReasoningEngine(
        knowledge_base_path=args.kb,
        verbose=not args.quiet,
        use_ai_retriever=not args.no_ai_retriever,
        auto_enrich_kb=not args.no_auto_enrich,
        min_rules_threshold=args.min_rules,
        use_multi_agent=args.multi_agent,  # 新增
        num_generators=args.num_generators,  # 新增
        generator_temperature=args.generator_temp,  # 新增
        critic_temperature=args.critic_temp  # 新增
    )

    # Solve problem / 
    results = engine.solve_problem(
        problem_text,
        include_validation=not args.no_validation,
        save_output=args.output
    )

    # Display results / 
    engine.display_results(results)

    # Exit with appropriate code / 
    sys.exit(0 if results.get("success") else 1)


# Example usage when run as a script / 
if __name__ == "__main__":
    # If no command-line arguments, run demo / 
    if len(sys.argv) == 1:
        print("Running demo problem...")
        print("...\n")

        demo_problem = """
     "$分别沿x轴正向和负向传播的两列简谐横波P、Q的振动方向相同，振幅均为5 cm，波长均为8 m，波速均为4 m/s。t=0时刻，P波刚好传播到坐标原点，该处的质点将自平衡位置向下振动；Q波刚好传到x=10 m处，该处的质点将自平衡位置向上振动。经过一段时间后，两列波相遇。$\n\n<img_1191>\n求出图示范围内的介质中，因两列波干涉而振动振幅最大的平衡位置。",

   """

        engine = CausalReasoningEngine()
        results = engine.solve_problem(demo_problem)
        engine.display_results(results)
    else:
        # Run with command-line arguments / 
        main()
