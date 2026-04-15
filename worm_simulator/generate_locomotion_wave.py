"""
Locomotion Wave Diagram
=======================

Shows the sinusoidal wave propagation along the worm body.
This is the fundamental principle of C. elegans locomotion:
each body segment follows the previous segment's angle with a phase lag.

Generates: plots/locomotion_wave.png
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

def generate_locomotion_wave():
    """Create a realistic worm locomotion wave visualization."""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("C. elegans Locomotion: Wave Propagation Model", fontsize=14, fontweight='bold')
    
    # ========== TOP: Phase Wave Over Time ==========
    segments = 24
    segment_idx = np.arange(segments)
    
    # Multiple time points showing wave propagation
    times = [0, 0.3, 0.6, 0.9, 1.2]
    colors_time = plt.cm.viridis(np.linspace(0, 1, len(times)))
    
    A = 1.5  # Amplitude (radians)
    omega = 2 * np.pi  # Angular frequency
    k = np.pi / 6  # Wavenumber (phase lag per segment)
    
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
    
    # ========== BOTTOM: Worm Body Visualization ==========
    # Draw actual worm body at a single time point
    t_snapshot = 0.5
    angles = A * np.sin(omega * t_snapshot - k * segment_idx)
    
    # Convert angles to x,y positions
    segment_length = 1.0  # pixels per segment
    x_pos = [0]
    y_pos = [0]
    
    for i, angle in enumerate(angles):
        x_new = x_pos[-1] + segment_length * np.cos(angle)
        y_new = y_pos[-1] + segment_length * np.sin(angle)
        x_pos.append(x_new)
        y_pos.append(y_new)
    
    # Draw the worm
    ax2.plot(x_pos, y_pos, 'o-', linewidth=3, markersize=6, 
            color=(0.8, 0.2, 0.2), label='Worm Body')
    
    # Highlight head
    ax2.scatter([x_pos[0]], [y_pos[0]], s=200, c='red', marker='o', 
               zorder=5, label='Head', edgecolors='darkred', linewidth=2)
    
    # Highlight tail
    ax2.scatter([x_pos[-1]], [y_pos[-1]], s=100, c='orange', marker='s', 
               zorder=5, label='Tail', edgecolors='darkorange', linewidth=2)
    
    # Add wave direction arrow
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
    plt.savefig("plots/locomotion_wave.png", dpi=300, bbox_inches='tight')
    print("✓ Generated: plots/locomotion_wave.png")
    plt.close()


if __name__ == "__main__":
    generate_locomotion_wave()
