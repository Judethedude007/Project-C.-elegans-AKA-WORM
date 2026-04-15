"""
Generate All Research Diagrams
===============================

Master script to generate all publication-ready diagrams for your paper:
  1. Locomotion wave diagram
  2. System architecture 
  3. Population dynamics graph
  4. Genetic variance evolution
  5. Key metrics summary

Run after simulation:
  python generate_all_diagrams.py

Creates: plots/*.png
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Ensure plots directory exists
os.makedirs("plots", exist_ok=True)


def generate_locomotion_wave():
    """Generate locomotion wave propagation diagram."""
    print("\n📊 Generating locomotion wave diagram...")
    from matplotlib.patches import Circle
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("C. elegans Locomotion: Wave Propagation Model", fontsize=14, fontweight='bold')
    
    segments = 24
    segment_idx = np.arange(segments)
    times = [0, 0.3, 0.6, 0.9, 1.2]
    colors_time = plt.cm.viridis(np.linspace(0, 1, len(times)))
    
    A = 1.5
    omega = 2 * np.pi
    k = np.pi / 6
    
    for t, color in zip(times, colors_time):
        y = A * np.sin(omega * t - k * segment_idx)
        ax1.plot(segment_idx, y, marker='o', markersize=6, 
                label=f't = {t:.1f}s', color=color, linewidth=2, alpha=0.7)
    
    ax1.set_xlabel("Body Segment Index (head → tail)", fontsize=11)
    ax1.set_ylabel("Lateral Angle (radians)", fontsize=11)
    ax1.set_title("Phase Wave Propagation: How the worm generates forward motion", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Worm body at snapshot
    t_snapshot = 0.5
    angles = A * np.sin(omega * t_snapshot - k * segment_idx)
    segment_length = 1.0
    x_pos = [0]
    y_pos = [0]
    
    for i, angle in enumerate(angles):
        x_new = x_pos[-1] + segment_length * np.cos(angle)
        y_new = y_pos[-1] + segment_length * np.sin(angle)
        x_pos.append(x_new)
        y_pos.append(y_new)
    
    ax2.plot(x_pos, y_pos, 'o-', linewidth=3, markersize=6, 
            color=(0.8, 0.2, 0.2), label='Worm Body')
    ax2.scatter([x_pos[0]], [y_pos[0]], s=200, c='red', marker='o', 
               zorder=5, label='Head', edgecolors='darkred', linewidth=2)
    ax2.scatter([x_pos[-1]], [y_pos[-1]], s=100, c='orange', marker='s', 
               zorder=5, label='Tail', edgecolors='darkorange', linewidth=2)
    
    mid_idx = segments // 2
    ax2.annotate('Wave travels\nfront to back', 
                xy=(x_pos[mid_idx], y_pos[mid_idx]), 
                xytext=(x_pos[mid_idx] + 5, y_pos[mid_idx] + 8),
                fontsize=10, color='darkblue',
                arrowprops=dict(arrowstyle='->', color='darkblue', lw=2))
    
    ax2.set_xlabel("Position (arbitrary units)", fontsize=11)
    ax2.set_ylabel("Position (arbitrary units)", fontsize=11)
    ax2.set_title(f"Worm Body Curvature at t = {t_snapshot:.1f}s (24 segments)", fontsize=12)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=10)
    
    plt.tight_layout()
    plt.savefig("plots/01_locomotion_wave.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Generated: plots/01_locomotion_wave.png")


def generate_architecture():
    """Generate system architecture diagram using matplotlib."""
    print("\n🏗️  Generating architecture diagram...")
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
    plt.close()
    print("  ✓ Generated: plots/02_architecture.png
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
    plt.close()
    print("  ✓ Generated: plots/02_architecture.png")


def generate_metrics_plots():
    """Generate plots from metrics.csv if available."""
    if not os.path.exists("metrics.csv"):
        print("\n📊 No metrics.csv found. Run simulator first to generate data.")
        return
    
    print("\n📈 Generating metrics plots from simulation data...")
    df = pd.read_csv("metrics.csv")
    
    # Plot 1: Population Dynamics
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["time_step"], df["population"], linewidth=2.5, color='green', label='Population')
    ax.fill_between(df["time_step"], df["population"], alpha=0.3, color='green')
    ax.set_xlabel("Time Step", fontsize=12)
    ax.set_ylabel("Number of Worms", fontsize=12)
    ax.set_title("Population Dynamics Over Simulation", fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig("plots/03_population_dynamics.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Generated: plots/03_population_dynamics.png")
    
    # Plot 2: Cluster Formation
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["time_step"], df["max_cluster_size"], linewidth=2.5, color='red', label='Max Cluster Size')
    ax.fill_between(df["time_step"], df["max_cluster_size"], alpha=0.3, color='red')
    ax.set_xlabel("Time Step", fontsize=12)
    ax.set_ylabel("Cluster Size (worms)", fontsize=12)
    ax.set_title("Collective Behavior: Cluster Formation", fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig("plots/04_clustering.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Generated: plots/04_clustering.png")
    
    # Plot 3: Genetic Variance (Evolution Signal)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["time_step"], df["speed_variance"], linewidth=2, label='Speed Gene Variance', color='purple')
    ax.plot(df["time_step"], df["food_sense_variance"], linewidth=2, label='Food Sense Variance', color='orange')
    ax.plot(df["time_step"], df["pheromone_sense_variance"], linewidth=2, label='Pheromone Sense Variance', color='brown')
    ax.set_xlabel("Time Step", fontsize=12)
    ax.set_ylabel("Gene Variance", fontsize=12)
    ax.set_title("Evolution: Genetic Diversity Over Time", fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig("plots/05_genetic_variance.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Generated: plots/05_genetic_variance.png")
    
    # Plot 4: Movement (MSD)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["time_step"], df["msd"], linewidth=2.5, color='blue')
    ax.fill_between(df["time_step"], df["msd"], alpha=0.3, color='blue')
    ax.set_xlabel("Time Step", fontsize=12)
    ax.set_ylabel("Mean Squared Displacement (pixels²)", fontsize=12)
    ax.set_title("Locomotion: Mean Squared Displacement", fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("plots/06_movement_msd.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Generated: plots/06_movement_msd.png")


def main():
    """Generate all research diagrams."""
    print("="*60)
    print("🔬 GENERATING PUBLICATION-READY RESEARCH DIAGRAMS")
    print("="*60)
    
    generate_locomotion_wave()
    generate_architecture()
    generate_metrics_plots()
    
    print("\n" + "="*60)
    print("✅ All diagrams generated!")
    print("="*60)
    print("\nGenerated files in plots/:")
    for f in sorted(os.listdir("plots")):
        size = os.path.getsize(os.path.join("plots", f)) / 1024
        print(f"  📄 {f} ({size:.1f} KB)")
    print("\nUse these in your paper, blog, or LinkedIn! 📊")


if __name__ == "__main__":
    main()
