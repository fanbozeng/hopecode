"""
Direct LLM Baseline
 LLM 

This method directly asks the LLM to solve the problem without any
chain-of-thought prompting or additional reasoning steps.

 LLM 

Usage:
    from baselines import DirectLLM

    solver = DirectLLM()
    answer = solver.solve("What is 2 + 2?")
"""

import re
from typing import Optional, Tuple
from engine.scaffolder import LLMClient
from .answer_extractor import extract_answer  # 修复：使用相对导入 / Fixed: use relative import


class DirectLLM:
    """
    Direct LLM Answer Method
     LLM 

    This is the simplest baseline where we directly ask the LLM
    to provide an answer without any structured reasoning.

     LLM 
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, temperature: float = 0.0):
        """
        Initialize Direct LLM solver
         LLM 

        Args:
            llm_client: LLM client instance (creates default if None)
                        LLM  None 
            temperature: Sampling temperature (0.0 for deterministic)
                         0.0 
        """
        self.llm_client = llm_client or LLMClient()
        self.temperature = temperature

    def solve(self, problem: str) -> str:
        """
        Solve problem using direct LLM
         LLM 

        Args:
            problem: Problem statement
                     

        Returns:
            Final answer
            
        """
        prompt = self._build_prompt(problem)

        try:
            response = self.llm_client.complete(prompt, temperature=self.temperature)
            answer = extract_answer(response)
            return answer
        except Exception as e:
            raise Exception(f"Direct LLM failed: {e}")

    def _build_prompt(self, problem: str) -> str:
        """
        Build prompt for direct LLM
         LLM 

        Args:
            problem: Problem statement
                     

        Returns:
            Formatted prompt
            
        """
        return f"""Solve the following problem and provide the final answer.

Problem: {problem}

IMPORTANT: You must end your response with your final answer in ONE of these formats:
- "Final answer: " followed by your result
- "The final answer is " followed by your result
- "Therefore, the answer is " followed by your result

Your final answer can be:
- A number (e.g., Final answer: 42)
- An interval (e.g., Final answer: [2, 5])
- A set (e.g., Final answer: {{1, 3, 5}})
- An expression (e.g., Final answer: 2x + 3)
- Any other mathematical result

Do NOT write placeholder text like "[your answer]" - write the actual computed result."""


# Example usage / 
if __name__ == "__main__":
    # Test the Direct LLM solver
    #  LLM 

    print("="*60)
    print("Direct LLM Baseline Test")
    print(" LLM ")
    print("="*60)

    solver = DirectLLM()

    # Test problems
    # 
    test_problems = [
       "将电动势为3.0 V的电源接入电路中,测得电源两极间的电压为2.4 V,当电路中有6 C的电荷流过时,求：\n外电路中有多少电能转化为其他形式的能；",

    ]

    for i, problem in enumerate(test_problems, 1):
        print(f"\nProblem {i}: {problem}")
        print(f" {i}: {problem}")

        try:
            answer = solver.solve(problem)
            print(f"Answer: {answer}")
            print(f": {answer}")
        except Exception as e:
            print(f"Error: {e}")
            print(f": {e}")
