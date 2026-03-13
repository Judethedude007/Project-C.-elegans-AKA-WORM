import math
import random
import numpy as np
from brain import Brain
from config import (
    WORM_SEGMENTS,
    WORLD_SIZE,
    FOOD_ENERGY,
    BRAIN_NEURONS,
    TURN_SPEED,
    WORM_SPEED,
    METABOLISM,
    PHEROMONE_DEPOSIT,
    REPRODUCTION_COST,
)


class Worm:

    def __init__(self, x, y, sex=None):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.time = 0

        self.energy = 100

        self.brain = Brain(BRAIN_NEURONS)
        self.sex = sex if sex else random.choice(["male", "hermaphrodite"])
        self.reproduction_cooldown = 0

    def sense(self, world):

        smell_x = self.x + math.cos(self.angle) * 6
        smell_y = self.y + math.sin(self.angle) * 6
        food_smell = world.get_food(smell_x, smell_y)

        touch = 1.0 if food_smell > 0.95 else 0.0

        temperature = 0.5

        pheromone = min(world.get_pheromone(self.x, self.y), 1.0)

        return np.array([food_smell, touch, temperature, pheromone], dtype=float)

    def update(self, world):

        if self.energy <= 0:
            return

        self.time += 0.1

        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1

        inputs = np.zeros(self.brain.n, dtype=float)
        inputs[:4] = self.sense(world)
        spikes = self.brain.step(inputs)

        turn_left = bool(spikes[0])
        turn_right = bool(spikes[1])
        forward = bool(spikes[2])

        if turn_left and not turn_right:
            self.angle -= TURN_SPEED
        elif turn_right and not turn_left:
            self.angle += TURN_SPEED

        ix = int(self.x) % WORLD_SIZE
        iy = int(self.y) % WORLD_SIZE
        left = world.food[(ix - 1) % WORLD_SIZE, iy]
        right = world.food[(ix + 1) % WORLD_SIZE, iy]

        self.angle += (right - left) * 0.2
        self.angle += random.uniform(-0.1, 0.1)

        move_scale = 1.2 if forward else 0.6
        self.x = (self.x + math.cos(self.angle) * WORM_SPEED * move_scale) % WORLD_SIZE
        self.y = (self.y + math.sin(self.angle) * WORM_SPEED * move_scale) % WORLD_SIZE

        food = world.eat(int(self.x), int(self.y))
        self.energy += food * FOOD_ENERGY

        world.deposit_pheromone(int(self.x), int(self.y), PHEROMONE_DEPOSIT)

        self.energy -= METABOLISM

    def can_reproduce(self):
        return self.energy > (100 + REPRODUCTION_COST) and self.reproduction_cooldown == 0

    def reproduce(self):
        self.energy -= REPRODUCTION_COST
        self.reproduction_cooldown = 300

    def body_points(self):

        points = []

        for i in range(WORM_SEGMENTS):

            dx = i * 4

            dy = math.sin(self.time * 2 + i * 0.7) * 5

            px = self.x - dx * math.cos(self.angle)
            py = self.y - dx * math.sin(self.angle) + dy

            points.append((px, py))

        return points
