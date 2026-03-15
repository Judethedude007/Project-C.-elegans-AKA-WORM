import matplotlib.pyplot as plt
import numpy as np

population_history = []
egg_history = []
time_history = []
avg_speed_history = []
avg_food_history = []
avg_phero_history = []

def record_stats(worms, eggs, simulation_time):
    population_history.append(len(worms))
    egg_history.append(len(eggs))
    time_history.append(simulation_time)
    avg_speed_history.append(np.mean([w.gene_speed for w in worms]) if worms else 0)
    avg_food_history.append(np.mean([w.gene_food_sense for w in worms]) if worms else 0)
    avg_phero_history.append(np.mean([w.gene_phero_sense for w in worms]) if worms else 0)

def plot_population():
    plt.figure()
    plt.plot(time_history, population_history, label="Worms")
    plt.plot(time_history, egg_history, label="Eggs")
    plt.title("Worm and Egg Population")
    plt.xlabel("Time")
    plt.ylabel("Count")
    plt.legend()
    plt.show()

def plot_gene_evolution():
    plt.figure()
    plt.plot(time_history, avg_speed_history, label="Avg Speed Gene")
    plt.plot(time_history, avg_food_history, label="Avg Food Sense")
    plt.plot(time_history, avg_phero_history, label="Avg Pheromone Sense")
    plt.title("Gene Evolution")
    plt.xlabel("Time")
    plt.ylabel("Gene Value")
    plt.legend()
    plt.show()
