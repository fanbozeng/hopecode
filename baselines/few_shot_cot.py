"""
Few-Shot Chain-of-Thought (CoT) Baseline


This method provides examples with step-by-step reasoning to guide
the LLM in solving similar problems.

 LLM 

Reference:
    Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", 2022

Usage:
    from baselines import FewShotCoT

    solver = FewShotCoT()
    answer, reasoning = solver.solve("What is 2 + 2?")
"""

import re
from typing import Optional, Tuple, List, Dict
from engine.scaffolder import LLMClient
from .answer_extractor import extract_answer  # 修复：使用相对导入 / Fixed: use relative import


class FewShotCoT:
    """
    Few-Shot Chain-of-Thought Method
    

    This method provides examples with step-by-step reasoning before
    asking the LLM to solve the target problem.

     LLM 
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        temperature: float = 0.3,
        examples: Optional[List[Dict[str, str]]] = None
    ):
        """
        Initialize Few-Shot CoT solver
         CoT 

        Args:
            llm_client: LLM client instance
                        LLM 
            temperature: Sampling temperature (higher = more creative)
                         
            examples: List of example problems with solutions
                      
        """
        self.llm_client = llm_client or LLMClient()
        self.temperature = temperature

        # Default examples if none provided
        # 
        self.examples = examples or self._get_default_examples()

    def _get_default_examples(self) -> List[Dict[str, str]]:
        """
        Get default few-shot examples
        

        Returns:
            List of example problems with step-by-step solutions
            
        """
        return [
            {
                "problem": "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?",
                "reasoning": """Step 1: Roger starts with 5 tennis balls.

Step 2: He buys 2 cans of tennis balls. Each can has 3 balls.
So the number of new balls = 2 cans × 3 balls/can = 6 balls

Step 3: Total tennis balls = Initial balls + New balls
Total = 5 + 6 = 11

Final answer: 11"""
            },
            {
                "problem": "A restaurant served 9 pizzas during lunch and 6 during dinner today. How many pizzas were served today?",
                "reasoning": """Step 1: Identify what we need to find - the total number of pizzas served today.

Step 2: During lunch, 9 pizzas were served.

Step 3: During dinner, 6 pizzas were served.

Step 4: Total pizzas = Lunch pizzas + Dinner pizzas
Total = 9 + 6 = 15

Final answer: 15"""
            },
            {
                "problem": "A store had 20 oranges in a bin. If they threw away 6 of the old ones and put 38 new ones in the bin, how many would be in the bin?",
                "reasoning": """Step 1: Start with 20 oranges in the bin.

Step 2: They threw away 6 old ones.
Remaining oranges = 20 - 6 = 14

Step 3: They added 38 new ones.
Final count = 14 + 38 = 52

Final answer: 52"""
            }
        ]

    def solve(self, problem: str) -> Tuple[str, str]:
        """
        Solve problem using Few-Shot CoT
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
            raise Exception(f"Few-Shot CoT failed: {e}")

    def _build_prompt(self, problem: str) -> str:
        """
        Build Few-Shot CoT prompt with examples
         CoT 

        Args:
            problem: Problem statement
                     

        Returns:
            Formatted prompt with examples
            
        """
        # Build examples section
        # 
        examples_text = ""
        for i, example in enumerate(self.examples, 1):
            examples_text += f"""Example {i}:
Problem: {example['problem']}

Solution:
{example['reasoning']}

"""

        # Build final prompt
        # 
        prompt = f"""Solve the following problems step by step, showing your reasoning clearly.

{examples_text}Now solve this problem:
Problem: {problem}

Solution:
IMPORTANT: You must end your solution with your final answer in ONE of these formats:
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

        return prompt

    def set_examples(self, examples: List[Dict[str, str]]):
        """
        Set custom examples for few-shot prompting
        

        Args:
            examples: List of dicts with 'problem' and 'reasoning' keys
                       'problem'  'reasoning' 
        """
        self.examples = examples

    def add_example(self, problem: str, reasoning: str):
        """
        Add a single example to the existing examples
        

        Args:
            problem: The example problem
                     
            reasoning: The step-by-step reasoning
                       
        """
        self.examples.append({
            "problem": problem,
            "reasoning": reasoning
        })


# Example usage / 
if __name__ == "__main__":
    print("="*60)
    print("Few-Shot Chain-of-Thought Baseline Test")
    print("")
    print("="*60)

    solver = FewShotCoT()

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
            # Print first 300 chars of reasoning
            print(reasoning[:300] + "..." if len(reasoning) > 300 else reasoning)

            print(f"\n--- Final Answer /  ---")
            print(f"Answer: {answer}")
            print(f": {answer}")

        except Exception as e:
            print(f"\nError: {e}")
            print(f": {e}")

    # Test with custom examples
    print(f"\n{'='*60}")
    print("Testing with Custom Examples")
    print("")
    print("="*60)

    custom_examples = [
        {
            "problem": "If a car travels 60 km/h for 2 hours, how far does it travel?",
            "reasoning": """Step 1: Identify the formula - Distance = Speed × Time

Step 2: Given values:
- Speed = 60 km/h
- Time = 2 hours

Step 3: Calculate distance:
Distance = 60 km/h × 2 hours = 120 km

Final answer: 120 km"""
        }
    ]

    custom_solver = FewShotCoT(examples=custom_examples)

    physics_problem = "A train travels at 80 km/h for 3 hours. How far does it travel?"
    print(f"\nProblem: {physics_problem}")
    print(f": {physics_problem}")

    try:
        answer, reasoning = custom_solver.solve(physics_problem)

        print(f"\n--- Reasoning /  ---")
        print(reasoning[:300] + "..." if len(reasoning) > 300 else reasoning)

        print(f"\n--- Final Answer /  ---")
        print(f"Answer: {answer}")
        print(f": {answer}")

    except Exception as e:
        print(f"\nError: {e}")
        print(f": {e}")
