import numpy as np
from config import LEARNING_RATE

class Brain:

    def __init__(self):

        self.num_inputs = 4
        self.num_outputs = 3

        # synaptic weights
        self.weights = np.random.randn(self.num_inputs, self.num_outputs)

    def activate(self, x):
        return 1 / (1 + np.exp(-x))

    def forward(self, inputs):

        self.last_inputs = np.array(inputs)

        output = np.dot(self.last_inputs, self.weights)

        return self.activate(output)

    def learn(self, reward):

        # simple reward learning
        self.weights += LEARNING_RATE * reward * np.outer(self.last_inputs, np.ones(self.num_outputs))
