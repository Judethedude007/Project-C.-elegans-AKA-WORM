"""
Ablation Configuration for Research Experiments
================================================

Toggle neural/behavioral features on/off for causal analysis.
Run different experiments to understand what drives emergence.

Usage:
    1. Edit the flags below
    2. Run: python main_gpu.py
    3. View results in metrics.csv and plot via plot_metrics.py

Example experiments:
    Normal mode:         All flags = True
    No pheromone:        ENABLE_PHEROMONE = False
    No evolution:        ENABLE_EVOLUTION = False  
    Neural-only:         ENABLE_PHEROMONE = False, ENABLE_EVOLUTION = False
    Isolation:           ENABLE_CLUSTERING = False
"""

# Core behavioral systems
ENABLE_PHEROMONE = True           # Allow worms to sense and follow colony pheromones
ENABLE_EVOLUTION = True            # Allow genetics to evolve through mutation/selection
ENABLE_NEURAL_BIAS = True          # Use neural network decision-making vs pure reflexes
ENABLE_CLUSTERING = True           # Allow aggregation (pheromone-based swarm)

# Logging & metrics
SAVE_METRICS = True                # Export CSV data for analysis
VERBOSE_ABLATIONS = False          # Print per-frame ablation status

# Preset experiments (uncomment one to use)
# Preset: Neural Only (No collective behavior)
# ENABLE_PHEROMONE = False
# ENABLE_EVOLUTION = False

# Preset: Pure Genetics (No neural computation)
# ENABLE_NEURAL_BIAS = False

# Preset: Static Behavior (No adaptation)
# ENABLE_EVOLUTION = False
# ENABLE_NEURAL_BIAS = False

# --- END ABLATION CONFIG ---

def get_ablation_summary():
    """Return human-readable ablation status."""
    return f"""
╔════════════════════════════════════════╗
║  ABLATION CONFIGURATION                ║
╠════════════════════════════════════════╣
║ Pheromone Sensing: {str(ENABLE_PHEROMONE).ljust(21)}║
║ Evolution:         {str(ENABLE_EVOLUTION).ljust(21)}║
║ Neural Bias:       {str(ENABLE_NEURAL_BIAS).ljust(21)}║
║ Clustering:        {str(ENABLE_CLUSTERING).ljust(21)}║
║ Save Metrics:      {str(SAVE_METRICS).ljust(21)}║
╚════════════════════════════════════════╝
    """
