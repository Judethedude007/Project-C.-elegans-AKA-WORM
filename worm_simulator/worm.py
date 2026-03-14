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


class Egg:

    def __init__(self, x, y, inherited_expression=None, inherited_genes=None):
        self.x = x % WORLD_SIZE
        self.y = y % WORLD_SIZE
        self.timer = random.uniform(20.0, 40.0)
        if inherited_expression is None:
            inherited_expression = {
                "foraging": 1.0,
                "stress": 0.0,
                "liquid": 0.0,
            }
        self.inherited_expression = dict(inherited_expression)
        if inherited_genes is None:
            inherited_genes = {}
        self.inherited_genes = dict(inherited_genes)

    def update(self, dt):
        self.timer -= dt
        return self.timer <= 0.0


class Worm:

    def __init__(self, x, y, genes=None, inherited_expression=None, inherited_genes=None):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.angular_velocity = random.uniform(-0.1, 0.1)
        self.time = 0.0
        self.wave_phase = 0.0
        self.neural_phase = 0.0
        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)
        self.direction = 1
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 40.0
        self.syn_left = 0.5
        self.syn_right = 0.5
        self.size = 0.3
        self.behavior = "roam"
        self.stage = "L1"
        self.locomotion_mode = "crawl"
        self.prev_food_signal = 0.0
        self.repro_timer = 0.0
        self.run_timer = random.uniform(2.0, 6.0)
        self.dauer = False
        self.neuron_aiy = 0.0
        self.neuron_aiz = 0.0
        self.neuron_avb = 0.0
        self.neuron_ava = 0.0
        self.syn_food = random.uniform(0.3, 0.7)
        self.syn_pheromone = random.uniform(0.3, 0.7)

        if inherited_genes is None:
            inherited_genes = {}

        # Evolution genes
        self.gene_speed = float(inherited_genes.get("gene_speed", random.uniform(0.8, 1.2)))
        self.gene_turn_bias = float(inherited_genes.get("gene_turn_bias", random.uniform(0.8, 1.2)))
        self.gene_food_weight = float(inherited_genes.get("gene_food_weight", random.uniform(0.8, 1.2)))
        self.gene_pheromone_weight = float(
            inherited_genes.get("gene_pheromone_weight", random.uniform(0.8, 1.2))
        )
        self.gene_reproduction_energy = float(
            inherited_genes.get("gene_reproduction_energy", random.uniform(180.0, 220.0))
        )

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

        default_expression = {
            "foraging": 1.0,
            "stress": 0.0,
            "liquid": 0.0,
        }
        if inherited_expression is None:
            self.gene_expression = default_expression
        else:
            self.gene_expression = {
                "foraging": float(inherited_expression.get("foraging", 1.0)),
                "stress": float(inherited_expression.get("stress", 0.0)),
                "liquid": float(inherited_expression.get("liquid", 0.0)),
            }

        self.brain = Brain()

    def sense_food(self, world):

        x = int(self.x) % WORLD_SIZE
        y = int(self.y) % WORLD_SIZE

        left = world.food_grid[(x - 3) % WORLD_SIZE, y]
        right = world.food_grid[(x + 3) % WORLD_SIZE, y]
        up = world.food_grid[x, (y - 3) % WORLD_SIZE]
        down = world.food_grid[x, (y + 3) % WORLD_SIZE]

        return left, right, up, down

    def _update_stage(self):
        if self.stage == "dauer":
            return

        if self.age > 200:
            self.stage = "adult"
            self.size = max(self.size, 1.0)
        elif self.age > 150:
            self.stage = "L4"
            self.size = max(self.size, 0.75)
        elif self.age > 100:
            self.stage = "L3"
            self.size = max(self.size, 0.55)
        elif self.age > 50:
            self.stage = "L2"
            self.size = max(self.size, 0.4)
        else:
            self.stage = "L1"
            self.size = max(self.size, 0.2)

    def _build_mutated_child_genes(self):
        mutation_rate = 0.05
        child_genes = {
            "gene_speed": self.gene_speed,
            "gene_turn_bias": self.gene_turn_bias,
            "gene_food_weight": self.gene_food_weight,
            "gene_pheromone_weight": self.gene_pheromone_weight,
            "gene_reproduction_energy": self.gene_reproduction_energy,
        }

        child_genes["gene_speed"] += random.gauss(0.0, mutation_rate)
        child_genes["gene_turn_bias"] += random.gauss(0.0, mutation_rate)
        child_genes["gene_food_weight"] += random.gauss(0.0, mutation_rate)
        child_genes["gene_pheromone_weight"] += random.gauss(0.0, mutation_rate)
        child_genes["gene_reproduction_energy"] += random.gauss(0.0, 5.0)

        child_genes["gene_speed"] = max(0.5, min(1.5, child_genes["gene_speed"]))
        child_genes["gene_turn_bias"] = max(0.5, min(1.5, child_genes["gene_turn_bias"]))
        child_genes["gene_food_weight"] = max(0.5, min(1.5, child_genes["gene_food_weight"]))
        child_genes["gene_pheromone_weight"] = max(0.5, min(1.5, child_genes["gene_pheromone_weight"]))
        return child_genes

    def update(self, world, dt=1 / 60, new_worms=None, new_eggs=None):

        if self.dead:
            return False

        self.time += dt
        self.age += dt
        self.repro_timer -= dt
        self._update_stage()
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
        food_here = world.get_food(self.x, self.y)
        pheromone_here = world.get_pheromone(self.x, self.y)

        left_food = world.sample_food(
            self.x + math.cos(self.angle + 0.3) * 8,
            self.y + math.sin(self.angle + 0.3) * 8,
        )
        right_food = world.sample_food(
            self.x + math.cos(self.angle - 0.3) * 8,
            self.y + math.sin(self.angle - 0.3) * 8,
        )

        food_turn = (left_food - right_food) * 0.05
        food_turn *= self.gene_food_weight

        pher_left = world.get_pheromone(*left_sensor_pos)
        pher_right = world.get_pheromone(*right_sensor_pos)
        pher_gradient = pher_right - pher_left
        pheromone_turn = pher_gradient * 0.3
        pheromone_turn *= self.gene_pheromone_weight

        food_signal = (food_here + left_food + right_food) / 3.0
        food_gradient = food_signal - self.prev_food_signal
        self.prev_food_signal = food_signal

        margin = 40
        min_edge_distance = min(self.x, world.width - self.x, self.y, world.height - self.y)
        food_left = left_food
        food_right = right_food
        pheromone = pheromone_here
        oxygen = max(0.0, min(1.0, 1.0 - food_signal / 5.0))
        touch = max(0.0, min(1.0, (margin - min_edge_distance) / margin)) * 3.0

        sensor_food = max(-1.0, min(1.0, food_left - food_right))
        sensor_pheromone = max(0.0, min(1.0, pheromone))
        sensor_oxygen = oxygen
        sensor_touch = touch

        if food_here < 0.02 and pheromone_here > 0.4:
            if random.random() < 0.002:
                self.dauer = True

        if self.dauer:
            self.stage = "dauer"
            self.size = min(self.size, 0.35)

        self.syn_food += sensor_food * 0.0001
        self.syn_pheromone += sensor_pheromone * 0.00005
        self.syn_food = max(0.0, min(1.0, self.syn_food))
        self.syn_pheromone = max(0.0, min(1.0, self.syn_pheromone))

        weighted_food = sensor_food * self.syn_food
        weighted_pheromone = sensor_pheromone * self.syn_pheromone
        self.neuron_aiy = 0.6 * weighted_food + 0.2 * weighted_pheromone - 0.1 * sensor_oxygen
        self.neuron_aiz = -0.5 * weighted_food + 0.3 * sensor_touch + 0.1 * sensor_oxygen
        self.neuron_avb = max(0.0, self.neuron_aiy)
        self.neuron_ava = max(0.0, self.neuron_aiz)

        if self.neuron_ava > 0.6:
            self.direction = -1
        elif self.neuron_avb > 0.2:
            self.direction = 1

        turn_bias = sensor_food * 0.4 + sensor_pheromone * 0.2

        self.run_timer -= dt
        if food_gradient > 0:
            self.run_timer += 0.5
        elif food_gradient < 0:
            self.run_timer -= 0.5
        if self.run_timer <= 0:
            self.angle += random.uniform(-0.6, 0.6)
            self.run_timer = random.uniform(2.0, 6.0)

        if food_here > 0.8:
            eating = True

        if food_signal > 1.2:
            self.behavior = "dwell"
        elif food_signal < 0.3:
            self.behavior = "roam"

        stress_target = max(0.0, min(1.0, pheromone_here / 2.0 - food_signal * 0.2))
        liquid_level = world.sample_medium(self.x, self.y)
        self.gene_expression["stress"] += (stress_target - self.gene_expression["stress"]) * 0.08
        self.gene_expression["liquid"] += (liquid_level - self.gene_expression["liquid"]) * 0.08
        self.gene_expression["foraging"] += (food_gradient * 0.5 - self.gene_expression["foraging"] + 1.0) * 0.04
        self.gene_expression["foraging"] = max(0.6, min(1.4, self.gene_expression["foraging"]))
        self.gene_expression["stress"] = max(0.0, min(1.0, self.gene_expression["stress"]))
        self.gene_expression["liquid"] = max(0.0, min(1.0, self.gene_expression["liquid"]))

        self.locomotion_mode = "swim" if self.gene_expression["liquid"] > 0.5 else "crawl"

        inputs = [food_x, food_y, 0, 0, 0, 0, 0, 0, 0, 0]

        for i in range(len(inputs)):
            inputs[i] += random.uniform(-0.002, 0.002)

        brain_output = self.brain.step(inputs)

        if brain_output[5]:
            self.angle -= 0.05

        if brain_output[6]:
            self.angle += 0.05

        curvature = brain_output[5] - brain_output[6]
        neural_turn = curvature * 0.03

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

        if food_gradient < 0 and random.random() < 0.02:
            self.angle += random.uniform(-0.3, 0.3)

        random_turn = random.uniform(-0.02, 0.02)
        if pheromone_here > 0.25:
            random_turn *= 0.3
        turn_combined = (
            0.6 * food_turn
            + 0.15 * random_turn
        )
        self.angular_velocity *= 0.75
        if abs(turn_combined) < 0.01:
            self.angular_velocity *= 0.6
        self.angular_velocity += turn_combined
        self.angular_velocity += pheromone_turn
        self.angular_velocity += turn_bias * self.gene_turn_bias

        if self.x < margin:
            self.angular_velocity += 0.05
        if self.x > world.width - margin:
            self.angular_velocity -= 0.05
        if self.y < margin:
            self.angular_velocity += 0.05
        if self.y > world.height - margin:
            self.angular_velocity -= 0.05

        self.angular_velocity = max(-0.12, min(0.12, self.angular_velocity))
        self.angle += self.angular_velocity * dt * 60

        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)

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

        self.neural_phase += dt * (3.0 + self.neuron_avb * 2.0)

        target_speed = 40.0
        self.speed = 0.9 * self.speed + 0.1 * target_speed
        move_speed = self.speed * self.gene_speed
        if pheromone_here > 0.25:
            move_speed *= 0.8

        energy_loss = 0.02 * dt
        if self.dauer:
            move_speed *= 0.2
            energy_loss *= 0.3

        self.x += math.cos(self.angle) * move_speed * dt * self.direction
        self.y += math.sin(self.angle) * move_speed * dt * self.direction

        self.energy -= energy_loss

        self.x = max(0, min(WORLD_SIZE, self.x))
        self.y = max(0, min(WORLD_SIZE, self.y))

        gx = int(self.x / WORLD_SIZE * GRID_SIZE)
        gy = int(self.y / WORLD_SIZE * GRID_SIZE)
        food_eaten = 0.0

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:

            if world.food[gx, gy] > 0 and not self.dauer:

                eaten = min(0.05, world.food[gx, gy])

                world.food[gx, gy] -= eaten
                self.energy += eaten * 5
                food_eaten += eaten
                eating = True

        self.size += 0.002 * food_eaten
        self.size += dt * 0.01
        self.size = min(self.size, 1.0)
        segment_length = BASE_SEGMENT_LENGTH * self.size

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
            world.pheromone[gx, gy] += 0.05

        local_density = world.count_worms_near(self.x, self.y, radius=20)
        if local_density > 20:
            self.energy -= 0.2 * dt

        if self.stage == "adult" and self.energy > self.gene_reproduction_energy and self.repro_timer <= 0:
            persistence = random.uniform(0.20, 0.34)
            inherited_expression = {
                "foraging": (1.0 - persistence) * 1.0 + persistence * self.gene_expression["foraging"],
                "stress": (1.0 - persistence) * 0.0 + persistence * self.gene_expression["stress"],
                "liquid": (1.0 - persistence) * 0.0 + persistence * self.gene_expression["liquid"],
            }
            child_genes = self._build_mutated_child_genes()
            egg = Egg(
                self.x + random.uniform(-5, 5),
                self.y + random.uniform(-5, 5),
                inherited_expression=inherited_expression,
                inherited_genes=child_genes,
            )
            if new_eggs is not None:
                new_eggs.append(egg)
            elif new_worms is not None:
                baby = Worm(
                    egg.x,
                    egg.y,
                    inherited_expression=egg.inherited_expression,
                    inherited_genes=egg.inherited_genes,
                )
                baby.size = 0.3
                baby.energy = 40
                baby.age = 0
                baby.stage = "L1"
                new_worms.append(baby)
            else:
                return True
            self.energy -= 80
            self.repro_timer = 30.0

        self.energy = max(0.0, self.energy)

        if self.energy <= 0:
            self.dead = True
            return False

        MAX_AGE = 1200 if self.stage == "dauer" else 500
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
