import pygame
from config import WORLD_SIZE


def draw_world(screen, camera, world):
    width, height = screen.get_size()
    sample_step = 6

    for sx in range(0, width, sample_step):
        wx = int(camera.x + (sx / max(camera.zoom, 0.001))) % WORLD_SIZE

        for sy in range(0, height, sample_step):
            wy = int(camera.y + (sy / max(camera.zoom, 0.001))) % WORLD_SIZE

            food = world.food[wx, wy]
            pheromone = world.pheromone[wx, wy]

            if food > 0.2:
                intensity = int(food * 180)
                color = (40, min(255, 120 + intensity), 40)
                pygame.draw.rect(screen, color, (sx, sy, sample_step, sample_step))

            if pheromone > 0.01:
                color = (40, 100, 180)
                pygame.draw.rect(screen, color, (sx, sy, sample_step, sample_step))


def draw_worm(screen, camera, worm):

    points = worm.body_points()

    for i, p in enumerate(points):

        x, y = camera.apply(p[0], p[1])

        radius = max(1, 6 - i // 2)
        pygame.draw.circle(screen, (255, 150, 150), (int(x), int(y)), radius)

    hx, hy = camera.apply(points[0][0], points[0][1])
    pygame.draw.circle(screen, (255, 255, 255), (int(hx), int(hy)), 3)
