from typing import Any, Dict, Tuple
import networkx as nx


class PlotlyGraphVisualizerAdapter:
    """Adapter to produce minimal Plotly-like JSON without legacy dependency."""

    @staticmethod
    def create_complete_visualization(G: Any, granularity: str, protein_id: int) -> Dict[str, Any]:
        if not isinstance(G, nx.Graph):
            raise TypeError("Expected a networkx.Graph")

        # Try to get true 3D coordinates from node attributes ('pos' set by analyzer)
        def _get_pos(g: nx.Graph) -> Dict[Any, Tuple[float, float, float]]:
            attrs = nx.get_node_attributes(g, "pos")
            if attrs and all(isinstance(v, (list, tuple)) and len(v) == 3 for v in attrs.values()):
                return attrs
            # Fallback to a 3D spring layout if no coordinates are available
            layout3d = nx.spring_layout(g, seed=42, dim=3)
            return layout3d

        # If this graph comes from Graphein, try its native plotly builder for parity with legacy
        try:
            from graphein.protein.visualisation import plotly_protein_structure_graph
            # Title in Spanish, matching legacy
            plot_title = f"Grafo de Átomos (ID: {protein_id})" if str(granularity).lower() == "atom" else f"Grafo de CA (ID: {protein_id})"
            # Use legacy-like styling parameters from Graphein
            fig = plotly_protein_structure_graph(
                G,
                colour_nodes_by="seq_position",
                colour_edges_by="kind",
                label_node_ids=False,
                node_size_multiplier=0,
                plot_title=plot_title,
            )

            # Configure layout akin to legacy GraphVisualizer.configure_plot_layout
            fig.update_layout(
                scene=dict(
                    xaxis=dict(
                        title="X",
                        showgrid=True,
                        zeroline=True,
                        backgroundcolor="rgba(240,240,240,0.9)",
                        showbackground=True,
                        gridcolor="lightgray",
                        showticklabels=True,
                        tickfont=dict(size=10),
                    ),
                    yaxis=dict(
                        title="Y",
                        showgrid=True,
                        zeroline=True,
                        backgroundcolor="rgba(240,240,240,0.9)",
                        showbackground=True,
                        gridcolor="lightgray",
                        showticklabels=True,
                        tickfont=dict(size=10),
                    ),
                    zaxis=dict(
                        title="Z",
                        showgrid=True,
                        zeroline=True,
                        backgroundcolor="rgba(240,240,240,0.9)",
                        showbackground=True,
                        gridcolor="lightgray",
                        showticklabels=True,
                        tickfont=dict(size=10),
                    ),
                    aspectmode="data",
                    bgcolor="white",
                ),
                paper_bgcolor="white",
                plot_bgcolor="white",
                showlegend=True,
                legend=dict(x=0.85, y=0.9, bgcolor="rgba(255,255,255,0.5)", bordercolor="black", borderwidth=1),
            )
            # Style traces to match legacy names and widths/opacities
            fig.update_traces(marker=dict(opacity=0.9), selector=dict(mode="markers"))
            fig.update_traces(line=dict(width=2), selector=dict(mode="lines"))
            for tr in list(fig.data or []):
                try:
                    if getattr(tr, "mode", None) == "markers":
                        tr.name = "Átomos" if str(granularity).lower() == "atom" else "Residuos"
                    elif getattr(tr, "mode", None) == "lines":
                        tr.name = "Conexiones"
                except Exception:
                    pass

            # Convert Plotly Figure to JSON-like dict for client
            fig_dict = fig.to_plotly_json()
            # Normalize numpy arrays/scalars to lists/primitives for JSON serialization
            import numpy as np
            def normalize(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (np.floating, np.integer, np.bool_)):
                    try:
                        return obj.item()
                    except Exception:
                        return bool(obj)
                if isinstance(obj, (list, tuple)):
                    return [normalize(x) for x in obj]
                if isinstance(obj, dict):
                    return {k: normalize(v) for k, v in obj.items()}
                return obj
            fig_dict = normalize(fig_dict)
            return {"data": fig_dict.get("data", []), "layout": fig_dict.get("layout", {})}
        except Exception:
            pass

        # Fallback: build our own 3D scatter from node positions
        pos3d = _get_pos(G)
        x_nodes = [float(pos3d[n][0]) for n in G.nodes()]
        y_nodes = [float(pos3d[n][1]) for n in G.nodes()]
        z_nodes = [float(pos3d[n][2]) for n in G.nodes()]

        edge_x, edge_y, edge_z = [], [], []
        for u, v in G.edges():
            edge_x += [float(pos3d[u][0]), float(pos3d[v][0]), None]
            edge_y += [float(pos3d[u][1]), float(pos3d[v][1]), None]
            edge_z += [float(pos3d[u][2]), float(pos3d[v][2]), None]

        data = [
            {"type": "scatter3d", "x": edge_x, "y": edge_y, "z": edge_z, "mode": "lines", "line": {"width": 2, "color": "#b0b0b0"}, "hoverinfo": "none", "name": "edges", "showlegend": False},
            {"type": "scatter3d", "x": x_nodes, "y": y_nodes, "z": z_nodes, "mode": "markers", "marker": {"size": 3, "color": "#1f77b4", "opacity": 0.9}, "text": [str(n) for n in G.nodes()], "hoverinfo": "text", "name": "nodes", "showlegend": False},
        ]
        # Legacy-like Spanish title and visible axes with grid
        layout = {
            "title": (f"Grafo de Átomos (ID: {protein_id})" if str(granularity).lower() == "atom" else f"Grafo de CA (ID: {protein_id})"),
            "scene": {
                "xaxis": {"title": "X", "showgrid": True, "zeroline": True, "backgroundcolor": "rgba(240,240,240,0.9)", "showbackground": True, "gridcolor": "lightgray", "showticklabels": True, "tickfont": {"size": 10}},
                "yaxis": {"title": "Y", "showgrid": True, "zeroline": True, "backgroundcolor": "rgba(240,240,240,0.9)", "showbackground": True, "gridcolor": "lightgray", "showticklabels": True, "tickfont": {"size": 10}},
                "zaxis": {"title": "Z", "showgrid": True, "zeroline": True, "backgroundcolor": "rgba(240,240,240,0.9)", "showbackground": True, "gridcolor": "lightgray", "showticklabels": True, "tickfont": {"size": 10}},
                "aspectmode": "data",
                "bgcolor": "white",
            },
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "showlegend": True,
            "legend": {"x": 0.85, "y": 0.9, "bgcolor": "rgba(255,255,255,0.5)", "bordercolor": "black", "borderwidth": 1},
            "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
            "hovermode": "closest",
        }
        try:
            import numpy as np
            def normalize(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (list, tuple)):
                    return [normalize(x) for x in obj]
                if isinstance(obj, dict):
                    return {k: normalize(v) for k, v in obj.items()}
                if isinstance(obj, (np.floating, np.integer)):
                    return obj.item()
                return obj
            return {"data": normalize(data), "layout": normalize(layout)}
        except Exception:
            return {"data": data, "layout": layout}

    @staticmethod
    def convert_numpy_to_lists(obj):
        try:
            import numpy as np  # type: ignore
        except Exception:
            np = None  # type: ignore

        if np is not None and isinstance(obj, np.ndarray):
            return obj.tolist()
        if np is not None and isinstance(obj, (getattr(np, 'floating', ()), getattr(np, 'integer', ()), getattr(np, 'bool_', ()))):
            try:
                return obj.item()
            except Exception:
                return bool(obj)
        if isinstance(obj, dict):
            return {k: PlotlyGraphVisualizerAdapter.convert_numpy_to_lists(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [PlotlyGraphVisualizerAdapter.convert_numpy_to_lists(x) for x in obj]
        return obj
