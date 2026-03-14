import random
import numpy as np
from config import WORLD_SIZE

GRID_SIZE = 128


class World:

    def __init__(self):
        self.width = WORLD_SIZE
        self.height = WORLD_SIZE
        self.worm_positions = []
        self.food_patches = []

        self.food = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.food_capacity = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.food_grid = np.zeros((WORLD_SIZE, WORLD_SIZE), dtype=np.float32)
        self.pheromone = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.chem = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.medium = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.oxygen = np.ones((GRID_SIZE, GRID_SIZE), dtype=np.float32)

        self._world_to_food_idx = np.linspace(0, GRID_SIZE - 1, WORLD_SIZE).astype(np.int32)

        for _ in range(6):
            cx = random.uniform(100.0, WORLD_SIZE - 100.0)
            cy = random.uniform(100.0, WORLD_SIZE - 100.0)
            self._add_food_gaussian(cx, cy, 120, 80)
            self.food_patches.append({"x": cx, "y": cy})

        np.clip(self.food, 0.0, 1.0, out=self.food)
        self.food_capacity[:] = self.food
        self.oxygen = 1.0 - (self.food * 0.3)

        for _ in range(5):
            gx = random.randint(0, GRID_SIZE - 1)
            gy = random.randint(0, GRID_SIZE - 1)
            self._add_medium_patch(gx, gy, radius=8, value=1.0)

    def _add_food_gaussian(self, cx_world, cy_world, std=40, n=3000):
        xs = np.random.normal(cx_world, std, n).astype(int)
        ys = np.random.normal(cy_world, std, n).astype(int)
        mask = (xs >= 0) & (xs < WORLD_SIZE) & (ys >= 0) & (ys < WORLD_SIZE)
        gxs = (xs[mask] * GRID_SIZE // WORLD_SIZE).clip(0, GRID_SIZE - 1)
        gys = (ys[mask] * GRID_SIZE // WORLD_SIZE).clip(0, GRID_SIZE - 1)
        np.add.at(self.food, (gxs, gys), 1)

    def _add_food_cluster(self, cx, cy, radius=10, amount=2.0):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                gx = (cx + dx) % GRID_SIZE
                gy = (cy + dy) % GRID_SIZE
                self.food[gx, gy] += amount

    def _add_medium_patch(self, cx, cy, radius=8, value=1.0):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                gx = (cx + dx) % GRID_SIZE
                gy = (cy + dy) % GRID_SIZE
                self.medium[gx, gy] = value

    def update(self, dt=1 / 60):
        time_scale = max(dt * 60.0, 0.0)

        # Food exists as a consumable resource grid that slowly spreads and respawns.
        food_diffusion = (
            np.roll(self.food, 1, 0)
            + np.roll(self.food, -1, 0)
            + np.roll(self.food, 1, 1)
            + np.roll(self.food, -1, 1)
        ) / 4
        self.food += 0.02 * (food_diffusion - self.food) * time_scale
        self.food *= 0.999 ** time_scale
        self.food += 0.0075 * self.food_capacity * time_scale
        np.clip(self.food, 0.0, 1.0, out=self.food)
        self.oxygen = 1.0 - (self.food * 0.3)
        np.clip(self.oxygen, 0.0, 1.0, out=self.oxygen)

        self.food_grid = self.food[np.ix_(self._world_to_food_idx, self._world_to_food_idx)]

        # Food releases chemical signal into the smell map.
        self.chem += self.food * 2.5 * time_scale

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
        self.pheromone *= 0.995 ** time_scale
        np.clip(self.pheromone, 0.0, 1000.0, out=self.pheromone)

    def get_food(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return self.food[gx % GRID_SIZE, gy % GRID_SIZE]

    def sample_food(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return float(self.food[gx % GRID_SIZE, gy % GRID_SIZE])

    def sample_pheromone(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return float(self.pheromone[gx % GRID_SIZE, gy % GRID_SIZE])

    def sample_medium(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return float(self.medium[gx % GRID_SIZE, gy % GRID_SIZE])

    def get_pheromone(self, x, y):
        return self.sample_pheromone(x, y)

    def set_worm_positions(self, worms):
        self.worm_positions = [(float(w.x), float(w.y)) for w in worms if not getattr(w, "dead", False)]

    def count_worms_near(self, x, y, radius=20):
        radius_sq = float(radius) * float(radius)
        count = 0
        for wx, wy in self.worm_positions:
            dx = wx - x
            dy = wy - y
            if dx * dx + dy * dy <= radius_sq:
                count += 1
        return count
