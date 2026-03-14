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
BASE_SEGMENT_LENGTH = 5
SEGMENT_LENGTH = BASE_SEGMENT_LENGTH
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
        self.neural_phase = 0.0
        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 1.5
        self.syn_left = 0.5
        self.syn_right = 0.5
        self.size = 0.4
        self.behavior = "roam"

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
        self.age = 0.0
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
        self.neural_phase += dt * 3.0
        growth_rate = 0.05
        self.size += growth_rate * dt
        self.size = min(self.size, 1.0)
        segment_length = BASE_SEGMENT_LENGTH * self.size

        left, right, up, down = self.sense_food(world)

        food_x = right - left
        food_y = down - up

        sensor_distance = self.genes["sensor_range"]
        left_sensor_pos = (
            self.x + math.cos(self.angle + 0.5) * sensor_distance,
            self.y + math.sin(self.angle + 0.5) * sensor_distance,
        )
        right_sensor_pos = (
            self.x + math.cos(self.angle - 0.5) * sensor_distance,
            self.y + math.sin(self.angle - 0.5) * sensor_distance,
        )

        left_sensor = sample_chem(world, *left_sensor_pos)
        right_sensor = sample_chem(world, *right_sensor_pos)
        left_sensor *= 1.5
        right_sensor *= 1.5

        eating = False
        feed_gx = int(self.x / WORLD_SIZE * GRID_SIZE)
        feed_gy = int(self.y / WORLD_SIZE * GRID_SIZE)
        food_here = 0.0
        if 0 <= feed_gx < GRID_SIZE and 0 <= feed_gy < GRID_SIZE:
            food_here = float(world.food[feed_gx, feed_gy])

        if food_here > 0.8:
            eating = True

        food_signal = food_here

        if food_signal > 1.2:
            self.behavior = "dwell"
        elif food_signal < 0.3:
            self.behavior = "roam"

        inputs = [food_x, food_y, 0, 0, 0, 0, 0, 0, 0, 0]

        for i in range(len(inputs)):
            inputs[i] += random.uniform(-0.002, 0.002)

        brain_output = self.brain.step(inputs)

        if brain_output[5]:
            self.angle -= 0.05

        if brain_output[6]:
            self.angle += 0.05

        curvature = brain_output[5] - brain_output[6]
        self.angle += curvature * 0.05

        self.angular_velocity += curvature
        self.angular_velocity *= 0.85

        self.angle += self.angular_velocity * dt * 60

        delta = (right_sensor - left_sensor) * 0.0002

        self.syn_left += delta
        self.syn_right -= delta

        self.syn_left = max(0.0, min(1.0, self.syn_left))
        self.syn_right = max(0.0, min(1.0, self.syn_right))

        turn = (
            right_sensor * self.syn_right
            - left_sensor * self.syn_left
        ) * 0.06
        MAX_TURN = 0.06
        turn = max(-MAX_TURN, min(MAX_TURN, turn))
        self.angle += turn * dt * 60

        self.angle += random.uniform(-0.02, 0.02)

        margin = 40
        if self.x < margin:
            self.angle += 0.05
        if self.x > WORLD_SIZE - margin:
            self.angle -= 0.05
        if self.y < margin:
            self.angle += 0.05
        if self.y > WORLD_SIZE - margin:
            self.angle -= 0.05

        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)

        self.energy -= self.genes["metabolism"] * dt * 0.7
        self.age += dt * 0.5

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

            diff = (dist - segment_length) / dist

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

        for i in range(SEGMENTS):

            phase = self.neural_phase - i * 0.45

            activation = math.sin(phase)

            self.muscle_left[i] = max(0.0, activation)
            self.muscle_right[i] = max(0.0, -activation)

        wave_strength = 0

        for i in range(SEGMENTS):
            wave_strength += abs(self.muscle_left[i] - self.muscle_right[i])

        wave_strength /= SEGMENTS

        speed = self.genes["speed"] * 1.4

        if eating:
            speed *= 0.65

        if self.behavior == "dwell":
            speed *= 0.6
        else:
            speed *= 1.0

        forward_speed = speed * dt * 30

        max_step = 2.0

        dx = math.cos(self.angle) * forward_speed
        dy = math.sin(self.angle) * forward_speed

        step = math.sqrt(dx * dx + dy * dy)

        if step > max_step:
            scale = max_step / step
            dx *= scale
            dy *= scale

        self.x += dx
        self.y += dy

        self.x = max(0, min(WORLD_SIZE, self.x))
        self.y = max(0, min(WORLD_SIZE, self.y))

        gx = int(self.x / WORLD_SIZE * GRID_SIZE)
        gy = int(self.y / WORLD_SIZE * GRID_SIZE)

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:

            if world.food[gx, gy] > 0:

                eaten = min(5, world.food[gx, gy])

                world.food[gx, gy] -= eaten
                self.energy += eaten * 5
                eating = True

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

            x -= math.cos(segment_angle) * segment_length
            y -= math.sin(segment_angle) * segment_length
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

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            world.pheromone[gx, gy] += 0.08

        if self.energy > 100 and self.size > 0.75:
            baby = Worm(
                self.x + random.uniform(-5, 5),
                self.y + random.uniform(-5, 5),
            )
            if new_worms is not None:
                new_worms.append(baby)
            else:
                return True
            self.energy *= 0.5

        self.energy = max(0.0, self.energy)

        if self.energy <= 0:
            self.dead = True
            return False

        MAX_AGE = 500
        if self.age > MAX_AGE:
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
