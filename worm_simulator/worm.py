import math
import random
from brain import Brain
from config import WORM_SEGMENTS, WORLD_SIZE


class Worm:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.angular_velocity = 0.0

        self.energy = 200
        self.age = 0
        self.dead = False

        self.brain = Brain()

    def sense_food(self, world):

        x = int(self.x) % WORLD_SIZE
        y = int(self.y) % WORLD_SIZE

        left = world.food[(x - 3) % WORLD_SIZE, y]
        right = world.food[(x + 3) % WORLD_SIZE, y]
        up = world.food[x, (y - 3) % WORLD_SIZE]
        down = world.food[x, (y + 3) % WORLD_SIZE]

        return left, right, up, down

    def update(self, world, dt=1 / 60):

        if self.dead:
            return

        self.energy -= 0.02
        self.age += dt

        left, right, up, down = self.sense_food(world)

        food_x = right - left
        food_y = down - up

        inputs = [food_x, food_y, 0, 0, 0, 0, 0, 0, 0, 0]

        for i in range(len(inputs)):
            inputs[i] += random.uniform(-0.02, 0.02)

        brain_output = self.brain.step(inputs)

        if brain_output[5]:
            self.angle -= 0.2

        if brain_output[6]:
            self.angle += 0.2

        curvature = brain_output[5] - brain_output[6]
        self.angle += curvature * 0.05

        self.angular_velocity += curvature
        self.angular_velocity *= 0.9

        self.angle += self.angular_velocity

        speed = 1.5
        self.x = (self.x + math.cos(self.angle) * speed) % WORLD_SIZE
        self.y = (self.y + math.sin(self.angle) * speed) % WORLD_SIZE

        x = int(self.x) % WORLD_SIZE
        y = int(self.y) % WORLD_SIZE

        food = world.food[x, y]

        if food > 0.2:

            eat = min(food, 0.3)

            world.food[x, y] -= eat

            self.energy += eat * 40

        if self.energy <= 0:
            self.dead = True

        if self.age > 1500:
            self.dead = True

    def body_points(self):

        points = []

        for i in range(WORM_SEGMENTS):
            dx = i * 3
            dy = math.sin(i * 0.5 + self.angle * 2) * 2
            px = self.x - dx * math.cos(self.angle)
            py = self.y - dx * math.sin(self.angle) + dy
            points.append((px, py))

        return points
