import random
import numpy as np
from config import WORLD_SIZE

GRID_SIZE = 128


class World:

    def __init__(self):

        self.food = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.food_grid = np.zeros((WORLD_SIZE, WORLD_SIZE), dtype=np.float32)
        self.pheromone = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.chem = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

        self._world_to_food_idx = np.linspace(0, GRID_SIZE - 1, WORLD_SIZE).astype(np.int32)

        for _ in range(12):
            gx = random.randint(4, GRID_SIZE - 5)
            gy = random.randint(4, GRID_SIZE - 5)
            self.food[gx - 2:gx + 3, gy - 2:gy + 3] = 1.0

    def update(self, dt=1 / 60):

        # Food exists as a consumable resource grid that slowly spreads and respawns.
        food_diffusion = (
            np.roll(self.food, 1, 0)
            + np.roll(self.food, -1, 0)
            + np.roll(self.food, 1, 1)
            + np.roll(self.food, -1, 1)
        ) / 4
        self.food += 0.02 * (food_diffusion - self.food)

        if random.random() < 0.002:
            fx = random.randint(0, GRID_SIZE - 1)
            fy = random.randint(0, GRID_SIZE - 1)
            self.food[fx, fy] += 10.0

        if random.random() < 0.02:
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.food[x, y] += random.uniform(3, 8)

        np.clip(self.food, 0.0, 100.0, out=self.food)

        self.food_grid = self.food[np.ix_(self._world_to_food_idx, self._world_to_food_idx)]

        # Food releases chemical signal into the smell map.
        self.chem += self.food * 2.5

        # Diffuse chemical concentration to neighboring cells.
        new_chem = np.zeros_like(self.chem)
        new_chem[1:-1, 1:-1] = (
            self.chem[1:-1, 1:-1] * 0.7
            + (
                self.chem[2:, 1:-1]
                + self.chem[:-2, 1:-1]
                + self.chem[1:-1, 2:]
                + self.chem[1:-1, :-2]
            )
            * 0.075
        )
        self.chem = np.clip(new_chem, 0.0, 100.0)

        if random.random() < 0.001:
            max_val = max(max(row) for row in self.chem)
            print("chem max:", max_val)

        # Pheromone decays slowly over time.
        self.pheromone[1:-1, 1:-1] *= 0.97
        np.clip(self.pheromone, 0.0, 1000.0, out=self.pheromone)

    def get_food(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return self.food[gx % GRID_SIZE, gy % GRID_SIZE]

    def get_pheromone(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return self.pheromone[gx % GRID_SIZE, gy % GRID_SIZE]
