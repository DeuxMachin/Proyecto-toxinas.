from dataclasses import dataclass
from typing import Dict, Any, Union
from src.application.ports.graph_service_port import GraphServicePort
from src.domain.models.value_objects import (
    Granularity,
    DistanceThreshold,
    SequenceSeparation,
)


@dataclass
class BuildProteinGraphInput:
    pdb_path: str
    granularity: Union[str, Granularity]
    long_threshold: Union[int, SequenceSeparation]
    distance_threshold: Union[float, DistanceThreshold]


class BuildProteinGraph:
    def __init__(self, graph_port: GraphServicePort):
        self.graph_port = graph_port

    def execute(self, inp: BuildProteinGraphInput) -> Dict[str, Any]:
        # Normalize VO inputs to primitives when needed
        granularity = inp.granularity.value if isinstance(inp.granularity, Granularity) else inp.granularity
        long_threshold = int(inp.long_threshold.value) if isinstance(inp.long_threshold, SequenceSeparation) else int(inp.long_threshold)
        distance_threshold = float(inp.distance_threshold.value) if isinstance(inp.distance_threshold, DistanceThreshold) else float(inp.distance_threshold)

        G = self.graph_port.build_graph(
            inp.pdb_path,
            granularity,
            long_threshold,
            distance_threshold,
        )
        props = self.graph_port.compute_metrics(G)
        return {"graph": G, "properties": props}
