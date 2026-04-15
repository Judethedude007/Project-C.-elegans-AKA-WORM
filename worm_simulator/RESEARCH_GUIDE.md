# 🧬 Worm Simulator: Research Framework

## Quick Start

### 1. Run Normal Simulation
```bash
python main_gpu.py
```

This will:
- Run the full ecosystem simulation with all features enabled
- Track metrics automatically (MSD, clustering, genetics, population)
- Export data to `metrics.csv` on exit
- Print ablation configuration on startup

### 2. Plot Results
```bash
python plot_metrics.py
```

Generates `metrics_plot.png` with 6 research-grade plots.

---

## 📊 Metrics System

### What Gets Tracked

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **MSD** | Mean Squared Displacement | Movement distance from initial position (exploring?) |
| **Cluster Size** | Max worms in one location | Collective behavior / pheromone effectiveness |
| **Gene Variance** | Standard deviation of genes | Evolution rate (adaptation signal) |
| **Population** | Number of live worms | Ecosystem stability |
| **Birth/Death Rate** | Reproduction vs starvation | Selection pressure |
| **Avg Energy** | Mean worm energy level | Food availability vs metabolic demand |

### Data Format (`metrics.csv`)

```
time_step,msd,speed_variance,food_sense_variance,...,avg_energy
0,0.0,0.0,0.0,...,500.0
1,12.45,0.003,0.002,...,485.3
2,28.91,0.005,0.004,...,470.8
...
```

---

## 🔥 Ablation Framework (The Research Part)

Ablation experiments isolate which behaviors drive emergence.

### Edit `ablation_config.py`

```python
# Experiment 1: Do worms need pheromones to cluster?
ENABLE_PHEROMONE = False         # Disable smell
ENABLE_EVOLUTION = True           # Keep adaptation
ENABLE_NEURAL_BIAS = True         # Keep neural circuits
```

### Run Experiments

**Experiment A: Normal**
```python
# ablation_config.py
ENABLE_PHEROMONE = True
ENABLE_EVOLUTION = True
ENABLE_NEURAL_BIAS = True
```
```bash
python main_gpu.py
# metrics_a_normal.csv
```

**Experiment B: No Pheromone**
```python
# ablation_config.py
ENABLE_PHEROMONE = False
ENABLE_EVOLUTION = True
ENABLE_NEURAL_BIAS = True
```
```bash
python main_gpu.py
# metrics_b_no_pheromone.csv
```

### Compare Results

| Condition | Clustering | MSD | Population |
|-----------|-----------|-----|-----------|
| Normal | ✅ High | Low | Stable |
| No Pheromone | ❌ Low | High | Unstable |
| No Evolution | ⚠️ Medium | Medium | Declining |

**Interpretation:**
- If clustering drops without pheromone → **pheromone drives aggregation**
- If MSD increases → **worms explore more when isolated**
- This proves causality (not just correlation)

---

## 🧪 Proposed Experiments

### Experiment 1: Neural Necessity
**Question:** Do you *need* neural circuits for adaptation?

```python
ENABLE_NEURAL_BIAS = False
ENABLE_EVOLUTION = True
```

**Prediction:** Population crashes (no learning, only fixed genetics)
**If wrong:** Maybe evolution + reflexes is already powerful enough?

### Experiment 2: Collective Intelligence
**Question:** Is pheromone the ONLY way worms coordinate?

```python
ENABLE_PHEROMONE = False
ENABLE_EVOLUTION = True
ENABLE_NEURAL_BIAS = True
```

**Prediction:** Still cluster (neural + evolution suffices)
**If wrong:** Pheromone is essential to emergence

### Experiment 3: Emergent Specialization
**Question:** Does population evolve roles (foragers vs egglayers)?

Look at: `genetic_metrics.history["reproduction_energy"]` variance increase

### Experiment 4: Response to Stress
**Question:** How do ablations affect crisis response?

Compare:
- Normal + starvation condition
- No evolution + starvation condition

---

## 📈 Publication-Ready Analysis

### Step 1: Collect Data
```bash
# Run each condition 3 times for statistics
for i in 1 2 3; do
    python main_gpu.py
    mv metrics.csv metrics_condition_run_${i}.csv
done
```

### Step 2: Aggregate
```python
import pandas as pd
import numpy as np

conditions = ["normal", "no_pheromone", "no_evolution"]
results = {}

for condition in conditions:
    dfs = [pd.read_csv(f"metrics_{condition}_run_{i}.csv") for i in range(1,4)]
    results[condition] = {
        "msd_mean": np.mean([df["msd"].iloc[-1] for df in dfs]),
        "msd_std": np.std([df["msd"].iloc[-1] for df in dfs]),
        "cluster_mean": np.mean([df["max_cluster_size"].iloc[-1] for df in dfs]),
        ...
    }
```

### Step 3: Plot with Error Bars
```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.bar(
    conditions,
    [results[c]["msd_mean"] for c in conditions],
    yerr=[results[c]["msd_std"] for c in conditions],
    capsize=5, alpha=0.7
)
ax.set_ylabel("MSD (pixels)")
ax.set_title("Effect of Pheromones on Movement Distance")
plt.savefig("figure_1_msd_ablation.png", dpi=300)
```

---

## 🔬 What Makes This Research-Grade

❌ **Not research:**
- "Worms cluster" (observation)
- "It's emergent" (vague)
- "Look how cool!" (demo)

✅ **Research:**
- "Clustering increases from 5±2 to 18±4 worms per cluster when pheromones enabled" (quantified)
- "Disabling pheromone decreases population MSD by 60% (ablation)"
- "Population exhibits density-dependent natural selection" (mechanism)

---

## 📋 Troubleshooting

### Q: metrics.csv is empty
**A:** Make sure `SAVE_METRICS = True` in ablation_config.py

### Q: plots look weird / unstable
**A:** Increase simulation length (more data = smoother trends)

### Q: How do I only run 1000 timesteps?
**A:** Exit early with `Ctrl+C`, metrics will still export

### Q: Can I compare my results with others?
**A:** Yes! metrics.csv is the standard format. Share conditions from `ablation_config.py`

---

## 🚀 Next Steps

1. ✅ Run normal simulation → `metrics.csv`
2. ✅ Plot results → `metrics_plot.png`
3. ✅ Run 3 ablation conditions
4. ✅ Create comparison chart
5. 🎯 Write figure caption for paper
6. 🎯 Submit results to research journal!

---

## For Questions / Issues

The metrics system is built on:
- `metrics.py` - Core tracking classes
- `ablation_config.py` - Experiment configuration
- `plot_metrics.py` - Visualization
- Integration in `main_gpu.py` after line 818

All are fully open for modification!
