import random
from pathlib import Path
import numpy as np
import pygame
from world import World
from worm import Worm
from camera import Camera
from render import draw_worm, draw_world
from connectome import load_connectome, default_connectome_graph, graph_from_connectome_df
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    ZOOM_SPEED,
    FOLLOW_LERP,
    SIMULATION_FIXED_DT,
    NUM_WORMS,
    MAX_WORMS,
    MATING_DISTANCE,
    WORLD_SIZE,
)

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Worm Simulator")

world = World()

connectome_file = Path(__file__).with_name("connectome.csv")
if connectome_file.exists():
    connectome_df = load_connectome(str(connectome_file))
    connections, neuron_order, sensory_map, motor_map = graph_from_connectome_df(connectome_df)
else:
    connections, neuron_order, sensory_map, motor_map = default_connectome_graph()

connectome_setup = {
    "connections": connections,
    "neuron_order": neuron_order,
    "sensory_map": sensory_map,
    "motor_map": motor_map,
}

worms = [
    Worm(
        random.uniform(0, WORLD_SIZE - 1),
        random.uniform(0, WORLD_SIZE - 1),
        connectome_setup,
    )
    for _ in range(NUM_WORMS)
]

camera = Camera()
camera.x = 1000 - SCREEN_WIDTH / 2
camera.y = 1000 - SCREEN_HEIGHT / 2
camera_target_x = camera.x
camera_target_y = camera.y

clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)

running = True
simulation_speed = 1
follow = True
paused = False
simulation_time = 0.0
target_index = 0

speed_by_key = {
    pygame.K_1: 1,
    pygame.K_2: 3,
    pygame.K_3: 5,
    pygame.K_4: 10,
    pygame.K_5: 20,
}

target_worm = worms[target_index] if worms else None

while running:

    dt = clock.get_time() / 1000.0
    if dt <= 0:
        dt = SIMULATION_FIXED_DT

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEWHEEL:
            camera.zoom += event.y * ZOOM_SPEED
            camera.zoom = max(0.2, min(camera.zoom, 5.0))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                follow = not follow
                if follow and worms:
                    target_worm = worms[target_index % len(worms)]
                else:
                    camera_target_x = camera.x
                    camera_target_y = camera.y
            if event.key == pygame.K_TAB and worms:
                target_index = (target_index + 1) % len(worms)
                target_worm = worms[target_index]
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key in speed_by_key:
                simulation_speed = speed_by_key[event.key]

    keys = pygame.key.get_pressed()

    camera_speed = (12 / max(camera.zoom, 0.2)) * dt * 60.0
    if not follow:
        if keys[pygame.K_LEFT]:
            camera_target_x -= camera_speed
        if keys[pygame.K_RIGHT]:
            camera_target_x += camera_speed
        if keys[pygame.K_UP]:
            camera_target_y -= camera_speed
        if keys[pygame.K_DOWN]:
            camera_target_y += camera_speed

    if not paused:
        simulation_time += dt * simulation_speed

        while simulation_time >= SIMULATION_FIXED_DT:
            world.update(SIMULATION_FIXED_DT)

            for w in worms:
                w.update(world, SIMULATION_FIXED_DT)

            worms = [w for w in worms if w.energy > 0]

            newborns = []
            if len(worms) < MAX_WORMS:
                males = [w for w in worms if w.sex == "male" and w.can_reproduce()]
                hermaphrodites = [w for w in worms if w.sex == "hermaphrodite" and w.can_reproduce()]

                for male in males:
                    for herm in hermaphrodites:
                        if len(worms) + len(newborns) >= MAX_WORMS:
                            break

                        dx_raw = abs(male.x - herm.x)
                        dy_raw = abs(male.y - herm.y)
                        dx = min(dx_raw, WORLD_SIZE - dx_raw)
                        dy = min(dy_raw, WORLD_SIZE - dy_raw)

                        if (dx * dx + dy * dy) <= (MATING_DISTANCE * MATING_DISTANCE):
                            male.reproduce()
                            herm.reproduce()

                            child = Worm(
                                (male.x + herm.x) * 0.5 + random.uniform(-5, 5),
                                (male.y + herm.y) * 0.5 + random.uniform(-5, 5),
                                connectome_setup,
                            )
                            child.x %= WORLD_SIZE
                            child.y %= WORLD_SIZE

                            child.brain.weights = np.clip(
                                (male.brain.weights + herm.brain.weights) * 0.5
                                + np.random.randn(*male.brain.weights.shape) * 0.02,
                                -2.0,
                                2.0,
                            )
                            newborns.append(child)
                            break

            worms.extend(newborns)

            simulation_time -= SIMULATION_FIXED_DT

    if worms and follow:
        target_index %= len(worms)
        if target_worm not in worms:
            target_worm = worms[target_index]
        target_x = target_worm.x - SCREEN_WIDTH / 2
        target_y = target_worm.y - SCREEN_HEIGHT / 2
        camera.x += (target_x - camera.x) * FOLLOW_LERP
        camera.y += (target_y - camera.y) * FOLLOW_LERP
    elif not worms:
        target_worm = None
    else:
        camera.x += (camera_target_x - camera.x) * 0.25
        camera.y += (camera_target_y - camera.y) * 0.25

    screen.fill((45, 35, 20))

    draw_world(screen, camera, world)
    for w in worms:
        draw_worm(screen, camera, w)

    if worms:
        avg_energy = sum(w.energy for w in worms) / len(worms)
    else:
        avg_energy = 0

    pygame.draw.rect(screen, (18, 18, 18), (0, 0, SCREEN_WIDTH, 40))
    text = (
        f"Worms:{len(worms)}  Avg Energy:{avg_energy:.1f}  Speed:{simulation_speed}x  "
        f"Zoom:{camera.zoom:.2f}  Follow:{'ON' if follow else 'OFF'}  "
        f"Target:{target_index + 1 if worms else 0}  {'PAUSED' if paused else ''}"
    )
    surface = font.render(text, True, (255, 255, 255))
    screen.blit(surface, (10, 10))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
