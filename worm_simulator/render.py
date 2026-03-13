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

            if food <= 0.02 and pheromone <= 0.02:
                continue

            color = (0, int(min(food * 255, 255)), int(min(pheromone * 90, 255)))
            pygame.draw.rect(screen, color, (sx, sy, sample_step, sample_step))


def draw_worm(screen, camera, worm):

    pts = worm.body_points()

    for i, p in enumerate(pts):

        x, y = camera.apply(p[0], p[1])

        radius = max(1, int((4 - i * 0.12) * camera.zoom))
        pygame.draw.circle(screen, (255, 100, 100), (int(x), int(y)), radius)

    head_x, head_y = camera.apply(pts[0][0], pts[0][1])
    pygame.draw.circle(screen, (255, 220, 220), (int(head_x), int(head_y)), max(2, int(3 * camera.zoom)))
