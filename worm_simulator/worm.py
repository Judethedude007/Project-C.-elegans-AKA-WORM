import math
import random
from brain import Brain
from config import WORLD_SIZE
from world import GRID_SIZE

METABOLISM = 0.3
MOVE_COST = 0.2
AGE_LIMIT = 5000
REPRODUCTION_COST = 2000
SEGMENTS = 24
SEGMENT_LENGTH = 4
STIFFNESS = 0.25
DAMPING = 0.85
MAX_STRETCH = SEGMENT_LENGTH * 2.0
SENSOR_DISTANCE = 6


def sample_chem(env, x, y):
    gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
    gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)

    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
        return float(env.chem[gx][gy])

    return 0.0


class Worm:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.angular_velocity = 0.0
        self.time = 0.0
        self.wave_phase = 0.0
        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)

        self.energy = 200
        self.age = 0
        self.dead = False
        self.trail = []
        self.segments = SEGMENTS
        self.body = [(self.x, self.y) for _ in range(self.segments)]
        self.vel = [(0.0, 0.0) for _ in range(self.segments)]

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

        self.time += dt

        left, right, up, down = self.sense_food(world)

        food_x = right - left
        food_y = down - up

        left_sensor = (
            self.x + math.cos(self.angle + 0.4) * SENSOR_DISTANCE,
            self.y + math.sin(self.angle + 0.4) * SENSOR_DISTANCE,
        )
        right_sensor = (
            self.x + math.cos(self.angle - 0.4) * SENSOR_DISTANCE,
            self.y + math.sin(self.angle - 0.4) * SENSOR_DISTANCE,
        )

        left_val = sample_chem(world, *left_sensor)
        right_val = sample_chem(world, *right_sensor)

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

        turn_strength = 0.05
        self.angle += (right_val - left_val) * turn_strength

        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)

        self.energy -= METABOLISM
        self.energy -= abs(self.angular_velocity) * MOVE_COST
        self.age += dt

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
        self.vel[0] = (0.0, 0.0)

        for i in range(1, SEGMENTS):

            px, py = self.body[i - 1]
            cx, cy = self.body[i]

            dx = cx - px
            dy = cy - py

            dist = math.sqrt(dx * dx + dy * dy)

            if dist == 0:
                continue

            # Clamp maximum stretch to prevent runaway segment explosions.
            if dist > MAX_STRETCH:
                cx = px + dx / dist * MAX_STRETCH
                cy = py + dy / dist * MAX_STRETCH
                dx = cx - px
                dy = cy - py
                dist = MAX_STRETCH

            diff = (dist - SEGMENT_LENGTH) / dist

            cx -= dx * diff * STIFFNESS
            cy -= dy * diff * STIFFNESS

            vx, vy = self.vel[i]
            vx *= DAMPING
            vy *= DAMPING

            cx += vx
            cy += vy

            self.body[i] = (cx, cy)
            self.vel[i] = (vx, vy)

        self.wave_phase += dt * 4
        for i in range(self.segments):
            x, y = self.body[i]
            wave = math.sin(self.wave_phase - i * 0.5)
            offset = wave * 2
            self.body[i] = (
                x + offset * self.direction_y,
                y - offset * self.direction_x,
            )

        self.body[0] = (self.x, self.y)

        hx, hy = self.body[0]
        if (not math.isfinite(hx)) or (not math.isfinite(hy)):
            self.body[0] = (self.x, self.y)
            self.vel[0] = (0.0, 0.0)
        elif abs(hx) > WORLD_SIZE * 2 or abs(hy) > WORLD_SIZE * 2:
            self.body[0] = (self.x, self.y)
            self.vel[0] = (0.0, 0.0)

        for i, (bx, by) in enumerate(self.body[1:], start=1):

            if (not math.isfinite(bx)) or (not math.isfinite(by)):
                self.body[i] = self.body[i - 1]
                self.vel[i] = (0.0, 0.0)
                continue

            if abs(bx) > WORLD_SIZE * 2 or abs(by) > WORLD_SIZE * 2:
                self.body[i] = self.body[i - 1]
                self.vel[i] = (0.0, 0.0)

        x = int(self.x) % WORLD_SIZE
        y = int(self.y) % WORLD_SIZE

        food = world.food[x, y]

        if food > 0.2:

            eat = min(food, 0.3)

            world.food[x, y] -= eat

            self.energy += eat * 40

        gx = int((self.x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((self.y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            world.pheromone[gx, gy] += 0.5

        if self.energy > REPRODUCTION_COST and random.random() < 0.002:
            self.energy *= 0.5
            baby = Worm(
                (self.x + random.uniform(-5, 5)) % WORLD_SIZE,
                (self.y + random.uniform(-5, 5)) % WORLD_SIZE,
            )
            baby.energy = self.energy
            return baby

        if self.energy <= 0:
            self.dead = True

        if self.age > AGE_LIMIT:
            self.dead = True

        return None

    def smooth_body(self):

        smooth_points = []

        for i in range(len(self.body) - 1):
            x1, y1 = self.body[i]
            x2, y2 = self.body[i + 1]

            if abs(x1 - x2) > 50 or abs(y1 - y2) > 50:
                continue

            smooth_points.append((x1, y1))
            smooth_points.append(((x1 + x2) / 2, (y1 + y2) / 2))

        if self.body:
            smooth_points.append(self.body[-1])

        return smooth_points

    def body_points(self):
        return self.smooth_body()
