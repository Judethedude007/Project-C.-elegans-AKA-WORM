import numpy as np
from config import WORLD_SIZE

GRID_SIZE = 128


class World:

    def __init__(self):

        self.food = np.random.rand(WORLD_SIZE, WORLD_SIZE).astype(np.float32)
        self.pheromone = np.zeros((WORLD_SIZE, WORLD_SIZE), dtype=np.float32)
        self.chem = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

        # Precompute a world->chemical index map for fast downsampling each frame.
        self._chem_world_idx = np.linspace(0, WORLD_SIZE - 1, GRID_SIZE).astype(np.int32)

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

        # Food releases chemical signal into the smell map.
        sampled_food = self.food[np.ix_(self._chem_world_idx, self._chem_world_idx)]
        self.chem += sampled_food * 5.0

        # Diffuse chemical concentration to neighboring cells.
        new_chem = np.zeros_like(self.chem)
        new_chem[1:-1, 1:-1] = (
            self.chem[1:-1, 1:-1] * 0.6
            + (
                self.chem[2:, 1:-1]
                + self.chem[:-2, 1:-1]
                + self.chem[1:-1, 2:]
                + self.chem[1:-1, :-2]
            )
            * 0.1
        )
        self.chem = np.clip(new_chem, 0.0, 1000.0)

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
