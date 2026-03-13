import numpy as np
from config import (
    WORLD_SIZE,
    FOOD_GROWTH,
    FOOD_SPREAD_CENTER,
    FOOD_SPREAD_NEIGHBOR,
    PHEROMONE_DIFFUSION,
    PHEROMONE_DECAY,
    OBSTACLE_DENSITY,
)


class World:

    def __init__(self):

        seed = (np.random.rand(WORLD_SIZE, WORLD_SIZE).astype(np.float32) ** 8) * 3.0
        self.food = np.clip(
            (
                seed
                + np.roll(seed, 1, axis=0)
                + np.roll(seed, -1, axis=0)
                + np.roll(seed, 1, axis=1)
                + np.roll(seed, -1, axis=1)
            )
            / 2.5,
            0,
            1,
        )
        self.pheromone = np.zeros((WORLD_SIZE, WORLD_SIZE), dtype=np.float32)

        gx = np.linspace(0, 2 * np.pi, WORLD_SIZE, dtype=np.float32)
        gy = np.linspace(0, 2 * np.pi, WORLD_SIZE, dtype=np.float32)
        xx, yy = np.meshgrid(gx, gy, indexing="ij")
        self.temperature = np.clip(
            0.5 + 0.25 * np.sin(xx * 0.7) + 0.25 * np.cos(yy * 1.1),
            0,
            1,
        ).astype(np.float32)

        obstacle_seed = (np.random.rand(WORLD_SIZE, WORLD_SIZE) < OBSTACLE_DENSITY).astype(np.float32)
        obstacle_smear = (
            obstacle_seed
            + np.roll(obstacle_seed, 1, axis=0)
            + np.roll(obstacle_seed, -1, axis=0)
            + np.roll(obstacle_seed, 1, axis=1)
            + np.roll(obstacle_seed, -1, axis=1)
        )
        self.obstacles = obstacle_smear > 1.5
        self.food[self.obstacles] = 0

    def update(self, dt):

        scale = dt * 60.0

        previous_food = self.food.copy()

        self.food += FOOD_GROWTH * scale
        self.food += previous_food * FOOD_SPREAD_CENTER * scale
        self.food += np.roll(previous_food, 1, axis=0) * FOOD_SPREAD_NEIGHBOR * scale
        self.food += np.roll(previous_food, -1, axis=0) * FOOD_SPREAD_NEIGHBOR * scale
        self.food += np.roll(previous_food, 1, axis=1) * FOOD_SPREAD_NEIGHBOR * scale
        self.food += np.roll(previous_food, -1, axis=1) * FOOD_SPREAD_NEIGHBOR * scale
        self.food = np.clip(self.food, 0, 1)
        self.food[self.obstacles] = 0

        # Diffuse and decay pheromone to form trails that fade over time.
        neighbors = (
            np.roll(self.pheromone, 1, axis=0)
            + np.roll(self.pheromone, -1, axis=0)
            + np.roll(self.pheromone, 1, axis=1)
            + np.roll(self.pheromone, -1, axis=1)
        ) / 4.0
        diffusion = min(1.0, PHEROMONE_DIFFUSION * scale)
        self.pheromone = (1 - diffusion) * self.pheromone + diffusion * neighbors
        self.pheromone *= PHEROMONE_DECAY ** scale
        self.pheromone[self.obstacles] = 0

    def eat(self, x, y):

        ix = int(x) % WORLD_SIZE
        iy = int(y) % WORLD_SIZE

        if self.obstacles[ix, iy]:
            return 0.0

        food = self.food[ix, iy]
        self.food[ix, iy] = 0
        return food

    def get_food(self, x, y):
        ix = int(x) % WORLD_SIZE
        iy = int(y) % WORLD_SIZE
        if self.obstacles[ix, iy]:
            return 0.0
        return self.food[ix, iy]

    def deposit_pheromone(self, x, y, amount):
        ix = int(x) % WORLD_SIZE
        iy = int(y) % WORLD_SIZE
        if self.obstacles[ix, iy]:
            return
        self.pheromone[ix, iy] += amount

    def get_pheromone(self, x, y):
        return self.pheromone[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE]

    def get_temperature(self, x, y):
        return self.temperature[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE]

    def is_obstacle(self, x, y):
        return bool(self.obstacles[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE])
