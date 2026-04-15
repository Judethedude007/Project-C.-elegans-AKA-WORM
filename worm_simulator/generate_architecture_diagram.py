"""
System Architecture Diagram
============================

Shows the entire simulation pipeline and how components interact.
This is critical for a research paper: illustrates what your system is actually doing.

Generates: plots/system_architecture.png (text-based because graphviz executable not installed)
"""

def generate_architecture_diagram():
    """Create system architecture diagram using matplotlib."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'C. elegans Simulator: System Architecture', 
           ha='center', fontsize=16, fontweight='bold')
    
    # Define colors
    colors = {
        'env': '#e8f4f8',
        'agent': '#ffcccc',
        'neural': '#e8ccff',
        'evolution': '#ccffcc',
        'metrics': '#ffccff',
        'output': '#ccffff'
    }
    
    # Layer 1: Environment (top)
    env_box = FancyBboxPatch((1, 8), 8, 0.8, boxstyle="round,pad=0.1", 
                            edgecolor='black', facecolor=colors['env'], linewidth=2)
    ax.add_patch(env_box)
    ax.text(5, 8.4, 'ENVIRONMENT LAYER\nFood | Pheromones | O₂ | Temperature', 
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Layer 2: Worm Agents
    worm_box = FancyBboxPatch((1, 6.5), 8, 0.8, boxstyle="round,pad=0.1", 
                             edgecolor='black', facecolor=colors['agent'], linewidth=2)
    ax.add_patch(worm_box)
    ax.text(5, 6.9, 'WORM AGENTS\nPhysics + Neural Circuits', 
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Layer 3a: Sensory (left)
    sensory_box = FancyBboxPatch((0.5, 4.5), 3.5, 1.2, boxstyle="round,pad=0.1", 
                                edgecolor='black', facecolor=colors['neural'], linewidth=2)
    ax.add_patch(sensory_box)
    ax.text(2.25, 5.1, 'SENSORY INTEGRATION\nNeural Computation', 
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Layer 3b: Motor (right)
    motor_box = FancyBboxPatch((6, 4.5), 3.5, 1.2, boxstyle="round,pad=0.1", 
                              edgecolor='black', facecolor=colors['neural'], linewidth=2)
    ax.add_patch(motor_box)
    ax.text(7.75, 5.1, 'MOTOR OUTPUT\nLocomotion Control', 
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Layer 4: Evolution (left-middle)
    evo_box = FancyBboxPatch((0.5, 2.5), 3.5, 1.2, boxstyle="round,pad=0.1", 
                            edgecolor='black', facecolor=colors['evolution'], linewidth=2)
    ax.add_patch(evo_box)
    ax.text(2.25, 3.1, 'GENETICS & EVOLUTION\nMutation | Selection', 
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Layer 5: Metrics (right-middle)
    metrics_box = FancyBboxPatch((6, 2.5), 3.5, 1.2, boxstyle="round,pad=0.1", 
                                edgecolor='black', facecolor=colors['metrics'], linewidth=2)
    ax.add_patch(metrics_box)
    ax.text(7.75, 3.1, 'RESEARCH METRICS\nMSD | Clustering | Variance', 
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Layer 6: Data Export (left-bottom)
    data_box = FancyBboxPatch((0.5, 0.5), 3.5, 1.2, boxstyle="round,pad=0.1", 
                             edgecolor='black', facecolor=colors['output'], linewidth=2)
    ax.add_patch(data_box)
    ax.text(2.25, 1.1, 'DATA EXPORT\nCSV | Plots', 
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Layer 6: Visualization (right-bottom)
    viz_box = FancyBboxPatch((6, 0.5), 3.5, 1.2, boxstyle="round,pad=0.1", 
                            edgecolor='black', facecolor=colors['output'], linewidth=2)
    ax.add_patch(viz_box)
    ax.text(7.75, 1.1, 'VISUALIZATION\nPygame UI | Rendering', 
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Arrows showing data flow
    arrow_props = dict(arrowstyle='->', lw=2, color='darkblue')
    
    # Environment -> Worm
    arrow1 = FancyArrowPatch((5, 8), (5, 7.3), **arrow_props)
    ax.add_patch(arrow1)
    
    # Worm -> Sensory
    arrow2 = FancyArrowPatch((2.25, 6.5), (2.25, 5.7), **arrow_props)
    ax.add_patch(arrow2)
    
    # Sensory -> Motor
    arrow3 = FancyArrowPatch((4, 5.1), (6, 5.1), **arrow_props)
    ax.add_patch(arrow3)
    ax.text(5, 5.35, 'integrate', ha='center', fontsize=8, style='italic')
    
    # Motor -> Worm
    arrow4 = FancyArrowPatch((7.75, 4.5), (7.75, 7), **arrow_props)
    ax.add_patch(arrow4)
    arrow4b = FancyArrowPatch((7.75, 7), (5.5, 6.9), **arrow_props)
    ax.add_patch(arrow4b)
    
    # Worm -> Evolution
    arrow5 = FancyArrowPatch((2.25, 6.5), (2.25, 3.7), **arrow_props)
    ax.add_patch(arrow5)
    
    # Evolution -> Worm
    arrow6 = FancyArrowPatch((1.5, 3.1), (1.5, 6.9), color='darkgreen', lw=2, arrowstyle='->')
    ax.add_patch(arrow6)
    
    # Worm -> Metrics
    arrow7 = FancyArrowPatch((7.75, 6.5), (7.75, 3.7), **arrow_props)
    ax.add_patch(arrow7)
    
    # Metrics -> Data
    arrow8 = FancyArrowPatch((7.75, 2.5), (2.25, 1.7), **arrow_props)
    ax.add_patch(arrow8)
    
    # Data -> Visualization
    arrow9 = FancyArrowPatch((4, 1.1), (6, 1.1), **arrow_props)
    ax.add_patch(arrow9)
    
    # Worm -> Visualization
    arrow10 = FancyArrowPatch((5.5, 6.5), (7.75, 1.7), color='purple', lw=1.5, arrowstyle='->', alpha=0.6)
    ax.add_patch(arrow10)
    
    # Add legend
    legend_y = -0.3
    ax.text(0.5, legend_y, '→ Data Flow', fontsize=9, color='darkblue', fontweight='bold')
    ax.text(3, legend_y, '← Feedback', fontsize=9, color='darkgreen', fontweight='bold')
    ax.text(5.5, legend_y, '⟷ Bidirectional', fontsize=9, color='purple', fontweight='bold', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig("plots/02_architecture.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("✓ Generated: plots/02_architecture.png")
    plt.close()


if __name__ == "__main__":
    print("🏗️  Generating architecture diagram...")
    generate_architecture_diagram()
