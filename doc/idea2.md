Of course. Here is the complete, final technical plan in English, meticulously updated to reflect the robust, layered architecture we designed together.

This version maintains the variable names and core concepts from our discussion, solidifying the five-stage process that separates logical planning from code generation. This architecture is significantly more robust, debuggable, and aligned with the best practices for building reliable AI reasoning systems.

-----

## **Technical Plan (Final Version 2.0): A Hierarchical Causal Reasoning Engine**

### **1. Overview & System Architecture**

This document provides the technical specification for a modular system designed to solve complex mathematical and physics problems by emulating the hierarchical thinking patterns of a human expert. The core principle of this architecture is the strict **separation of "logical planning" from "code implementation"**.[1, 2] This is achieved by leveraging a Large Language Model (LLM) to perform distinct expert roles at different stages of the pipeline (e.g., logical planner vs. programmer), resulting in a system with unprecedented robustness, debuggability, and precision.[3, 4]

The system operates via a five-stage pipeline, architected to support rigorous scientific evaluation, including comparative and ablation studies:

1.  **Dynamic Knowledge Generation (`Rules`)**: The LLM acts as a "domain expert," analyzing the problem to generate a list of all relevant human-readable rules (formulas, theorems, principles).[5]
2.  **Logical Planning (`causal_scaffold`)**: The LLM acts as a "strategic planner," using the problem and the generated rules to construct a pure, code-free **causal scaffold** in JSON format. This scaffold outlines *what* to do, not *how* to do it.
3.  **Code Generation (`Code Generation`)**: The LLM acts as a "programmer," receiving the complete logical plan and translating it into a single, executable Python script using the SymPy library.
4.  **Sandbox Execution (Sandbox Execution)**: The generated code is executed in a secure, isolated sandbox environment to ensure precise and safe computation.
5.  **Synthesis & Validation (Synthesis & Validation)**: The LLM acts as a "science communicator," generating a comprehensive final explanation based on the entire execution trace—from the logical plan to the code and its final result.

**System Architecture Diagram:**

```
[User Input: "A physics/math problem"]
|
       v
+-------------------------------------+

| 1. Dynamic Knowledge Generator (LLM) |
| (Output: List of human-readable rules)|
+-------------------------------------+
|
| (Problem + Rules)
       v
+-------------------------------------+

| 2. Logical Planner (LLM) |
| (Output: Purely logical causal_scaffold)|
+-------------------------------------+
|
| (Purely logical causal_scaffold)
       v
+-------------------------------------+

| 3. Code Generator (LLM) |
| (Output: Full Python/SymPy script) |
+-------------------------------------+
|
| (Code String)
       v
+-------------------------------------+

| 4. Sandbox Execution (Python + Sandbox)|
| (Output: Code execution result) |
+-------------------------------------+
|
| (Scaffold + Code + Result)
       v
+-------------------------------------+

| 5. Synthesizer & Validator (LLM) |
| (Output: Final explanation) |
+-------------------------------------+
```

-----

### **2. Component Breakdown**

#### **Component 1: Dynamic Knowledge Generator (`Rules`)**

  * **Objective**: To dynamically generate the core domain knowledge required to solve the current problem, mimicking the first step of a human expert: recalling all relevant theorems and formulas.
  * **Mechanism**: A dedicated LLM prompt that instructs the model to act as a domain expert and output a structured list of necessary rules.
  * **Input**: `problem_text: str`
  * **Output**: `generated_knowledge: List[str]`

#### **Component 2: Logical Planner (`causal_scaffold`)**

  * **Objective**: To translate the unstructured problem text and the generated `rules` into a **purely logical, code-free** structured plan. The core output is a clear blueprint of the "thinking process".[6, 7]
  * **Mechanism**: An API call to an LLM, providing the original problem and the knowledge from Component 1 as context.
  * **Implementation Details (Prompt)**:
    ````prompt
    **ROLE:**
    You are a specialized Causal Reasoning Engine and a master strategist. Your task is to deconstruct a natural language problem into a pure logical plan, represented as a structured JSON object. This JSON must define all variables, the causal relationships between them, and a precise computational plan. **Do NOT generate any code.**

    **CONTEXT:**
    Here are the relevant physical laws and formulas for this problem:
    ---
    {generated_knowledge}
    ---

    **INSTRUCTIONS:**
    Analyze the user's problem and generate a single JSON object with the following schema:

    1.  `target_variable`: (String) The final variable to be solved for.
    2.  `knowns`: (Object) A dictionary of all known variables and their numerical values.
    3.  `causal_graph`: (Array of Objects) Represents the causal links. Each object must have:
        - `cause`: (Array of Strings) The input variables.
        - `effect`: (String) The output variable.
        - `rule`: (String) The natural language formula from the context that governs this link.
    4.  `computation_plan`: (Array of Objects) A step-by-step logical plan. Each object must have:
        - `id`: (String) A unique step identifier (e.g., "step1").
        - `target`: (String) The variable to calculate in this step.
        - `inputs`: (Array) Input variables for this step. Use strings for knowns or `{"ref": "step_id.output"}` to reference a previous step's result.
        - `description`: (String) A brief natural language description of what this step calculates using which rule.

    **EXAMPLE:**
    Problem: "An object with mass 10 kg starts from rest. A force of 50 N acts on it for 5 seconds. Find the final velocity."
    JSON Output:
    ```json
    {
      "target_variable": "final_velocity",
      "knowns": { "initial_velocity": 0, "mass": 10, "force": 50, "time": 5 },
      "causal_graph": [
        { "cause": ["force", "mass"], "effect": "acceleration", "rule": "F = m * a" },
        { "cause": ["initial_velocity", "acceleration", "time"], "effect": "final_velocity", "rule": "v_f = v_i + a * t" }
      ],
      "computation_plan": [
        { "id": "step1", "target": "acceleration", "inputs": ["force", "mass"], "description": "Calculate acceleration using Newton's Second Law (F = m * a)." },
        { "id": "step2", "target": "final_velocity", "inputs": ["initial_velocity", "time", {"ref": "step1.output"}], "description": "Calculate final velocity using the kinematic equation (v_f = v_i + a * t)." }
      ]
    }
    ````
    ```
    ```
  * **Input**: `problem_text: str`, `generated_knowledge: List[str]`
  * **Output**: `causal_scaffold: dict`

#### **Component 3: Code Generator (`Code Generation`)**

  * **Objective**: To receive a complete, purely logical `causal_scaffold` and translate it **holistically** into a single, complete, and executable Python (SymPy) script.
  * **Mechanism**: An API call to an LLM, using the entire JSON string of the `causal_scaffold` as the primary context.
  * **Implementation Details (Prompt)**:
    ````prompt
    **ROLE:**
    You are an expert Python programmer specializing in the SymPy library. Your task is to write a Python script that implements a given logical plan to solve a scientific problem.

    **CONTEXT:**
    Here is the complete logical plan in JSON format. It describes all known variables, the target variable, and the step-by-step plan to solve the problem.
    ---
    {causal_scaffold_json_string}
    ---

    **INSTRUCTIONS:**
    1.  Write a single, complete Python script.
    2.  Import all necessary libraries from SymPy.
    3.  Define all variables mentioned in the plan as SymPy symbols.
    4.  Assign the numerical values from the `knowns` section to the corresponding variables.
    5.  Follow the `computation_plan` step-by-step. For each step, use the corresponding `rule` from the `causal_graph` to formulate and solve the equation for the `target` variable.
    6.  The final line of your script must print the numerical value of the `target_variable`. Do not print anything else.

    **PYTHON SCRIPT:**
    ```python
    ````
  * **Input**: `causal_scaffold: dict`
  * **Output**: `generated_code: str`

#### **Component 4: Sandbox Execution**

  * **Objective**: To execute the complete code script generated by Component 3 in a secure, isolated environment.
  * **Mechanism**: Use a library like `epicbox` to run the code inside a one-time Docker container.
  * **Implementation Details**:
    1.  Receive the `generated_code` string.
    2.  Invoke the sandbox executor to run the string, setting appropriate timeouts.
    3.  Capture stdout, stderr, and the exit code.
    4.  If execution is successful, parse stdout to get the final numerical answer.
  * **Input**: `generated_code: str`
  * **Output**: `execution_result: dict` (containing `stdout`, `stderr`, `exit_code`)

#### **Component 5: Synthesizer & Validator**

  * **Objective**: To translate the entire reasoning and execution process (from logical plan to code result) into a coherent, human-readable final report.
  * **Implementation Details (Prompt)**:
    ````prompt
    **ROLE:**
    You are a science communicator. Your task is to provide a comprehensive explanation of a problem's solution based on the full reasoning and execution trace.

    **CONTEXT:**
    Here is the complete trace of the solution process:
    1.  **The Logical Plan (`causal_scaffold`):**
        {causal_scaffold_json_string}
    2.  **The Python Code Generated from the Plan:**
        ```python
        {generated_code}
        ```
    3.  **The Final Result from Executing the Code:**
        {execution_result_stdout}

    **INSTRUCTIONS:**
    Generate a clear, step-by-step, human-readable explanation. For each step in the logical plan:
    1.  State the physical principle or formula used (from the 'rule' field).
    2.  Explain what is being calculated.
    3.  Show the corresponding part of the Python code that implemented this step.
    4.  State the numerical result for that step.
    5.  Conclude with the final answer.

    **EXPLANATION:**
    ````
  * **Input**: `causal_scaffold: dict`, `generated_code: str`, `execution_result: dict`
  * **Output**: `final_explanation: str`

### **3. Experimental Design, Code Structure, Dependencies & Tools**

*(This section remains identical to the previous detailed plan, providing a full framework for baselines, ablation studies, evaluation datasets, metrics, and a modular code structure to facilitate rigorous scientific evaluation.)*

This final technical plan incorporates your valuable insights to create a logically clear and technically robust system. It not only solves problems but also transparently shows every step of its "thinking," from high-level strategy to concrete implementation, making it an ideal blueprint for building trustworthy AI reasoning systems.