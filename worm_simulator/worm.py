import math
import random
from brain import Brain
from config import WORLD_SIZE
from world import GRID_SIZE

METABOLISM = 0.3
MOVE_COST = 0.2
AGE_LIMIT = 5000
REPRODUCTION_COST = 2000
SEGMENTS = 16
SEGMENT_LENGTH = 5
STIFFNESS = 0.25
DAMPING = 0.85
MAX_STRETCH = SEGMENT_LENGTH * 2.0
SENSOR_DISTANCE = 25


def sample_chem(env, x, y):
    gx = int(x / WORLD_SIZE * GRID_SIZE)
    gy = int(y / WORLD_SIZE * GRID_SIZE)

    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
        return float(env.chem[gx][gy])

    return 0.0


class Worm:

    def __init__(self, x, y, genes=None):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.angular_velocity = 0.0
        self.time = 0.0
        self.wave_phase = 0.0
        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 1.5

        if genes is None:
            genes = {
                "speed": 1.0,
                "sensor_range": float(SENSOR_DISTANCE),
                "turn_sensitivity": 0.25,
                "metabolism": 0.01,
            }

        self.genes = {
            "speed": float(genes.get("speed", 1.0)),
            "sensor_range": float(genes.get("sensor_range", SENSOR_DISTANCE)),
            "turn_sensitivity": float(genes.get("turn_sensitivity", 0.25)),
            "metabolism": float(genes.get("metabolism", 0.01)),
        }

        self.energy = 100
        self.age = 0
        self.dead = False
        self.trail = []
        self.segments = SEGMENTS
        self.body = [(self.x, self.y) for _ in range(self.segments)]
        self.vel = [(0.0, 0.0) for _ in range(self.segments)]
        self.muscle_left = [0.0] * SEGMENTS
        self.muscle_right = [0.0] * SEGMENTS

        self.brain = Brain()

    def sense_food(self, world):

        x = int(self.x) % WORLD_SIZE
        y = int(self.y) % WORLD_SIZE

        left = world.food_grid[(x - 3) % WORLD_SIZE, y]
        right = world.food_grid[(x + 3) % WORLD_SIZE, y]
        up = world.food_grid[x, (y - 3) % WORLD_SIZE]
        down = world.food_grid[x, (y + 3) % WORLD_SIZE]

        return left, right, up, down

    def update(self, world, dt=1 / 60, new_worms=None):

        if self.dead:
            return False

        self.time += dt

        left, right, up, down = self.sense_food(world)

        food_x = right - left
        food_y = down - up

        sensor_distance = self.genes["sensor_range"]
        left_sensor = (
            self.x + math.cos(self.angle + 0.5) * sensor_distance,
            self.y + math.sin(self.angle + 0.5) * sensor_distance,
        )
        right_sensor = (
            self.x + math.cos(self.angle - 0.5) * sensor_distance,
            self.y + math.sin(self.angle - 0.5) * sensor_distance,
        )

        left_val = sample_chem(world, *left_sensor)
        right_val = sample_chem(world, *right_sensor)

        eating = False
        feed_gx = int(self.x / WORLD_SIZE * GRID_SIZE)
        feed_gy = int(self.y / WORLD_SIZE * GRID_SIZE)
        food_here = 0.0
        if 0 <= feed_gx < GRID_SIZE and 0 <= feed_gy < GRID_SIZE:
            food_here = float(world.food[feed_gx, feed_gy])

        if food_here > 0:
            eating = True

        inputs = [food_x, food_y, 0, 0, 0, 0, 0, 0, 0, 0]

        for i in range(len(inputs)):
            inputs[i] += random.uniform(-0.002, 0.002)

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

        turn_strength = self.genes["turn_sensitivity"]
        diff = (right_val - left_val) / 100.0
        turn_signal = diff * turn_strength
        turn_signal = max(-0.15, min(0.15, turn_signal))
        if eating:
            self.angle += turn_signal * 0.1
        else:
            self.angle += turn_signal

        self.angle += random.uniform(-0.02, 0.02)

        margin = 40
        if self.x < margin:
            self.angle = 0
        if self.x > WORLD_SIZE - margin:
            self.angle = math.pi
        if self.y < margin:
            self.angle = math.pi / 2
        if self.y > WORLD_SIZE - margin:
            self.angle = -math.pi / 2

        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)

        self.energy -= self.genes["metabolism"] * dt
        self.age += dt

        self.body[0] = (self.x, self.y)
        self.vel[0] = (0.0, 0.0)

        for i in range(2, SEGMENTS):

            px, py = self.body[i - 1]
            cx, cy = self.body[i]

            dx = cx - px
            dy = cy - py

            dist = math.sqrt(dx * dx + dy * dy)

            if dist == 0:
                continue

            diff = (dist - SEGMENT_LENGTH) / dist

            offset_x = dx * diff * 0.5
            offset_y = dy * diff * 0.5

            px += offset_x
            py += offset_y

            cx -= offset_x
            cy -= offset_y

            px = max(0.0, min(WORLD_SIZE, px))
            py = max(0.0, min(WORLD_SIZE, py))
            cx = max(0.0, min(WORLD_SIZE, cx))
            cy = max(0.0, min(WORLD_SIZE, cy))

            self.body[i - 1] = (px, py)
            self.body[i] = (cx, cy)

        phase = self.time * 4
        for i in range(SEGMENTS):

            activation = math.sin(phase - i * 0.5)

            self.muscle_left[i] = max(0, activation)
            self.muscle_right[i] = max(0, -activation)

        wave_strength = 0

        for i in range(SEGMENTS):
            wave_strength += abs(self.muscle_left[i] - self.muscle_right[i])

        wave_strength /= SEGMENTS

        speed = self.genes["speed"] * 1.4

        if eating:
            speed *= 0.2

        forward = speed * (0.5 + wave_strength)

        self.x += math.cos(self.angle) * forward * dt
        self.y += math.sin(self.angle) * forward * dt

        self.x = max(0.0, min(self.x, WORLD_SIZE - 1e-6))
        self.y = max(0.0, min(self.y, WORLD_SIZE - 1e-6))

        dx = self.x - self.trail[-1][0] if self.trail else 0
        dy = self.y - self.trail[-1][1] if self.trail else 0

        if dx * dx + dy * dy > 100:
            self.trail.clear()

        self.trail.append((self.x, self.y))
        if len(self.trail) > 100:
            self.trail.pop(0)

        base_angle = self.angle
        x, y = self.x, self.y

        self.body[0] = (self.x, self.y)

        for i in range(1, SEGMENTS):
            bend = max(-1, min(1, self.muscle_left[i] - self.muscle_right[i]))
            segment_angle = base_angle + bend * 0.25

            x -= math.cos(segment_angle) * SEGMENT_LENGTH
            y -= math.sin(segment_angle) * SEGMENT_LENGTH
            self.body[i] = (
                x,
                y,
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

        gx = int(self.x / WORLD_SIZE * GRID_SIZE)
        gy = int(self.y / WORLD_SIZE * GRID_SIZE)

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE and world.food[gx, gy] > 0:

            eaten = min(world.food[gx, gy], 0.5)

            world.food[gx, gy] -= eaten

            self.energy += eaten * 20
            eating = True

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            world.pheromone[gx, gy] += 0.5

        if self.energy > 160:
            self.energy *= 0.5

            child_genes = {
                "speed": max(0.5, min(2.5, self.genes["speed"] + random.uniform(-0.05, 0.05))),
                "sensor_range": max(8.0, min(40.0, self.genes["sensor_range"] + random.uniform(-1.0, 1.0))),
                "turn_sensitivity": max(
                    0.05,
                    min(0.6, self.genes["turn_sensitivity"] + random.uniform(-0.03, 0.03)),
                ),
                "metabolism": max(0.002, min(0.05, self.genes["metabolism"] + random.uniform(-0.001, 0.001))),
            }

            baby = Worm(
                (self.x + random.uniform(-5, 5)) % WORLD_SIZE,
                (self.y + random.uniform(-5, 5)) % WORLD_SIZE,
                genes=child_genes,
            )
            if new_worms is not None:
                new_worms.append(baby)
            else:
                return True

        self.energy = max(0.0, self.energy)

        if self.energy <= 0:
            self.dead = True
            return False

        if self.age > AGE_LIMIT:
            self.dead = True
            return False

        return True

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
