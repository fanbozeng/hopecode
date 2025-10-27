"""
Causal Graph Visualizer
因果图可视化器

Simple module to generate visual graphs from causal scaffolds.
简单模块，从因果脚手架生成可视化图表。

Usage in main.py:
    from engine.causal_visualizer import generate_causal_image
    
    causal_plan = self.scaffolder.generate_scaffold(problem_text, relevant_rules)
    generate_causal_image(causal_plan, output_path="output/causal_graph.png")
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Try to import visualization libraries
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def generate_causal_image(
    causal_plan: Dict[str, Any],
    output_path: str = "visualization_output/causal_graph.png",
    method: str = "auto",
    verbose: bool = False
) -> Optional[str]:
    """
    Generate a visual image of the causal graph from causal_plan.
    从causal_plan生成因果图的可视化图像。
    
    Args:
        causal_plan: The causal scaffold dictionary from scaffolder
                    从scaffolder生成的因果脚手架字典
        output_path: Path to save the output image (PNG, PDF, SVG supported)
                    输出图像的保存路径（支持PNG、PDF、SVG）
        method: Visualization method ('graphviz', 'matplotlib', 'text', 'auto')
               可视化方法（'graphviz'、'matplotlib'、'text'、'auto'）
        verbose: Print detailed information
                打印详细信息
    
    Returns:
        Path to the generated image file, or None if failed
        生成的图像文件路径，如果失败则返回None
    
    Example:
        causal_plan = scaffolder.generate_scaffold(problem, rules)
        image_path = generate_causal_image(causal_plan, "output/graph.png")
    """
    if verbose:
        print("\n📊 Generating causal graph visualization...")
        print("📊 生成因果图可视化...")
    
    # Validate input
    if not causal_plan or 'causal_graph' not in causal_plan:
        if verbose:
            print("⚠️  No causal graph found in plan")
        return None
    
    # Create output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Select method
    if method == "auto":
        if HAS_GRAPHVIZ:
            method = "graphviz"
        elif HAS_MATPLOTLIB:
            method = "matplotlib"
        else:
            method = "text"
    
    # Generate visualization
    try:
        if method == "graphviz" and HAS_GRAPHVIZ:
            result = _generate_graphviz(causal_plan, output_file, verbose)
        elif method == "matplotlib" and HAS_MATPLOTLIB:
            result = _generate_matplotlib(causal_plan, output_file, verbose)
        else:
            result = _generate_text(causal_plan, output_file, verbose)
        
        if verbose and result:
            print(f"✓ Causal graph saved to: {result}")
            print(f"✓ 因果图已保存到: {result}")
        
        return result
        
    except Exception as e:
        if verbose:
            print(f"❌ Error generating visualization: {e}")
        return None


def _generate_graphviz(causal_plan: Dict[str, Any], output_path: Path, verbose: bool) -> Optional[str]:
    """Generate using Graphviz (high quality)"""
    if verbose:
        print("  Using Graphviz...")
    
    causal_graph = causal_plan.get('causal_graph', [])
    knowns = causal_plan.get('knowns', {})
    target_variable = causal_plan.get('target_variable', 'unknown')
    
    # Create directed graph
    dot = graphviz.Digraph(comment='Causal Graph')
    dot.attr(rankdir='LR', dpi='300')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='11')
    dot.attr('edge', fontname='Arial', fontsize='9', color='#4A90E2')
    
    # Track all nodes
    all_nodes = set()
    
    # Add edges
    for link in causal_graph:
        causes = link.get('cause', [])
        effect = link.get('effect', '')
        rule = link.get('rule', '')
        
        if isinstance(causes, str):
            causes = [causes]
        
        all_nodes.update(causes)
        all_nodes.add(effect)
        
        for cause in causes:
            # Shorten rule for label
            short_rule = rule[:35] + '...' if len(rule) > 35 else rule
            dot.edge(cause, effect, label=short_rule)
    
    # Style nodes
    for node in all_nodes:
        if node in knowns:
            dot.node(node, node, fillcolor='#A8E6CF', color='#56B08E', penwidth='2')
        elif node == target_variable:
            dot.node(node, node, fillcolor='#FFB3BA', color='#FF6B6B', penwidth='3')
        else:
            dot.node(node, node, fillcolor='#B4D4FF', color='#6B9BD1', penwidth='2')
    
    # Determine output format from extension
    output_format = output_path.suffix[1:] or 'png'  # Remove the dot
    if output_format not in ['png', 'pdf', 'svg']:
        output_format = 'png'
    
    # Render
    output_base = str(output_path.with_suffix(''))
    dot.render(output_base, format=output_format, cleanup=True)
    
    return str(output_path)


def _generate_matplotlib(causal_plan: Dict[str, Any], output_path: Path, verbose: bool) -> Optional[str]:
    """Generate using Matplotlib (pure Python)"""
    if verbose:
        print("  Using Matplotlib...")
    
    causal_graph = causal_plan.get('causal_graph', [])
    knowns = causal_plan.get('knowns', {})
    target_variable = causal_plan.get('target_variable', 'unknown')
    
    # Build node positions (simple layout)
    nodes_dict = {}
    for link in causal_graph:
        causes = link.get('cause', [])
        effect = link.get('effect', '')
        if isinstance(causes, str):
            causes = [causes]
        for cause in causes:
            nodes_dict[cause] = 'cause'
        nodes_dict[effect] = 'effect'
    
    # Simple vertical layout
    nodes = list(nodes_dict.keys())
    node_positions = {}
    
    # Group by type
    known_nodes = [n for n in nodes if n in knowns]
    intermediate_nodes = [n for n in nodes if n not in knowns and n != target_variable]
    target_nodes = [target_variable] if target_variable in nodes else []
    
    # Layout
    y_pos = 0
    for i, node in enumerate(known_nodes):
        node_positions[node] = (0, y_pos)
        y_pos -= 1.5
    
    for i, node in enumerate(intermediate_nodes):
        node_positions[node] = (3, i * 1.5 - len(intermediate_nodes) * 0.75)
    
    for i, node in enumerate(target_nodes):
        node_positions[node] = (6, 0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Draw edges
    for link in causal_graph:
        causes = link.get('cause', [])
        effect = link.get('effect', '')
        rule = link.get('rule', '')
        
        if isinstance(causes, str):
            causes = [causes]
        
        for cause in causes:
            if cause in node_positions and effect in node_positions:
                x1, y1 = node_positions[cause]
                x2, y2 = node_positions[effect]
                
                arrow = FancyArrowPatch(
                    (x1 + 0.5, y1), (x2 - 0.5, y2),
                    arrowstyle='->', mutation_scale=20,
                    color='#4A90E2', linewidth=2, alpha=0.7
                )
                ax.add_patch(arrow)
                
                # Add rule as text (shortened)
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                short_rule = rule[:20] + '...' if len(rule) > 20 else rule
                ax.text(mid_x, mid_y + 0.2, short_rule, fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7),
                       ha='center')
    
    # Draw nodes
    for node, (x, y) in node_positions.items():
        if node in knowns:
            color = '#A8E6CF'
            edge_color = '#56B08E'
        elif node == target_variable:
            color = '#FFB3BA'
            edge_color = '#FF6B6B'
        else:
            color = '#B4D4FF'
            edge_color = '#6B9BD1'
        
        # Draw box
        box = FancyBboxPatch(
            (x - 0.5, y - 0.3), 1, 0.6,
            boxstyle='round,pad=0.05',
            facecolor=color, edgecolor=edge_color, linewidth=2
        )
        ax.add_patch(box)
        
        # Add text
        ax.text(x, y, node, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#A8E6CF', edgecolor='#56B08E', label='Known / 已知'),
        mpatches.Patch(facecolor='#FFB3BA', edgecolor='#FF6B6B', label='Target / 目标'),
        mpatches.Patch(facecolor='#B4D4FF', edgecolor='#6B9BD1', label='Intermediate / 中间')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # Title
    ax.set_title(f'Causal Graph: {target_variable}', fontsize=14, fontweight='bold', pad=15)
    
    # Set limits and remove axes
    ax.set_xlim(-1, 7)
    ax.set_ylim(min(y for _, y in node_positions.values()) - 1, 
                max(y for _, y in node_positions.values()) + 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return str(output_path)


def _generate_text(causal_plan: Dict[str, Any], output_path: Path, verbose: bool) -> Optional[str]:
    """Generate text representation (fallback when no viz libraries available)"""
    if verbose:
        print("  Using text representation...")
    
    causal_graph = causal_plan.get('causal_graph', [])
    knowns = causal_plan.get('knowns', {})
    target_variable = causal_plan.get('target_variable', 'unknown')
    
    lines = []
    lines.append("="*70)
    lines.append("CAUSAL GRAPH VISUALIZATION (Text)")
    lines.append("因果图可视化（文本）")
    lines.append("="*70)
    lines.append("")
    lines.append(f"Target: {target_variable}")
    lines.append(f"目标: {target_variable}")
    lines.append("")
    lines.append("Known Variables / 已知变量:")
    for k, v in knowns.items():
        lines.append(f"  🟢 {k} = {v}")
    lines.append("")
    lines.append("Causal Relationships / 因果关系:")
    lines.append("")
    
    for i, link in enumerate(causal_graph, 1):
        causes = link.get('cause', [])
        effect = link.get('effect', '')
        rule = link.get('rule', '')
        
        if isinstance(causes, str):
            causes = [causes]
        
        causes_str = ', '.join(causes)
        lines.append(f"{i}. [{causes_str}] → [{effect}]")
        lines.append(f"   Rule: {rule}")
        lines.append("")
    
    text_content = '\n'.join(lines)
    
    # Save as text file
    text_path = output_path.with_suffix('.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    return str(text_path)


def generate_causal_images_batch(
    causal_plans: List[Dict[str, Any]],
    output_dir: str = "visualization_output",
    verbose: bool = False
) -> List[str]:
    """
    Generate images for multiple causal plans.
    为多个因果计划生成图像。
    
    Args:
        causal_plans: List of causal scaffold dictionaries
        output_dir: Directory to save images
        verbose: Print detailed information
        
    Returns:
        List of generated image paths
    """
    results = []
    
    for i, plan in enumerate(causal_plans):
        output_path = f"{output_dir}/causal_graph_{i+1}.png"
        result = generate_causal_image(plan, output_path, verbose=verbose)
        if result:
            results.append(result)
    
    return results


# Export main function
__all__ = ['generate_causal_image', 'generate_causal_images_batch']


# Demo/test
if __name__ == "__main__":
    # Test with a sample causal plan
    test_plan = {
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
                "rule": "F = m × a"
            },
            {
                "cause": ["initial_velocity", "acceleration", "time"],
                "effect": "final_velocity",
                "rule": "v_f = v_i + a × t"
            }
        ]
    }
    
    print("Testing causal graph visualizer...")
    print("测试因果图可视化器...\n")
    
    # Generate image
    result = generate_causal_image(
        test_plan,
        output_path="visualization_output/test_causal_graph.png",
        verbose=True
    )
    
    if result:
        print(f"\n✓ Test completed successfully!")
        print(f"✓ 测试成功完成！")
        print(f"Check: {result}")
    else:
        print(f"\n⚠️  Visualization generated as text (install graphviz or matplotlib for images)")
        print(f"⚠️  已生成文本可视化（安装graphviz或matplotlib以生成图像）")


