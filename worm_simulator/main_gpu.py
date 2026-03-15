import random
import math
import os
import shutil
import subprocess
import sys
import numpy as np
import pygame
import stats

# Evolution Dashboard toggle (must be global)
show_dashboard = False

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
from evolution_logger import EvolutionLogger

ZOOM_MIN = 1.0
ZOOM_MAX = 20.0
DEFAULT_ZOOM = 2.0
WORM_THICKNESS_SCALE = 2.0
TARGET_FPS = 60
FIXED_DT = 1.0 / 60.0
RENDER_GRID_STEP = 4
DEBUG_VISIBILITY_LOG_INTERVAL = 1.0
CAMERA_SMOOTHING = 0.1
TRAIL_STEPS = 28
UI_WIDTH = 320
WINDOW_WIDTH = SCREEN_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT
CAMERA_MODE_FREE = 0
CAMERA_MODE_DOMINANT = 1
MODE_ECOSYSTEM = "ecosystem"
MODE_OPENWORM = "openworm"

# Keep world rendering robust on Windows by defaulting to software 2D composition.
USE_OPENGL_WORLD = False

UI_MARGIN_X = 20
UI_SLIDER_WIDTH = 250
UI_SLIDER_STEP = 70
UI_SECTION_GAP = 30
UI_TITLE_STEP = 40
UI_BUTTON_STEP = 50
UI_SCROLL_SPEED = 40
LOG_INTERVAL_SECONDS = 2.0
RUNS_DIR_NAME = "runs"
UI_STATS_LINE_HEIGHT = 18
UI_HELP_LINE_HEIGHT = 17
UI_PANEL_BOTTOM_PADDING = 120
UI_STATS_COUNT = 32
UI_HELP_COUNT = 10
BACKGROUND_STAR_COUNT = 200
GRID_OVERLAY_STEP = 80
ENVIRONMENT_SLIDERS = ("temperature", "water", "oxygen", "food_growth")
EVOLUTION_SLIDERS = ("mutation",)
SIMULATION_SLIDERS = ("sim_speed", "season_speed")

pygame.init()
display_flags = pygame.DOUBLEBUF | pygame.HWSURFACE
if USE_OPENGL_WORLD:
    display_flags |= pygame.OPENGL
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), display_flags, vsync=1)
pygame.display.set_caption("Worm Simulator GPU")
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 20)
fullscreen = False
screen_width, screen_height = screen.get_size()
world_view_width = max(1, screen_width - UI_WIDTH)
world_surface = pygame.Surface((world_view_width, screen_height), flags=pygame.SRCALPHA)
ui_surface = pygame.Surface((UI_WIDTH, screen_height), flags=pygame.SRCALPHA)
show_ui = True

# Correct output folder path
OUTPUT_FOLDER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../openworm/output'))

SEASON_COLORS = {
    "Spring": (60, 200, 60),
    "Summer": (220, 220, 60),
    "Autumn": (255, 140, 40),
    "Winter": (80, 120, 255),
}

def open_output_folder():
    import os
    import sys
    import subprocess
    output_path = OUTPUT_FOLDER_PATH
    if sys.platform.startswith("win"):
        os.startfile(output_path)
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", output_path])
    else:
        subprocess.Popen(["xdg-open", output_path])

def generate_background_stars(width, height, count):
    stars = []
    for _ in range(count):
        stars.append((random.randint(0, max(0, width - 1)), random.randint(0, max(0, height - 1)), random.randint(30, 90)))
    return stars

background_stars = generate_background_stars(world_view_width, screen_height, BACKGROUND_STAR_COUNT)

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

class UIButton:
    def __init__(self, x, y, width, height, label, bg=(68, 68, 68)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.bg = bg  # background color (tuple)
    def configure(self, text=None, bg=None):
        if text is not None:
            self.label = text
        if bg is not None:
            self.bg = bg
    def draw(self, surface, text_font, selected=False):
        bg = self.bg
        border = (180, 195, 225) if selected else (100, 100, 115)
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=6)
        text = text_font.render(self.label, True, (235, 235, 235))
        surface.blit(text, (self.rect.x + 8, self.rect.y + 6))
    def hit(self, local_pos):
        return self.rect.collidepoint(local_pos)

# --- Climate Toggle Button (must be after UIButton class is fully defined) ---
def toggle_climate():
    world.climate_enabled = not world.climate_enabled
    if world.climate_enabled:
        climate_button.configure(
            text="Climate ON",
            bg=(59, 130, 246)  # blue
        )
    else:
        climate_button.configure(
            text="Enable Climate",
            bg=(68, 68, 68)  # gray
        )
climate_button = UIButton(20, 0, 250, 30, "Enable Climate", bg=(68, 68, 68))

# --- Scroll Bar Drawing Function ---
def draw_scroll_bar(surface, scroll_offset, max_scroll, panel_height, x, y, width, height):
    if max_scroll <= 0:
        return None  # No need for a scroll bar
    # Scroll bar background
    bar_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (60, 60, 60), bar_rect, border_radius=6)
    # Scroll thumb size and position
    visible_ratio = panel_height / (panel_height + max_scroll)
    thumb_height = max(30, int(height * visible_ratio))
    scroll_ratio = -scroll_offset / max_scroll if max_scroll > 0 else 0
    thumb_y = y + int((height - thumb_height) * scroll_ratio)
    thumb_rect = pygame.Rect(x, thumb_y, width, thumb_height)
    pygame.draw.rect(surface, (180, 180, 180), thumb_rect, border_radius=6)
    return thumb_rect

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

def get_active_slider_keys():
    keys = []
    if not section_collapsed["environment"]:
        keys.extend(ENVIRONMENT_SLIDERS)
    if not section_collapsed["evolution"]:
        keys.extend(EVOLUTION_SLIDERS)
    if not section_collapsed["simulation"]:
        keys.extend(SIMULATION_SLIDERS)
    return tuple(keys)

def update_ui_layout(scroll_offset):
    ui_y = 20 + scroll_offset
    mode_title_y = ui_y
    ui_y += UI_TITLE_STEP

    mode_buttons[MODE_ECOSYSTEM].rect.update(UI_MARGIN_X, ui_y, 130, 30)
    mode_buttons[MODE_OPENWORM].rect.update(UI_MARGIN_X + 140, ui_y, 130, 30)
    ui_y += UI_BUTTON_STEP

    section_buttons["environment"].rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 26)
    ui_y += UI_BUTTON_STEP

    if not section_collapsed["environment"]:
        for slider_key in ENVIRONMENT_SLIDERS:
            slider = control_sliders[slider_key]
            slider.rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 20)
            ui_y += UI_SLIDER_STEP
        ui_y += UI_SECTION_GAP

    section_buttons["evolution"].rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 26)
    ui_y += UI_BUTTON_STEP

    if not section_collapsed["evolution"]:
        for slider_key in EVOLUTION_SLIDERS:
            slider = control_sliders[slider_key]
            slider.rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 20)
            ui_y += UI_SLIDER_STEP
        ui_y += UI_SECTION_GAP

    section_buttons["simulation"].rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 26)
    ui_y += UI_BUTTON_STEP

    if not section_collapsed["simulation"]:
        for slider_key in SIMULATION_SLIDERS:
            slider = control_sliders[slider_key]
            slider.rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 20)
            ui_y += UI_SLIDER_STEP

        export_graph_button.rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 30)
        ui_y += UI_BUTTON_STEP
        ui_y += UI_SECTION_GAP

        # Place the climate button below the export graph button
        climate_button.rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 30)
        ui_y += UI_BUTTON_STEP
        # Add extra gap before the season speed slider
        ui_y += 32
        control_sliders["season_speed"].rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 20)
        ui_y += UI_SLIDER_STEP
        ui_y += UI_SECTION_GAP

    section_buttons["stats"].rect.update(UI_MARGIN_X, ui_y, UI_SLIDER_WIDTH, 26)
    ui_y += UI_BUTTON_STEP

    stats_y = ui_y

    if section_collapsed["stats"]:
        content_bottom = ui_y + UI_PANEL_BOTTOM_PADDING
    else:
        stats_height = 24 + UI_STATS_COUNT * UI_STATS_LINE_HEIGHT
        help_height = 4 + UI_HELP_COUNT * UI_HELP_LINE_HEIGHT
        content_bottom = stats_y + stats_height + help_height + UI_PANEL_BOTTOM_PADDING + 40  # Extra scrollable space

    return {
        "stats_y": stats_y,
        "mode_title_y": mode_title_y,
        "content_bottom": content_bottom,
        "scroll_offset": scroll_offset,
    }

world = World()
toggle_climate()
worms = []
eggs = []
simulation_mode = MODE_ECOSYSTEM
ui_scroll = 0
openworm_status = "OpenWorm not launched"
graph_status = "Graph export not started"
sim_time = 0.0
next_log_time = 0.0

mode_buttons = {
    MODE_ECOSYSTEM: UIButton(20, 52, 130, 30, "Ecosystem"),
    MODE_OPENWORM: UIButton(160, 52, 130, 30, "OpenWorm"),
}
export_graph_button = UIButton(20, 0, 250, 30, "Export Graph")
section_buttons = {
    "environment": UIButton(20, 0, 250, 26, "Environment v"),
    "evolution": UIButton(20, 0, 250, 26, "Evolution v"),
    "simulation": UIButton(20, 0, 250, 26, "Simulation v"),
    "stats": UIButton(20, 0, 250, 26, "Stats v"),
}
section_collapsed = {
    "environment": False,
    "evolution": False,
    "simulation": False,
    "stats": False,
}

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

runs_dir = os.path.join(os.path.dirname(__file__), RUNS_DIR_NAME)
evolution_logger = EvolutionLogger(runs_dir, flush_every=1)
graph_status = f"Logging to {os.path.basename(evolution_logger.csv_path)}"

renderer = GPURenderer(SCREEN_WIDTH, SCREEN_HEIGHT) if USE_OPENGL_WORLD else None
if renderer is not None:
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

scroll_dragging = False
scroll_drag_offset = 0

def spawn_initial_population(count=INITIAL_WORMS):
    worms.clear()
    eggs.clear()
    for _ in range(max(1, int(count))):
        worms.append(spawn_worm_near_food())

def switch_to_ecosystem():
    spawn_initial_population(INITIAL_WORMS)

def launch_openworm():
    root = os.path.dirname(os.path.dirname(__file__))
    openworm_root = os.path.join(root, "openworm")
    run_py = os.path.join(openworm_root, "run.py")
    run_cmd = os.path.join(openworm_root, "run.cmd")
    run_sh = os.path.join(openworm_root, "run.sh")
    fallback_py = os.path.join(openworm_root, "master_openworm.py")

    if not os.path.isdir(openworm_root):
        return False, f"OpenWorm folder not found: {openworm_root}"

    try:
        if os.path.exists(run_py):
            subprocess.Popen([sys.executable, run_py], cwd=openworm_root)
            return True, "OpenWorm launched via run.py"

        if os.name == "nt" and os.path.exists(run_cmd):
            if shutil.which("docker") is None:
                return False, "OpenWorm run.cmd requires Docker in PATH"
            subprocess.Popen(["cmd", "/c", run_cmd], cwd=openworm_root)
            return True, "OpenWorm launched via run.cmd"

        if os.path.exists(run_sh):
            if shutil.which("docker") is None:
                return False, "OpenWorm run.sh requires Docker in PATH"
            subprocess.Popen(["bash", run_sh], cwd=openworm_root)
            return True, "OpenWorm launched via run.sh"

        if os.path.exists(fallback_py):
            subprocess.Popen([sys.executable, fallback_py], cwd=openworm_root)
            return True, "OpenWorm launched via master_openworm.py"

        return False, f"OpenWorm runner not found in: {openworm_root}"
    except Exception as exc:
        return False, f"OpenWorm launch failed: {exc}"

def launch_graph_export(csv_path):
    plot_script = os.path.join(os.path.dirname(__file__), "plot_evolution.py")
    if not os.path.exists(plot_script):
        return False, f"Plot script missing: {plot_script}"
    if not csv_path or not os.path.exists(csv_path):
        return False, "No evolution CSV available to plot"

    try:
        subprocess.Popen([sys.executable, plot_script, csv_path], cwd=os.path.dirname(plot_script))
        return True, f"Opened graph for {os.path.basename(csv_path)}"
    except Exception as exc:
        return False, f"Graph export failed: {exc}"

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

switch_to_ecosystem()

if worms:
    camera_x = sum(w.x for w in worms) / len(worms)
    camera_y = sum(w.y for w in worms) / len(worms)

while running:

    # Always recalculate layout and scroll region at the start of each frame
    ui_layout = update_ui_layout(ui_scroll)
    panel_height = screen_height - 20
    # FIX: Subtract the current scroll offset to get the true absolute height
    absolute_content_bottom = ui_layout["content_bottom"] - ui_scroll
    max_scroll = max(0, int(absolute_content_bottom - panel_height))
    ui_scroll = max(-max_scroll, min(0, ui_scroll))
    if ui_scroll != ui_layout["scroll_offset"]:
        ui_layout = update_ui_layout(ui_scroll)
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
                simulation_mode = MODE_ECOSYSTEM
                switch_to_ecosystem()
            if event.key == pygame.K_2:
                simulation_mode = MODE_OPENWORM
                launched, openworm_status = launch_openworm()
            if event.key == pygame.K_3:
                view_mode = 2
            if event.key == pygame.K_i:
                show_ui = not show_ui
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
            if event.key == pygame.K_z:
                zoom *= 1.1
            if event.key == pygame.K_x:
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
                if renderer is not None:
                    renderer.ctx.viewport = (0, 0, world_view_width, screen_height)
                world_surface, ui_surface = create_render_surfaces(world_view_width, screen_height)
                background_stars = generate_background_stars(world_view_width, screen_height, BACKGROUND_STAR_COUNT)
            if event.key == pygame.K_c:
                if camera_mode == CAMERA_MODE_FREE:
                    camera_mode = CAMERA_MODE_DOMINANT
                else:
                    camera_mode = CAMERA_MODE_FREE
            # Toggle Evolution Dashboard overlay with TAB
            if event.key == pygame.K_TAB:
                show_dashboard = not show_dashboard

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if event.type == pygame.MOUSEMOTION:
                event_pos = event.pos
            else:
                event_pos = getattr(event, "pos", pygame.mouse.get_pos())
            local_pos = (event_pos[0] - world_view_width, event_pos[1])
            if show_ui and local_pos[0] >= 0:
                if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", 0) == 1:
                    if mode_buttons[MODE_ECOSYSTEM].hit(local_pos):
                        simulation_mode = MODE_ECOSYSTEM
                        switch_to_ecosystem()
                    elif mode_buttons[MODE_OPENWORM].hit(local_pos):
                        simulation_mode = MODE_OPENWORM
                        launched, openworm_status = launch_openworm()
                    elif section_buttons["environment"].hit(local_pos):
                        section_collapsed["environment"] = not section_collapsed["environment"]
                    elif section_buttons["evolution"].hit(local_pos):
                        section_collapsed["evolution"] = not section_collapsed["evolution"]
                    elif section_buttons["simulation"].hit(local_pos):
                        section_collapsed["simulation"] = not section_collapsed["simulation"]
                    elif section_buttons["stats"].hit(local_pos):
                        section_collapsed["stats"] = not section_collapsed["stats"]
                    elif (not section_collapsed["simulation"]) and export_graph_button.hit(local_pos):
                        launched, graph_status = launch_graph_export(evolution_logger.csv_path)
                    elif (not section_collapsed["simulation"]) and climate_button.hit(local_pos):
                        toggle_climate()
                    # Check for Open Output Folder button click
                    elif (not section_collapsed["stats"]) and open_output_folder_button_rect is not None and open_output_folder_button_rect.collidepoint(local_pos):
                        open_output_folder()

                slider_changed = False
                for slider_key in get_active_slider_keys():
                    slider = control_sliders[slider_key]
                    if slider.handle_event(event, local_pos):
                        slider_changed = True
                if slider_changed:
                    simulation_speed = control_sliders["sim_speed"].value
                    apply_world_controls(world, control_sliders)

        if event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x > world_view_width:  # Only scroll if mouse is over UI panel
                ui_scroll += event.y * UI_SCROLL_SPEED
                ui_scroll = max(-max_scroll, min(0, ui_scroll))
            elif mouse_x < world_view_width:
                zoom += event.y * 0.1
                zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x > world_view_width:
                local_x = mouse_x - world_view_width
                local_y = mouse_y
                # Check if click is on scroll bar thumb
                if 'scroll_thumb_rect' in locals() and scroll_thumb_rect and scroll_thumb_rect.collidepoint(local_x, local_y):
                    scroll_dragging = True
                    scroll_drag_offset = local_y - scroll_thumb_rect.y

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            scroll_dragging = False

        if event.type == pygame.MOUSEMOTION and scroll_dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x > world_view_width:
                local_y = mouse_y
                # Calculate new scroll offset based on thumb drag
                thumb_track_height = panel_height - (scroll_thumb_rect.height if 'scroll_thumb_rect' in locals() and scroll_thumb_rect else 0)
                if thumb_track_height > 0 and 'scroll_thumb_rect' in locals() and scroll_thumb_rect:
                    thumb_y = local_y - scroll_drag_offset
                    thumb_y = max(0, min(thumb_y, thumb_track_height))
                    scroll_ratio = thumb_y / thumb_track_height
                    ui_scroll = -int(scroll_ratio * max_scroll)

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

        sim_time += FIXED_DT
        accumulator -= FIXED_DT

        # Record stats each frame
        stats.record_stats(worms, eggs, sim_time)

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

    if renderer is not None:
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
    else:
        screen.fill((8, 8, 12))

    world_surface.fill((6, 8, 14, 255))
    for sx, sy, v in background_stars:
        world_surface.set_at((sx, sy), (v, v, min(120, v + 20), 255))

    for gx in range(0, world_view_width, GRID_OVERLAY_STEP):
        pygame.draw.line(world_surface, (18, 22, 35, 55), (gx, 0), (gx, screen_height), 1)
    for gy in range(0, screen_height, GRID_OVERLAY_STEP):
        pygame.draw.line(world_surface, (18, 22, 35, 55), (0, gy), (world_view_width, gy), 1)

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
                    if intensity > 105:
                        pygame.draw.circle(world_surface, (50, 210, 70), (int(sx), int(sy)), 2)
                        pygame.draw.circle(world_surface, (0, 120, 60), (int(sx), int(sy)), 2, 1)
                    else:
                        ix = int(sx)
                        iy = int(sy)
                        if 0 <= ix < world_view_width and 0 <= iy < screen_height:
                            world_surface.set_at((ix, iy), (0, max(20, intensity), 0))

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
            segment_points = list(worm.visual_body_points())
            if len(segment_points) < 2:
                continue

            worm_rgb = tuple(int(max(0.0, min(1.0, c)) * 255) for c in getattr(worm, "color_current", (0.8, 0.8, 0.8)))
            base_color = worm_rgb
            head_color = (255, 80, 80)
            tail_color = (150, 150, 150)

            trail_points = []
            for tx, ty in getattr(worm, "trail", [])[-20:]:
                tsx, tsy = world_to_screen(tx, ty, camera_x, camera_y, zoom, world_view_width, screen_height)
                trail_points.append((int(tsx), int(tsy)))
            for i, p in enumerate(trail_points):
                alpha = (i + 1) / float(max(1, len(trail_points)))
                radius = max(1, int(1 + alpha * 2))
                pygame.draw.circle(world_surface, (50, 50, 80, int(35 + 80 * alpha)), p, radius)

            visible_segments = max(2, min(len(segment_points), int(round(len(segment_points) * max(0.25, worm.size)))))
            screen_points = []
            for px, py in segment_points[:visible_segments]:
                sx, sy = world_to_screen(px, py, camera_x, camera_y, zoom, world_view_width, screen_height)
                screen_points.append((int(sx), int(sy)))

            shadow_points = [(x + 3, y + 3) for (x, y) in screen_points]
            for i in range(1, len(shadow_points)):
                width = int(8 * (1.0 - (i - 1) / float(max(1, len(shadow_points) - 1))))
                width = max(width, 2)
                pygame.draw.line(world_surface, (20, 20, 20), shadow_points[i - 1], shadow_points[i], width)

            for i in range(1, len(screen_points)):
                width = int(8 * (1.0 - (i - 1) / float(max(1, len(screen_points) - 1))))
                width = max(width, 2)
                pygame.draw.line(world_surface, base_color, screen_points[i - 1], screen_points[i], width)

            head = screen_points[0]
            tail = screen_points[-1]
            pygame.draw.circle(world_surface, head_color, head, 6)
            pygame.draw.circle(world_surface, tail_color, tail, 3)

        for egg in eggs:
            sx, sy = world_to_screen(egg.x, egg.y, camera_x, camera_y, zoom, world_view_width, screen_height)
            if 0 <= sx < world_view_width and 0 <= sy < screen_height:
                pygame.draw.circle(world_surface, (255, 90, 90), (int(sx), int(sy)), 2)

    screen.blit(world_surface, (0, 0))

    # Draw Evolution Dashboard overlay if enabled
    if show_dashboard:
        avg_speed = np.mean([w.gene_speed for w in worms]) if worms else 0
        avg_food = np.mean([w.gene_food_sense for w in worms]) if worms else 0
        dashboard_text = (
            f"Worms: {len(worms)}\n"
            f"Eggs: {len(eggs)}\n"
            f"Avg Speed Gene: {avg_speed:.2f}\n"
            f"Avg Food Sense: {avg_food:.2f}\n"
            f"Mutation Rate: {world.mutation_rate:.3f}\n"
            f"Climate: {'ON' if world.climate_enabled else 'OFF'}"
        )
        overlay_rect = pygame.Rect(40, 40, 260, 140)
        pygame.draw.rect(screen, (30, 30, 50, 220), overlay_rect, border_radius=12)
        pygame.draw.rect(screen, (120, 180, 255), overlay_rect, width=2, border_radius=12)
        lines = dashboard_text.split("\n")
        for i, line in enumerate(lines):
            text_surf = font.render(line, True, (230, 255, 255))
            screen.blit(text_surf, (overlay_rect.x + 16, overlay_rect.y + 12 + i * 26))

    avg_energy = (sum(w.energy for w in worms) / len(worms)) if worms else 0.0
    worm_count = len(worms)
    egg_count = len(eggs)
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

    if sim_time >= next_log_time:
        evolution_logger.log(
            sim_time=round(sim_time, 3),
            worms=worm_count,
            eggs=egg_count,
            avg_energy=round(avg_energy, 3),
            total_births=total_births,
            total_deaths=total_deaths,
            lineages=total_lineages,
            largest_colony=largest_colony,
            dominant_lineage=dominant_lineage,
            food_total=round(total_food, 6),
            food_density=round(food_density, 6),
            pheromone_density=round(pheromone_density, 6),
            season=world.season_name,
            temperature=round(float(getattr(world, "temperature", control_sliders["temperature"].value)), 3),
            water_level=round(float(getattr(world, "water_level", control_sliders["water"].value)), 3),
            oxygen_level=round(float(getattr(world, "oxygen_level", control_sliders["oxygen"].value)), 3),
        )
        while next_log_time <= sim_time:
            next_log_time += LOG_INTERVAL_SECONDS

    if show_ui:
        ui_surface.fill((25, 25, 30))
        ui_surface.blit(font.render("Simulation Mode", True, (235, 235, 235)), (20, ui_layout["mode_title_y"]))
        mode_buttons[MODE_ECOSYSTEM].draw(ui_surface, small_font, selected=(simulation_mode == MODE_ECOSYSTEM))
        mode_buttons[MODE_OPENWORM].draw(ui_surface, small_font, selected=(simulation_mode == MODE_OPENWORM))

        section_buttons["environment"].label = f"Environment {'>' if section_collapsed['environment'] else 'v'}"
        section_buttons["evolution"].label = f"Evolution {'>' if section_collapsed['evolution'] else 'v'}"
        section_buttons["simulation"].label = f"Simulation {'>' if section_collapsed['simulation'] else 'v'}"
        section_buttons["stats"].label = f"Stats {'>' if section_collapsed['stats'] else 'v'}"

        for key in ("environment", "evolution", "simulation", "stats"):
            section_buttons[key].draw(ui_surface, small_font, selected=(not section_collapsed[key]))

        if not section_collapsed["environment"]:
            for slider_key in ENVIRONMENT_SLIDERS:
                control_sliders[slider_key].draw(ui_surface, font, small_font)

        if not section_collapsed["evolution"]:
            for slider_key in EVOLUTION_SLIDERS:
                control_sliders[slider_key].draw(ui_surface, font, small_font)

        if not section_collapsed["simulation"]:
            for slider_key in SIMULATION_SLIDERS:
                control_sliders[slider_key].draw(ui_surface, font, small_font)
            export_graph_button.draw(ui_surface, small_font)
            climate_button.label = ("Disable Climate" if world.climate_enabled else "Enable Climate")
            climate_button.draw(ui_surface, small_font)
            # Draw the season speed slider directly under the climate button
            control_sliders["season_speed"].draw(ui_surface, font, small_font)

        stats_groups = [
            (
                "Environment",
                (
                    f"Temperature: {world.temperature:.1f} C",
                    f"Water: {world.water_level:.2f}",
                    f"Oxygen: {world.oxygen_level:.2f}",
                    # Season line will be handled separately
                    f"Food Total: {total_food:.1f}",
                ),
            ),
            (
                "Population",
                (
                    f"Worms: {worm_count}",
                    f"Eggs: {egg_count}",
                    f"Births: {total_births}",
                    f"Deaths: {total_deaths}",
                    f"Lineages: {total_lineages}",
                    f"Largest Colony: {largest_colony}",
                ),
            ),
            (
                "Evolution",
                (
                    f"Mutation Rate: {world.mutation_rate:.4f}",
                    f"Dominant lineage: {dominant_lineage}",
                    f"Avg Energy: {avg_energy:.1f}",
                ),
            ),
            (
                "Simulation",
                (
                    f"Target: {simulation_mode}",
                    f"Sim Time: {sim_time:.1f}s",
                    f"Births/s: {births_per_sec:.2f}",
                    f"Deaths/s: {deaths_per_sec:.2f}",
                    f"OpenWorm: {openworm_status}",
                    f"CSV: {os.path.basename(evolution_logger.csv_path)}",
                    f"Graph: {graph_status}",
                ),
            ),
        ]

        if not section_collapsed["stats"]:

            y = ui_layout["stats_y"]
            ui_surface.blit(font.render("Simulation Stats", True, (190, 210, 255)), (20, y))
            y += 24
            for group_title, lines in stats_groups:
                ui_surface.blit(small_font.render(group_title, True, (170, 200, 255)), (20, y))
                y += UI_STATS_LINE_HEIGHT
                for line in lines:
                    # Custom season color rendering
                    if group_title == "Environment" and line.startswith("Food Total"):
                        season_color = SEASON_COLORS.get(world.season_name, (200, 200, 200))
                        season_text = f"Season: {world.season_name}"
                        season_render = small_font.render(season_text, True, season_color)
                        ui_surface.blit(season_render, (20, y))
                        y += UI_STATS_LINE_HEIGHT
                    ui_surface.blit(small_font.render(line, True, (230, 230, 230)), (20, y))
                    y += UI_STATS_LINE_HEIGHT
                y += 4

            # Output folder display (use correct path)
            output_label = f"Output Folder:\n{OUTPUT_FOLDER_PATH}"
            for line in output_label.split("\n"):
                ui_surface.blit(small_font.render(line, True, (200, 255, 200)), (20, y))
                y += UI_STATS_LINE_HEIGHT

            # 'Open Output Folder' button (track rect globally for event handling)
            # (No global statement needed here)
            open_output_folder_button_rect = pygame.Rect(20, y, 200, 28)
            pygame.draw.rect(ui_surface, (60, 120, 60), open_output_folder_button_rect, border_radius=6)
            pygame.draw.rect(ui_surface, (180, 255, 180), open_output_folder_button_rect, width=2, border_radius=6)
            btn_text = small_font.render("Open Output Folder", True, (255, 255, 255))
            ui_surface.blit(btn_text, (open_output_folder_button_rect.x + 10, open_output_folder_button_rect.y + 4))
            y += 36

            camera_mode_name = "Free camera" if camera_mode == CAMERA_MODE_FREE else "Follow dominant lineage"
            y += 4
            for line in (
                "I: Toggle UI",
                "1: Ecosystem simulator",
                "2: Launch OpenWorm",
                "Export Graph button: plot latest run",
                "F: Fullscreen, C: Camera",
                "WASD/Arrows: Pan",
                "Z/X: Zoom",
                "TAB: Evolution Dashboard",
                "Mouse wheel on panel: scroll",
                "Mouse wheel on world: zoom",
                f"Camera: {camera_mode_name}",
            ):
                ui_surface.blit(small_font.render(line, True, (190, 190, 200)), (20, y))
                y += UI_HELP_LINE_HEIGHT

        screen.blit(ui_surface, (world_view_width, 0))
        pygame.draw.line(screen, (80, 80, 80), (world_view_width, 0), (world_view_width, screen_height), 2)
        # Draw the scroll bar on the UI panel
        scroll_thumb_rect = draw_scroll_bar(
            ui_surface,
            ui_scroll,
            max_scroll,
            panel_height,
            UI_WIDTH - 16,  # x position (right edge of UI panel)
            0,              # y position (top of UI panel)
            12,             # width of scroll bar
            panel_height    # height of scroll bar
        )

    pygame.display.set_caption(
        f"Target:{simulation_mode} Worms:{len(worms)} Food:{total_food:.0f} Lineages:{total_lineages} "
        f"Gen:{max_generation} Season:{world.season_name}"
    )

    pygame.display.flip()

if imgui_renderer:
    imgui_renderer.shutdown()
evolution_logger.close()
pygame.quit()

# Plot stats graphs after simulation ends
stats.plot_population()
stats.plot_gene_evolution()
