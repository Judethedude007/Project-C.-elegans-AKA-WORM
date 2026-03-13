import random
from pathlib import Path
import numpy as np
import pygame
from world import World
from worm import Worm
from camera import Camera
from render import draw_worm, draw_world
from connectome import load_connectome, connectome_to_weights
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    ZOOM_SPEED,
    NUM_WORMS,
    MAX_WORMS,
    MATING_DISTANCE,
    BRAIN_NEURONS,
    WORLD_SIZE,
)

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Worm Simulator")

world = World()
worms = [
    Worm(random.uniform(0, WORLD_SIZE - 1), random.uniform(0, WORLD_SIZE - 1))
    for _ in range(NUM_WORMS)
]

camera = Camera()
camera.x = 1000 - SCREEN_WIDTH / 2
camera.y = 1000 - SCREEN_HEIGHT / 2

connectome_file = Path(__file__).with_name("connectome.csv")
if connectome_file.exists():
    connectome_df = load_connectome(str(connectome_file))
    connectome_weights = connectome_to_weights(connectome_df, BRAIN_NEURONS)
    for w in worms:
        w.brain.weights = connectome_weights.copy()

clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEWHEEL:
            camera.zoom += event.y * ZOOM_SPEED
            camera.zoom = max(0.2, min(camera.zoom, 5.0))

    keys = pygame.key.get_pressed()

    camera_speed = 12 / max(camera.zoom, 0.2)
    if keys[pygame.K_LEFT]:
        camera.move(-camera_speed, 0)
    if keys[pygame.K_RIGHT]:
        camera.move(camera_speed, 0)
    if keys[pygame.K_UP]:
        camera.move(0, -camera_speed)
    if keys[pygame.K_DOWN]:
        camera.move(0, camera_speed)

    world.update()

    for w in worms:
        w.update(world)

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
                    )
                    child.x %= WORLD_SIZE
                    child.y %= WORLD_SIZE

                    child.brain.weights = (
                        (male.brain.weights + herm.brain.weights) * 0.5
                        + np.random.randn(*male.brain.weights.shape) * 0.02
                    )
                    newborns.append(child)
                    break

    worms.extend(newborns)

    screen.fill((5, 5, 8))

    draw_world(screen, camera, world)
    for w in worms:
        draw_worm(screen, camera, w)

    if worms:
        avg_energy = sum(w.energy for w in worms) / len(worms)
    else:
        avg_energy = 0

    hud = font.render(
        f"Worms: {len(worms)}  Avg Energy: {avg_energy:.1f}  Zoom: {camera.zoom:.2f}",
        True,
        (240, 240, 240),
    )
    screen.blit(hud, (12, 12))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
