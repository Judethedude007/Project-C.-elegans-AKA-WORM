import numpy as np
from config import BRAIN_LEARNING_RATE


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


class Brain:

    def __init__(self, connections, neuron_order, sensory_map, motor_map):

        self.neuron_order = list(neuron_order)
        self.index = {name: i for i, name in enumerate(self.neuron_order)}
        self.n = len(self.neuron_order)

        self.sensory_map = dict(sensory_map)
        self.motor_map = dict(motor_map)

        self.neurons = [Neuron() for _ in self.neuron_order]
        self.spikes = np.zeros(self.n, dtype=float)

        self.weights = np.zeros((self.n, self.n), dtype=float)
        self.connection_mask = np.zeros((self.n, self.n), dtype=bool)

        for src, targets in connections.items():
            if src not in self.index:
                continue
            src_i = self.index[src]
            for dst, weight in targets:
                if dst not in self.index:
                    continue
                dst_i = self.index[dst]
                self.weights[src_i, dst_i] += float(weight)
                self.connection_mask[src_i, dst_i] = True

        max_abs = np.max(np.abs(self.weights)) if self.weights.size else 0
        if max_abs > 0:
            self.weights = (self.weights / max_abs) * 0.5

    def step(self, sensor_inputs):

        feed_input = np.zeros(self.n, dtype=float)
        for sensor_name, value in sensor_inputs.items():
            neuron_name = self.sensory_map.get(sensor_name)
            if neuron_name in self.index:
                feed_input[self.index[neuron_name]] += float(value)

        recurrent_input = self.spikes @ self.weights
        total_input = feed_input + recurrent_input

        new_spikes = np.zeros(self.n, dtype=float)
        for i, neuron in enumerate(self.neurons):
            new_spikes[i] = neuron.step(total_input[i])

        # Memristor-like Hebbian plasticity on existing synapses.
        pre = new_spikes[:, None]
        post = new_spikes[None, :]
        self.weights[self.connection_mask] += (BRAIN_LEARNING_RATE * (pre * post))[self.connection_mask]
        self.weights = np.clip(self.weights, -2.0, 2.0)

        self.spikes = new_spikes

        motor_outputs = {"left": 0.0, "right": 0.0, "forward": 0.0}
        for key in motor_outputs:
            neuron_name = self.motor_map.get(key)
            if neuron_name in self.index:
                motor_outputs[key] = float(new_spikes[self.index[neuron_name]])

        return motor_outputs, new_spikes
