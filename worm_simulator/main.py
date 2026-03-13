import random
from pathlib import Path
import pygame
from world import World
from worm import Worm
from camera import Camera
from render import draw_worm, draw_world
from config import SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, ZOOM_SPEED, WORLD_SIZE

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Worm Simulator")

world = World()

worms = []
for _ in range(10):
    random_x = random.uniform(0, WORLD_SIZE - 1)
    random_y = random.uniform(0, WORLD_SIZE - 1)
    worms.append(Worm(random_x, random_y))

connectome_file = Path(__file__).with_name("connectome.txt")
if connectome_file.exists():
    for w in worms:
        w.brain.load_connectome(str(connectome_file))

camera = Camera()
camera.x = (WORLD_SIZE * CELL_SIZE) / 2 - SCREEN_WIDTH / 2
camera.y = (WORLD_SIZE * CELL_SIZE) / 2 - SCREEN_HEIGHT / 2
camera_target_x = camera.x
camera_target_y = camera.y

clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)

running = True
simulation_speed = 1
follow = True
paused = False
target_index = 0

target_worm = worms[target_index] if worms else None

while running:

    dt = clock.get_time() / 1000.0
    if dt <= 0:
        dt = 1 / 60

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
            if event.key == pygame.K_1:
                simulation_speed = 1
            if event.key == pygame.K_2:
                simulation_speed = 3
            if event.key == pygame.K_3:
                simulation_speed = 5
            if event.key == pygame.K_4:
                simulation_speed = 10

    keys = pygame.key.get_pressed()

    camera_speed = 14 / max(camera.zoom, 0.2)
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
        for _ in range(simulation_speed):
            world.update(dt)

            for w in worms:
                w.update(world, dt)

            worms = [w for w in worms if not w.dead]

    if worms and follow:
        target_index %= len(worms)
        if target_worm not in worms:
            target_worm = worms[target_index]
        target_x = target_worm.x * CELL_SIZE - SCREEN_WIDTH / 2
        target_y = target_worm.y * CELL_SIZE - SCREEN_HEIGHT / 2
        camera.x += (target_x - camera.x) * 0.15
        camera.y += (target_y - camera.y) * 0.15
    elif not worms:
        target_worm = None
    else:
        camera.x += (camera_target_x - camera.x) * 0.15
        camera.y += (camera_target_y - camera.y) * 0.15

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
