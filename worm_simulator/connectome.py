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


def build_connectome_graph(df):
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

    connections = {}
    for src, dst, data in graph.edges(data=True):
        connections.setdefault(src, []).append((dst, float(data.get("weight", 1.0))))

    return connections, list(graph.nodes())


def default_connectome_graph():
    connections = {
        "AWA": [("AIY", 1.0), ("AIZ", 0.5)],
        "ASH": [("AIZ", 0.9), ("AVA", 0.4)],
        "AFD": [("AIY", 0.8)],
        "PHA": [("AIY", 0.7)],
        "AIY": [("AVB", 1.0), ("MOTOR_FORWARD", 0.6)],
        "AIZ": [("AVA", 1.0)],
        "AVA": [("MOTOR_LEFT", 1.0), ("MOTOR_RIGHT", -0.3)],
        "AVB": [("MOTOR_RIGHT", 1.0), ("MOTOR_LEFT", -0.3)],
        "MOTOR_LEFT": [("MOTOR_FORWARD", 0.2)],
        "MOTOR_RIGHT": [("MOTOR_FORWARD", 0.2)],
    }

    neuron_order = [
        "AWA",
        "ASH",
        "AFD",
        "PHA",
        "AIY",
        "AIZ",
        "AVA",
        "AVB",
        "MOTOR_LEFT",
        "MOTOR_RIGHT",
        "MOTOR_FORWARD",
    ]

    sensory_map = {
        "food_smell": "AWA",
        "touch": "ASH",
        "temperature": "AFD",
        "pheromone": "PHA",
    }

    motor_map = {
        "left": "MOTOR_LEFT",
        "right": "MOTOR_RIGHT",
        "forward": "MOTOR_FORWARD",
    }

    return connections, neuron_order, sensory_map, motor_map


def graph_from_connectome_df(df):
    connections, neuron_order = build_connectome_graph(df)

    sensory_candidates = ["AWA", "ASH", "AFD", "PHA"]
    sensory_map = {
        "food_smell": next((n for n in sensory_candidates if n in neuron_order), neuron_order[0]),
        "touch": next((n for n in sensory_candidates if n in neuron_order), neuron_order[min(1, len(neuron_order) - 1)]),
        "temperature": next((n for n in sensory_candidates if n in neuron_order), neuron_order[min(2, len(neuron_order) - 1)]),
        "pheromone": next((n for n in sensory_candidates if n in neuron_order), neuron_order[min(3, len(neuron_order) - 1)]),
    }

    motor_map = {
        "left": next((n for n in ["SMDDL", "MOTOR_LEFT", "RMDL", "AVL"] if n in neuron_order), neuron_order[-1]),
        "right": next((n for n in ["SMDDR", "MOTOR_RIGHT", "RMDR", "AVR"] if n in neuron_order), neuron_order[-1]),
        "forward": next((n for n in ["AVB", "MOTOR_FORWARD", "DB1"] if n in neuron_order), neuron_order[-1]),
    }

    return connections, neuron_order, sensory_map, motor_map
