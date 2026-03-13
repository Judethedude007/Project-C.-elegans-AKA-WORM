import random
import numpy as np
import pygame
from world import World
from worm import Worm
from camera import Camera
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, WORLD_SIZE
from gpu_renderer import GPURenderer

pygame.init()

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.OPENGL | pygame.DOUBLEBUF,
)
pygame.display.set_caption("Worm Simulator GPU")

world = World()
worms = [Worm(random.uniform(0, WORLD_SIZE - 1), random.uniform(0, WORLD_SIZE - 1)) for _ in range(10)]

camera = Camera()
camera.x = (WORLD_SIZE * CELL_SIZE) / 2 - SCREEN_WIDTH / 2
camera.y = (WORLD_SIZE * CELL_SIZE) / 2 - SCREEN_HEIGHT / 2
camera.zoom = 1.0

renderer = GPURenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
clock = pygame.time.Clock()

running = True

while running:

    dt = clock.get_time() / 1000.0
    if dt <= 0:
        dt = 1 / 60

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    world.update(dt)

    for w in worms:
        w.update(world, dt)

    worms = [w for w in worms if not w.dead]

    # CPU simulation produces world-space worm positions.
    worm_positions = np.array([[w.x * CELL_SIZE, w.y * CELL_SIZE] for w in worms], dtype=np.float32)

    # GPU handles rendering only.
    renderer.render(worm_positions, camera.x, camera.y, camera.zoom)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
