from neuron import Neuron


class Brain:

    def __init__(self):

        self.neurons = [Neuron() for _ in range(10)]

        self.connections = {
            0: [(5, 0.6)],
            1: [(6, 0.6)],
            2: [(7, 0.5)],
            3: [(8, 0.5)],
        }

    def step(self, inputs):

        spikes = [0] * len(self.neurons)

        for i, n in enumerate(self.neurons):
            spikes[i] = n.step(inputs[i])

        next_inputs = [0] * len(self.neurons)

        for src in self.connections:

            if spikes[src]:

                for dst, w in self.connections[src]:
                    next_inputs[dst] += w

        return next_inputs

    def load_connectome(self, path):
        # Format: neuronA neuronB weight
        edges = []
        neuron_names = set()

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) != 3:
                    continue

                src, dst, weight = parts
                w = float(weight)

                neuron_names.add(src)
                neuron_names.add(dst)
                edges.append((src, dst, w))

        ordered = sorted(neuron_names)
        index = {name: i for i, name in enumerate(ordered)}

        self.neurons = [Neuron() for _ in ordered]
        self.connections = {}

        for src, dst, w in edges:
            src_i = index[src]
            dst_i = index[dst]
            self.connections.setdefault(src_i, []).append((dst_i, w))

        return index
