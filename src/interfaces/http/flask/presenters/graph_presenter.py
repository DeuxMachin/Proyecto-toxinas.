from typing import Any, Dict
from src.application.dto.graph_dto import GraphResponseDTO
import math
import numpy as np

class GraphPresenter:
    @staticmethod
    def present(properties: Dict[str, Any], meta: Dict[str, Any], fig_json: Dict[str, Any]) -> Dict[str, Any]:
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
        # Compute summary statistics and top-5 residues without legacy dependency
        cent = properties.get("centrality", {})
        def _stats(vals: Dict[Any, float]):
            if not vals:
                return {"min": 0.0, "max": 0.0, "mean": 0.0, "top": {"residues": [], "value": 0.0}, "top_residues": "-"}
            values = list(vals.values())
            vmin, vmax = min(values), max(values)
            mean = sum(values) / len(values)
            max_res = [str(k) for k, v in vals.items() if math.isclose(v, vmax, rel_tol=1e-9) or v == vmax]
            return {
                "min": vmin,
                "max": vmax,
                "mean": mean,
                "top": {"residues": max_res, "value": vmax},
                "top_residues": ", ".join(max_res) if max_res else "-",
            }

        summary_stats = {
            "degree_centrality": _stats(cent.get("degree", {})),
            "betweenness_centrality": _stats(cent.get("betweenness", {})),
            "closeness_centrality": _stats(cent.get("closeness", {})),
            "clustering_coefficient": _stats(cent.get("clustering", {})),
        }

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

        # Match frontend expected keys with *_centrality and clustering_coefficient
        top5_residues = {
            "degree_centrality": _top5(cent.get("degree", {})),
            "betweenness_centrality": _top5(cent.get("betweenness", {})),
            "closeness_centrality": _top5(cent.get("closeness", {})),
            "clustering_coefficient": _top5(cent.get("clustering", {})),
        }

        # Provide key_residues (string summaries) mirroring the client-side analyzer format
        key_residues = {
            "degree_centrality": summary_stats.get("degree_centrality", {}).get("top_residues", "-"),
            "betweenness_centrality": summary_stats.get("betweenness_centrality", {}).get("top_residues", "-"),
            "closeness_centrality": summary_stats.get("closeness_centrality", {}).get("top_residues", "-"),
            "clustering_coefficient": summary_stats.get("clustering_coefficient", {}).get("top_residues", "-"),
        }

        base = GraphResponseDTO(properties=normalize(properties), meta=normalize(meta)).__dict__
        base.update({
            "plotData": normalize(fig_json.get("data")),
            "layout": normalize(fig_json.get("layout")),
            "summary_statistics": normalize(summary_stats),
            "top_5_residues": normalize(top5_residues),
            "key_residues": normalize(key_residues),
        })
        return normalize(base)
