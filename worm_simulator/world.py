import numpy as np
from config import WORLD_SIZE


class World:

    def __init__(self):

        self.food = np.random.rand(WORLD_SIZE, WORLD_SIZE).astype(np.float32)
        self.pheromone = np.zeros((WORLD_SIZE, WORLD_SIZE), dtype=np.float32)

    def update(self, dt=1 / 60):

        self.food += 0.0005

        diffusion = (
            np.roll(self.food, 1, 0)
            + np.roll(self.food, -1, 0)
            + np.roll(self.food, 1, 1)
            + np.roll(self.food, -1, 1)
        ) / 4

        self.food += 0.1 * (diffusion - self.food)
        self.food = np.clip(self.food, 0, 1)

        # Keep pheromone trails but let them fade over time.
        self.pheromone *= 0.995

        neighbors = (
            np.roll(self.pheromone, 1, axis=0)
            + np.roll(self.pheromone, -1, axis=0)
            + np.roll(self.pheromone, 1, axis=1)
            + np.roll(self.pheromone, -1, axis=1)
        ) / 4.0
        self.pheromone = (self.pheromone * 0.9) + (neighbors * 0.1)

    def get_food(self, x, y):
        return self.food[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE]

    def get_pheromone(self, x, y):
        return self.pheromone[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE]
