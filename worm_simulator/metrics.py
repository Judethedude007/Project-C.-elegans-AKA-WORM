import csv
from typing import Any, Iterable, List

import numpy as np


class MetricsManager:
    """Centralized per-step metrics collection for research runs."""

    def __init__(self, cluster_radius: float = 20.0):
        self.cluster_radius = float(cluster_radius)

        self.time_steps: List[int] = []

        # Population and events
        self.population: List[int] = []
        self.births: List[int] = []
        self.deaths: List[int] = []
        self.birth_rate: List[float] = []
        self.death_rate: List[float] = []

        # Movement
        self.msd: List[float] = []

        # Genetics
        self.speed_var: List[float] = []
        self.food_var: List[float] = []
        self.pheromone_var: List[float] = []
        self.reproduction_energy_var: List[float] = []

        # Clustering
        self.max_cluster_size: List[int] = []
        self.num_clusters: List[int] = []

        # Energy
        self.avg_energy: List[float] = []

        # Optional lineage/generation signals
        self.avg_generation: List[float] = []
        self.lineage_count: List[int] = []

        # Internal state for MSD
        self.initial_positions = {}

    def update(self, step: int, worms: Iterable[Any], births_this_step: int, deaths_this_step: int, dt: float = 1.0):
        worms = list(worms)
        pop = len(worms)

        self.time_steps.append(int(step))
        self.population.append(pop)

        births_this_step = int(births_this_step)
        deaths_this_step = int(deaths_this_step)
        self.births.append(births_this_step)
        self.deaths.append(deaths_this_step)

        safe_dt = max(float(dt), 1e-6)
        self.birth_rate.append(float(births_this_step) / safe_dt)
        self.death_rate.append(float(deaths_this_step) / safe_dt)

        self.msd.append(self.compute_msd(worms))

        if pop > 0:
            speeds = [self._gene_value(w, "gene_speed", "speed", default=0.0) for w in worms]
            foods = [self._gene_value(w, "gene_food_sense", "food_sense", default=0.0) for w in worms]
            phers = [self._gene_value(w, "gene_phero_sense", "pheromone_sense", default=0.0) for w in worms]
            repros = [
                self._gene_value(
                    w,
                    "gene_reproduction_energy",
                    "reproduction_energy",
                    default=0.0,
                )
                for w in worms
            ]

            self.speed_var.append(float(np.var(speeds)))
            self.food_var.append(float(np.var(foods)))
            self.pheromone_var.append(float(np.var(phers)))
            self.reproduction_energy_var.append(float(np.var(repros)))

            self.avg_energy.append(float(np.mean([float(getattr(w, "energy", 0.0)) for w in worms])))
            self.avg_generation.append(float(np.mean([float(getattr(w, "generation", 0.0)) for w in worms])))
            self.lineage_count.append(len({int(getattr(w, "lineage_id", -1)) for w in worms}))
        else:
            self.speed_var.append(0.0)
            self.food_var.append(0.0)
            self.pheromone_var.append(0.0)
            self.reproduction_energy_var.append(0.0)
            self.avg_energy.append(0.0)
            self.avg_generation.append(0.0)
            self.lineage_count.append(0)

        max_cluster, cluster_count = self.compute_clusters(worms, radius=self.cluster_radius)
        self.max_cluster_size.append(int(max_cluster))
        self.num_clusters.append(int(cluster_count))

    @staticmethod
    def _gene_value(worm: Any, primary: str, fallback: str, default: float = 0.0) -> float:
        value = getattr(worm, primary, None)
        if value is None:
            value = getattr(worm, fallback, default)
        return float(value)

    def compute_msd(self, worms: Iterable[Any]) -> float:
        worms = list(worms)
        if not worms:
            return 0.0

        total = 0.0
        count = 0

        for worm in worms:
            wid = id(worm)
            if wid not in self.initial_positions:
                self.initial_positions[wid] = (float(worm.x), float(worm.y))

            x0, y0 = self.initial_positions[wid]
            dx = float(worm.x) - x0
            dy = float(worm.y) - y0
            total += dx * dx + dy * dy
            count += 1

        return total / count if count > 0 else 0.0

    @staticmethod
    def compute_clusters(worms: Iterable[Any], radius: float = 20.0):
        worms = list(worms)
        n = len(worms)
        if n == 0:
            return 0, 0

        visited = set()
        max_cluster = 0
        cluster_count = 0
        radius_sq = float(radius) * float(radius)

        for i in range(n):
            if i in visited:
                continue

            cluster_count += 1
            stack = [i]
            size = 0

            while stack:
                idx = stack.pop()
                if idx in visited:
                    continue

                visited.add(idx)
                size += 1

                wx = float(worms[idx].x)
                wy = float(worms[idx].y)

                for j in range(n):
                    if j in visited:
                        continue
                    dx = wx - float(worms[j].x)
                    dy = wy - float(worms[j].y)
                    if dx * dx + dy * dy <= radius_sq:
                        stack.append(j)

            if size > max_cluster:
                max_cluster = size

        return max_cluster, cluster_count

    def save_csv(self, filename: str = "metrics.csv"):
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "time",
                    "time_step",
                    "population",
                    "births",
                    "deaths",
                    "birth_rate",
                    "death_rate",
                    "msd",
                    "speed_var",
                    "food_var",
                    "pheromone_var",
                    "speed_variance",
                    "food_sense_variance",
                    "pheromone_sense_variance",
                    "reproduction_energy_variance",
                    "max_cluster",
                    "max_cluster_size",
                    "num_clusters",
                    "avg_energy",
                    "avg_generation",
                    "lineage_count",
                ]
            )

            for i in range(len(self.time_steps)):
                speed_variance = self.speed_var[i]
                food_variance = self.food_var[i]
                pheromone_variance = self.pheromone_var[i]
                row = [
                    int(self.time_steps[i]),
                    int(self.time_steps[i]),
                    int(self.population[i]),
                    int(self.births[i]),
                    int(self.deaths[i]),
                    round(float(self.birth_rate[i]), 6),
                    round(float(self.death_rate[i]), 6),
                    round(float(self.msd[i]), 6),
                    round(float(speed_variance), 6),
                    round(float(food_variance), 6),
                    round(float(pheromone_variance), 6),
                    round(float(speed_variance), 6),
                    round(float(food_variance), 6),
                    round(float(pheromone_variance), 6),
                    round(float(self.reproduction_energy_var[i]), 6),
                    int(self.max_cluster_size[i]),
                    int(self.max_cluster_size[i]),
                    int(self.num_clusters[i]),
                    round(float(self.avg_energy[i]), 6),
                    round(float(self.avg_generation[i]), 6),
                    int(self.lineage_count[i]),
                ]
                writer.writerow(row)

        print(f"✓ Metrics exported to {filename}")


def export_metrics_to_csv(*args, filename: str = "metrics.csv"):
    """Compatibility export helper.

    Supports either:
      - export_metrics_to_csv(metrics_manager, filename="metrics.csv")
      - export_metrics_to_csv(movement, genetic, cluster, ecosystem, filename="metrics.csv")
    """

    if len(args) == 1 and isinstance(args[0], MetricsManager):
        args[0].save_csv(filename=filename)
        return

    if len(args) != 4:
        raise ValueError("Expected either MetricsManager or 4 legacy metric objects")

    movement_metrics, genetic_metrics, cluster_metrics, ecosystem_metrics = args

    manager = MetricsManager()
    n_steps = len(getattr(movement_metrics, "msd_history", []))

    for step in range(n_steps):
        manager.time_steps.append(step)
        manager.population.append(
            int(ecosystem_metrics.population_history[step]) if step < len(ecosystem_metrics.population_history) else 0
        )

        births = 0.0
        deaths = 0.0
        if step < len(getattr(ecosystem_metrics, "birth_rate_history", [])):
            births = float(ecosystem_metrics.birth_rate_history[step])
        if step < len(getattr(ecosystem_metrics, "death_rate_history", [])):
            deaths = float(ecosystem_metrics.death_rate_history[step])

        manager.birth_rate.append(births)
        manager.death_rate.append(deaths)
        manager.births.append(int(round(births)))
        manager.deaths.append(int(round(deaths)))

        manager.msd.append(float(movement_metrics.msd_history[step]) if step < len(movement_metrics.msd_history) else 0.0)

        manager.speed_var.append(
            float(genetic_metrics.history.get("speed", [0.0] * n_steps)[step]) if step < len(genetic_metrics.history.get("speed", [])) else 0.0
        )
        manager.food_var.append(
            float(genetic_metrics.history.get("food_sense", [0.0] * n_steps)[step]) if step < len(genetic_metrics.history.get("food_sense", [])) else 0.0
        )
        manager.pheromone_var.append(
            float(genetic_metrics.history.get("pheromone_sense", [0.0] * n_steps)[step]) if step < len(genetic_metrics.history.get("pheromone_sense", [])) else 0.0
        )
        manager.reproduction_energy_var.append(
            float(genetic_metrics.history.get("reproduction_energy", [0.0] * n_steps)[step]) if step < len(genetic_metrics.history.get("reproduction_energy", [])) else 0.0
        )

        manager.max_cluster_size.append(
            int(cluster_metrics.cluster_sizes[step]) if step < len(cluster_metrics.cluster_sizes) else 0
        )
        manager.num_clusters.append(
            int(cluster_metrics.cluster_count_history[step]) if step < len(cluster_metrics.cluster_count_history) else 0
        )

        manager.avg_energy.append(
            float(ecosystem_metrics.avg_energy_history[step]) if step < len(ecosystem_metrics.avg_energy_history) else 0.0
        )
        manager.avg_generation.append(
            float(ecosystem_metrics.avg_generation_history[step]) if step < len(getattr(ecosystem_metrics, "avg_generation_history", [])) else 0.0
        )
        manager.lineage_count.append(
            int(ecosystem_metrics.lineage_count_history[step]) if step < len(getattr(ecosystem_metrics, "lineage_count_history", [])) else 0
        )

    manager.save_csv(filename=filename)
