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

from world import World, GRID_SIZE
from worm import Worm, Egg, SEGMENTS, SEGMENT_LENGTH
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WORLD_SIZE,
    INITIAL_WORMS,
    MAX_WORMS,
    TEMPERATURE,
    WATER_LEVEL,
    OXYGEN_LEVEL,
    FOOD_GROWTH_RATE,
    MUTATION_RATE,
    SEASON_SPEED,
)
from gpu_renderer import GPURenderer

ZOOM_MIN = 1.0
ZOOM_MAX = 20.0
DEFAULT_ZOOM = 2.0
WORM_THICKNESS_SCALE = 2.0
TARGET_FPS = 60
FIXED_DT = 1.0 / 60.0
RENDER_GRID_STEP = 4
DEBUG_VISIBILITY_LOG_INTERVAL = 1.0
CAMERA_SMOOTHING = 0.05
TRAIL_STEPS = 28
UI_WIDTH = 320
WINDOW_WIDTH = SCREEN_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT
CAMERA_MODE_FREE = 0
CAMERA_MODE_DOMINANT = 1

pygame.init()
display_flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), display_flags, vsync=1)
pygame.display.set_caption("Worm Simulator GPU")
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 20)
fullscreen = False
screen_width, screen_height = screen.get_size()
world_view_width = max(1, screen_width - UI_WIDTH)
world_surface = pygame.Surface((world_view_width, screen_height), flags=pygame.SRCALPHA)
ui_surface = pygame.Surface((UI_WIDTH, screen_height), flags=pygame.SRCALPHA)

if IMGUI_AVAILABLE:
    imgui.create_context()
    imgui_renderer = PygameRenderer()
else:
    imgui_renderer = None


class Slider:

    def __init__(self, x, y, width, min_val, max_val, value, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min = float(min_val)
        self.max = float(max_val)
        self.value = float(value)
        self.label = label
        self.dragging = False

    def _set_from_x(self, x):
        local = max(0.0, min(float(self.rect.width), float(x - self.rect.x)))
        ratio = local / max(1.0, float(self.rect.width))
        self.value = self.min + (self.max - self.min) * ratio

    def handle_event(self, event, local_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(local_pos):
                self.dragging = True
                self._set_from_x(local_pos[0])
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(local_pos[0])
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self.dragging
            self.dragging = False
            if was_dragging:
                self._set_from_x(local_pos[0])
                return True
        return False

    def draw(self, surface, title_font, value_font):
        pygame.draw.rect(surface, (60, 60, 70), self.rect, border_radius=6)
        ratio = 0.0
        if self.max > self.min:
            ratio = (self.value - self.min) / (self.max - self.min)
        ratio = max(0.0, min(1.0, ratio))
        knob_x = self.rect.x + int(ratio * self.rect.width)
        pygame.draw.circle(surface, (210, 210, 210), (knob_x, self.rect.y + self.rect.height // 2), 8)
        text = value_font.render(f"{self.label}: {self.value:.4f}" if self.max <= 0.02 else f"{self.label}: {self.value:.2f}", True, (225, 225, 225))
        surface.blit(text, (self.rect.x, self.rect.y - 20))


def create_render_surfaces(view_width, view_height):
    world_surf = pygame.Surface((max(1, view_width), max(1, view_height)), flags=pygame.SRCALPHA)
    ui_surf = pygame.Surface((UI_WIDTH, max(1, view_height)), flags=pygame.SRCALPHA)
    return world_surf, ui_surf


def apply_world_controls(world_obj, sliders):
    world_obj.set_environment_controls(
        temperature=sliders["temperature"].value,
        water_level=sliders["water"].value,
        oxygen_level=sliders["oxygen"].value,
        food_growth_rate=sliders["food_growth"].value,
        mutation_rate=sliders["mutation"].value,
        season_speed=sliders["season_speed"].value,
    )


world = World()
worms = []
eggs = []

control_sliders = {
    "temperature": Slider(20, 80, 250, 0.5, 2.0, TEMPERATURE, "Temperature"),
    "water": Slider(20, 140, 250, 0.2, 2.0, WATER_LEVEL, "Water"),
    "oxygen": Slider(20, 200, 250, 0.2, 2.0, OXYGEN_LEVEL, "Oxygen"),
    "food_growth": Slider(20, 260, 250, 0.0001, 0.01, FOOD_GROWTH_RATE, "Food Growth"),
    "mutation": Slider(20, 320, 250, 0.0, 0.1, MUTATION_RATE, "Mutation"),
    "season_speed": Slider(20, 380, 250, 0.00005, 0.01, SEASON_SPEED, "Season Speed"),
    "sim_speed": Slider(20, 440, 250, 0.25, 8.0, 1.0, "Sim Speed"),
}
apply_world_controls(world, control_sliders)

renderer = GPURenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
renderer.ctx.viewport = (0, 0, world_view_width, screen_height)
clock = pygame.time.Clock()
accumulator = 0.0

running = True
simulation_speed = 1.0
world_scale = 1.0

avg_x = sum(w.x for w in worms) / len(worms) if worms else 0.0
avg_y = sum(w.y for w in worms) / len(worms) if worms else 0.0

camera_x = avg_x
camera_y = avg_y
zoom = DEFAULT_ZOOM

camera_mode = CAMERA_MODE_DOMINANT
births_per_sec = 0.0
deaths_per_sec = 0.0
total_births = 0
total_deaths = 0
max_generation = 0
view_mode = 0
debug_log_timer = 0.0


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
        head_bulge = 0.18 * math.exp(-8.0 * u)
        body_taper = 1.0 - 0.82 * (u ** 0.9)
        width_profile = max(0.16, body_taper + head_bulge)
        width = base_width * width_profile

        mesh.append((p[0] + nx * width, p[1] + ny * width))
        mesh.append((p[0] - nx * width, p[1] - ny * width))

    return np.array(mesh, dtype="f4") if mesh else np.empty((0, 2), dtype="f4")


def spawn_worm_near_food():
    spawn_center_x = float(getattr(world, "food_center_x", WORLD_SIZE * 0.5))
    spawn_center_y = float(getattr(world, "food_center_y", WORLD_SIZE * 0.5))
    x = spawn_center_x + random.uniform(-20.0, 20.0)
    y = spawn_center_y + random.uniform(-20.0, 20.0)
    x = max(0.0, min(x, WORLD_SIZE - 1.0))
    y = max(0.0, min(y, WORLD_SIZE - 1.0))
    return Worm(x, y, inherited_genes={"generation": 0})


def toggle_fullscreen_state(current_fullscreen):
    next_fullscreen = not current_fullscreen
    flags = display_flags | (pygame.FULLSCREEN if next_fullscreen else 0)
    size = (0, 0) if next_fullscreen else (SCREEN_WIDTH, SCREEN_HEIGHT)
    new_screen = pygame.display.set_mode(size, flags, vsync=1)
    new_width, new_height = new_screen.get_size()
    new_world_width = max(1, new_width - UI_WIDTH)
    return next_fullscreen, new_screen, new_width, new_height, new_world_width


def world_to_screen(world_x, world_y, camera_x, camera_y, zoom, view_width, view_height):
    camera_norm_x = (camera_x / WORLD_SIZE) * world_scale
    camera_norm_y = (camera_y / WORLD_SIZE) * world_scale
    norm_x = (world_x / WORLD_SIZE) * world_scale
    norm_y = (world_y / WORLD_SIZE) * world_scale
    clip_x = (norm_x - camera_norm_x) * zoom
    clip_y = (norm_y - camera_norm_y) * zoom
    screen_x = (clip_x * 0.5 + 0.5) * view_width
    screen_y = (0.5 - clip_y * 0.5) * view_height
    return screen_x, screen_y


for _ in range(INITIAL_WORMS):
    worms.append(spawn_worm_near_food())

if worms:
    camera_x = sum(w.x for w in worms) / len(worms)
    camera_y = sum(w.y for w in worms) / len(worms)

while running:

    simulation_speed = control_sliders["sim_speed"].value
    frame_time = clock.tick(TARGET_FPS) / 1000.0
    if frame_time <= 0.0:
        frame_time = FIXED_DT
    frame_time = min(frame_time, 0.25)
    accumulator += frame_time * simulation_speed

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
                control_sliders["sim_speed"].value = simulation_speed
            if event.key == pygame.K_5:
                simulation_speed = 1.0
                control_sliders["sim_speed"].value = simulation_speed
            if event.key == pygame.K_6:
                simulation_speed = 2.0
                control_sliders["sim_speed"].value = simulation_speed
            if event.key == pygame.K_7:
                simulation_speed = 5.0
                control_sliders["sim_speed"].value = simulation_speed

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
                fullscreen, screen, screen_width, screen_height, world_view_width = toggle_fullscreen_state(fullscreen)
                renderer.ctx.viewport = (0, 0, world_view_width, screen_height)
                world_surface, ui_surface = create_render_surfaces(world_view_width, screen_height)
            if event.key == pygame.K_c:
                if camera_mode == CAMERA_MODE_FREE:
                    camera_mode = CAMERA_MODE_DOMINANT
                else:
                    camera_mode = CAMERA_MODE_FREE

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if event.type == pygame.MOUSEMOTION:
                event_pos = event.pos
            else:
                event_pos = getattr(event, "pos", pygame.mouse.get_pos())
            local_pos = (event_pos[0] - world_view_width, event_pos[1])
            if local_pos[0] >= 0:
                slider_changed = False
                for slider in control_sliders.values():
                    if slider.handle_event(event, local_pos):
                        slider_changed = True
                if slider_changed:
                    simulation_speed = control_sliders["sim_speed"].value
                    apply_world_controls(world, control_sliders)

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= 1.1
            elif event.y < 0:
                zoom /= 1.1
            zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))

    simulation_speed = control_sliders["sim_speed"].value
    apply_world_controls(world, control_sliders)

    keys = pygame.key.get_pressed()
    cam_speed = 10.0 / max(zoom, 1e-3)
    if camera_mode == CAMERA_MODE_FREE:
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            camera_x -= cam_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            camera_x += cam_speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            camera_y -= cam_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            camera_y += cam_speed

    births = 0
    deaths = 0

    while accumulator >= FIXED_DT:
        active_chunks = world.get_active_chunks_near_worms(worms, radius_chunks=2)
        world.update(FIXED_DT, active_chunks=active_chunks)
        world.set_worm_positions(worms)

        pre_count = len(worms)
        new_worms = []
        new_eggs = []
        active_worms = []
        for worm in worms:
            if worm.update(world, FIXED_DT, new_worms, new_eggs, worms):
                active_worms.append(worm)
        worms = active_worms
        eggs.extend(new_eggs)

        hatched_worms = []
        active_eggs = []
        for egg in eggs:
            if egg.update(FIXED_DT):
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
                larva._refresh_visual_color()
                hatched_worms.append(larva)
            else:
                active_eggs.append(egg)
        eggs = active_eggs

        step_births = len(hatched_worms)
        step_deaths = max(0, pre_count - len(worms))
        births += step_births
        deaths += step_deaths
        total_births += step_births
        total_deaths += step_deaths

        worms.extend(new_worms)
        worms.extend(hatched_worms)
        if len(worms) > MAX_WORMS:
            worms = worms[:MAX_WORMS]

        if worms:
            max_generation = max(max_generation, max(getattr(w, "generation", 0) for w in worms))
        if eggs:
            max_generation = max(max_generation, max(getattr(e, "generation", 0) for e in eggs))

        accumulator -= FIXED_DT

    instant_births = births / max(frame_time, 1e-6)
    instant_deaths = deaths / max(frame_time, 1e-6)
    births_per_sec = births_per_sec * 0.9 + instant_births * 0.1
    deaths_per_sec = deaths_per_sec * 0.9 + instant_deaths * 0.1

    if len(worms) == 0:
        for _ in range(2):
            worms.append(spawn_worm_near_food())
        if worms:
            camera_x = sum(w.x for w in worms) / len(worms)
            camera_y = sum(w.y for w in worms) / len(worms)

    debug_log_timer += frame_time
    if debug_log_timer >= DEBUG_VISIBILITY_LOG_INTERVAL:
        print(f"worms: {len(worms)} zoom: {zoom:.2f}")
        debug_log_timer = 0.0

    for worm in worms:
        if len(worm.body) == 0:
            continue

        hx, hy = worm.body[0]
        if (not np.isfinite(hx)) or (not np.isfinite(hy)) or abs(hx) > WORLD_SIZE * 3 or abs(hy) > WORLD_SIZE * 3:
            worm.x = WORLD_SIZE / 2
            worm.y = WORLD_SIZE / 2
            worm.body = [(worm.x, worm.y) for _ in range(SEGMENTS)]
            worm.vel = [(0.0, 0.0) for _ in range(SEGMENTS)]

    if worms and camera_mode == CAMERA_MODE_DOMINANT:
        lineage_centers = {}
        for worm in worms:
            lineage_id = int(getattr(worm, "lineage_id", -1))
            if lineage_id not in lineage_centers:
                lineage_centers[lineage_id] = [0.0, 0.0, 0]
            lineage_centers[lineage_id][0] += float(worm.x)
            lineage_centers[lineage_id][1] += float(worm.y)
            lineage_centers[lineage_id][2] += 1

        dominant_data = max(lineage_centers.values(), key=lambda item: item[2])
        target_x = dominant_data[0] / max(1, dominant_data[2])
        target_y = dominant_data[1] / max(1, dominant_data[2])
        camera_x += (target_x - camera_x) * CAMERA_SMOOTHING
        camera_y += (target_y - camera_y) * CAMERA_SMOOTHING

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

                zoom_visibility_boost = max(1.0, 2.0 / max(zoom, 1e-3))
                base_width_world = max(
                    2.0,
                    SEGMENT_LENGTH * max(worm.size, 0.2) * WORM_THICKNESS_SCALE * zoom_visibility_boost,
                )
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

    for x in range(0, GRID_SIZE, 1):
        for y in range(0, GRID_SIZE, 1):
            gx = ((x + 0.5) / GRID_SIZE) * world_scale
            gy = ((y + 0.5) / GRID_SIZE) * world_scale

            food_value = world.food[x, y]
            if food_value > 0.7:
                food_high.append([gx, gy])
            elif food_value > 0.3:
                food_mid.append([gx, gy])
            elif food_value > 0.05:
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

    world_surface.fill((0, 0, 0, 0))
    if view_mode == 0:
        cell_px_w = max(1, int((world_view_width * zoom) / (2.0 * GRID_SIZE)))
        cell_px_h = max(1, int((screen_height * zoom) / (2.0 * GRID_SIZE)))

        for fx in range(GRID_SIZE):
            for fy in range(GRID_SIZE):
                center_x = ((fx + 0.5) / GRID_SIZE) * WORLD_SIZE
                center_y = ((fy + 0.5) / GRID_SIZE) * WORLD_SIZE
                sx, sy = world_to_screen(center_x, center_y, camera_x, camera_y, zoom, world_view_width, screen_height)

                if sx < -cell_px_w or sx > world_view_width + cell_px_w or sy < -cell_px_h or sy > screen_height + cell_px_h:
                    continue

                food_value = float(world.food[fx, fy])
                if food_value > 0.005:
                    intensity = min(255, int(food_value * 255.0))
                    bacteria_color = (0, max(20, intensity), 0)
                    ix = int(sx)
                    iy = int(sy)
                    if 0 <= ix < world_view_width and 0 <= iy < screen_height:
                        world_surface.set_at((ix, iy), bacteria_color)
                    if intensity > 120:
                        pygame.draw.circle(world_surface, (0, intensity // 3, 0), (int(sx), int(sy)), 2)

                pheromone_value = float(world.pheromone[fx, fy])
                if pheromone_value > 0.2:
                    blue = min(140, int(pheromone_value * 0.2))
                    pher_rect = pygame.Rect(
                        int(sx - cell_px_w * 0.5),
                        int(sy - cell_px_h * 0.5),
                        cell_px_w,
                        cell_px_h,
                    )
                    pygame.draw.rect(world_surface, (0, 0, blue), pher_rect)

        for worm in worms:
            points = worm.body_points()
            if len(points) < 2:
                continue

            worm_rgb = tuple(int(max(0.0, min(1.0, c)) * 255) for c in getattr(worm, "color", (0.8, 0.8, 0.8)))
            screen_points = []
            for px, py in points:
                sx, sy = world_to_screen(px, py, camera_x, camera_y, zoom, world_view_width, screen_height)
                screen_points.append((int(sx), int(sy)))

            point_count = len(screen_points)
            if point_count >= 2:
                for idx, (sx, sy) in enumerate(screen_points):
                    u = idx / float(max(1, point_count - 1))
                    radius = max(1, int((6.5 * (1.0 - u) + 1.2) * max(0.7, min(1.8, zoom))))
                    shade = 0.72 + 0.28 * (1.0 - u)
                    seg_color = (
                        min(255, int(worm_rgb[0] * shade)),
                        min(255, int(worm_rgb[1] * shade)),
                        min(255, int(worm_rgb[2] * shade)),
                    )
                    pygame.draw.circle(world_surface, (12, 12, 12), (sx, sy + 1), radius)
                    pygame.draw.circle(world_surface, seg_color, (sx, sy), radius)

                head_x, head_y = screen_points[0]
                if 0 <= head_x < world_view_width and 0 <= head_y < screen_height:
                    pygame.draw.circle(world_surface, (255, 255, 255), (head_x, head_y), 2)

        for egg in eggs:
            sx, sy = world_to_screen(egg.x, egg.y, camera_x, camera_y, zoom, world_view_width, screen_height)
            if 0 <= sx < world_view_width and 0 <= sy < screen_height:
                pygame.draw.circle(world_surface, (255, 90, 90), (int(sx), int(sy)), 2)

    screen.blit(world_surface, (0, 0))

    avg_energy = (sum(w.energy for w in worms) / len(worms)) if worms else 0.0
    total_food = float(np.sum(world.food))
    total_pheromone = float(np.sum(world.pheromone))
    food_density = total_food / float(GRID_SIZE * GRID_SIZE)
    pheromone_density = total_pheromone / float(GRID_SIZE * GRID_SIZE)
    lineage_counts = {}
    for worm in worms:
        lineage_id = int(getattr(worm, "lineage_id", -1))
        lineage_counts[lineage_id] = lineage_counts.get(lineage_id, 0) + 1
    total_lineages = len(lineage_counts)
    dominant_lineage = max(lineage_counts, key=lineage_counts.get) if lineage_counts else -1
    largest_colony = max(lineage_counts.values()) if lineage_counts else 0

    ui_surface.fill((25, 25, 30))
    ui_surface.blit(font.render("Control Panel", True, (235, 235, 235)), (20, 12))
    ui_surface.blit(small_font.render("Environment Controls", True, (190, 210, 255)), (20, 44))

    for slider_key in ("temperature", "water", "oxygen", "food_growth", "mutation", "season_speed", "sim_speed"):
        control_sliders[slider_key].draw(ui_surface, font, small_font)

    stats = [
        f"Worms: {len(worms)}",
        f"Avg Energy: {avg_energy:.1f}",
        f"Births: {total_births}",
        f"Deaths: {total_deaths}",
        f"Lineages: {total_lineages}",
        f"Food Total: {total_food:.1f}",
        f"Season: {world.season_name}",
        f"Temperature: {world.temperature:.1f} C",
        f"Births/s: {births_per_sec:.2f}",
        f"Deaths/s: {deaths_per_sec:.2f}",
        f"Dominant lineage: {dominant_lineage}",
    ]

    y = 500
    ui_surface.blit(font.render("Simulation Stats", True, (190, 210, 255)), (20, y))
    y += 24
    for stat in stats:
        ui_surface.blit(small_font.render(stat, True, (230, 230, 230)), (20, y))
        y += 20

    camera_mode_name = "Free camera" if camera_mode == CAMERA_MODE_FREE else "Follow dominant lineage"
    y += 8
    for line in (
        f"Camera: {camera_mode_name}",
        f"View mode: {view_mode} (1/2/3)",
        "F fullscreen, C camera mode",
        "WASD/Arrows pan, Q/E zoom",
    ):
        ui_surface.blit(small_font.render(line, True, (190, 190, 200)), (20, y))
        y += 18

    screen.blit(ui_surface, (world_view_width, 0))
    pygame.draw.line(screen, (80, 80, 80), (world_view_width, 0), (world_view_width, screen_height), 2)

    pygame.display.set_caption(
        f"Worms:{len(worms)} Food:{total_food:.0f} Lineages:{total_lineages} "
        f"Gen:{max_generation} Season:{world.season_name}"
    )

    pygame.display.flip()

if imgui_renderer:
    imgui_renderer.shutdown()
pygame.quit()
