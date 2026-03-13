import pygame
from config import WORLD_SIZE, CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT


def draw_world(screen, camera, world):
    zoom = max(camera.zoom, 0.2)
    view_cell_size = CELL_SIZE * zoom

    start_x = int(camera.x // CELL_SIZE)
    start_y = int(camera.y // CELL_SIZE)

    end_x = start_x + int(SCREEN_WIDTH // max(view_cell_size, 1)) + 2
    end_y = start_y + int(SCREEN_HEIGHT // max(view_cell_size, 1)) + 2

    for x in range(start_x, end_x):
        for y in range(start_y, end_y):

            if 0 <= x < WORLD_SIZE and 0 <= y < WORLD_SIZE:

                food = world.food[x, y]
                pher = world.pheromone[x, y]

                sx = (x * CELL_SIZE - camera.x) * zoom
                sy = (y * CELL_SIZE - camera.y) * zoom

                if food > 0.1:

                    color = (40, min(255, 100 + int(food * 150)), 40)

                    pygame.draw.rect(
                        screen,
                        color,
                        (sx, sy, view_cell_size, view_cell_size),
                    )

                if pher > 0.01:
                    pygame.draw.rect(
                        screen,
                        (40, 100, 180),
                        (sx, sy, view_cell_size, view_cell_size),
                    )


def draw_worm(screen, camera, worm):

    points = worm.body_points()

    for i, p in enumerate(points):

        x, y = camera.apply(p[0] * CELL_SIZE, p[1] * CELL_SIZE)

        radius = max(1, 5 - i // 2)
        pygame.draw.circle(screen, (255, 140, 140), (int(x), int(y)), radius)

    hx, hy = camera.apply(points[0][0] * CELL_SIZE, points[0][1] * CELL_SIZE)
    pygame.draw.circle(screen, (255, 255, 255), (int(hx), int(hy)), 3)
