import numpy as np
import pandas as pd
import networkx as nx


def load_connectome(path):

    df = pd.read_csv(path)

    return df


def _pick_column(df, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    raise ValueError(f"Could not find any of these columns: {candidates}")


def connectome_to_weights(df, n):
    src_col = _pick_column(df, ["source", "pre", "from", "neuron1", "src"])
    dst_col = _pick_column(df, ["target", "post", "to", "neuron2", "dst"])
    weight_col = next((c for c in ["weight", "strength", "synapses"] if c in df.columns), None)

    graph = nx.DiGraph()

    for _, row in df.iterrows():
        src = str(row[src_col])
        dst = str(row[dst_col])
        w = float(row[weight_col]) if weight_col else 1.0
        if graph.has_edge(src, dst):
            graph[src][dst]["weight"] += w
        else:
            graph.add_edge(src, dst, weight=w)

    if graph.number_of_edges() == 0:
        return np.random.randn(n, n) * 0.1

    weights = np.zeros((n, n), dtype=float)
    nodes = list(graph.nodes())
    index = {name: i % n for i, name in enumerate(nodes)}

    for src, dst, data in graph.edges(data=True):
        weights[index[src], index[dst]] += data.get("weight", 1.0)

    max_abs = np.max(np.abs(weights))
    if max_abs > 0:
        weights = (weights / max_abs) * 0.5

    return weights
