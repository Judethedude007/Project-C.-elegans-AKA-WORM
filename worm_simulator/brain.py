import numpy as np


class Brain:

    def __init__(self, n):

        self.n = n

        self.v = np.zeros(n)
        self.threshold = 1

        self.weights = np.random.randn(n, n) * 0.1
        self.last_spikes = np.zeros(n)

    def step(self, inputs):

        inputs = np.asarray(inputs, dtype=float)

        recurrent_drive = self.weights @ self.last_spikes
        self.v += inputs + recurrent_drive

        spikes = self.v > self.threshold

        self.v[spikes] = 0
        self.last_spikes = spikes.astype(float)

        return spikes
