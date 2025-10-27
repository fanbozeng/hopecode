"""
Enhanced Causal Scaffolding Module with Variable Annotation Support


This module extends the scaffolder to work with variable_symbols.
 variable_symbols
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from engine.scaffolder import CausalScaffolder, LLMClient


class EnhancedCausalScaffolder(CausalScaffolder):
    """
    Enhanced Causal Scaffolder with Variable Annotation Support
    

    Extends the base scaffolder to:
    - Use the enhanced prompt template (v2)
    - Validate variable_symbols field
    - Check annotation consistency
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_template_path: str = "prompts/scaffolding_prompt_v2.txt",
        require_annotations: bool = True
    ):
        """
        Initialize enhanced scaffolder / 

        Args:
            llm_client: LLM client instance
            prompt_template_path: Path to enhanced prompt template (default: v2)
            require_annotations: If True, scaffolds without variable_symbols will fail validation
        """
        super().__init__(llm_client, prompt_template_path)
        self.require_annotations = require_annotations

    def validate_scaffold(self, scaffold: Dict[str, Any]) -> bool:
        """
        Enhanced validation with variable_symbols checks
         variable_symbols 

        Args:
            scaffold: The scaffold dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation from parent class / 
        if not super().validate_scaffold(scaffold):
            return False

        # Check for variable_symbols field /  variable_symbols 
        if "variable_symbols" not in scaffold:
            if self.require_annotations:
                print(" Error: variable_symbols field is missing (required)")
                print("  variable_symbols ")
                return False
            else:
                print(" Warning: variable_symbols field is missing (continuing in legacy mode)")
                print("  variable_symbols ")
                return True  # Allow legacy scaffolds

        # Validate variable_symbols structure /  variable_symbols 
        variable_symbols = scaffold.get("variable_symbols", {})

        if not isinstance(variable_symbols, dict):
            print(" Error: variable_symbols must be a dictionary")
            print(" variable_symbols ")
            return False

        if len(variable_symbols) == 0:
            print(" Error: variable_symbols is empty")
            print(" variable_symbols ")
            return False

        # Check that all knowns have symbols / 
        knowns = scaffold.get("knowns", {})
        for known_var in knowns.keys():
            if known_var not in variable_symbols:
                print(f" Warning: Known variable '{known_var}' missing from variable_symbols")
                print(f"  '{known_var}'  variable_symbols ")

        # Check that target variable has a symbol / 
        target_var = scaffold.get("target_variable")
        if target_var and target_var not in variable_symbols:
            print(f" Warning: Target variable '{target_var}' missing from variable_symbols")
            print(f"  '{target_var}'  variable_symbols ")

        # Validate rules have annotations / 
        causal_graph = scaffold.get("causal_graph", [])
        for i, link in enumerate(causal_graph):
            rule = link.get("rule", "")
            if not self._is_rule_annotated(rule):
                print(f" Warning: Rule {i+1} is not properly annotated: {rule}")
                print(f"  {i+1} : {rule}")

        # Check for symbol conflicts / 
        symbols = list(variable_symbols.values())
        if len(symbols) != len(set(symbols)):
            duplicates = [s for s in symbols if symbols.count(s) > 1]
            print(f" Warning: Duplicate symbols found: {set(duplicates)}")
            print(f" : {set(duplicates)}")

        print(" Scaffold validation passed (with variable_symbols)")
        print("  variable_symbols")
        return True

    def _is_rule_annotated(self, rule: str) -> bool:
        """
        Check if a rule is properly annotated
        

        Annotated format: "symbol (variable_name) = ..."
        "symbol (variable_name) = ..."

        Args:
            rule: The rule string to check

        Returns:
            True if properly annotated
        """
        # Pattern: symbol (variable_name)
        # Example: "F (force)", "v_f (final_velocity)"
        annotation_pattern = r'\w+\s*\([a-z_]+\)'

        # Check if rule contains at least one annotation / 
        matches = re.findall(annotation_pattern, rule, re.IGNORECASE)

        # A properly annotated rule should have 2+ annotations (both sides of equation)
        #  2+ 
        return len(matches) >= 2


def create_scaffolder(use_enhanced: bool = True, **kwargs) -> CausalScaffolder:
    """
    Factory function to create appropriate scaffolder
    

    Args:
        use_enhanced: If True, use enhanced scaffolder with annotation support
        **kwargs: Arguments passed to scaffolder constructor

    Returns:
        Scaffolder instance
    """
    if use_enhanced:
        return EnhancedCausalScaffolder(**kwargs)
    else:
        return CausalScaffolder(**kwargs)


# Example usage / 
if __name__ == "__main__":
    print("=" * 70)
    print("Testing Enhanced Scaffolder Validation")
    print("")
    print("=" * 70)

    # Test 1: Valid annotated scaffold /  1
    print("\n--- Test 1: Valid Annotated Scaffold ---")
    valid_scaffold = {
        "target_variable": "density",
        "knowns": {"mass": 20, "volume": 2},
        "variable_symbols": {
            "density": "ρ",
            "mass": "m",
            "volume": "V"
        },
        "causal_graph": [{
            "cause": ["mass", "volume"],
            "effect": "density",
            "rule": "ρ (density) = m (mass) / V (volume)"
        }],
        "computation_plan": [{
            "id": "step1",
            "operation": "solve_for",
            "target": "density",
            "inputs": ["mass", "volume"],
            "tool": "symbolic_solver"
        }]
    }

    scaffolder = EnhancedCausalScaffolder()
    is_valid = scaffolder.validate_scaffold(valid_scaffold)
    print(f"Result: {'PASS' if is_valid else 'FAIL'}")

    # Test 2: Missing variable_symbols /  2 variable_symbols
    print("\n--- Test 2: Missing variable_symbols (strict mode) ---")
    legacy_scaffold = {
        "target_variable": "density",
        "knowns": {"mass": 20, "volume": 2},
        "causal_graph": [{
            "cause": ["mass", "volume"],
            "effect": "density",
            "rule": "ρ = m / V"
        }],
        "computation_plan": [{
            "id": "step1",
            "operation": "solve_for",
            "target": "density",
            "inputs": ["mass", "volume"],
            "tool": "symbolic_solver"
        }]
    }

    scaffolder_strict = EnhancedCausalScaffolder(require_annotations=True)
    is_valid = scaffolder_strict.validate_scaffold(legacy_scaffold)
    print(f"Result: {'PASS' if is_valid else 'FAIL'} (expected FAIL)")

    # Test 3: Missing variable_symbols (lenient mode) /  3 variable_symbols
    print("\n--- Test 3: Missing variable_symbols (lenient mode) ---")
    scaffolder_lenient = EnhancedCausalScaffolder(require_annotations=False)
    is_valid = scaffolder_lenient.validate_scaffold(legacy_scaffold)
    print(f"Result: {'PASS' if is_valid else 'FAIL'} (expected PASS)")

    print("\n" + "=" * 70)
