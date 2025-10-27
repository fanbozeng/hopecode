"""
Enhanced Causal Graph Visualizer
增强的因果图可视化器

Based on scaffolding_prompt_v3.txt structure:
- constraints_and_premises
- problem_model  
- chosen_strategy
- target_variable
- expected_answer_type
- knowns
- causal_graph
- computation_plan
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
    import matplotlib.lines as mlines
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Run: pip install matplotlib")


def generate_causal_graph_image(
    causal_scaffold: Dict[str, Any],
    output_path: str = "causal_graph.png",
    dpi: int = 300,
    figsize: tuple = (16, 10)
) -> Optional[str]:
    """
    Generate a high-quality PNG visualization of the causal graph.
    生成高质量的因果图PNG可视化
    
    Args:
        causal_scaffold: Complete scaffold from scaffolder (with all fields)
        output_path: Output PNG file path
        dpi: Image resolution (default 300 for high quality)
        figsize: Figure size in inches
        
    Returns:
        Path to generated PNG, or None if failed
    """
    if not HAS_MATPLOTLIB:
        print("❌ Matplotlib not available. Install with: pip install matplotlib")
        return None
    
    # Extract all fields from scaffold
    causal_graph = causal_scaffold.get('causal_graph', [])
    knowns = causal_scaffold.get('knowns', {})
    target_variable = causal_scaffold.get('target_variable', 'unknown')
    computation_plan = causal_scaffold.get('computation_plan', [])
    
    # Additional metadata (from v3 prompt)
    problem_model = causal_scaffold.get('problem_model', '')
    chosen_strategy = causal_scaffold.get('chosen_strategy', '')
    expected_answer_type = causal_scaffold.get('expected_answer_type', '')
    constraints = causal_scaffold.get('constraints_and_premises', [])
    
    if not causal_graph:
        print("⚠️  No causal graph found in scaffold")
        return None
    
    # Create figure with subplots for better layout
    fig = plt.figure(figsize=figsize, facecolor='white')
    
    # Main graph area (70%)
    ax_main = plt.subplot2grid((4, 3), (0, 0), colspan=2, rowspan=4)
    
    # Info panel (30%)
    ax_info = plt.subplot2grid((4, 3), (0, 2), rowspan=4)
    ax_info.axis('off')
    
    # === MAIN GRAPH VISUALIZATION ===
    
    # Set background color for graph area
    ax_main.set_facecolor('#F8F9FA')
    
    # Build node structure from causal_graph
    nodes = {}
    edges = []
    
    for link in causal_graph:
        causes = link.get('cause', [])
        effect = link.get('effect', '')
        rule = link.get('rule', '')
        
        if isinstance(causes, str):
            causes = [causes]
        
        for cause in causes:
            if cause not in nodes:
                nodes[cause] = {'type': 'known' if cause in knowns else 'intermediate'}
        
        if effect not in nodes:
            nodes[effect] = {'type': 'target' if effect == target_variable else 'intermediate'}
        
        for cause in causes:
            edges.append({
                'from': cause,
                'to': effect,
                'rule': rule
            })
    
    # Simple hierarchical layout based on computation steps
    node_positions = {}
    step_levels = {}
    
    # Assign levels based on computation_plan
    for i, step in enumerate(computation_plan):
        target_var = step.get('target', '')
        step_levels[target_var] = i
    
    # Position known variables on left
    known_vars = [n for n in nodes if n in knowns]
    intermediate_vars = [n for n in nodes if n not in knowns and n != target_variable]
    target_vars = [target_variable] if target_variable in nodes else []
    
    # Layout: left to right, top to bottom
    y_spacing = 1.5
    x_spacing = 4
    
    # Known variables (column 0)
    for i, var in enumerate(known_vars):
        node_positions[var] = (0, -i * y_spacing)
    
    # Intermediate variables (based on computation order)
    intermediate_sorted = sorted(intermediate_vars, 
                                key=lambda x: step_levels.get(x, 999))
    for i, var in enumerate(intermediate_sorted):
        node_positions[var] = (x_spacing, -i * y_spacing)
    
    # Target variable (rightmost)
    for i, var in enumerate(target_vars):
        node_positions[var] = (x_spacing * 2, 0)
    
    # Draw edges (arrows with rules)
    for edge in edges:
        from_node = edge['from']
        to_node = edge['to']
        rule = edge['rule']
        
        if from_node in node_positions and to_node in node_positions:
            x1, y1 = node_positions[from_node]
            x2, y2 = node_positions[to_node]
            
            # Draw curved arrow with gradient effect
            arrow = FancyArrowPatch(
                (x1 + 0.6, y1), (x2 - 0.6, y2),
                arrowstyle='-|>', mutation_scale=30,
                color='#4A90E2', linewidth=3, alpha=0.85,
                connectionstyle="arc3,rad=0.15",
                zorder=2
            )
            ax_main.add_patch(arrow)
            
            # Add rule label with improved styling
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            # Shorten rule if too long
            display_rule = rule if len(rule) <= 30 else rule[:27] + '...'
            ax_main.text(mid_x, mid_y + 0.15, display_rule, 
                        fontsize=9, ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.5', 
                                facecolor='#FFFEF7', alpha=0.95,
                                edgecolor='#4A90E2', linewidth=1.5),
                        color='#2C5AA0', fontweight='600',
                        zorder=3)
    
    # Draw nodes with improved visual style
    for node, pos in node_positions.items():
        x, y = pos
        node_type = nodes[node]['type']
        
        # Enhanced color scheme with gradients and shadows
        if node_type == 'known':
            color = '#A8E6CF'  # Soft mint green
            edge_color = '#3D9970'  # Rich green
            edge_width = 3.0
        elif node_type == 'target':
            color = '#FFB3BA'  # Soft red
            edge_color = '#E63946'  # Bold red
            edge_width = 3.5
        else:
            color = '#BAE1FF'  # Light blue
            edge_color = '#1E88E5'  # Bold blue
            edge_width = 2.5
        
        # Draw shadow for depth effect
        width, height = 1.2, 0.6
        shadow = FancyBboxPatch(
            (x - width/2 + 0.03, y - height/2 - 0.03), width, height,
            boxstyle='round,pad=0.05',
            facecolor='gray', edgecolor='none',
            linewidth=0, alpha=0.3
        )
        ax_main.add_patch(shadow)
        
        # Draw main rounded rectangle
        box = FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle='round,pad=0.05',
            facecolor=color, edgecolor=edge_color, 
            linewidth=edge_width, alpha=0.95
        )
        ax_main.add_patch(box)
        
        # Add node label
        # Show value for known variables
        if node in knowns:
            label = f"{node}\n= {knowns[node]}"
            fontsize = 10
        else:
            label = node
            fontsize = 11
        
        ax_main.text(x, y, label, ha='center', va='center', 
                    fontsize=fontsize, fontweight='bold',
                    color='#000000')
    
    # Set axis limits
    if node_positions:
        all_x = [pos[0] for pos in node_positions.values()]
        all_y = [pos[1] for pos in node_positions.values()]
        ax_main.set_xlim(min(all_x) - 1.5, max(all_x) + 1.5)
        ax_main.set_ylim(min(all_y) - 1.5, max(all_y) + 1.5)
    
    # Add subtle grid for better readability
    ax_main.grid(True, linestyle='--', alpha=0.15, color='#CCCCCC', linewidth=0.5)
    
    ax_main.axis('off')  # Still turn off axis, grid will remain
    ax_main.set_aspect('equal')
    
    # === INFO PANEL ===
    
    info_text = []
    
    # Title
    info_text.append("[GRAPH ANALYSIS]")
    info_text.append("=" * 30)
    info_text.append("")
    
    # Target
    info_text.append("[TARGET]")
    info_text.append(f"  {target_variable}")
    info_text.append("")
    
    # Answer type
    if expected_answer_type:
        info_text.append("[ANSWER TYPE]")
        info_text.append(f"  {expected_answer_type}")
        info_text.append("")
    
    # Strategy
    if chosen_strategy:
        info_text.append("[STRATEGY]")
        # Wrap long strategy
        strategy_lines = [chosen_strategy[i:i+25] for i in range(0, len(chosen_strategy), 25)]
        for line in strategy_lines:
            info_text.append(f"  {line}")
        info_text.append("")
    
    # Known variables
    info_text.append(f"[KNOWN] ({len(knowns)} vars):")
    for k, v in knowns.items():
        info_text.append(f"  * {k} = {v}")
    info_text.append("")
    
    # Computation steps
    info_text.append("[STEPS]")
    for i, step in enumerate(computation_plan, 1):
        target_var = step.get('target', '')
        desc = step.get('description', '')
        # Truncate long descriptions
        if len(desc) > 35:
            desc = desc[:32] + "..."
        info_text.append(f"  {i}. {target_var}")
        if desc:
            info_text.append(f"     {desc}")
    info_text.append("")
    
    # Legend
    info_text.append("[LEGEND]")
    info_text.append("  [G] Known Variable")
    info_text.append("  [R] Target Variable")
    info_text.append("  [B] Intermediate Var")
    
    # Render info text
    info_y = 0.95
    for line in info_text:
        if line.startswith("="):
            # Separator lines
            ax_info.text(0.05, info_y, line, fontsize=8, 
                        family='monospace', va='top', color='#888888')
        elif line.startswith("[") and line.endswith("]") or line.startswith("[") and ":" in line:
            # Section headers
            ax_info.text(0.05, info_y, line, fontsize=10, 
                        fontweight='bold', va='top', color='#2E86AB')
        else:
            # Regular text
            ax_info.text(0.05, info_y, line, fontsize=9, va='top', color='#333333')
        info_y -= 0.04
    
    ax_info.set_xlim(0, 1)
    ax_info.set_ylim(0, 1)
    
    # === MAIN TITLE ===
    
    title_text = "⚡ Causal Reasoning Graph ⚡" if problem_model else "Causal Reasoning Graph"
    if problem_model:
        # Shorten problem model for title
        model_short = problem_model[:60] + "..." if len(problem_model) > 60 else problem_model
        title_text = f"Causal Reasoning Graph\n{model_short}"
    
    fig.suptitle(title_text, fontsize=16, fontweight='bold', y=0.98,
                color='#2C3E50', bbox=dict(boxstyle='round,pad=0.8', 
                                          facecolor='#ECF0F1', alpha=0.8))
    
    # Save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=dpi, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✓ Causal graph saved: {output_file}")
    return str(output_file)


# Convenience function for easy import
def visualize_causal_graph(scaffold, output_path="causal_graph.png"):
    """
    Simple wrapper for easy use.
    简单包装函数，便于使用
    
    Usage:
        from engine.causal_graph_visualizer import visualize_causal_graph
        
        causal_plan = scaffolder.generate_scaffold(problem, rules)
        visualize_causal_graph(causal_plan, "my_graph.png")
    """
    return generate_causal_graph_image(scaffold, output_path)


if __name__ == "__main__":
    # Test with sample data
    test_scaffold = {
        "constraints_and_premises": [
            "Object with mass 10 kg starts from rest",
            "Force of 50 N applied for 5 seconds"
        ],
        "problem_model": "Physics problem with constant force applied to object",
        "chosen_strategy": "Apply Newton's Second Law followed by Kinematics",
        "target_variable": "velocity",
        "expected_answer_type": "Numerical",
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
                "rule": "acceleration = force / mass"
            },
            {
                "cause": ["initial_velocity", "acceleration", "time"],
                "effect": "velocity",
                "rule": "velocity = initial_velocity + acceleration * time"
            }
        ],
        "computation_plan": [
            {
                "id": "step1",
                "target": "acceleration",
                "inputs": ["force", "mass"],
                "description": "Calculate acceleration using F = m * a"
            },
            {
                "id": "step2",
                "target": "velocity",
                "inputs": ["initial_velocity", {"ref": "step1"}, "time"],
                "description": "Calculate final velocity using v = u + at"
            }
        ]
    }
    
    print("Testing Enhanced Causal Graph Visualizer...")
    result = generate_causal_graph_image(
        test_scaffold,
        "visualization_output/enhanced_test_graph.png",
        dpi=300
    )
    
    if result:
        print(f"✓ Test completed! Check: {result}")
    else:
        print("❌ Test failed")


