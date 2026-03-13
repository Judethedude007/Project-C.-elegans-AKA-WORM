import random
import numpy as np
import pygame

try:
    import imgui
    from imgui.integrations.pygame import PygameRenderer
    IMGUI_AVAILABLE = True
except Exception:
    imgui = None
    PygameRenderer = None
    IMGUI_AVAILABLE = False

from world import World
from worm import Worm, SEGMENTS
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_SIZE
from gpu_renderer import GPURenderer

ZOOM_MIN = max(0.2, 2.0 / WORLD_SIZE)
ZOOM_MAX = 100.0
CAMERA_STEP = 12.0

pygame.init()

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.OPENGL | pygame.DOUBLEBUF,
)
pygame.display.set_caption("Worm Simulator GPU")

if IMGUI_AVAILABLE:
    imgui.create_context()
    imgui_renderer = PygameRenderer()
else:
    imgui_renderer = None

world = World()
worms = [Worm(random.uniform(0, WORLD_SIZE - 1), random.uniform(0, WORLD_SIZE - 1)) for _ in range(10)]

renderer = GPURenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
clock = pygame.time.Clock()

running = True
simulation_speed = 1.0
world_scale = 1.0

avg_x = sum(w.x for w in worms) / len(worms) if worms else 0.0
avg_y = sum(w.y for w in worms) / len(worms) if worms else 0.0

camera_x = avg_x
camera_y = avg_y
zoom = 10.0

follow_index = 0
follow_mode = True
births_per_sec = 0.0
deaths_per_sec = 0.0

while running:

    frame_time = clock.get_time() / 1000.0
    if frame_time <= 0:
        frame_time = 1 / 60

    dt = frame_time * simulation_speed

    for event in pygame.event.get():
        if imgui_renderer:
            imgui_renderer.process_event(event)

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                simulation_speed = 0.5
            if event.key == pygame.K_2:
                simulation_speed = 1.0
            if event.key == pygame.K_3:
                simulation_speed = 2.0
            if event.key == pygame.K_4:
                simulation_speed = 5.0

            if event.key == pygame.K_w:
                camera_y += CAMERA_STEP / max(zoom, 0.001)
            if event.key == pygame.K_s:
                camera_y -= CAMERA_STEP / max(zoom, 0.001)
            if event.key == pygame.K_a:
                camera_x -= CAMERA_STEP / max(zoom, 0.001)
            if event.key == pygame.K_d:
                camera_x += CAMERA_STEP / max(zoom, 0.001)

            if event.key == pygame.K_q:
                zoom *= 1.1
            if event.key == pygame.K_e:
                zoom /= 1.1

            zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))

            if event.key == pygame.K_f:
                follow_mode = not follow_mode
            if event.key == pygame.K_TAB and worms:
                follow_index = (follow_index + 1) % len(worms)

    world.update(dt)

    pre_count = len(worms)
    new_worms = []
    survivors = [w for w in worms if w.update(world, dt, new_worms)]
    births = len(new_worms)
    deaths = max(0, pre_count - len(survivors))
    worms = survivors
    worms.extend(new_worms)

    instant_births = births / max(dt, 1e-6)
    instant_deaths = deaths / max(dt, 1e-6)
    births_per_sec = births_per_sec * 0.9 + instant_births * 0.1
    deaths_per_sec = deaths_per_sec * 0.9 + instant_deaths * 0.1

    for worm in worms:
        if len(worm.body) == 0:
            continue

        hx, hy = worm.body[0]
        if (not np.isfinite(hx)) or (not np.isfinite(hy)) or abs(hx) > WORLD_SIZE * 3 or abs(hy) > WORLD_SIZE * 3:
            worm.x = WORLD_SIZE / 2
            worm.y = WORLD_SIZE / 2
            worm.body = [(worm.x, worm.y) for _ in range(SEGMENTS)]
            worm.vel = [(0.0, 0.0) for _ in range(SEGMENTS)]

    if follow_mode and worms:
        target = worms[follow_index % len(worms)]
        camera_x = target.x
        camera_y = target.y

    camera_x = max(0.0, min(camera_x, float(WORLD_SIZE)))
    camera_y = max(0.0, min(camera_y, float(WORLD_SIZE)))

    worm_strips = []
    head_positions = []

    for worm in worms:
        strip = []
        for p in worm.smooth_body():
            x = (p[0] / WORLD_SIZE) * world_scale
            y = (p[1] / WORLD_SIZE) * world_scale
            strip.append([x, y])
        if strip:
            energy = worm.energy
            if energy < 60.0:
                t = max(0.0, min(energy / 60.0, 1.0))
                color = (1.0, 0.2 + 0.8 * t, 0.2 + 0.8 * t)
            elif energy > 140.0:
                t = max(0.0, min((energy - 140.0) / 120.0, 1.0))
                color = (1.0 - 0.6 * t, 1.0 - 0.3 * t, 1.0)
            else:
                color = (1.0, 1.0, 1.0)

            worm_strips.append((np.array(strip, dtype="f4"), color))
            head_positions.append(strip[0])

    food_low = []
    food_mid = []
    food_high = []
    chem_buckets = [[] for _ in range(5)]
    pheromone_positions = []

    for x in range(WORLD_SIZE):
        for y in range(WORLD_SIZE):
            gx = (x / WORLD_SIZE) * world_scale
            gy = (y / WORLD_SIZE) * world_scale

            food_value = world.food_grid[x, y]
            if food_value > 5.0 and random.random() < 0.18:
                food_high.append([gx, gy])
            elif food_value > 1.0 and random.random() < 0.12:
                food_mid.append([gx, gy])
            elif food_value > 0.2 and random.random() < 0.06:
                food_low.append([gx, gy])

    pheromone_grid_size = world.pheromone.shape[0]
    for px in range(pheromone_grid_size):
        for py in range(pheromone_grid_size):
            pv = world.pheromone[px, py]
            if pv > 0.1 and random.random() < 0.18:
                gx = (px / pheromone_grid_size) * world_scale
                gy = (py / pheromone_grid_size) * world_scale
                pheromone_positions.append([gx, gy])

    chem_grid_size = world.chem.shape[0]
    for cx in range(chem_grid_size):
        for cy in range(chem_grid_size):
            chem_value = world.chem[cx, cy]
            gx = (cx / chem_grid_size) * world_scale
            gy = (cy / chem_grid_size) * world_scale

            if chem_value > 0.1 and random.random() < 0.25:
                intensity = min(chem_value / 100.0, 1.0)
                bucket = min(int(intensity * len(chem_buckets)), len(chem_buckets) - 1)
                chem_buckets[bucket].append([gx, gy])

    food_layers = [
        (
            np.array(food_low, dtype="f4") if food_low else np.empty((0, 2), dtype="f4"),
            (0.1, 0.45, 0.1),
        ),
        (
            np.array(food_mid, dtype="f4") if food_mid else np.empty((0, 2), dtype="f4"),
            (0.15, 0.7, 0.15),
        ),
        (
            np.array(food_high, dtype="f4") if food_high else np.empty((0, 2), dtype="f4"),
            (0.25, 1.0, 0.25),
        ),
    ]

    chemical_layers = []
    for i, bucket in enumerate(chem_buckets, start=1):
        intensity = i / len(chem_buckets)
        vertices = np.array(bucket, dtype="f4") if bucket else np.empty((0, 2), dtype="f4")
        chemical_layers.append((vertices, (0.0, intensity, 0.0)))

    pheromone_positions = (
        np.array(pheromone_positions, dtype="f4") if pheromone_positions else np.empty((0, 2), dtype="f4")
    )
    head_positions = np.array(head_positions, dtype="f4") if head_positions else np.empty((0, 2), dtype="f4")

    renderer.render(
        worm_strips,
        pheromone_positions,
        food_layers,
        chemical_layers,
        head_positions,
        (camera_x / WORLD_SIZE) * world_scale,
        (camera_y / WORLD_SIZE) * world_scale,
        zoom,
    )

    avg_energy = (sum(w.energy for w in worms) / len(worms)) if worms else 0.0
    total_food = float(np.sum(world.food))
    total_pheromone = float(np.sum(world.pheromone))

    if imgui_renderer:
        imgui_renderer.process_inputs()
        imgui.new_frame()
        imgui.begin("Simulation")
        imgui.text(f"Worms: {len(worms)}")
        imgui.text(f"Avg Energy: {avg_energy:.1f}")
        imgui.text(f"Food Total: {total_food:.1f}")
        imgui.text(f"Pheromone Total: {total_pheromone:.1f}")
        imgui.text(f"Births/s: {births_per_sec:.2f}")
        imgui.text(f"Deaths/s: {deaths_per_sec:.2f}")
        imgui.text(f"Speed: {simulation_speed:.1f}x")
        imgui.text(f"Zoom: {zoom:.2f}")
        imgui.text(f"Follow: {'ON' if follow_mode else 'OFF'}")
        imgui.end()
        imgui.render()
        imgui_renderer.render(imgui.get_draw_data())
    else:
        pygame.display.set_caption(
            f"Worm Simulator GPU | Worms:{len(worms)} AvgEnergy:{avg_energy:.1f} "
            f"Food:{total_food:.0f} Phero:{total_pheromone:.0f} "
            f"B/s:{births_per_sec:.2f} D/s:{deaths_per_sec:.2f} "
            f"Speed:{simulation_speed:.1f}x Zoom:{zoom:.2f}"
        )

    pygame.display.flip()
    clock.tick(60)

if imgui_renderer:
    imgui_renderer.shutdown()
pygame.quit()
