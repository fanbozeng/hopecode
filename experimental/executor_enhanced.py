"""
Enhanced Symbolic Execution Engine with Variable Annotation Support


This module extends the original executor to support LLM-annotated variables,
eliminating ambiguity in symbol interpretation while maintaining backward compatibility.

 LLM 

"""

import sympy as sp
import re
from typing import Dict, List, Any, Optional, Union
from copy import deepcopy


class ExecutionError(Exception):
    """Custom exception for execution errors / """
    pass


class EnhancedSymbolicExecutor:
    """
    Enhanced Symbolic Executor with Variable Annotation Support
    

    Features / :
    -  Supports LLM-annotated variables (variable_symbols field)
    -  Falls back to legacy inference for old scaffolds
    -  Zero symbol ambiguity with annotations
    -  Backward compatible with existing code
    """

    def __init__(self, precision: int = 15, verbose: bool = True):
        """Initialize the executor / """
        self.variables: Dict[str, Union[float, int]] = {}
        self.step_results: Dict[str, Union[float, int]] = {}
        self.precision = precision
        self.epsilon = 10 ** (-precision)
        self.verbose = verbose

        # Variable annotation support / 
        self.variable_symbols: Dict[str, str] = {}  # var_name -> symbol
        self.symbol_to_variable: Dict[str, str] = {}  # symbol -> var_name
        self.use_annotation = False  # Flag for annotation mode

    def execute_plan(self, causal_scaffold: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a causal computation plan / 

        Automatically detects if scaffold has variable_symbols and uses appropriate mode.
         scaffold  variable_symbols 
        """
        # Reset state / 
        self.variables = {}
        self.step_results = {}
        self.variable_symbols = {}
        self.symbol_to_variable = {}

        # Check for variable annotation / 
        if "variable_symbols" in causal_scaffold:
            self.use_annotation = True
            self.variable_symbols = causal_scaffold["variable_symbols"]
            self.symbol_to_variable = {v: k for k, v in self.variable_symbols.items()}
            self._print(" Using ANNOTATED mode (variable_symbols detected)")
            self._print("  variable_symbols")
            self._print(f"   Variable mapping: {len(self.variable_symbols)} variables")
        else:
            self.use_annotation = False
            self._print(" Using LEGACY mode (no variable_symbols, falling back to inference)")
            self._print("  variable_symbols")

        executed_scaffold = deepcopy(causal_scaffold)

        try:
            # Load known variables / 
            self.variables = dict(causal_scaffold.get("knowns", {}))

            # Execute computation plan / 
            computation_plan = causal_scaffold.get("computation_plan", [])
            causal_graph = causal_scaffold.get("causal_graph", [])

            for step in computation_plan:
                if self.use_annotation:
                    self._execute_step_annotated(step, causal_graph)
                else:
                    # Fall back to legacy method / 
                    from engine.executor import SymbolicExecutor
                    legacy_executor = SymbolicExecutor(precision=self.precision)
                    legacy_executor.variables = self.variables.copy()
                    legacy_executor._execute_step(step, causal_graph, computation_plan)
                    self.variables.update(legacy_executor.variables)
                    self.step_results.update(legacy_executor.step_results)

            # Add results / 
            executed_scaffold["results"] = self.step_results

            target_var = causal_scaffold.get("target_variable")
            if target_var in self.variables:
                executed_scaffold["final_answer"] = self.variables[target_var]
            else:
                self._print(f" Warning: Target variable '{target_var}' not found")

            self._print(" Symbolic execution completed successfully")
            self._print(" ")

            return executed_scaffold

        except Exception as e:
            self._print(f" Execution error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _execute_step_annotated(
        self,
        step: Dict[str, Any],
        causal_graph: List[Dict[str, Any]]
    ) -> None:
        """
        Execute a step using annotated variables / 

        This is the NEW logic that uses variable_symbols for precise symbol resolution.
         variable_symbols 
        """
        step_id = step.get("id")
        operation = step.get("operation")
        target = step.get("target")
        inputs = step.get("inputs", [])

        self._print(f"\n Executing {step_id}: {operation} for '{target}'")

        # Find rule / 
        rule = self._find_rule(target, causal_graph)
        if not rule:
            raise ExecutionError(f"No rule found for target: {target}")

        self._print(f"  Rule: {rule}")

        # Parse annotated equation / 
        equation = self._parse_annotated_equation(rule)
        self._print(f"  Parsed equation: {equation}")

        # Extract symbols from equation / 
        equation_symbols = self._extract_symbols_from_equation(equation)
        self._print(f"  Symbols in equation: {equation_symbols}")

        # Create SymPy symbols /  SymPy 
        symbol_objs = {sym: sp.Symbol(sym, real=True) for sym in equation_symbols}

        # Parse equation sides / 
        lhs_str, rhs_str = equation.split("=")
        lhs_expr = sp.sympify(lhs_str.strip(), locals=symbol_objs)
        rhs_expr = sp.sympify(rhs_str.strip(), locals=symbol_objs)

        self._print(f"  LHS: {lhs_expr}, RHS: {rhs_expr}")

        # Substitute known values / 
        for var_name in inputs:
            if var_name in self.variables:
                var_symbol = self.variable_symbols.get(var_name)
                if var_symbol and var_symbol in symbol_objs:
                    var_value = self.variables[var_name]
                    lhs_expr = lhs_expr.subs(symbol_objs[var_symbol], var_value)
                    rhs_expr = rhs_expr.subs(symbol_objs[var_symbol], var_value)
                    self._print(f"  Substituted: {var_name} ({var_symbol}) = {var_value}")

        # Auto-substitute other known variables / 
        for var_name, var_value in self.variables.items():
            if var_name not in inputs:
                var_symbol = self.variable_symbols.get(var_name)
                if var_symbol and var_symbol in symbol_objs:
                    lhs_expr = lhs_expr.subs(symbol_objs[var_symbol], var_value)
                    rhs_expr = rhs_expr.subs(symbol_objs[var_symbol], var_value)
                    self._print(f"  Auto-substituted: {var_name} ({var_symbol}) = {var_value}")

        # Find target symbol / 
        target_symbol = self.variable_symbols.get(target)
        if not target_symbol or target_symbol not in symbol_objs:
            raise ExecutionError(
                f"Target variable '{target}' symbol '{target_symbol}' not found in equation. "
                f"Available symbols: {list(symbol_objs.keys())}"
            )

        self._print(f"  Solving for: {target} (symbol: {target_symbol})")

        # Solve equation / 
        equation_to_solve = sp.Eq(lhs_expr, rhs_expr)
        solution = sp.solve(equation_to_solve, symbol_objs[target_symbol])

        if not solution:
            raise ExecutionError(f"No solution found for {target}")

        # Extract numerical result / 
        result = self._select_physical_solution(solution, target, target_symbol)

        # Store result / 
        self.step_results[step_id] = result
        self.variables[target] = result

        self._print(f"   Result: {target} = {result}")

    def _parse_annotated_equation(self, rule: str) -> str:
        """
        Parse annotated equation to extract pure mathematical expression
        

        Input:  "F (force) = m (mass) * a (acceleration)"
        Output: "F = m * a"
        """
        # Remove annotations in parentheses / 
        # Pattern: symbol (variable_name) -> symbol
        cleaned = re.sub(r'(\w+)\s*\([^)]+\)', r'\1', rule)

        # Check if it has an equation / 
        if '=' not in cleaned:
            # Try to extract from parentheses / 
            match = re.search(r'\((.*?=.*?)\)', rule)
            if match:
                return match.group(1)

            # Last resort: the whole rule might be the equation / 
            if '=' in rule:
                return rule

            raise ExecutionError(f"Cannot parse equation from rule: {rule}")

        return cleaned.strip()

    def _extract_symbols_from_equation(self, equation: str) -> set:
        """
        Extract all mathematical symbols from equation
        
        """
        # Match variable names: letters, underscores, numbers (but not starting with number)
        # 
        symbols = set(re.findall(r'[a-zA-Z_Δθπρσμλφψωαβγδεζηικνξοτυχ]\w*', equation))

        # Filter out common mathematical functions / 
        math_functions = {'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt', 'abs'}
        symbols = symbols - math_functions

        return symbols

    def _select_physical_solution(
        self,
        solutions: list,
        target_var: str,
        equation_var: str
    ) -> Union[float, int]:
        """
        Select physically reasonable solution from multiple solutions
        
        """
        # Convert to real numbers / 
        real_solutions = []
        for sol in solutions:
            try:
                if sol.is_real or (hasattr(sol, 'evalf') and sp.im(sol.evalf()) == 0):
                    val_precise = sol.evalf(self.precision)
                    if hasattr(val_precise, 'as_real_imag'):
                        real_part, imag_part = val_precise.as_real_imag()
                        if abs(float(imag_part)) < self.epsilon:
                            real_solutions.append(float(real_part))
                    else:
                        real_solutions.append(float(val_precise))
            except (ValueError, TypeError, AttributeError):
                continue

        if not real_solutions:
            raise ExecutionError(f"No real solution found for {target_var}")

        self._print(f"  Found {len(real_solutions)} real solution(s): {real_solutions}")

        # Apply physical constraints / 
        non_negative_vars = {
            't', 'time', 'm', 'mass', 'rho', 'ρ', 'density',
            'r', 'radius', 'V', 'volume', 'A', 'area', 'E', 'energy'
        }

        physical_solutions = []
        for sol in real_solutions:
            is_valid = True

            # Check non-negativity constraints / 
            if equation_var in non_negative_vars or target_var in non_negative_vars:
                if sol < -self.epsilon:
                    self._print(f"  Rejecting {sol} (must be non-negative)")
                    is_valid = False
                elif -self.epsilon <= sol < 0:
                    sol = 0.0  # Treat tiny negative as zero

            # Check range / 
            if abs(sol) > 1e308 or (0 < abs(sol) < 1e-308):
                self._print(f"  Rejecting {sol} (out of range)")
                is_valid = False

            if is_valid:
                physical_solutions.append(sol)

        if not physical_solutions:
            raise ExecutionError(
                f"No physically valid solution for {target_var}. "
                f"Real solutions: {real_solutions}"
            )

        # Prefer positive solutions / 
        if len(physical_solutions) > 1:
            positive_solutions = [s for s in physical_solutions if s > 0]
            if positive_solutions:
                return min(positive_solutions, key=abs)

        return physical_solutions[0]

    def _find_rule(self, target: str, causal_graph: List[Dict[str, Any]]) -> Optional[str]:
        """Find rule for target variable / """
        for link in causal_graph:
            if link.get("effect") == target:
                return link.get("rule")
        return None

    def _print(self, message: str) -> None:
        """Print if verbose mode enabled / """
        if self.verbose:
            print(message)

    def get_final_answer(self, target_variable: str) -> Optional[Union[float, int]]:
        """Get final answer / """
        return self.variables.get(target_variable)

    def get_all_results(self) -> Dict[str, Union[float, int]]:
        """Get all results / """
        return self.variables.copy()


# ============================================================================
# Integration Helper / 
# ============================================================================

def create_executor(use_enhanced: bool = True, **kwargs) -> Union[EnhancedSymbolicExecutor, 'SymbolicExecutor']:
    """
    Factory function to create appropriate executor
    

    Args:
        use_enhanced: If True, use enhanced executor with annotation support
                       True
        **kwargs: Arguments passed to executor constructor
                  

    Returns:
        Executor instance / 
    """
    if use_enhanced:
        return EnhancedSymbolicExecutor(**kwargs)
    else:
        from engine.executor import SymbolicExecutor
        return SymbolicExecutor(**kwargs)


# Example usage / 
if __name__ == "__main__":
    print("=" * 70)
    print("Testing Enhanced Symbolic Executor")
    print("")
    print("=" * 70)

    # Test with annotated scaffold /  scaffold 
    annotated_scaffold = {
        "target_variable": "final_velocity",
        "knowns": {
            "mass": 10,
            "force": 50,
            "time": 5,
            "initial_velocity": 0
        },
        "variable_symbols": {
            "force": "F",
            "mass": "m",
            "acceleration": "a",
            "initial_velocity": "v_i",
            "final_velocity": "v_f",
            "time": "t"
        },
        "causal_graph": [
            {
                "cause": ["force", "mass"],
                "effect": "acceleration",
                "rule": "F (force) = m (mass) * a (acceleration)"
            },
            {
                "cause": ["initial_velocity", "acceleration", "time"],
                "effect": "final_velocity",
                "rule": "v_f (final_velocity) = v_i (initial_velocity) + a (acceleration) * t (time)"
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
        ]
    }

    executor = EnhancedSymbolicExecutor()
    result = executor.execute_plan(annotated_scaffold)

    if result:
        print("\n" + "=" * 70)
        print(f" Final Answer: {result.get('final_answer')}")
        print(f" All Results: {result.get('results')}")
        print("=" * 70)
