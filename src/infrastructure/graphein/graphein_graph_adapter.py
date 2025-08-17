from typing import Any, Dict
import networkx as nx


class GrapheinGraphAdapter:
    """Adapter that implements the graph port using the analyzer in graphs/* (no legacy)."""

    def build_graph(
        self,
        pdb_path: str,
        granularity: str,
        long_threshold: int,
        distance_threshold: float,
    ) -> Any:
        # When atom-level granularity is requested, use Graphein for construction like legacy
        # Build with Graphein using distance-threshold edges (required)
        from functools import partial
        from graphein.protein.config import ProteinGraphConfig
        from graphein.protein.graphs import construct_graph
        from graphein.protein.edges.distance import add_distance_threshold

        try:
            edge_fns = [
                partial(
                    add_distance_threshold,
                    long_interaction_threshold=int(long_threshold),
                    threshold=float(distance_threshold),
                )
            ]
            config = ProteinGraphConfig(
                granularity=("atom" if str(granularity).lower() == "atom" else "CA"),
                edge_construction_functions=edge_fns,
                save_graphs=False,
                pdb_dir=None,
            )
            G = construct_graph(config=config, pdb_code=None, path=pdb_path)
            return G
        except Exception as e:
            # Graphein must be used; surface a clear error
            raise RuntimeError(f"Graphein graph construction failed for {pdb_path}: {e}")

    def compute_metrics(self, G: Any) -> Dict[str, Any]:
        if not isinstance(G, nx.Graph):
            raise TypeError("Expected a networkx.Graph")

        degree = nx.degree_centrality(G)
        between = nx.betweenness_centrality(G)
        close = nx.closeness_centrality(G)
        cluster = nx.clustering(G)

        return {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "density": float(nx.density(G)),
            "avg_clustering": float(sum(cluster.values()) / len(cluster)) if cluster else 0.0,
            "centrality": {
                "degree": degree,
                "betweenness": between,
                "closeness": close,
                "clustering": cluster,
            },
        }
