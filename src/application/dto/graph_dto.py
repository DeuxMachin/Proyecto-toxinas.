from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class GraphRequestDTO:
    source: str
    pid: int
    granularity: str = 'CA'
    long_threshold: int = 5
    distance_threshold: float = 10.0

@dataclass
class GraphResponseDTO:
    properties: Dict[str, Any]
    meta: Dict[str, Any]
