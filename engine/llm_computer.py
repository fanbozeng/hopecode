"""
LLM-Based Computer (Alternative to Symbolic Executor)
基于LLM的计算器（符号执行器的替代方案）

This module provides an alternative to symbolic execution by using LLM to compute
results based on the causal scaffold. This is useful for ablation studies comparing
symbolic execution vs. LLM-based computation.

此模块提供了符号执行的替代方案，使用LLM基于因果脚手架计算结果。
这对于比较符号执行与基于LLM的计算的消融研究很有用。
"""

import json
from typing import Dict, Any, Optional
from .scaffolder import LLMClient


class LLMComputer:
    """
    LLM-based computation alternative to symbolic executor.
    基于LLM的计算器，作为符号执行器的替代方案。

    This class takes a causal scaffold and uses LLM to perform computations,
    instead of generating and executing Python code.

    该类接收因果脚手架并使用LLM执行计算，而不是生成和执行Python代码。
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, verbose: bool = True):
        """
        Initialize LLM Computer / 初始化LLM计算器

        Args:
            llm_client: LLM client instance (optional)
                       LLM客户端实例（可选）
            verbose: Print detailed output
                    打印详细输出
        """
        self.llm_client = llm_client or LLMClient()
        self.verbose = verbose

    def _print(self, message: str) -> None:
        """Print message if verbose / 如果verbose则打印消息"""
        if self.verbose:
            print(message)

    def compute_from_scaffold(
        self,
        causal_scaffold: Dict[str, Any],
        problem_text: str
    ) -> Dict[str, Any]:
        """
        Compute answer using LLM based on causal scaffold.
        使用LLM基于因果脚手架计算答案。

        This method takes the causal scaffold (which outlines the logical structure
        and computation steps) and asks LLM to perform the actual computation.

        此方法接收因果脚手架（概述逻辑结构和计算步骤），并要求LLM执行实际计算。

        Args:
            causal_scaffold: The causal scaffold containing computation plan
                           包含计算计划的因果脚手架
            problem_text: Original problem text
                         原始问题文本

        Returns:
            Dictionary with computation results:
            包含计算结果的字典：
            {
                'success': bool,
                'result': final answer,
                'reasoning': computation steps,
                'error': error message if failed
            }
        """
        self._print("\n--- LLM-BASED COMPUTATION (Alternative to Symbolic Execution) ---")
        self._print("--- 基于LLM的计算（符号执行的替代方案）---\n")

        try:
            # Extract key information from scaffold
            # 从脚手架中提取关键信息
            variables = causal_scaffold.get('variables', {})
            dependencies = causal_scaffold.get('dependencies', {})
            computation_plan = causal_scaffold.get('computation_plan', [])
            target_variable = causal_scaffold.get('target_variable', '')

            self._print(f"Target variable to compute: {target_variable}")
            self._print(f"要计算的目标变量: {target_variable}")
            self._print(f"Number of computation steps: {len(computation_plan)}")
            self._print(f"计算步骤数: {len(computation_plan)}\n")

            # Create a structured prompt for LLM
            # 为LLM创建结构化提示
            prompt = self._create_computation_prompt(
                problem_text=problem_text,
                causal_scaffold=causal_scaffold,
                variables=variables,
                dependencies=dependencies,
                computation_plan=computation_plan,
                target_variable=target_variable
            )

            self._print("Calling LLM for computation...")
            self._print("调用LLM进行计算...\n")

            # Call LLM to compute
            # 调用LLM计算
            response = self.llm_client.complete(prompt, temperature=0.0)
            print( response);

            if not response:
                return {
                    'success': False,
                    'result': None,
                    'reasoning': None,
                    'error': 'LLM returned empty response'
                }

            self._print(f"✓ LLM response received ({len(response)} characters)")
            self._print(f"✓ 已收到LLM响应 ({len(response)} 字符)\n")

            # Extract final answer from response
            # 从响应中提取最终答案
            final_answer = self._extract_final_answer(response)

            if final_answer is None:
                self._print("⚠ Warning: Could not extract final answer from LLM response")
                self._print("⚠ 警告: 无法从LLM响应中提取最终答案")
                return {
                    'success': False,
                    'result': None,
                    'reasoning': response,
                    'error': 'Could not extract final answer'
                }

            self._print(f"✓ Final answer computed: {final_answer}")
            self._print(f"✓ 计算出的最终答案: {final_answer}\n")

            return {
                'success': True,
                'result': final_answer,
                'reasoning': response,
                'error': None
            }

        except Exception as e:
            self._print(f"\n❌ Error during LLM computation: {e}")
            self._print(f"❌ LLM计算过程中出错: {e}\n")

            return {
                'success': False,
                'result': None,
                'reasoning': None,
                'error': str(e)
            }

    def _create_computation_prompt(
        self,
        problem_text: str,
        causal_scaffold: Dict[str, Any],
        variables: Dict[str, Any],
        dependencies: Dict[str, Any],
        computation_plan: list,
        target_variable: str
    ) -> str:
        """
        Create a structured prompt for LLM computation.
        为LLM计算创建结构化提示。
        """
        # Format variables
        # 格式化变量
        variables_str = "\n".join([
            f"  - {name}: {info.get('description', 'N/A')}"
            for name, info in variables.items()
        ])

        # Format dependencies
        # 格式化依赖关系
        dependencies_str = "\n".join([
            f"  - {var} depends on: {', '.join(deps)}"
            for var, deps in dependencies.items()
        ])

        # Format computation plan
        # 格式化计算计划
        computation_steps_str = "\n".join([
            f"  {i+1}. {step.get('description', step.get('operation', 'N/A'))}"
            for i, step in enumerate(computation_plan)
        ])

        prompt = f"""You are a mathematical computation assistant. Given a causal scaffold that outlines the logical structure of a problem, perform the actual numerical computation step by step.

**Problem:**
{problem_text}

**Causal Scaffold:**

**Variables:**
{variables_str}

**Dependencies:**
{dependencies_str}

**Computation Plan:**
{computation_steps_str}

**Target Variable:** {target_variable}

---

**Instructions:**
1. Follow the computation plan step by step
2. Show your work for each step
3. Compute intermediate values as needed
4. Extract numerical values from the problem text
5. Perform all arithmetic operations carefully
6. Provide the final answer for the target variable: {target_variable}

**Output Format:**
```
Step 1: [description]
  Calculation: [show calculation]
  Result: [intermediate result]

Step 2: [description]
  Calculation: [show calculation]
  Result: [intermediate result]

...

Final Answer: [numerical value for {target_variable}]
```

**Important:**
- Your final line MUST be in the format: "Final Answer: [value]"
- Be precise with numerical calculations
- Show all intermediate steps clearly

Now, perform the computation:
"""
        return prompt

    def _extract_final_answer(self, response: str) -> Optional[Any]:
        """
        Extract final answer from LLM response.
        从LLM响应中提取最终答案。

        Args:
            response: LLM response text
                     LLM响应文本

        Returns:
            Final answer (number or string), or None if not found
            最终答案（数字或字符串），如果未找到则返回None
        """
        import re

        # Only look for "Final Answer:" pattern - simple and reliable
        # 只查找 "Final Answer:" 模式 - 简单可靠
        pattern = r'Final Answer:\s*([^\n]+)'
        match = re.search(pattern, response, re.IGNORECASE)

        if match:
            answer_text = match.group(1).strip()

            if self.verbose:
                print(f"[DEBUG] Found Final Answer: '{answer_text}'")

            # Return the answer as-is, let _compare_answers handle the comparison
            # 直接返回答案，让 _compare_answers 处理比较
            return answer_text

        # Could not find Final Answer pattern
        # 无法找到 Final Answer 模式
        if self.verbose:
            print(f"[DEBUG] No 'Final Answer:' pattern found in response")
        return None


# Export class / 导出类
__all__ = ['LLMComputer']
