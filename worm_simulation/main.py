import pygame
from environment import Environment
from worm import Worm
from config import GRID_SIZE, CELL_SIZE

pygame.init()

screen = pygame.display.set_mode((GRID_SIZE*CELL_SIZE, GRID_SIZE*CELL_SIZE))

env = Environment()
worm = Worm(GRID_SIZE//2, GRID_SIZE//2)

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    worm.step(env)

    screen.fill((0,0,0))

    # draw food
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):

            food = env.food[x,y]

            if food > 0:
                color = (0, int(food*5), 0)

                pygame.draw.rect(screen, color,
                    (x*CELL_SIZE,y*CELL_SIZE,CELL_SIZE,CELL_SIZE))

    # draw worm (larger, with outline)
    pygame.draw.rect(screen, (255, 0, 0),
        (worm.x*CELL_SIZE, worm.y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, (255, 255, 255),
        (worm.x*CELL_SIZE, worm.y*CELL_SIZE, CELL_SIZE, CELL_SIZE), 2)
    
    # display worm stats
    font = pygame.font.Font(None, 24)
    energy_text = font.render(f"Energy: {worm.energy:.1f}", True, (255, 255, 255))
    screen.blit(energy_text, (10, 10))

    pygame.display.update()
