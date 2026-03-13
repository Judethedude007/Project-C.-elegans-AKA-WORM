import numpy as np
from config import WORLD_SIZE, FOOD_GROWTH, PHEROMONE_DIFFUSION, PHEROMONE_DECAY


class World:

    def __init__(self):

        self.food = np.random.rand(WORLD_SIZE, WORLD_SIZE)
        self.pheromone = np.zeros((WORLD_SIZE, WORLD_SIZE))

    def update(self):

        self.food += FOOD_GROWTH
        self.food = np.clip(self.food, 0, 1)

        # Diffuse and decay pheromone to form trails that fade over time.
        neighbors = (
            np.roll(self.pheromone, 1, axis=0)
            + np.roll(self.pheromone, -1, axis=0)
            + np.roll(self.pheromone, 1, axis=1)
            + np.roll(self.pheromone, -1, axis=1)
        ) / 4.0
        self.pheromone = (1 - PHEROMONE_DIFFUSION) * self.pheromone + PHEROMONE_DIFFUSION * neighbors
        self.pheromone *= PHEROMONE_DECAY

    def eat(self, x, y):

        ix = int(x) % WORLD_SIZE
        iy = int(y) % WORLD_SIZE

        food = self.food[ix, iy]
        self.food[ix, iy] = 0
        return food

    def get_food(self, x, y):
        return self.food[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE]

    def deposit_pheromone(self, x, y, amount):
        ix = int(x) % WORLD_SIZE
        iy = int(y) % WORLD_SIZE
        self.pheromone[ix, iy] += amount

    def get_pheromone(self, x, y):
        return self.pheromone[int(x) % WORLD_SIZE, int(y) % WORLD_SIZE]
