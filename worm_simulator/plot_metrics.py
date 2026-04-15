"""
Plot metrics for research analysis.
Run after simulation: python plot_metrics.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Try to load metrics
if not os.path.exists("metrics.csv"):
    print("❌ metrics.csv not found. Run simulation first.")
    exit(1)

df = pd.read_csv("metrics.csv")

# Create figure with subplots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle("Worm Simulator: Research Metrics", fontsize=16, fontweight='bold')

# 1. Mean Squared Displacement
ax = axes[0, 0]
ax.plot(df["time_step"], df["msd"], label="MSD", linewidth=2, color='blue')
ax.fill_between(df["time_step"], df["msd"], alpha=0.3, color='blue')
ax.set_xlabel("Time Step")
ax.set_ylabel("MSD (pixels²)")
ax.set_title("Movement: Mean Squared Displacement")
ax.grid(True, alpha=0.3)

# 2. Cluster Formation Over Time
ax = axes[0, 1]
ax.plot(df["time_step"], df["max_cluster_size"], label="Max Cluster Size", linewidth=2, color='red')
ax.fill_between(df["time_step"], df["max_cluster_size"], alpha=0.3, color='red')
ax.set_xlabel("Time Step")
ax.set_ylabel("Max Cluster Size (worms)")
ax.set_title("Clustering: Max Cluster Size")
ax.grid(True, alpha=0.3)

# 3. Population Dynamics
ax = axes[0, 2]
ax.plot(df["time_step"], df["population"], label="Population", linewidth=2, color='green')
ax.fill_between(df["time_step"], df["population"], alpha=0.3, color='green')
ax.set_xlabel("Time Step")
ax.set_ylabel("Number of Worms")
ax.set_title("Population Dynamics")
ax.grid(True, alpha=0.3)

# 4. Genetic Variance (Evolution)
ax = axes[1, 0]
ax.plot(df["time_step"], df["speed_variance"], label="Speed Gene", linewidth=2, color='purple')
ax.plot(df["time_step"], df["food_sense_variance"], label="Food Sense Gene", linewidth=2, color='orange')
ax.plot(df["time_step"], df["pheromone_sense_variance"], label="Pheromone Sense Gene", linewidth=2, color='brown')
ax.set_xlabel("Time Step")
ax.set_ylabel("Variance")
ax.set_title("Genetic Diversity: Gene Variance")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# 5. Birth/Death Rates
ax = axes[1, 1]
ax.plot(df["time_step"], df["birth_rate"], label="Birth Rate", linewidth=2, color='green')
ax.plot(df["time_step"], df["death_rate"], label="Death Rate", linewidth=2, color='red')
ax.fill_between(df["time_step"], 0, df["birth_rate"], alpha=0.2, color='green')
ax.fill_between(df["time_step"], 0, df["death_rate"], alpha=0.2, color='red')
ax.set_xlabel("Time Step")
ax.set_ylabel("Rate (worms/sec)")
ax.set_title("Population Turnover")
ax.legend()
ax.grid(True, alpha=0.3)

# 6. Average Energy
ax = axes[1, 2]
ax.plot(df["time_step"], df["avg_energy"], label="Avg Energy", linewidth=2, color='cyan')
ax.fill_between(df["time_step"], df["avg_energy"], alpha=0.3, color='cyan')
ax.set_xlabel("Time Step")
ax.set_ylabel("Energy (per worm)")
ax.set_title("Population Energy: Metabolic Health")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("metrics_plot.png", dpi=300, bbox_inches='tight')
print("✓ Plot saved to metrics_plot.png")
plt.show()
