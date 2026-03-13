class Neuron:

    def __init__(self):

        self.v = 0
        self.threshold = 1
        self.decay = 0.95

    def step(self, input_current):

        self.v = self.v * self.decay + input_current

        if self.v > self.threshold:
            self.v = 0
            return 1

        return 0
