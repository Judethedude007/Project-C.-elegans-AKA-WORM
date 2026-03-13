import math
import random
import numpy as np
from brain import Brain
from config import (
    WORM_SEGMENTS,
    WORLD_SIZE,
    FOOD_ENERGY,
    WORM_SPEED,
    METABOLISM,
    PHEROMONE_DEPOSIT,
    REPRODUCTION_COST,
    SEGMENT_LENGTH,
    MUSCLE_GAIN,
    SEGMENT_DAMPING,
    SEGMENT_PROPAGATION,
)


class Worm:

    def __init__(self, x, y, connectome_setup, sex=None):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.time = 0.0

        self.energy = 100

        self.segment_angles = np.zeros(WORM_SEGMENTS, dtype=float)
        self.segment_velocity = np.zeros(WORM_SEGMENTS, dtype=float)

        self.brain = Brain(
            connectome_setup["connections"],
            connectome_setup["neuron_order"],
            connectome_setup["sensory_map"],
            connectome_setup["motor_map"],
        )
        self.sex = sex if sex else random.choice(["male", "hermaphrodite"])
        self.reproduction_cooldown = 0.0
        self.preferred_temperature = random.uniform(0.35, 0.65)

    def sense(self, world):

        smell_x = self.x + math.cos(self.angle) * 6
        smell_y = self.y + math.sin(self.angle) * 6
        food_smell = world.get_food(smell_x, smell_y)

        touch_x = self.x + math.cos(self.angle) * 3
        touch_y = self.y + math.sin(self.angle) * 3
        touch = 1.0 if world.is_obstacle(touch_x, touch_y) else 0.0

        temperature = world.get_temperature(self.x, self.y)
        pheromone = min(world.get_pheromone(self.x, self.y), 1.0)

        return {
            "food_smell": float(food_smell),
            "touch": float(touch),
            "temperature": float(temperature),
            "pheromone": float(pheromone),
        }

    def update(self, world, dt=1 / 60):

        if self.energy <= 0:
            return

        scale = dt * 60.0
        self.time += dt

        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown = max(0.0, self.reproduction_cooldown - dt)

        # Step 2: local food sensing for chemotaxis.
        ix = int(self.x) % WORLD_SIZE
        iy = int(self.y) % WORLD_SIZE

        left = world.food[(ix - 1) % WORLD_SIZE, iy]
        right = world.food[(ix + 1) % WORLD_SIZE, iy]

        up = world.food[ix, (iy - 1) % WORLD_SIZE]
        down = world.food[ix, (iy + 1) % WORLD_SIZE]

        turn = (right - left) * 0.5
        self.angle += turn

        # Step 6: larger attraction radius.
        food_gradient_x = world.food[(ix + 3) % WORLD_SIZE, iy] - world.food[(ix - 3) % WORLD_SIZE, iy]
        food_gradient_y = world.food[ix, (iy + 3) % WORLD_SIZE] - world.food[ix, (iy - 3) % WORLD_SIZE]
        self.angle += food_gradient_x * 0.2
        self.angle += food_gradient_y * 0.05

        # Step 8: pheromone following.
        pher = world.pheromone[ix, iy]
        self.angle += pher * 0.1

        # Step 4: very small randomness to prevent locking into circles.
        self.angle += random.uniform(-0.02, 0.02)

        curvature = (turn + food_gradient_x * 0.2 + food_gradient_y * 0.05 + pher * 0.1) * MUSCLE_GAIN

        self.segment_velocity[0] += curvature * 0.25 * scale
        self.segment_velocity[0] *= SEGMENT_DAMPING
        self.segment_angles[0] += self.segment_velocity[0] * dt

        for i in range(1, WORM_SEGMENTS):
            force = (self.segment_angles[i - 1] - self.segment_angles[i]) * SEGMENT_PROPAGATION
            self.segment_velocity[i] += force * scale
            self.segment_velocity[i] *= SEGMENT_DAMPING
            self.segment_angles[i] += self.segment_velocity[i] * dt

        self.segment_angles *= 0.995
        self.angle += self.segment_angles[0] * 0.6 * scale

        # Step 7: hungry worms search more aggressively.
        if self.energy < 50:
            speed = 2.0
        else:
            speed = 1.0

        # Step 3: forward exploration.
        base_speed = 1.5
        next_x = (self.x + math.cos(self.angle) * base_speed * speed * scale) % WORLD_SIZE
        next_y = (self.y + math.sin(self.angle) * base_speed * speed * scale) % WORLD_SIZE

        if world.is_obstacle(next_x, next_y):
            self.angle += random.uniform(-1.2, 1.2)
        else:
            self.x = next_x
            self.y = next_y

        cx = int(self.x) % WORLD_SIZE
        cy = int(self.y) % WORLD_SIZE

        # Step 5: eat food when reaching it.
        food = world.food[cx, cy]
        if food > 0.2:
            self.energy += food * 10
            world.food[cx, cy] *= 0.5

        # Step 8: leave pheromone trail.
        world.pheromone[cx, cy] += 0.01 * scale

        self.energy -= METABOLISM * scale

    def can_reproduce(self):
        return self.energy > (100 + REPRODUCTION_COST) and self.reproduction_cooldown <= 0

    def reproduce(self):
        self.energy -= REPRODUCTION_COST
        self.reproduction_cooldown = 5.0

    def body_points(self):

        points = [(self.x, self.y)]
        px = self.x
        py = self.y
        heading = self.angle

        for i in range(1, WORM_SEGMENTS):
            heading += self.segment_angles[i - 1]
            px -= SEGMENT_LENGTH * math.cos(heading)
            py -= SEGMENT_LENGTH * math.sin(heading)
            points.append((px, py))

        return points
