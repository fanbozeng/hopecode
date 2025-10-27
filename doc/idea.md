  * * Of course. Here is a detailed technical plan for implementing the "Hybrid Causal Reasoning Engine" using a prompt-driven architecture. This plan is designed to be comprehensive enough to guide you and a code-generation assistant like Cursor in building the system.
      
        ------
      
        
      
        ## **Technical Plan: Prompt-Driven Causal Reasoning Engine**
      
        
      
        
      
        ### **1. Overview & System Architecture**
      
        
      
        This document outlines the technical specification for a system designed to solve mathematical and physics problems by emulating causal reasoning. The core principle is to deconstruct the problem-solving process into distinct, verifiable stages, leveraging a Large Language Model (LLM) as a "causal coordinator" rather than an end-to-end solver. This neuro-symbolic approach combines the LLM's language understanding with the precision of external symbolic tools, addressing known LLM weaknesses in multi-step logic and computational accuracy.1
      
        The system operates via a four-stage pipeline, managed by a central orchestrator script:
      
        1. **Knowledge Retrieval (RAG):** Fetches relevant formulas and principles.
        2. **Causal Scaffolding:** The LLM plans the solution by generating a structured JSON object (a computational representation of a Structural Causal Model).
        3. **Symbolic Execution:** An external tool executes the plan, ensuring mathematical precision.
        4. **Synthesis & Validation:** The LLM explains the result and validates its causal understanding through counterfactual reasoning.
      
        **System Architecture Diagram:**
      
        ```
        |
               v
        +--------------------------+
        
        | 1. Knowledge Retriever |
        | (RAG Module) |
        +--------------------------+
        
        | (Problem + Relevant Rules)
               v
        +--------------------------+
        
        | 2. Causal Scaffolding |
        | (LLM Prompt) |
        +--------------------------+
        
        | (Structured JSON Plan)
               v
        +--------------------------+
        
        | 3. Symbolic Execution |
        | (Python + SymPy/API) |
        +--------------------------+
        
        | (JSON Plan with Results)
               v
        +--------------------------+
        
        | 4. Synthesis & Validation|
        | (LLM Prompts) |
        +--------------------------+
        |
               v
        [Final Answer: Explanation & Validation]
        ```
      
        ------
      
        
      
        ### **2. Component Breakdown**
      
        
      
        
      
        #### **Component 1: Knowledge Retriever (RAG)**
      
        
      
        - **Objective:** To provide the LLM with accurate, domain-specific knowledge (formulas, constants, principles) relevant to the input problem, mitigating knowledge gaps and hallucinations.3
      
        - **Mechanism:**
      
          1. **Keyword Extraction:** A simple LLM call or a regex-based function extracts key physical or mathematical concepts from the user's problem (e.g., "force", "mass", "velocity", "integral").
          2. **Knowledge Base Query:** The extracted keywords are used to search a local knowledge base.
      
        - **Implementation Details:**
      
          - **Knowledge Base:** Create a `knowledge_base.json` file. This file will contain a list of objects, each with "keywords" and a "rule" or "formula".
      
            JSON
      
            ```
            [
              {
                "keywords": ["force", "mass", "acceleration"],
                "rule": "Newton's Second Law: Force equals mass times acceleration (F=ma)."
              },
              {
                "keywords": ["velocity", "acceleration", "time", "initial velocity"],
                "rule": "Kinematic Equation: Final velocity equals initial velocity plus acceleration multiplied by time (v_f = v_i + a*t)."
              }
            ]
            ```
      
          - **Retrieval Logic:** A Python script will load this JSON, iterate through the list, and return any "rule" where its "keywords" overlap with the keywords extracted from the problem.
      
        - **Input:** `problem_text: str`
      
        - **Output:** `retrieved_knowledge: List[str]`
      
        
      
        #### **Component 2: Causal Scaffolding Engine**
      
        
      
        - **Objective:** To translate the unstructured problem text into a structured, machine-readable JSON plan. This step forces the LLM to perform explicit logical planning before attempting a solution.5
      
        - **Mechanism:** A single, detailed API call to an LLM, using a carefully constructed prompt that includes the problem and the retrieved knowledge.
      
        - **Implementation Details (Prompt):** This is the core prompt of the system. It uses role-setting, few-shot examples, and strict formatting instructions to guide the LLM.7
      
          Đoạn mã
      
          ```
          **ROLE:**
          You are a specialized Causal Reasoning Engine for science. Your task is to deconstruct a natural language problem into a structured JSON object representing a Structural Causal Model (SCM). This JSON must define all variables, the causal relationships between them, and a precise computational plan.
          
          **CONTEXT:**
          Here are the relevant physical laws and formulas for this problem:
          ---
          {retrieved_knowledge}
          ---
          
          **INSTRUCTIONS:**
          Analyze the user's problem and generate a single JSON object with the following schema. Do NOT solve the problem or output any other text.
          
          1.  `target_variable`: (String) The final variable to be solved for.
          2.  `knowns`: (Object) A dictionary of all known variables and their numerical values from the problem text. Use snake_case for variable names.
          3.  `causal_graph`: (Array of Objects) Represents the causal links. Each object must have:
              - `cause`: (Array of Strings) The input variables.
              - `effect`: (String) The output variable.
              - `rule`: (String) The specific formula governing this link.
          4.  `computation_plan`: (Array of Objects) A step-by-step plan to solve for the target. Each object must have:
              - `id`: (String) A unique step identifier (e.g., "step1").
              - `operation`: (String) The operation to perform (e.g., "solve_for").
              - `target`: (String) The variable to calculate in this step.
              - `inputs`: (Array) Input variables for this step. Use strings for knowns or `{"ref": "step_id.output"}` to reference a previous step's result.
              - `tool`: (String) The required tool, e.g., "symbolic_solver".
          
          **EXAMPLE:**
          ---
          Problem: "What is the density of an object with a mass of 20 kg and a volume of 2 cubic meters?"
          JSON Output:
          ```json
          {
            "target_variable": "density",
            "knowns": { "mass": 20, "volume": 2 },
            "causal_graph": [
              { "cause": ["mass", "volume"], "effect": "density", "rule": "ρ = m/V" }
            ],
            "computation_plan": [
              { "id": "step1", "operation": "solve_for", "target": "density", "inputs": ["mass", "volume"], "tool": "symbolic_solver" }
            ]
          }
          ```
      
          ------
      
          **YOUR TASK:**
      
          Problem:
      
          {problem_text}
      
          **JSON Output:**
      
          ```
          
          ```
      
        - **Input:** `problem_text: str`, `retrieved_knowledge: List[str]`
      
        - **Output:** `causal_scaffold: dict` (a parsed JSON object)
      
        
      
        #### **Component 3: Symbolic Execution Engine**
      
        
      
        - **Objective:** To execute the `computation_plan` with perfect accuracy, offloading the calculation from the probabilistic LLM to a deterministic symbolic math library.9
        - **Mechanism:** A Python script that parses the `causal_scaffold` JSON and executes each step in order.
        - **Implementation Details:**
          1. Initialize a dictionary `results` to store the output of each step.
          2. Load the `knowns` from the JSON into a dictionary `variables`.
          3. Loop through the `computation_plan` array.
          4. For each step:
             - Resolve the `inputs` by fetching values from the `variables` dictionary or the `results` dictionary (for `{"ref":...}` dependencies).
             - Find the corresponding `rule` from the `causal_graph`.
             - Use the **SymPy** library to solve the equation.
               - Define symbols (`sympy.symbols`).
               - Create the equation (`sympy.Eq`).
               - Solve for the target variable (`sympy.solve`).
             - Store the numerical result in `results[step['id']]` and also add it to the `variables` dictionary.
          5. After the loop, append the `results` to the original `causal_scaffold` JSON for the next stage.
        - **Input:** `causal_scaffold: dict`
        - **Output:** `executed_scaffold: dict` (the original scaffold now including a `results` key with all computed values).
      
        
      
        #### **Component 4: Causal Synthesizer & Validator**
      
        
      
        - **Objective:** To translate the structured, solved plan back into a human-readable explanation and to validate the model's causal understanding using counterfactual prompts.11
      
        - **Mechanism:** Two distinct LLM prompt-based functions.
      
        - **Implementation Details:**
      
          1. **Explanation Generation Prompt:**
      
             Đoạn mã
      
             ```
             **ROLE:**
             You are a science communicator. Your task is to explain the solution to a physics problem based on a provided structured plan and its results.
             
             **INSTRUCTIONS:**
             Generate a clear, step-by-step, human-readable explanation of how the final answer was calculated. Follow the computation plan, state the rule or formula used for each step, and present the calculated values.
             
             **SOLVED PLAN:**
             {executed_scaffold_json_string}
             
             **EXPLANATION:**
             ```
      
          2. **Counterfactual Validation Prompt:**
      
             Đoạn mã
      
             ```
             **ROLE:**
             You are a causal analyst. Your task is to reason about a hypothetical change to a problem based on its established causal structure. Do not resolve the entire problem from scratch; use the provided causal graph to predict the outcome.
             
             **INSTRUCTIONS:**
             Based on the provided causal structure, answer the "What if" question. Explain which downstream variables would be affected by the change and calculate the new final answer.
             
             **ORIGINAL CAUSAL STRUCTURE:**
             {causal_scaffold_json_string}
             
             **COUNTERFACTUAL QUESTION:**
             "Based on the original problem, what would the '{target_variable}' be if the value of '{variable_to_change}' was {new_value} instead?"
             
             **ANALYSIS AND NEW RESULT:**
             ```
      
        - **Input:** `executed_scaffold: dict`
      
        - **Output:** `explanation: str`, `validation_response: str`
      
        ------
      
        
      
        ### **3. Implementation Workflow & Code Structure**
      
        
      
        A central `main.py` script will orchestrate the entire process.
      
        **Suggested Project Structure:**
      
        ```
        /causal-reasoning-engine/
        
        |-- main.py                 # Main orchestrator
        |-- engine/
        | |-- __init__.py
        | |-- retriever.py          # Component 1: Knowledge Retriever
        | |-- scaffolder.py         # Component 2: Causal Scaffolding
        | |-- executor.py           # Component 3: Symbolic Execution
        | |-- synthesizer.py        # Component 4: Synthesis & Validation
        |-- prompts/
        | |-- scaffolding_prompt.txt
        | |-- explanation_prompt.txt
        | |-- validation_prompt.txt
        |-- data/
        | |-- knowledge_base.json
        |-- requirements.txt
        ```
      
        **Workflow in `main.py`:**
      
        Python
      
        ```
        # main.py
        from engine import retriever, scaffolder, executor, synthesizer
        
        def solve_problem(problem_text):
            # Stage 1: Retrieve Knowledge
            relevant_rules = retriever.get_knowledge(problem_text)
        
            # Stage 2: Generate Causal Scaffold
            causal_plan = scaffolder.generate_scaffold(problem_text, relevant_rules)
            if not causal_plan:
                return "Failed to generate a plan."
        
            # Stage 3: Execute the Plan
            solved_plan = executor.execute_plan(causal_plan)
            if not solved_plan:
                return "Failed during execution."
        
            # Stage 4: Synthesize and Validate
            explanation = synthesizer.generate_explanation(solved_plan)
            validation = synthesizer.run_counterfactual_check(solved_plan) # Example check
        
            # Combine and return the final output
            return f"--- Explanation ---\n{explanation}\n\n--- Validation ---\n{validation}"
        
        if __name__ == "__main__":
            problem = "An object with a mass of 10 kg is initially at rest. A constant force of 50 Newtons is applied to it for 5 seconds. What is its final velocity?"
            solution = solve_problem(problem)
            print(solution)
        ```
      
        ------
      
        
      
        ### **4. Dependencies & Tools 4. 依赖关系与工具**
      
        
      
        - **Python 3.9+**
        - **LLM API Access:** 这里我用的硅基流动的api
        - **Python Libraries (`requirements.txt`):
          Python 库 ( `requirements.txt` ):**
          - `openai` or `anthropic` (for LLM API calls)
             `openai` 或 `anthropic` (用于 LLM API 调用)
          - `sympy` (for symbolic mathematics)
             `sympy` (用于符号数学)
          - `python-dotenv` (for managing API keys)
             `python-dotenv` (用于管理 API 密钥)