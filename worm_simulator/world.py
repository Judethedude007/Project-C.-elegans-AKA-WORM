import random
import math
import numpy as np
from config import (
    WORLD_SIZE,
    WORLD_CHUNK_SIZE,
    TEMPERATURE,
    WATER_LEVEL,
    OXYGEN_LEVEL,
    FOOD_GROWTH_RATE,
    MUTATION_RATE,
    SEASON_SPEED,
)

GRID_SIZE = 128
SEASON_DURATION = 300.0
SEASON_NAMES = ("Spring", "Summer", "Autumn", "Winter")
SEASON_GROWTH_MULTIPLIER = (1.5, 1.0, 0.6, 0.3)
SEASON_TEMPERATURE = (22.0, 28.0, 16.0, 6.0)
LOGISTIC_GROWTH_RATE = 0.0025
FOOD_MAX_DENSITY = 1.0


class World:
    @property
    def season_progress(self):
        """
        Returns the progress through the current season as a float in [0.0, 1.0).
        Each season is a quarter of the full 2π phase cycle.
        """
        # Normalize phase to [0, 2π)
        phase = self.season_phase % (2.0 * math.pi)
        # Each season is 1/4 of the cycle
        season_length = (2.0 * math.pi) / 4.0
        # Progress within the current season
        progress = (phase % season_length) / season_length
        return progress

    def __init__(self):
        self.width = WORLD_SIZE
        self.height = WORLD_SIZE
        self.worm_positions = []
        self.worm_density = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.food_patches = []

        self.food = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.food_age = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.food_capacity = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.pheromone = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.chem = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.medium = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.oxygen = np.ones((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self.chunk_world_size = max(1, int(WORLD_CHUNK_SIZE))
        self.chunk_count = max(1, WORLD_SIZE // self.chunk_world_size)
        self.chunk_food_cells = max(1, GRID_SIZE // self.chunk_count)
        self.season_time = 0.0
        self.season_phase = 0.0
        self.season_signal = 0.0
        self.season_index = 0
        self.season_name = SEASON_NAMES[self.season_index]
        self.base_temperature = SEASON_TEMPERATURE[self.season_index]
        self.temperature = self.base_temperature
        self.control_temperature = float(TEMPERATURE)
        self.water_level = float(WATER_LEVEL)
        self.oxygen_level = float(OXYGEN_LEVEL)
        self.food_growth_rate = float(FOOD_GROWTH_RATE)
        self.mutation_rate = float(MUTATION_RATE)

        self.season_speed = float(SEASON_SPEED)

        # Climate toggle state
        self.climate_enabled = False
        self.control_temperature = float(TEMPERATURE)
        self.water_level = float(WATER_LEVEL)
        self.mutation_rate = float(MUTATION_RATE)

        axis = np.linspace(-1.0, 1.0, GRID_SIZE, dtype=np.float32)
        edge_x, edge_y = np.meshgrid(axis, axis, indexing="ij")
        radial = np.sqrt(edge_x * edge_x + edge_y * edge_y)
        edge_factor = np.clip(radial / np.sqrt(2.0), 0.0, 1.0)
        self.edge_oxygen = 0.65 + 0.35 * edge_factor

        for _ in range(6):
            cx = random.uniform(100.0, WORLD_SIZE - 100.0)
            cy = random.uniform(100.0, WORLD_SIZE - 100.0)
            self._add_food_gaussian(cx, cy, 120, 80)
            self.food_patches.append({"x": cx, "y": cy})

        if self.food_patches:
            self.food_center_x = float(sum(p["x"] for p in self.food_patches) / len(self.food_patches))
            self.food_center_y = float(sum(p["y"] for p in self.food_patches) / len(self.food_patches))
        else:
            self.food_center_x = WORLD_SIZE * 0.5
            self.food_center_y = WORLD_SIZE * 0.5

        np.clip(self.food, 0.0, 1.0, out=self.food)
        self.food_capacity[:] = self.food
        self.oxygen = np.clip(self.edge_oxygen - self.food * 0.35, 0.0, 1.0)

        for _ in range(5):
            gx = random.randint(0, GRID_SIZE - 1)
            gy = random.randint(0, GRID_SIZE - 1)
            self._add_medium_patch(gx, gy, radius=8, value=1.0)

    def set_environment_controls(
        self,
        temperature=None,
        water_level=None,
        oxygen_level=None,
        food_growth_rate=None,
        mutation_rate=None,
        season_speed=None,
    ):
        if temperature is not None:
            self.control_temperature = max(0.5, min(2.0, float(temperature)))
        if water_level is not None:
            self.water_level = max(0.2, min(2.0, float(water_level)))
        if oxygen_level is not None:
            self.oxygen_level = max(0.2, min(2.0, float(oxygen_level)))
        if food_growth_rate is not None:
            self.food_growth_rate = max(0.0001, min(0.01, float(food_growth_rate)))
        if mutation_rate is not None:
            self.mutation_rate = max(0.0, min(0.1, float(mutation_rate)))
        if season_speed is not None:
            self.season_speed = max(0.00005, min(0.01, float(season_speed)))

    def _add_food_gaussian(self, cx_world, cy_world, std=40, n=3000):
        xs = np.random.normal(cx_world, std, n).astype(int)
        ys = np.random.normal(cy_world, std, n).astype(int)
        mask = (xs >= 0) & (xs < WORLD_SIZE) & (ys >= 0) & (ys < WORLD_SIZE)
        gxs = (xs[mask] * GRID_SIZE // WORLD_SIZE).clip(0, GRID_SIZE - 1)
        gys = (ys[mask] * GRID_SIZE // WORLD_SIZE).clip(0, GRID_SIZE - 1)
        np.add.at(self.food, (gxs, gys), 1)

    def _add_food_cluster(self, cx, cy, radius=10, amount=2.0):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                gx = (cx + dx) % GRID_SIZE
                gy = (cy + dy) % GRID_SIZE
                self.food[gx, gy] += amount

    def _add_medium_patch(self, cx, cy, radius=8, value=1.0):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                gx = (cx + dx) % GRID_SIZE
                gy = (cy + dy) % GRID_SIZE
                self.medium[gx, gy] = value

    def get_active_chunks_near_worms(self, worms, radius_chunks=1):
        active_chunks = set()
        radius = max(0, int(radius_chunks))
        for worm in worms:
            if getattr(worm, "dead", False):
                continue

            cx = int(float(worm.x) / self.chunk_world_size)
            cy = int(float(worm.y) / self.chunk_world_size)
            cx = max(0, min(self.chunk_count - 1, cx))
            cy = max(0, min(self.chunk_count - 1, cy))

            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx = cx + dx
                    ny = cy + dy
                    if 0 <= nx < self.chunk_count and 0 <= ny < self.chunk_count:
                        active_chunks.add((nx, ny))

        return active_chunks

    def _build_active_mask(self, active_chunks, margin_cells=1):
        if not active_chunks:
            return None

        mask = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        for cx, cy in active_chunks:
            x0 = max(0, cx * self.chunk_food_cells - margin_cells)
            x1 = min(GRID_SIZE, (cx + 1) * self.chunk_food_cells + margin_cells)
            y0 = max(0, cy * self.chunk_food_cells - margin_cells)
            y1 = min(GRID_SIZE, (cy + 1) * self.chunk_food_cells + margin_cells)
            mask[x0:x1, y0:y1] = True

        return mask if np.any(mask) else None


    def update(self, dt=1 / 60, active_chunks=None):
        # Climate toggle logic
        if self.climate_enabled:
            self.control_temperature += random.uniform(-0.01, 0.01)
            self.control_temperature = max(0.8, min(1.2, self.control_temperature))

            self.water_level += random.uniform(-0.005, 0.005)
            self.water_level = max(0.7, min(1.3, self.water_level))

            self.mutation_rate += random.uniform(-0.0001, 0.0001)
            self.mutation_rate = max(0.005, min(0.05, self.mutation_rate))

        time_scale = max(dt * 60.0, 0.0)
        self.season_time += dt
        if self.climate_enabled:
            self.season_phase += self.season_speed * time_scale
            self.season_signal = math.sin(self.season_phase)
            phase_norm = (self.season_phase % (2.0 * math.pi)) / (2.0 * math.pi)
            self.season_index = int(phase_norm * 4.0) % 4
            self.season_name = SEASON_NAMES[self.season_index]
            self.base_temperature = SEASON_TEMPERATURE[self.season_index]
            self.temperature = self.base_temperature * self.control_temperature
        seasonal_growth = 0.5 + 0.5 * self.season_signal
        active_mask = self._build_active_mask(active_chunks, margin_cells=1)
        self.food_age += dt

        # Logistic bacterial growth gives self-limited patch expansion.
        logistic_growth = LOGISTIC_GROWTH_RATE * seasonal_growth * self.food * (1.0 - self.food / FOOD_MAX_DENSITY)
        user_growth = self.food_growth_rate * seasonal_growth

        # Food patch spreading creates organic cluster growth rather than static fields.
        # Food diffusion: existing patches spread organically to neighbouring cells.
        food_candidate = self.food + user_growth * time_scale + logistic_growth * time_scale + 0.15 * seasonal_growth * (
            np.roll(self.food, 1, axis=0)
            + np.roll(self.food, -1, axis=0)
            + np.roll(self.food, 1, axis=1)
            + np.roll(self.food, -1, axis=1)
            - 4.0 * self.food
        ) * time_scale

        decay_base = max(0.997, 0.999 - (1.0 - seasonal_growth) * 0.0005)
        food_candidate *= decay_base ** time_scale
        if active_mask is None:
            self.food = food_candidate
        else:
            self.food[active_mask] = food_candidate[active_mask]

        # Sparse regrowth seeds new patches where food is depleted.
        regrow_chance = min(1.0, 0.0005 * time_scale * seasonal_growth)
        regrow_mask = (self.food < 0.1) & (np.random.random(self.food.shape) < regrow_chance)
        if active_mask is not None:
            regrow_mask &= active_mask
        self.food[regrow_mask] += 0.05
        self.food_age[regrow_mask] = 0.0

        np.clip(self.food, 0.0, 1.0, out=self.food)

        # Oxygen is higher near plate edges and lower in dense food/worm clusters.
        oxygen_candidate = self.edge_oxygen * self.oxygen_level - self.food * 0.35 - self.worm_density * 0.2
        oxygen_candidate = np.clip(oxygen_candidate, 0.0, 1.0)
        if active_mask is None:
            self.oxygen = oxygen_candidate
        else:
            self.oxygen[active_mask] = oxygen_candidate[active_mask]
        np.clip(self.oxygen, 0.0, 1.0, out=self.oxygen)

        # Food releases chemical signal into the smell map.
        chem_release = self.food * 2.5 * seasonal_growth * time_scale
        if active_mask is None:
            self.chem += chem_release
        else:
            self.chem[active_mask] += chem_release[active_mask]

        # Diffuse chemical concentration to neighboring cells.
        new_chem = np.zeros_like(self.chem)
        new_chem[1:-1, 1:-1] = (
            self.chem[1:-1, 1:-1] * 0.7
            + (
                self.chem[2:, 1:-1]
                + self.chem[:-2, 1:-1]
                + self.chem[1:-1, 2:]
                + self.chem[1:-1, :-2]
            )
            * 0.075
        )
        if active_mask is None:
            self.chem = np.clip(new_chem, 0.0, 100.0)
        else:
            self.chem[active_mask] = np.clip(new_chem[active_mask], 0.0, 100.0)

        if random.random() < 0.001:
            max_val = max(max(row) for row in self.chem)
            print("chem max:", max_val)

        # Pheromone decays slowly over time.
        pheromone_decay = 0.995 ** time_scale
        if active_mask is None:
            self.pheromone *= pheromone_decay
        else:
            self.pheromone[active_mask] *= pheromone_decay
        np.clip(self.pheromone, 0.0, 1000.0, out=self.pheromone)

    def get_food(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return self.food[gx % GRID_SIZE, gy % GRID_SIZE]

    def sample_food(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return float(self.food[gx % GRID_SIZE, gy % GRID_SIZE])

    def sample_pheromone(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return float(self.pheromone[gx % GRID_SIZE, gy % GRID_SIZE])

    def sample_medium(self, x, y):
        gx = int((x % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        gy = int((y % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
        return float(self.medium[gx % GRID_SIZE, gy % GRID_SIZE]) * self.water_level

    def get_pheromone(self, x, y):
        return self.sample_pheromone(x, y)

    def set_worm_positions(self, worms):
        self.worm_positions = [(float(w.x), float(w.y)) for w in worms if not getattr(w, "dead", False)]
        self.worm_density.fill(0.0)

        total_worms = len(self.worm_positions)
        if total_worms == 0:
            return

        for wx, wy in self.worm_positions:
            gx = int((wx % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
            gy = int((wy % WORLD_SIZE) / WORLD_SIZE * GRID_SIZE)
            self.worm_density[gx % GRID_SIZE, gy % GRID_SIZE] += 1.0

        self.worm_density /= float(total_worms)
        self.worm_density = (
            self.worm_density
            + np.roll(self.worm_density, 1, 0)
            + np.roll(self.worm_density, -1, 0)
            + np.roll(self.worm_density, 1, 1)
            + np.roll(self.worm_density, -1, 1)
        ) / 5.0

    def count_worms_near(self, x, y, radius=20):
        radius_sq = float(radius) * float(radius)
        count = 0
        for wx, wy in self.worm_positions:
            dx = wx - x
            dy = wy - y
            if dx * dx + dy * dy <= radius_sq:
                count += 1
        return count
