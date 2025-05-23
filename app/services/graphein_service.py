from graphein.protein.config import ProteinGraphConfig
from graphein.protein.graphs import construct_graph
from graphein.protein.edges.distance import add_distance_threshold

def build_protein_graph(pdb_path, distance_threshold=8.0):
    config = ProteinGraphConfig(
        edge_construction_functions=[add_distance_threshold],
        distance_threshold=distance_threshold,
        granularity="CA"
    )
    G = construct_graph(config=config, pdb_path=pdb_path)
    return G
