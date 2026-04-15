import numpy as np
from scipy.spatial import KDTree


class MovementMetrics:
    """Track Mean Squared Displacement of worm population."""
    def __init__(self):
        self.initial_positions = {}
        self.msd_history = []

    def update(self, worms):
        displacements = []

        for i, w in enumerate(worms):
            if i not in self.initial_positions:
                self.initial_positions[i] = (w.x, w.y)

            x0, y0 = self.initial_positions[i]
            dx = w.x - x0
            dy = w.y - y0

            displacements.append(dx*dx + dy*dy)

        if displacements:
            self.msd_history.append(np.mean(displacements))
        else:
            self.msd_history.append(0.0)


class GeneticMetrics:
    """Track genetic variance (evolution signal)."""
    def __init__(self):
        self.history = {
            "speed": [],
            "food_sense": [],
            "pheromone_sense": [],
            "reproduction_energy": []
        }

    def update(self, worms):
        if not worms:
            self.history["speed"].append(0.0)
            self.history["food_sense"].append(0.0)
            self.history["pheromone_sense"].append(0.0)
            self.history["reproduction_energy"].append(0.0)
            return

        speed = [float(w.gene_speed) for w in worms]
        food = [float(w.gene_food_sense) for w in worms]
        pher = [float(w.gene_phero_sense) for w in worms]
        repro = [float(w.gene_reproduction_energy) for w in worms]

        self.history["speed"].append(np.var(speed))
        self.history["food_sense"].append(np.var(food))
        self.history["pheromone_sense"].append(np.var(pher))
        self.history["reproduction_energy"].append(np.var(repro))


class ClusterMetrics:
    """Detect and track worm clustering behavior."""
    def __init__(self, radius=20):
        self.radius = radius
        self.cluster_sizes = []
        self.cluster_count_history = []

    def update(self, worms):
        if len(worms) < 2:
            self.cluster_sizes.append(0)
            self.cluster_count_history.append(0)
            return

        points = np.array([(float(w.x), float(w.y)) for w in worms])
        tree = KDTree(points)

        visited = set()
        clusters = []

        for i in range(len(points)):
            if i in visited:
                continue

            # Connected-component clustering over the radius-neighbor graph.
            stack = [i]
            component = set()
            while stack:
                idx = stack.pop()
                if idx in visited:
                    continue
                visited.add(idx)
                component.add(idx)
                neighbors = tree.query_ball_point(points[idx], self.radius)
                for n_idx in neighbors:
                    if n_idx not in visited:
                        stack.append(n_idx)

            clusters.append(len(component))

        if clusters:
            self.cluster_sizes.append(max(clusters))
            self.cluster_count_history.append(len(clusters))
        else:
            self.cluster_sizes.append(0)
            self.cluster_count_history.append(0)


class EcosystemMetrics:
    """High-level ecosystem health metrics."""
    def __init__(self):
        self.population_history = []
        self.birth_rate_history = []
        self.death_rate_history = []
        self.avg_energy_history = []
        self.avg_generation_history = []
        self.lineage_count_history = []

    def update(self, worms, eggs, births, deaths, frame_time):
        self.population_history.append(len(worms))
        
        # Compute rates per second
        if frame_time > 0:
            self.birth_rate_history.append(births / frame_time)
            self.death_rate_history.append(deaths / frame_time)
        else:
            self.birth_rate_history.append(0.0)
            self.death_rate_history.append(0.0)

        avg_energy = np.mean([float(w.energy) for w in worms]) if worms else 0.0
        self.avg_energy_history.append(avg_energy)

        if worms:
            generations = [float(getattr(w, "generation", 0)) for w in worms]
            lineages = {int(getattr(w, "lineage_id", -1)) for w in worms}
            self.avg_generation_history.append(float(np.mean(generations)))
            self.lineage_count_history.append(len(lineages))
        else:
            self.avg_generation_history.append(0.0)
            self.lineage_count_history.append(0)


def export_metrics_to_csv(movement_metrics, genetic_metrics, cluster_metrics, ecosystem_metrics, filename="metrics.csv"):
    """Export all metrics to CSV file for analysis."""
    import csv
    
    # Determine number of timesteps
    n_steps = len(movement_metrics.msd_history)
    
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "time_step",
            "msd",
            "speed_variance",
            "food_sense_variance",
            "pheromone_sense_variance",
            "reproduction_energy_variance",
            "max_cluster_size",
            "num_clusters",
            "population",
            "birth_rate",
            "death_rate",
            "avg_energy",
            "avg_generation",
            "lineage_count",
        ])
        
        # Data rows
        for i in range(n_steps):
            msd = movement_metrics.msd_history[i] if i < len(movement_metrics.msd_history) else 0.0
            speed_var = genetic_metrics.history["speed"][i] if i < len(genetic_metrics.history["speed"]) else 0.0
            food_var = genetic_metrics.history["food_sense"][i] if i < len(genetic_metrics.history["food_sense"]) else 0.0
            pher_var = genetic_metrics.history["pheromone_sense"][i] if i < len(genetic_metrics.history["pheromone_sense"]) else 0.0
            repro_var = genetic_metrics.history["reproduction_energy"][i] if i < len(genetic_metrics.history["reproduction_energy"]) else 0.0
            cluster_size = cluster_metrics.cluster_sizes[i] if i < len(cluster_metrics.cluster_sizes) else 0
            cluster_count = cluster_metrics.cluster_count_history[i] if i < len(cluster_metrics.cluster_count_history) else 0
            pop = ecosystem_metrics.population_history[i] if i < len(ecosystem_metrics.population_history) else 0
            birth_rate = ecosystem_metrics.birth_rate_history[i] if i < len(ecosystem_metrics.birth_rate_history) else 0.0
            death_rate = ecosystem_metrics.death_rate_history[i] if i < len(ecosystem_metrics.death_rate_history) else 0.0
            avg_energy = ecosystem_metrics.avg_energy_history[i] if i < len(ecosystem_metrics.avg_energy_history) else 0.0
            avg_generation = ecosystem_metrics.avg_generation_history[i] if i < len(ecosystem_metrics.avg_generation_history) else 0.0
            lineage_count = ecosystem_metrics.lineage_count_history[i] if i < len(ecosystem_metrics.lineage_count_history) else 0
            
            writer.writerow([
                i,
                round(msd, 4),
                round(speed_var, 6),
                round(food_var, 6),
                round(pher_var, 6),
                round(repro_var, 4),
                int(cluster_size),
                int(cluster_count),
                int(pop),
                round(birth_rate, 4),
                round(death_rate, 4),
                round(avg_energy, 2),
                round(avg_generation, 3),
                int(lineage_count),
            ])
    
    print(f"✓ Metrics exported to {filename}")
