import math
import random
from brain import Brain
from config import WORLD_SIZE
from world import GRID_SIZE

METABOLISM = 0.3
MOVE_COST = 0.2
AGE_LIMIT = 5000
REPRODUCTION_COST = 2000
MAX_AGE = 600
SEGMENTS = 24
BASE_SEGMENT_LENGTH = 5
BASE_LENGTH = BASE_SEGMENT_LENGTH * SEGMENTS
SEGMENT_LENGTH = BASE_SEGMENT_LENGTH
STIFFNESS = 0.25
DAMPING = 0.85
MAX_STRETCH = SEGMENT_LENGTH * 2.0
SENSOR_DISTANCE = 25
GROUND_FRICTION = 0.82
SEGMENT_SPRING = 8.0
MUSCLE_FORCE = 3.0
WAVE_AMPLITUDE = 0.35
WAVE_FREQUENCY = 1.2
WAVE_SPACING = 0.45


def sample_chem(env, x, y):
    gx = int(x / WORLD_SIZE * GRID_SIZE)
    gy = int(y / WORLD_SIZE * GRID_SIZE)

    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
        return float(env.chem[gx][gy])

    return 0.0


class Egg:

    def __init__(
        self,
        x,
        y,
        inherited_expression=None,
        inherited_genes=None,
        inherited_genome=None,
        generation=0,
        lineage_id=None,
    ):
        self.x = x % WORLD_SIZE
        self.y = y % WORLD_SIZE
        self.hatch_timer = random.uniform(30.0, 60.0)
        self.timer = self.hatch_timer
        self.generation = int(generation)
        if lineage_id is None:
            lineage_id = random.randint(0, 1000000)
        self.lineage_id = int(lineage_id)
        if inherited_expression is None:
            inherited_expression = {
                "foraging": 1.0,
                "stress": 0.0,
                "liquid": 0.0,
            }
        self.inherited_expression = dict(inherited_expression)
        if inherited_genome is None and inherited_genes is not None:
            inherited_genome = inherited_genes
        if inherited_genome is None:
            inherited_genome = {}
        self.inherited_genome = dict(inherited_genome)
        if inherited_genes is None:
            inherited_genes = {}
        self.inherited_genes = dict(inherited_genes)

    def update(self, dt):
        self.hatch_timer -= dt
        self.timer = self.hatch_timer
        return self.hatch_timer <= 0.0


class Worm:

    def __init__(self, x, y, genes=None, inherited_expression=None, inherited_genes=None):

        self.x = x
        self.y = y

        self.angle = random.uniform(0, math.tau)
        self.angular_velocity = random.uniform(-0.1, 0.1)
        self.time = 0.0
        self.wave_phase = random.random() * 6.28
        self.wave_freq = 1.8
        self.wave_amp = 0.35
        self.forward_signal = 0.0
        self.turn_signal = 0.0
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
        self.stage = "juvenile"
        self.locomotion_mode = "crawl"
        self.prev_food_signal = 0.0
        self.food_adaptation = 0.0
        self.repro_timer = 0.0
        self.generation = 0
        self.state = "RUN"
        self.run_timer = 0.0
        self.dauer = False
        self.neurons = {
            "food": 0.0,
            "pheromone": 0.0,
            "oxygen": 0.0,
            "interA": 0.0,
            "interB": 0.0,
            "forward": 0.0,
            "turnL": 0.0,
            "turnR": 0.0,
        }

        if inherited_genes is None:
            inherited_genes = {}

        self.generation = int(inherited_genes.get("generation", 0))
        self.lineage_id = int(inherited_genes.get("lineage_id", random.randint(0, 1000000)))
        self.color = self._lineage_color(self.lineage_id)

        base_gene_speed = float(
            inherited_genes.get("gene_speed", inherited_genes.get("speed", random.uniform(0.8, 1.2)))
        )
        base_gene_food_sense = float(
            inherited_genes.get(
                "gene_food_sense",
                inherited_genes.get("food_sense", inherited_genes.get("gene_food_weight", random.uniform(0.8, 1.2))),
            )
        )
        base_gene_phero_sense = float(
            inherited_genes.get(
                "gene_phero_sense",
                inherited_genes.get(
                    "pheromone_sense",
                    inherited_genes.get("gene_pheromone_weight", random.uniform(0.8, 1.2)),
                ),
            )
        )
        base_gene_reproduction_energy = float(
            inherited_genes.get(
                "gene_reproduction_energy",
                inherited_genes.get("reproduction_energy", random.uniform(150.0, 220.0)),
            )
        )

        self.gene_speed = max(0.6, min(1.4, base_gene_speed))
        self.gene_food_sense = max(0.6, min(1.4, base_gene_food_sense))
        self.gene_phero_sense = max(0.6, min(1.4, base_gene_phero_sense))
        self.gene_reproduction_energy = max(120.0, min(280.0, base_gene_reproduction_energy))

        self.genome = {
            "speed": self.gene_speed,
            "turn_bias": float(
                inherited_genes.get("turn_bias", inherited_genes.get("gene_turn_bias", random.uniform(0.9, 1.1)))
            ),
            "food_sense": self.gene_food_sense,
            "pheromone_sense": self.gene_phero_sense,
            "energy_efficiency": float(inherited_genes.get("energy_efficiency", random.uniform(0.9, 1.1))),
            "reproduction_energy": self.gene_reproduction_energy,
        }

        self.genome["speed"] = max(0.6, min(1.4, self.genome["speed"]))
        self.genome["food_sense"] = max(0.6, min(1.4, self.genome["food_sense"]))
        self.genome["pheromone_sense"] = max(0.6, min(1.4, self.genome["pheromone_sense"]))
        self.genome["turn_bias"] = max(0.75, min(1.25, self.genome["turn_bias"]))
        self.genome["energy_efficiency"] = max(0.75, min(1.25, self.genome["energy_efficiency"]))
        self.genome["reproduction_energy"] = self.gene_reproduction_energy

        # Evolution genes
        self.gene_speed = self.genome["speed"]
        self.gene_turn_bias = self.genome["turn_bias"]
        self.gene_food_sense = self.genome["food_sense"]
        self.gene_phero_sense = self.genome["pheromone_sense"]
        self.gene_food_weight = self.gene_food_sense
        self.gene_pheromone_weight = self.gene_phero_sense
        self.gene_reproduction_energy = self.genome["reproduction_energy"]

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
        self.segment_angle = [0.0] * SEGMENTS
        self.num_segments = self.segments
        self.segment_angles = self.segment_angle

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
        if self.dauer:
            self.stage = "dauer"
            self.size = min(self.size, 0.35)
            return

        if self.age > 40.0:
            self.stage = "adult"
            self.size = max(self.size, 1.0)
        else:
            self.stage = "juvenile"
            juvenile_progress = max(0.0, min(1.0, self.age / 40.0))
            target_size = 0.25 + juvenile_progress * 0.75
            self.size = max(self.size, target_size)

    def _build_mutated_child_genes(self):
        child_lineage_id = self.lineage_id
        if random.random() < 0.02:
            child_lineage_id = random.randint(0, 1000000)

        child_gene_speed = max(0.6, min(1.4, self.gene_speed * random.uniform(0.95, 1.05)))
        child_gene_food_sense = max(0.6, min(1.4, self.gene_food_sense * random.uniform(0.95, 1.05)))
        child_gene_phero_sense = max(0.6, min(1.4, self.gene_phero_sense * random.uniform(0.95, 1.05)))
        child_gene_reproduction_energy = max(
            120.0,
            min(280.0, self.gene_reproduction_energy * random.uniform(0.95, 1.05)),
        )

        child_genes = {
            "gene_speed": child_gene_speed,
            "gene_food_sense": child_gene_food_sense,
            "gene_phero_sense": child_gene_phero_sense,
            "gene_reproduction_energy": child_gene_reproduction_energy,
            "speed": child_gene_speed,
            "food_sense": child_gene_food_sense,
            "pheromone_sense": child_gene_phero_sense,
            "reproduction_energy": child_gene_reproduction_energy,
            "turn_bias": self.genome["turn_bias"],
            "energy_efficiency": self.genome["energy_efficiency"],
            "lineage_id": child_lineage_id,
            "generation": self.generation + 1,
        }
        return child_genes

    @staticmethod
    def _lineage_color(lineage_id):
        rng = random.Random(int(lineage_id))
        return (
            rng.randint(120, 255) / 255.0,
            rng.randint(120, 255) / 255.0,
            rng.randint(120, 255) / 255.0,
        )

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

        time_scale = max(dt * 60.0, 0.0)
        self.food_adaptation += food_here * 0.02 * dt
        self.food_adaptation *= 0.995 ** time_scale
        adaptation_scale = 1.0 + self.food_adaptation

        food_turn = ((left_food - right_food) / adaptation_scale) * 0.05
        food_turn *= self.gene_food_sense

        pher_left = world.get_pheromone(*left_sensor_pos)
        pher_right = world.get_pheromone(*right_sensor_pos)
        pher_gradient = pher_right - pher_left
        pheromone_signal = pher_gradient
        pheromone_signal *= self.gene_phero_sense
        pheromone_turn = pheromone_signal * 0.3
        pheromone_signal_here = pheromone_here * self.gene_phero_sense

        sensory_food_signal = ((food_here + left_food + right_food) / 3.0) / adaptation_scale
        food_gradient = sensory_food_signal - self.prev_food_signal
        food_signal = food_here + food_gradient
        food_signal /= adaptation_scale
        food_signal *= self.gene_food_sense
        gradient_change = food_signal - self.prev_food_signal
        self.prev_food_signal = food_signal

        margin = 40
        min_edge_distance = min(self.x, world.width - self.x, self.y, world.height - self.y)
        food_left = left_food
        food_right = right_food
        pheromone = pheromone_here
        oxygen_here = 1.0
        if 0 <= feed_gx < GRID_SIZE and 0 <= feed_gy < GRID_SIZE:
            oxygen_here = float(world.oxygen[feed_gx, feed_gy])
        oxygen_pref = 0.08
        oxygen_signal = oxygen_pref - oxygen_here
        oxygen_turn = oxygen_signal * 0.3
        touch = max(0.0, min(1.0, (margin - min_edge_distance) / margin)) * 3.0

        local_density = world.count_worms_near(self.x, self.y, radius=20)
        collision_signal = max(touch, max(0.0, min(1.0, (local_density - 1.0) / 10.0)))

        if 0 <= feed_gx < GRID_SIZE and 0 <= feed_gy < GRID_SIZE:
            self.neurons["food"] = float(world.food[feed_gx, feed_gy])
            self.neurons["pheromone"] = float(world.pheromone[feed_gx, feed_gy])
            self.neurons["oxygen"] = float(world.oxygen[feed_gx, feed_gy])
        else:
            self.neurons["food"] = 0.0
            self.neurons["pheromone"] = 0.0
            self.neurons["oxygen"] = 1.0

        self.neurons["food"] = max(0.0, min(1.0, self.neurons["food"]))
        self.neurons["pheromone"] = max(0.0, min(1.0, self.neurons["pheromone"] / 1000.0))
        self.neurons["oxygen"] = max(0.0, min(1.0, self.neurons["oxygen"]))

        self.neurons["interA"] = (
            0.6 * self.neurons["food"]
            - 0.3 * self.neurons["oxygen"]
        )
        self.neurons["interB"] = (
            0.5 * self.neurons["pheromone"]
        )
        self.neurons["interA"] = math.tanh(self.neurons["interA"])
        self.neurons["interB"] = math.tanh(self.neurons["interB"])

        self.neurons["forward"] = max(
            0.0,
            0.7 * self.neurons["interA"],
        )
        self.neurons["turnL"] = max(
            0.0,
            0.5 * self.neurons["interB"],
        )
        self.neurons["turnR"] = max(
            0.0,
            -0.5 * self.neurons["interB"],
        )

        turn = self.neurons["turnR"] - self.neurons["turnL"]
        pheromone_signal_here = self.neurons["pheromone"]

        if (not self.dauer) and food_here < 0.05 and pheromone_signal_here > 0.2 and self.energy < 80:
            self.dauer = True
            self.stage = "dauer"
            self.size = min(self.size, 0.35)

        if self.dauer and food_here > 0.15:
            self.dauer = False

        self.direction = 1
        turn_bias = turn * 0.4 + collision_signal * 0.15

        self.run_timer += dt
        if self.state == "RUN":
            if gradient_change < -0.02 and random.random() < 0.15:
                self.state = "PIROUETTE"

        if self.state == "PIROUETTE":
            self.angle += random.uniform(-1.2, 1.2)
            self.state = "RUN"
            self.run_timer = 0.0

        if food_here > 0.8:
            eating = True

        if food_signal > 1.2:
            self.behavior = "dwell"
        elif food_signal < 0.3:
            self.behavior = "roam"

        stress_target = max(0.0, min(1.0, pheromone_signal_here / 2.0 - food_signal * 0.2))
        liquid_level = world.sample_medium(self.x, self.y)
        self.gene_expression["stress"] += (stress_target - self.gene_expression["stress"]) * 0.08
        self.gene_expression["liquid"] += (liquid_level - self.gene_expression["liquid"]) * 0.08
        self.gene_expression["foraging"] += (food_gradient * 0.5 - self.gene_expression["foraging"] + 1.0) * 0.04
        self.gene_expression["foraging"] = max(0.6, min(1.4, self.gene_expression["foraging"]))
        self.gene_expression["stress"] = max(0.0, min(1.0, self.gene_expression["stress"]))
        self.gene_expression["liquid"] = max(0.0, min(1.0, self.gene_expression["liquid"]))

        self.locomotion_mode = "swim" if self.gene_expression["liquid"] > 0.5 else "crawl"

        if food_gradient < 0 and random.random() < 0.02:
            self.angle += random.uniform(-0.25, 0.25)

        random_turn = random.uniform(-0.02, 0.02)
        if pheromone_signal_here > 0.25:
            random_turn *= 0.3
        if self.dauer:
            random_turn *= 2.0
        turn_combined = (
            0.7 * turn
            + 0.2 * oxygen_turn
            + 0.1 * random_turn
        )
        self.angular_velocity *= 0.75
        if abs(turn_combined) < 0.01:
            self.angular_velocity *= 0.6
        self.angular_velocity += turn_combined
        self.angular_velocity += turn_bias * self.genome["turn_bias"]
        turn_signal = turn
        self.angular_velocity *= 0.6
        self.angular_velocity += turn_signal
        self.forward_signal = max(0.0, self.neurons["forward"])
        self.turn_signal = turn_signal
        if abs(turn_signal) < 0.01:
            self.angular_velocity *= 0.7

        if self.x < margin:
            self.angular_velocity += 0.05
        if self.x > world.width - margin:
            self.angular_velocity -= 0.05
        if self.y < margin:
            self.angular_velocity += 0.05
        if self.y > world.height - margin:
            self.angular_velocity -= 0.05

        self.angular_velocity = max(-0.08, min(0.08, self.angular_velocity))
        self.angle += self.angular_velocity * dt * 60

        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)

        self.wave_freq = 1.5 + 0.8 * self.forward_signal
        self.wave_amp = 0.25 + 0.15 * abs(self.turn_signal)
        self.wave_phase += dt * self.wave_freq

        for i in range(self.num_segments):
            phase = self.wave_phase - i * 0.5
            bend = math.sin(phase) * self.wave_amp
            self.segment_angles[i] = bend
            self.muscle_left[i] = max(0.0, bend)
            self.muscle_right[i] = max(0.0, -bend)

        head_bias = self.angular_velocity * 0.4
        self.segment_angle[0] += head_bias
        if SEGMENTS > 1:
            self.segment_angle[1] += head_bias * 0.6
        self.segment_angle[0] = max(-0.7, min(0.7, self.segment_angle[0]))
        if SEGMENTS > 1:
            self.segment_angle[1] = max(-0.7, min(0.7, self.segment_angle[1]))
        self.muscle_left[0] = max(0.0, self.segment_angle[0])
        self.muscle_right[0] = max(0.0, -self.segment_angle[0])
        if SEGMENTS > 1:
            self.muscle_left[1] = max(0.0, self.segment_angle[1])
            self.muscle_right[1] = max(0.0, -self.segment_angle[1])

        wave_strength = 0

        for i in range(SEGMENTS):
            wave_strength += abs(self.segment_angle[i])

        wave_strength /= SEGMENTS

        BASE_SPEED = 40.0
        serotonin = min(1.0, food_here * 4)

        target_speed = 0.0

        if self.state == "RUN":
            speed = BASE_SPEED * self.neurons["forward"]
            target_speed = speed
            target_speed *= (0.7 + serotonin * 0.6)
            target_speed *= self.gene_speed
            if pheromone_here > 0.25:
                target_speed *= 0.8
            if self.dauer:
                target_speed *= 0.2

            self.angle += random.uniform(-0.03, 0.03)

        head_vx, head_vy = self.vel[0]
        head_vx *= GROUND_FRICTION
        head_vy *= GROUND_FRICTION

        target_vx = math.cos(self.angle) * target_speed * self.direction
        target_vy = math.sin(self.angle) * target_speed * self.direction
        drive_blend = min(1.0, dt * 6.0)
        head_vx += (target_vx - head_vx) * drive_blend
        head_vy += (target_vy - head_vy) * drive_blend
        head_vx *= 0.9
        head_vy *= 0.9

        MAX_SPEED = 6.0
        speed = math.sqrt(head_vx * head_vx + head_vy * head_vy)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            head_vx *= scale
            head_vy *= scale

        self.x += head_vx * dt
        self.y += head_vy * dt
        self.vel[0] = (head_vx, head_vy)

        self.x = max(0, min(WORLD_SIZE, self.x))
        self.y = max(0, min(WORLD_SIZE, self.y))
        self.body[0] = (self.x, self.y)

        # Segment dynamics: spring constraints + muscle-driven lateral forces + ground friction.
        for i in range(1, SEGMENTS):
            px, py = self.body[i - 1]
            cx, cy = self.body[i]
            seg_vx, seg_vy = self.vel[i]

            seg_vx *= GROUND_FRICTION
            seg_vy *= GROUND_FRICTION

            dx = cx - px
            dy = cy - py
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1e-6:
                dist = 1e-6

            MAX_SEGMENT = segment_length * 1.5
            if dist > MAX_SEGMENT:
                scale = MAX_SEGMENT / dist
                dx *= scale
                dy *= scale
                cx = px + dx
                cy = py + dy
                dist = MAX_SEGMENT

            stretch = dist - segment_length
            spring_force = -stretch * SEGMENT_SPRING
            MAX_FORCE = 2.5
            spring_force = max(-MAX_FORCE, min(MAX_FORCE, spring_force))
            seg_vx += (dx / dist) * spring_force * dt
            seg_vy += (dy / dist) * spring_force * dt

            bend = self.segment_angle[i]
            nx = -dy / dist
            ny = dx / dist
            seg_vx += nx * bend * MUSCLE_FORCE * dt
            seg_vy += ny * bend * MUSCLE_FORCE * dt
            seg_vx *= 0.9
            seg_vy *= 0.9

            speed = math.sqrt(seg_vx * seg_vx + seg_vy * seg_vy)
            if speed > MAX_SPEED:
                scale = MAX_SPEED / speed
                seg_vx *= scale
                seg_vy *= scale

            cx += seg_vx * dt
            cy += seg_vy * dt

            self.vel[i] = (seg_vx, seg_vy)
            self.body[i] = (cx, cy)

        for _ in range(2):
            self.body[0] = (self.x, self.y)
            for i in range(1, SEGMENTS):
                px, py = self.body[i - 1]
                cx, cy = self.body[i]
                dx = cx - px
                dy = cy - py
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 1e-6:
                    continue

                diff = (dist - segment_length) / dist
                if i == 1:
                    cx -= dx * diff
                    cy -= dy * diff
                else:
                    px += dx * 0.5 * diff
                    py += dy * 0.5 * diff
                    cx -= dx * 0.5 * diff
                    cy -= dy * 0.5 * diff
                    self.body[i - 1] = (px, py)

                cx = max(0.0, min(WORLD_SIZE, cx))
                cy = max(0.0, min(WORLD_SIZE, cy))
                self.body[i] = (cx, cy)

        gx = int(self.x / WORLD_SIZE * GRID_SIZE)
        gy = int(self.y / WORLD_SIZE * GRID_SIZE)
        food_here = 0.0
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            food_here = float(world.food[gx, gy])

        efficiency = max(0.6, self.genome["energy_efficiency"])
        energy_loss = (0.02 / efficiency) * dt
        if food_here < 0.05:
            energy_loss *= 1.5
        density = 0.0
        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            density = float(world.worm_density[gx, gy])
        energy_loss *= (1.0 + density * 15.0)
        if self.dauer:
            energy_loss *= 0.1

        self.energy -= energy_loss

        food_eaten = 0.0

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            if world.food[gx, gy] > 0 and not self.dauer:

                eaten = min(0.05 * time_scale, world.food[gx, gy])

                world.food[gx, gy] -= eaten
                world.food_age[gx, gy] = 0.0
                self.energy += eaten * 7
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

        if (not self.dauer) and self.stage == "adult" and self.energy > self.gene_reproduction_energy and self.repro_timer <= 0:
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
                inherited_genome=child_genes,
                inherited_genes=child_genes,
                generation=self.generation + 1,
                lineage_id=child_genes.get("lineage_id", self.lineage_id),
            )
            if new_eggs is not None:
                new_eggs.append(egg)
            elif new_worms is not None:
                baby = Worm(
                    egg.x,
                    egg.y,
                    inherited_expression=egg.inherited_expression,
                    inherited_genes=getattr(egg, "inherited_genome", egg.inherited_genes),
                )
                baby.size = 0.3
                baby.energy = 40
                baby.age = 0
                baby.stage = "juvenile"
                baby.generation = int(getattr(egg, "generation", self.generation + 1))
                baby.lineage_id = int(getattr(egg, "lineage_id", self.lineage_id))
                baby.color = self._lineage_color(baby.lineage_id)
                new_worms.append(baby)
            else:
                return True
            self.energy -= 60
            self.repro_timer = 30.0

        self.energy = max(0.0, self.energy)

        if self.energy <= 0:
            self.dead = True
            return False

        if self.age > 350.0:
            death_prob = max(0.0, min(1.0, (self.age - 350.0) / 150.0))
            if random.random() < death_prob * dt:
                self.dead = True
                return False

        return True

    def smooth_body(self, points=None):
        def catmull_rom(p0, p1, p2, p3, t):
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2.0 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2.0 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
            )
            return (x, y)

        source_points = self.body if points is None else points
        valid_points = []
        for bx, by in source_points:
            if (not math.isfinite(bx)) or (not math.isfinite(by)):
                continue
            valid_points.append((bx, by))

        if len(valid_points) < 2:
            return valid_points

        max_gap = BASE_SEGMENT_LENGTH * max(self.size, 0.2) * 2.5
        max_gap_sq = max_gap * max_gap
        strips = []
        current_strip = [valid_points[0]]

        for p in valid_points[1:]:
            dx = p[0] - current_strip[-1][0]
            dy = p[1] - current_strip[-1][1]
            if dx * dx + dy * dy > max_gap_sq:
                if len(current_strip) >= 2:
                    strips.append(current_strip)
                current_strip = [p]
            else:
                current_strip.append(p)

        if len(current_strip) >= 2:
            strips.append(current_strip)

        smooth_points = []
        interpolation_steps = 4

        for strip in strips:
            if len(strip) < 4:
                smooth_points.extend(strip)
                continue

            padded = [strip[0]] + strip + [strip[-1]]
            for i in range(1, len(padded) - 2):
                p0 = padded[i - 1]
                p1 = padded[i]
                p2 = padded[i + 1]
                p3 = padded[i + 2]

                smooth_points.append(p1)
                for step in range(interpolation_steps):
                    t = step / float(interpolation_steps - 1)
                    if t <= 0.0:
                        continue
                    smooth_points.append(catmull_rom(p0, p1, p2, p3, t))

            smooth_points.append(strip[-1])

        return smooth_points

    def body_points(self):
        growth = min(1.0, self.age / 40.0)
        body_length = BASE_LENGTH * (0.4 + 0.6 * growth)
        visible_ratio = max(0.1, min(1.0, body_length / BASE_LENGTH))
        visible_segments = max(2, min(self.segments, int(round(self.segments * visible_ratio))))
        return self.smooth_body(points=self.body[:visible_segments])
