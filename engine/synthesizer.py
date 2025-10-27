"""
Causal Synthesizer & Validator Module
因果合成与验证模块

This module translates structured computational results back into human-readable
explanations and validates the causal understanding through counterfactual reasoning.

本模块将结构化的计算结果转换回人类可读的解释，并通过反事实推理验证因果理解。
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from .scaffolder import LLMClient


class CausalSynthesizer:
    """
    Causal Synthesis and Validation Engine.
    因果合成与验证引擎

    This class generates human-readable explanations from executed scaffolds
    and validates causal understanding using counterfactual reasoning.

    此类从执行的脚手架生成人类可读的解释，并使用反事实推理验证因果理解。
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        explanation_prompt_path: str = "prompts/explanation_prompt.txt",
        validation_prompt_path: str = "prompts/validation_prompt.txt"
    ):
        """
        Initialize the causal synthesizer.
        初始化因果合成器

        Args:
            llm_client: LLM client instance (creates default if None)
                        LLM客户端实例（如果为None则创建默认实例）
            explanation_prompt_path: Path to explanation prompt template
                                     解释提示词模板的路径
            validation_prompt_path: Path to validation prompt template
                                    验证提示词模板的路径
        """
        self.llm_client = llm_client or LLMClient()
        self.explanation_template = self._load_template(explanation_prompt_path, "explanation")
        self.validation_template = self._load_template(validation_prompt_path, "validation")

    def _load_template(self, template_path: str, template_type: str) -> str:
        """
        Load a prompt template from file.
        

        Args:
            template_path: Path to the template file
                           
            template_type: Type of template ('explanation' or 'validation')
                           'explanation'  'validation'

        Returns:
            The template string
            
        """
        path = Path(template_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Return default template
            # 
            if template_type == "explanation":
                return self._get_default_explanation_template()
            elif template_type == "validation":
                return self._get_default_validation_template()
            else:
                raise ValueError(f"Unknown template type: {template_type}")

    def _get_default_explanation_template(self) -> str:
        """
        Get default explanation prompt template.
        

        Returns:
            Default explanation template
            
        """
        return """**ROLE:**
You are a science communicator. Your task is to explain the solution to a physics or mathematics problem based on a provided structured plan and its results.

**INSTRUCTIONS:**
Generate a clear, step-by-step, human-readable explanation of how the final answer was calculated. Follow the computation plan, state the rule or formula used for each step, and present the calculated values.

**SOLVED PLAN:**
{executed_scaffold}

**EXPLANATION:**
Please provide a concise, clear explanation of the solution process.
"""

    def _get_default_validation_template(self) -> str:
        """
        Get default validation prompt template.
        

        Returns:
            Default validation template
            
        """
        return """**ROLE:**
You are a causal analyst. Your task is to reason about a hypothetical change to a problem based on its established causal structure. Do not resolve the entire problem from scratch; use the provided causal graph to predict the outcome.

**INSTRUCTIONS:**
Based on the provided causal structure, answer the "What if" question. Explain which downstream variables would be affected by the change and calculate the new final answer.

**ORIGINAL CAUSAL STRUCTURE:**
{causal_scaffold}

**COUNTERFACTUAL QUESTION:**
{counterfactual_question}

**ANALYSIS AND NEW RESULT:**
Please provide your reasoning and the new calculated result.
"""

    def generate_explanation(self, executed_scaffold: Dict[str, Any]) -> str:
        """
        Generate a human-readable explanation from an executed scaffold.
        从执行的脚手架生成人类可读的解释

        This method takes the structured results and produces a natural language
        explanation of the solution process.

        此方法获取结构化结果并生成解决过程的自然语言解释。

        Args:
            executed_scaffold: The scaffold with execution results
                               包含执行结果的脚手架

        Returns:
            Natural language explanation
            自然语言解释
        """
        print("Generating explanation...")
        print("正在生成解释...")

        # Format the executed scaffold as JSON string
        #  JSON 
        scaffold_str = json.dumps(executed_scaffold, indent=2, ensure_ascii=False)

        # Construct the prompt
        # 
        prompt = self.explanation_template.format(executed_scaffold=scaffold_str)

        # Get LLM response
        #  LLM 
        try:
            explanation = self.llm_client.complete(prompt, temperature=0.3)
            print("Explanation generated successfully.")
            print("")
            return explanation
        except Exception as e:
            print(f"Error generating explanation: {e}")
            print(f": {e}")
            return f"Error generating explanation: {e}"

    def run_counterfactual_check(
        self,
        executed_scaffold: Dict[str, Any],
        variable_to_change: Optional[str] = None,
        new_value: Optional[float] = None,
        custom_question: Optional[str] = None
    ) -> str:
        """
        Perform counterfactual validation using causal reasoning.
        

        This method tests the model's causal understanding by asking
        "what if" questions about changes to input variables.

        ""

        Args:
            executed_scaffold: The original executed scaffold
                               
            variable_to_change: Variable to modify in the counterfactual
                                
            new_value: New value for the variable
                       
            custom_question: Custom counterfactual question (overrides auto-generation)
                             

        Returns:
            LLM's counterfactual analysis
            LLM 
        """
        print("Running counterfactual validation...")
        print("...")

        # Check if this is a symbolic problem (has null values in knowns)
        # 检查是否为符号问题（knowns中有null值）
        knowns = executed_scaffold.get("knowns", {})
        is_symbolic = any(v is None for v in knowns.values())

        if is_symbolic:
            print("Skipping counterfactual validation for symbolic problem.")
            print("符号问题跳过反事实验证。")
            return "Counterfactual validation is not applicable for symbolic expressions. The result is a general formula that represents all possible input combinations."

        # Extract original causal structure (without results)
        #
        causal_scaffold = {
            "target_variable": executed_scaffold.get("target_variable"),
            "knowns": executed_scaffold.get("knowns"),
            "causal_graph": executed_scaffold.get("causal_graph"),
            "computation_plan": executed_scaffold.get("computation_plan")
        }

        scaffold_str = json.dumps(causal_scaffold, indent=2, ensure_ascii=False)

        # Generate or use custom counterfactual question
        #
        if custom_question:
            counterfactual_q = custom_question
        else:
            # Auto-generate question
            #
            if not variable_to_change or new_value is None:
                # Use a default example variable
                #
                if knowns:
                    variable_to_change = list(knowns.keys())[0]
                    original_value = knowns[variable_to_change]
                    new_value = original_value * 2  # Double the value as example

            target = executed_scaffold.get("target_variable", "result")
            counterfactual_q = (
                f"Based on the original problem, what would the '{target}' be if "
                f"the value of '{variable_to_change}' was {new_value} instead?"
            )

        # Construct the prompt
        # 
        prompt = self.validation_template.format(
            causal_scaffold=scaffold_str,
            counterfactual_question=counterfactual_q
        )

        # Get LLM response
        #  LLM 
        try:
            validation = self.llm_client.complete(prompt, temperature=0.3)
            print("Counterfactual validation completed.")
            print("")
            return validation
        except Exception as e:
            print(f"Error in counterfactual validation: {e}")
            print(f": {e}")
            return f"Error in validation: {e}"

    def validate_with_multiple_counterfactuals(
        self,
        executed_scaffold: Dict[str, Any],
        counterfactual_scenarios: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Run multiple counterfactual scenarios for comprehensive validation.
        

        Args:
            executed_scaffold: The original executed scaffold
                               
            counterfactual_scenarios: List of scenarios, each with 'variable' and 'new_value'
                                       'variable'  'new_value'

        Returns:
            List of validation results
            
        """
        results = []

        for i, scenario in enumerate(counterfactual_scenarios, 1):
            print(f"\n--- Counterfactual Scenario {i} ---")
            print(f"---  {i} ---")

            var = scenario.get("variable")
            val = scenario.get("new_value")

            result = self.run_counterfactual_check(
                executed_scaffold,
                variable_to_change=var,
                new_value=val
            )
            results.append(result)

        return results

    def generate_full_report(
        self,
        executed_scaffold: Dict[str, Any],
        include_validation: bool = True
    ) -> str:
        """
        Generate a comprehensive report with explanation and validation.
        

        Args:
            executed_scaffold: The executed scaffold
                               
            include_validation: Whether to include counterfactual validation
                                

        Returns:
            Full report string
            
        """
        report_parts = []

        # Add header
        # 
        report_parts.append("=" * 60)
        report_parts.append("CAUSAL REASONING REPORT")
        report_parts.append("")
        report_parts.append("=" * 60)

        # Add explanation section
        # 
        report_parts.append("\n--- SOLUTION EXPLANATION ---")
        report_parts.append("---  ---\n")
        explanation = self.generate_explanation(executed_scaffold)
        report_parts.append(explanation)

        # Add validation section if requested
        # 
        if include_validation:
            report_parts.append("\n\n--- COUNTERFACTUAL VALIDATION ---")
            report_parts.append("---  ---\n")
            validation = self.run_counterfactual_check(executed_scaffold)
            report_parts.append(validation)

        # Add footer
        # 
        report_parts.append("\n" + "=" * 60)

        return "\n".join(report_parts)


# Example usage / 
if __name__ == "__main__":
    # Test executed scaffold / 
    test_executed_scaffold = {
        "target_variable": "final_velocity",
        "knowns": {
            "mass": 10,
            "force": 50,
            "time": 5,
            "initial_velocity": 0
        },
        "causal_graph": [
            {
                "cause": ["force", "mass"],
                "effect": "acceleration",
                "rule": "Newton's Second Law (F = m * a)"
            },
            {
                "cause": ["initial_velocity", "acceleration", "time"],
                "effect": "final_velocity",
                "rule": "Kinematic Equation (v_f = v_i + a * t)"
            }
        ],
        "computation_plan": [
            {
                "id": "step1",
                "operation": "solve_for",
                "target": "acceleration",
                "inputs": ["force", "mass"],
                "tool": "symbolic_solver"
            },
            {
                "id": "step2",
                "operation": "solve_for",
                "target": "final_velocity",
                "inputs": ["initial_velocity", "acceleration", "time"],
                "tool": "symbolic_solver"
            }
        ],
        "results": {
            "step1": 5.0,
            "step2": 25.0
        },
        "final_answer": 25.0
    }

    # Initialize synthesizer / 
    synthesizer = CausalSynthesizer()

    # Generate full report / 
    report = synthesizer.generate_full_report(test_executed_scaffold)
    print(report)
