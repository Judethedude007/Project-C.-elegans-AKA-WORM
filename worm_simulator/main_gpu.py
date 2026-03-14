import random
import math
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
from worm import Worm, Egg, SEGMENTS, SEGMENT_LENGTH
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_SIZE, INITIAL_WORMS, MAX_WORMS
from gpu_renderer import GPURenderer

ZOOM_MIN = 0.5
ZOOM_MAX = 20.0
CAMERA_STEP = 12.0
WORM_THICKNESS_SCALE = 2.0 / 3.0
TARGET_FPS = 60

pygame.init()

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE,
    vsync=1,
)
pygame.display.set_caption("Worm Simulator GPU")

if IMGUI_AVAILABLE:
    imgui.create_context()
    imgui_renderer = PygameRenderer()
else:
    imgui_renderer = None

world = World()
worms = []
for _ in range(INITIAL_WORMS):
    patch = random.choice(world.food_patches)
    x = patch["x"] + random.uniform(-15.0, 15.0)
    y = patch["y"] + random.uniform(-15.0, 15.0)
    x = max(0.0, min(x, WORLD_SIZE - 1.0))
    y = max(0.0, min(y, WORLD_SIZE - 1.0))
    worms.append(Worm(x, y, inherited_genes={"generation": 0}))
eggs = []

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
total_births = 0
total_deaths = 0
max_generation = 0
view_mode = 0


def split_by_gap(points, max_gap):
    strips = []
    current_strip = []
    prev = None

    for p in points:
        if prev is not None:
            dx = p[0] - prev[0]
            dy = p[1] - prev[1]
            if math.sqrt(dx * dx + dy * dy) > max_gap:
                if len(current_strip) >= 2:
                    strips.append(current_strip)
                current_strip = []

        current_strip.append(p)
        prev = p

    if len(current_strip) >= 2:
        strips.append(current_strip)

    return strips


def build_tapered_mesh(points, base_width):
    n = len(points)
    if n < 2:
        return np.empty((0, 2), dtype="f4")

    mesh = []
    denom = max(1, n - 1)

    for i, p in enumerate(points):
        if i == 0:
            tx = points[1][0] - p[0]
            ty = points[1][1] - p[1]
        elif i == n - 1:
            tx = p[0] - points[i - 1][0]
            ty = p[1] - points[i - 1][1]
        else:
            tx = points[i + 1][0] - points[i - 1][0]
            ty = points[i + 1][1] - points[i - 1][1]

        tlen = math.sqrt(tx * tx + ty * ty)
        if tlen < 1e-9:
            continue

        nx = -ty / tlen
        ny = tx / tlen

        u = i / float(denom)
        width_profile = 1.0 - abs(u - 0.5) * 1.5
        width_profile = max(0.22, width_profile)
        width = base_width * width_profile

        mesh.append((p[0] + nx * width, p[1] + ny * width))
        mesh.append((p[0] - nx * width, p[1] - ny * width))

    return np.array(mesh, dtype="f4") if mesh else np.empty((0, 2), dtype="f4")

while running:

    dt = clock.tick(TARGET_FPS) / 1000.0
    if dt <= 0:
        dt = 1.0 / TARGET_FPS
    dt *= simulation_speed

    for event in pygame.event.get():
        if imgui_renderer:
            imgui_renderer.process_event(event)

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                view_mode = 0
            if event.key == pygame.K_2:
                view_mode = 1
            if event.key == pygame.K_3:
                view_mode = 2
            if event.key == pygame.K_4:
                simulation_speed = 0.5
            if event.key == pygame.K_5:
                simulation_speed = 1.0
            if event.key == pygame.K_6:
                simulation_speed = 2.0
            if event.key == pygame.K_7:
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
            plus_keys = (pygame.K_EQUALS, getattr(pygame, "K_PLUS", pygame.K_EQUALS), pygame.K_KP_PLUS)
            if event.key in plus_keys:
                zoom *= 1.1
            minus_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
            if event.key in minus_keys:
                zoom /= 1.1

            zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))

            if event.key == pygame.K_f:
                follow_mode = not follow_mode
            if event.key == pygame.K_TAB and worms:
                follow_index = (follow_index + 1) % len(worms)

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= 1.1
            elif event.y < 0:
                zoom /= 1.1
            zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))

    world.update(dt)
    world.set_worm_positions(worms)

    pre_count = len(worms)
    new_worms = []
    new_eggs = []
    worms = [w for w in worms if w.update(world, dt, new_worms, new_eggs)]
    eggs.extend(new_eggs)

    hatched_worms = []
    active_eggs = []
    for egg in eggs:
        if egg.update(dt):
            larva = Worm(
                egg.x,
                egg.y,
                inherited_expression=egg.inherited_expression,
                inherited_genes=getattr(egg, "inherited_genome", getattr(egg, "inherited_genes", None)),
            )
            larva.size = 0.3
            larva.energy = 40
            larva.age = 0
            larva.stage = "juvenile"
            larva.generation = int(getattr(egg, "generation", 0))
            larva.lineage_id = int(getattr(egg, "lineage_id", getattr(larva, "lineage_id", 0)))
            larva.color = larva._lineage_color(larva.lineage_id)
            hatched_worms.append(larva)
        else:
            active_eggs.append(egg)
    eggs = active_eggs

    births = len(hatched_worms)
    deaths = max(0, pre_count - len(worms))
    total_births += births
    total_deaths += deaths
    worms.extend(new_worms)
    worms.extend(hatched_worms)
    if len(worms) > MAX_WORMS:
        worms = worms[:MAX_WORMS]

    if worms:
        max_generation = max(max_generation, max(getattr(w, "generation", 0) for w in worms))
    if eggs:
        max_generation = max(max_generation, max(getattr(e, "generation", 0) for e in eggs))

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
        points = worm.body_points()
        if points:
            if getattr(worm, "dauer", False):
                color = (0.35, 0.55, 1.0)
            else:
                color = tuple(getattr(worm, "color", (0.8, 0.8, 0.8)))

            max_gap = SEGMENT_LENGTH * 2.0
            strips = split_by_gap(points, max_gap)

            for strip in strips:
                strip_norm = [
                    ((p[0] / WORLD_SIZE) * world_scale, (p[1] / WORLD_SIZE) * world_scale)
                    for p in strip
                ]

                base_width_world = max(0.6, SEGMENT_LENGTH * max(worm.size, 0.2) * 0.6 * WORM_THICKNESS_SCALE)
                base_width_norm = (base_width_world / WORLD_SIZE) * world_scale
                mesh = build_tapered_mesh(strip_norm, base_width_norm)
                if len(mesh) >= 4:
                    worm_strips.append((mesh, color, "triangle_strip"))
                else:
                    worm_strips.append((np.array(strip_norm, dtype="f4"), color, "line_strip"))

            if strips:
                head_positions.append(
                    [
                        (strips[0][0][0] / WORLD_SIZE) * world_scale,
                        (strips[0][0][1] / WORLD_SIZE) * world_scale,
                    ]
                )

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
            if food_value > 0.7 and random.random() < 0.18:
                food_high.append([gx, gy])
            elif food_value > 0.3 and random.random() < 0.12:
                food_mid.append([gx, gy])
            elif food_value > 0.08 and random.random() < 0.06:
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

    empty_points = np.empty((0, 2), dtype="f4")

    if view_mode == 0:
        render_worm_strips = worm_strips
        render_food_layers = food_layers
        render_chemical_layers = []
        render_pheromone_positions = empty_points
        render_head_positions = head_positions
    elif view_mode == 1:
        render_worm_strips = []
        render_food_layers = []
        render_chemical_layers = chemical_layers
        render_pheromone_positions = empty_points
        render_head_positions = empty_points
    else:
        render_worm_strips = []
        render_food_layers = []
        render_chemical_layers = []
        render_pheromone_positions = pheromone_positions
        render_head_positions = empty_points

    renderer.render(
        render_worm_strips,
        render_pheromone_positions,
        render_food_layers,
        render_chemical_layers,
        render_head_positions,
        (camera_x / WORLD_SIZE) * world_scale,
        (camera_y / WORLD_SIZE) * world_scale,
        zoom,
    )

    if view_mode == 0:
        camera_norm_x = (camera_x / WORLD_SIZE) * world_scale
        camera_norm_y = (camera_y / WORLD_SIZE) * world_scale
        for worm in worms:
            if not worm.body:
                continue

            hx, hy = worm.body[0]
            head_x = (hx / WORLD_SIZE) * world_scale
            head_y = (hy / WORLD_SIZE) * world_scale

            clip_x = (head_x - camera_norm_x) * zoom
            clip_y = (head_y - camera_norm_y) * zoom

            hx = (clip_x * 0.5 + 0.5) * SCREEN_WIDTH
            hy = (0.5 - clip_y * 0.5) * SCREEN_HEIGHT
            radius = max(3, int(4 * zoom))

            if 0 <= hx < SCREEN_WIDTH and 0 <= hy < SCREEN_HEIGHT:
                # draw worm head
                pygame.draw.circle(
                    screen,
                    (255, 120, 120),
                    (int(hx), int(hy)),
                    radius,
                )

        # draw eggs as small red circles
        for egg in eggs:
            egg_norm_x = (egg.x / WORLD_SIZE) * world_scale
            egg_norm_y = (egg.y / WORLD_SIZE) * world_scale
            clip_x = (egg_norm_x - camera_norm_x) * zoom
            clip_y = (egg_norm_y - camera_norm_y) * zoom
            sx = (clip_x * 0.5 + 0.5) * SCREEN_WIDTH
            sy = (0.5 - clip_y * 0.5) * SCREEN_HEIGHT
            if 0 <= sx < SCREEN_WIDTH and 0 <= sy < SCREEN_HEIGHT:
                pygame.draw.circle(screen, (255, 80, 80), (int(sx), int(sy)), 2)

    avg_energy = (sum(w.energy for w in worms) / len(worms)) if worms else 0.0
    total_food = float(np.sum(world.food))
    total_pheromone = float(np.sum(world.pheromone))
    lineage_counts = {}
    for worm in worms:
        lineage_id = int(getattr(worm, "lineage_id", -1))
        lineage_counts[lineage_id] = lineage_counts.get(lineage_id, 0) + 1
    total_lineages = len(lineage_counts)
    dominant_lineage = max(lineage_counts, key=lineage_counts.get) if lineage_counts else -1
    largest_colony = max(lineage_counts.values()) if lineage_counts else 0

    if imgui_renderer:
        imgui_renderer.process_inputs()
        imgui.new_frame()
        imgui.begin("Simulation")
        imgui.text(f"Worms: {len(worms)}")
        imgui.text(f"Eggs: {len(eggs)}")
        imgui.text(f"Generation: {max_generation}")
        imgui.text(f"Births: {total_births}")
        imgui.text(f"Deaths: {total_deaths}")
        imgui.text(f"Avg Energy: {avg_energy:.1f}")
        imgui.text(f"Food Total: {total_food:.1f}")
        imgui.text(f"Pheromone Total: {total_pheromone:.1f}")
        imgui.text(f"Births/s: {births_per_sec:.2f}")
        imgui.text(f"Deaths/s: {deaths_per_sec:.2f}")
        imgui.text(f"Dominant lineage: {dominant_lineage}")
        imgui.text(f"Largest colony: {largest_colony} worms")
        imgui.text(f"Total lineages: {total_lineages}")
        imgui.text(f"Speed: {simulation_speed:.1f}x")
        imgui.text(f"View: {view_mode} (1:Eco 2:Chem 3:Phero)")
        imgui.text(f"Zoom: {zoom:.2f}")
        imgui.text(f"Follow: {'ON' if follow_mode else 'OFF'}")
        imgui.end()
        imgui.render()
        imgui_renderer.render(imgui.get_draw_data())
    else:
        pygame.display.set_caption(
            f"Worm Simulator GPU | Worms:{len(worms)} Eggs:{len(eggs)} Gen:{max_generation} "
            f"Births:{total_births} Deaths:{total_deaths} AvgEnergy:{avg_energy:.1f} "
            f"Food:{total_food:.0f} Phero:{total_pheromone:.0f} "
            f"B/s:{births_per_sec:.2f} D/s:{deaths_per_sec:.2f} "
            f"DomLineage:{dominant_lineage} Largest:{largest_colony} Lineages:{total_lineages} "
            f"Speed:{simulation_speed:.1f}x View:{view_mode} Zoom:{zoom:.2f}"
        )

    pygame.display.flip()

if imgui_renderer:
    imgui_renderer.shutdown()
pygame.quit()
