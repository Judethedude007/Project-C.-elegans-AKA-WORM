import random
from config import INITIAL_ENERGY, METABOLISM, FOOD_ENERGY
from brain import Brain

class Worm:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.energy = INITIAL_ENERGY

        self.brain = Brain()

    def sense(self, env):

        left = env.get_food(self.x - 1, self.y)
        right = env.get_food(self.x + 1, self.y)
        here = env.get_food(self.x, self.y)

        return [left, right, self.energy/100, here]

    def step(self, env):

        inputs = self.sense(env)

        output = self.brain.forward(inputs)

        turn_left, turn_right, eat = output

        if turn_left > 0.5:
            self.x -= 1

        elif turn_right > 0.5:
            self.x += 1

        if eat > 0.5:
            food = env.get_food(self.x, self.y)

            if food > 0:

                env.eat_food(self.x, self.y, 1)

                self.energy += FOOD_ENERGY

                self.brain.learn(1)

        self.energy -= METABOLISM
