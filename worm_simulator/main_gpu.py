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
from worm import Worm
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_SIZE
from gpu_renderer import GPURenderer

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

camera_x = 0.0
camera_y = 0.0
zoom = 1.0

follow_index = 0
follow_mode = True

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
                camera_y += 0.1
            if event.key == pygame.K_s:
                camera_y -= 0.1
            if event.key == pygame.K_a:
                camera_x -= 0.1
            if event.key == pygame.K_d:
                camera_x += 0.1

            if event.key == pygame.K_q:
                zoom *= 1.1
            if event.key == pygame.K_e:
                zoom /= 1.1

            if event.key == pygame.K_f:
                follow_mode = not follow_mode
            if event.key == pygame.K_TAB and worms:
                follow_index = (follow_index + 1) % len(worms)

    world.update(dt)

    for worm in worms:
        worm.update(world, dt)

    worms = [w for w in worms if not w.dead]

    if follow_mode and worms:
        target = worms[follow_index % len(worms)]
        camera_x = (target.x / WORLD_SIZE) * 2 - 1
        camera_y = (target.y / WORLD_SIZE) * 2 - 1

    positions = []
    trail_strips = []

    for worm in worms:
        for p in worm.body_points():
            x = (p[0] / WORLD_SIZE) * 2 - 1
            y = (p[1] / WORLD_SIZE) * 2 - 1
            positions.append([x, y])

        if worm.trail:
            strip = []
            for t in worm.trail:
                tx = (t[0] / WORLD_SIZE) * 2 - 1
                ty = (t[1] / WORLD_SIZE) * 2 - 1
                strip.append([tx, ty])
            if len(strip) > 1:
                trail_strips.append(np.array(strip, dtype="f4"))

    worm_positions = np.array(positions, dtype="f4") if positions else np.empty((0, 2), dtype="f4")

    food_positions = []
    for x in range(WORLD_SIZE):
        for y in range(WORLD_SIZE):
            if world.food[x, y] > 0.5:
                gx = (x / WORLD_SIZE) * 2 - 1
                gy = (y / WORLD_SIZE) * 2 - 1
                food_positions.append([gx, gy])

    food_positions = np.array(food_positions, dtype="f4") if food_positions else np.empty((0, 2), dtype="f4")

    renderer.render(worm_positions, trail_strips, food_positions, camera_x, camera_y, zoom)

    avg_energy = (sum(w.energy for w in worms) / len(worms)) if worms else 0.0

    if imgui_renderer:
        imgui_renderer.process_inputs()
        imgui.new_frame()
        imgui.begin("Simulation")
        imgui.text(f"Worms: {len(worms)}")
        imgui.text(f"Avg Energy: {avg_energy:.1f}")
        imgui.text(f"Speed: {simulation_speed:.1f}x")
        imgui.text(f"Zoom: {zoom:.2f}")
        imgui.text(f"Follow: {'ON' if follow_mode else 'OFF'}")
        imgui.end()
        imgui.render()
        imgui_renderer.render(imgui.get_draw_data())
    else:
        pygame.display.set_caption(
            f"Worm Simulator GPU | Worms:{len(worms)} AvgEnergy:{avg_energy:.1f} "
            f"Speed:{simulation_speed:.1f}x Zoom:{zoom:.2f}"
        )

    pygame.display.flip()
    clock.tick(60)

if imgui_renderer:
    imgui_renderer.shutdown()
pygame.quit()
