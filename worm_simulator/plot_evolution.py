import argparse
import csv
import os
from typing import Dict, List

import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(description="Plot evolutionary run statistics from a CSV log.")
    parser.add_argument("csv_path", nargs="?", default=None, help="Path to evolution_run_*.csv")
    parser.add_argument("--no-show", action="store_true", help="Save image only and skip interactive window")
    return parser.parse_args()


def find_latest_csv(search_dir: str):
    if not os.path.isdir(search_dir):
        return None
    candidates = []
    for name in os.listdir(search_dir):
        if name.startswith("evolution_run_") and name.endswith(".csv"):
            candidates.append(os.path.join(search_dir, name))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def load_series(csv_path: str):
    series: Dict[str, List[float]] = {
        "sim_time": [],
        "worms": [],
        "avg_energy": [],
        "total_births": [],
        "total_deaths": [],
        "lineages": [],
        "food_total": [],
        "food_density": [],
        "pheromone_density": [],
    }

    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for key in series:
                value = row.get(key, "")
                if value == "":
                    series[key].append(0.0)
                else:
                    series[key].append(float(value))

    return series


def main():
    args = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    runs_dir = os.path.join(script_dir, "runs")

    csv_path = args.csv_path or find_latest_csv(runs_dir)
    if not csv_path:
        raise SystemExit("No run CSV found. Generate a run first or pass an explicit CSV path.")
    if not os.path.exists(csv_path):
        raise SystemExit(f"CSV not found: {csv_path}")

    data = load_series(csv_path)
    if not data["sim_time"]:
        raise SystemExit(f"CSV has no rows: {csv_path}")

    time_axis = data["sim_time"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    fig.suptitle("Evolution Run Statistics", fontsize=14)

    axes[0, 0].plot(time_axis, data["worms"], color="#3B82F6", linewidth=1.8)
    axes[0, 0].set_title("Population")
    axes[0, 0].set_xlabel("Simulation Time")
    axes[0, 0].set_ylabel("Worm Count")
    axes[0, 0].grid(alpha=0.25)

    axes[0, 1].plot(time_axis, data["avg_energy"], color="#10B981", linewidth=1.8)
    axes[0, 1].set_title("Average Energy")
    axes[0, 1].set_xlabel("Simulation Time")
    axes[0, 1].set_ylabel("Energy")
    axes[0, 1].grid(alpha=0.25)

    axes[1, 0].plot(time_axis, data["total_births"], label="Births", color="#F59E0B", linewidth=1.6)
    axes[1, 0].plot(time_axis, data["total_deaths"], label="Deaths", color="#EF4444", linewidth=1.6)
    axes[1, 0].set_title("Cumulative Births vs Deaths")
    axes[1, 0].set_xlabel("Simulation Time")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].legend(loc="best")
    axes[1, 0].grid(alpha=0.25)

    axes[1, 1].plot(time_axis, data["lineages"], label="Lineages", color="#8B5CF6", linewidth=1.6)
    axes[1, 1].plot(time_axis, data["food_total"], label="Food Total", color="#22C55E", linewidth=1.6)
    axes[1, 1].set_title("Lineages and Food")
    axes[1, 1].set_xlabel("Simulation Time")
    axes[1, 1].set_ylabel("Value")
    axes[1, 1].legend(loc="best")
    axes[1, 1].grid(alpha=0.25)

    image_path = os.path.splitext(csv_path)[0] + ".png"
    fig.savefig(image_path, dpi=160)
    print(f"Saved graph image: {image_path}")

    if not args.no_show:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
