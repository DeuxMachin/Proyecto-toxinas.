from typing import Any, Dict
from src.application.dto.graph_dto import GraphResponseDTO
import math
import numpy as np

class GraphPresenter:
    @staticmethod
    def present(properties: Dict[str, Any], meta: Dict[str, Any], graph_data: Dict[str, Any]) -> Dict[str, Any]:
        # Helper to normalize numpy arrays/scalars into JSON-serializable types
        def normalize(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.floating, np.integer)):
                return obj.item()
            if isinstance(obj, dict):
                return {k: normalize(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [normalize(x) for x in obj]
            return obj
        
        # Helper to parse residue identifiers like "A:VAL:21:CA" or "A:VAL:21"
        def parse_residue_key(key: Any):
            try:
                s = str(key)
                parts = s.split(":")
                if len(parts) >= 3:
                    chain = parts[0]
                    residue_name = parts[1]
                    residue_num = parts[2]
                    return chain, residue_name, residue_num
            except Exception:
                pass
            return None, None, str(key)
        
        # Helper to get top 5 residues
        def _top5(vals: Dict[Any, float]):
            items = []
            for k, v in sorted(vals.items(), key=lambda kv: kv[1], reverse=True)[:5]:
                chain, res_name, res_num = parse_residue_key(k)
                entry = {"residue": str(res_num), "value": v}
                if res_name is not None:
                    entry["residueName"] = res_name
                if chain is not None:
                    entry["chain"] = chain
                items.append(entry)
            return items

        cent = properties.get("centrality", {})
        
        # Try to use the common graph_metrics module
        try:
            from src.infrastructure.graph.graph_metrics import calculate_summary_statistics, find_top_residues
            
            # Use common module for statistics
            summary_stats = calculate_summary_statistics(cent)
            summary_stats_renamed = {
                "degree_centrality": summary_stats.get("degree", {}),
                "betweenness_centrality": summary_stats.get("betweenness", {}),
                "closeness_centrality": summary_stats.get("closeness", {}),
                "clustering_coefficient": summary_stats.get("clustering", {}),
            }
            
            # Use common module for top residues
            top5_residues = {
                "degree_centrality": _top5(cent.get("degree", {})),
                "betweenness_centrality": _top5(cent.get("betweenness", {})),
                "closeness_centrality": _top5(cent.get("closeness", {})),
                "clustering_coefficient": _top5(cent.get("clustering", {})),
            }
            
        except ImportError as e:
            # Fallback if import fails
            print(f"Warning: Could not import graph_metrics: {e}")
            
            def _stats(vals: Dict[Any, float]):
                if not vals:
                    return {"min": 0.0, "max": 0.0, "mean": 0.0, "top_residues": "-"}
                values = list(vals.values())
                vmin, vmax = min(values), max(values)
                mean = sum(values) / len(values)
                max_res = [str(k) for k, v in vals.items() if math.isclose(v, vmax, rel_tol=1e-9) or v == vmax]
                return {
                    "min": vmin,
                    "max": vmax,
                    "mean": mean,
                    "top_residues": ", ".join(max_res) if max_res else "-",
                }

            summary_stats_renamed = {
                "degree_centrality": _stats(cent.get("degree", {})),
                "betweenness_centrality": _stats(cent.get("betweenness", {})),
                "closeness_centrality": _stats(cent.get("closeness", {})),
                "clustering_coefficient": _stats(cent.get("clustering", {})),
            }
            
            # Fallback for top5
            top5_residues = {
                "degree_centrality": _top5(cent.get("degree", {})),
                "betweenness_centrality": _top5(cent.get("betweenness", {})),
                "closeness_centrality": _top5(cent.get("closeness", {})),
                "clustering_coefficient": _top5(cent.get("clustering", {})),
            }

        # Provide key_residues (string summaries) mirroring the client-side analyzer format
        key_residues = {
            "degree_centrality": summary_stats_renamed.get("degree_centrality", {}).get("top_residues", "-"),
            "betweenness_centrality": summary_stats_renamed.get("betweenness_centrality", {}).get("top_residues", "-"),
            "closeness_centrality": summary_stats_renamed.get("closeness_centrality", {}).get("top_residues", "-"),
            "clustering_coefficient": summary_stats_renamed.get("clustering_coefficient", {}).get("top_residues", "-"),
        }

        base = GraphResponseDTO(properties=normalize(properties), meta=normalize(meta)).__dict__
        base.update({
            "nodes": normalize(graph_data.get("nodes", [])),
            "edges": normalize(graph_data.get("edges", [])),
            "graphMetadata": normalize(graph_data.get("metadata", {})),
            "summary_statistics": normalize(summary_stats_renamed),
            "top_5_residues": normalize(top5_residues),
            "key_residues": normalize(key_residues),
        })
        return normalize(base)
