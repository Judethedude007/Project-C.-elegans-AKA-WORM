import numpy as np
from config import GRID_SIZE, MAX_FOOD

class Environment:

    def __init__(self):
        self.food = np.random.rand(GRID_SIZE, GRID_SIZE) * MAX_FOOD
        self.barrier = np.zeros((GRID_SIZE, GRID_SIZE))

    def get_food(self, x, y):
        return self.food[x % GRID_SIZE, y % GRID_SIZE]

    def eat_food(self, x, y, amount):
        self.food[x % GRID_SIZE, y % GRID_SIZE] -= amount
        if self.food[x % GRID_SIZE, y % GRID_SIZE] < 0:
            self.food[x % GRID_SIZE, y % GRID_SIZE] = 0
