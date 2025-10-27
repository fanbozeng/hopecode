"""
Zero-Shot Chain-of-Thought (CoT) Baseline


This method uses the "Let's think step by step" prompt to elicit
chain-of-thought reasoning from the LLM without providing examples.

"" LLM 


Reference:
    Kojima et al., "Large Language Models are Zero-Shot Reasoners", 2022

Usage:
    from baselines import ZeroShotCoT

    solver = ZeroShotCoT()
    answer, reasoning = solver.solve("What is 2 + 2?")
"""

import re
from typing import Optional, Tuple
from engine.scaffolder import LLMClient
from .answer_extractor import extract_answer  # 修复：使用相对导入 / Fixed: use relative import


class ZeroShotCoT:
    """
    Zero-Shot Chain-of-Thought Method
    

    This method prompts the LLM to think step-by-step without
    providing any examples, following the approach from Kojima et al. (2022).

     LLM 
     Kojima 2022
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        temperature: float = 0.3
    ):
        """
        Initialize Zero-Shot CoT solver
         CoT 

        Args:
            llm_client: LLM client instance
                        LLM 
            temperature: Sampling temperature (higher = more creative)
                         
        """
        self.llm_client = llm_client or LLMClient()
        self.temperature = temperature

    def solve(self, problem: str) -> Tuple[str, str]:
        """
        Solve problem using Zero-Shot CoT
         CoT 

        Args:
            problem: Problem statement
                     

        Returns:
            Tuple of (answer, reasoning_steps)
            (, ) 
        """
        prompt = self._build_prompt(problem)

        try:
            response = self.llm_client.complete(prompt, temperature=self.temperature)
            answer = extract_answer(response)
            return answer, response
        except Exception as e:
            raise Exception(f"Zero-Shot CoT failed: {e}")

    def _build_prompt(self, problem: str) -> str:
        """
        Build Zero-Shot CoT prompt
         CoT 

        The key is the "Let's think step by step" phrase which triggers
        chain-of-thought reasoning.

        ""

        Args:
            problem: Problem statement
                     

        Returns:
            Formatted prompt
            
        """
        return f"""Solve the following problem step by step. Think carefully and show your reasoning.

Problem: {problem}

Let's think step by step:

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
"""


# Example usage / 
if __name__ == "__main__":
    print("="*60)
    print("Zero-Shot Chain-of-Thought Baseline Test")
    print("")
    print("="*60)

    solver = ZeroShotCoT()

    # Test problems
    test_problems = [
        "Janet's ducks lay 16 eggs per day. She eats three for breakfast and bakes four into muffins. She sells the rest for $2 each. How much does she make per day?",
        "A store has 20 apples. They sell 8 in the morning and 5 in the afternoon. How many are left?",
        "If John reads 3 books per week, how many books does he read in 4 weeks?"
    ]

    for i, problem in enumerate(test_problems, 1):
        print(f"\n{'='*60}")
        print(f"Problem {i}:")
        print(problem)
        print(f"\n {i}:")
        print(problem)

        try:
            answer, reasoning = solver.solve(problem)

            print(f"\n--- Reasoning /  ---")
            # Print first 200 chars of reasoning
            print(reasoning[:200] + "..." if len(reasoning) > 200 else reasoning)

            print(f"\n--- Final Answer /  ---")
            print(f"Answer: {answer}")
            print(f": {answer}")

        except Exception as e:
            print(f"\nError: {e}")
            print(f": {e}")
