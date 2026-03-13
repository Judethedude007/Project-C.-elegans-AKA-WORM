import math
import random
from brain import Brain
from config import WORLD_SIZE


class Worm:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.angular_velocity = 0.0
        self.time = 0.0

        self.energy = 200
        self.age = 0
        self.dead = False
        self.trail = []
        self.segments = 20
        self.body = [(self.x, self.y) for _ in range(self.segments)]

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
            return None

        self.energy -= 0.02
        self.age += dt
        self.time += dt

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

        dx = self.x - self.trail[-1][0] if self.trail else 0
        dy = self.y - self.trail[-1][1] if self.trail else 0

        if dx * dx + dy * dy > 100:
            self.trail.clear()

        self.trail.append((self.x, self.y))
        if len(self.trail) > 100:
            self.trail.pop(0)

        self.body[0] = (self.x, self.y)

        for i in range(1, self.segments):

            px, py = self.body[i - 1]
            cx, cy = self.body[i]

            dx = px - cx
            dy = py - cy

            dist = (dx * dx + dy * dy) ** 0.5

            target = 4

            if dist > 0:
                cx += dx / dist * (dist - target)
                cy += dy / dist * (dist - target)

            self.body[i] = (cx, cy)

        x = int(self.x) % WORLD_SIZE
        y = int(self.y) % WORLD_SIZE

        food = world.food[x, y]

        if food > 0.2:

            eat = min(food, 0.3)

            world.food[x, y] -= eat

            self.energy += eat * 40

        world.pheromone[x, y] += 1

        if self.energy > 4000:
            self.energy *= 0.5
            baby = Worm(
                (self.x + random.uniform(-5, 5)) % WORLD_SIZE,
                (self.y + random.uniform(-5, 5)) % WORLD_SIZE,
            )
            baby.energy = self.energy
            return baby

        if self.energy <= 0:
            self.dead = True

        if self.age > 1500:
            self.dead = True

        return None

    def body_points(self):

        smooth_points = []

        for i in range(len(self.body) - 1):
            x1, y1 = self.body[i]
            x2, y2 = self.body[i + 1]

            smooth_points.append((x1, y1))
            smooth_points.append(((x1 + x2) / 2, (y1 + y2) / 2))

        if self.body:
            smooth_points.append(self.body[-1])

        return smooth_points
