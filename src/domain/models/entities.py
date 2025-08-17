from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

from .value_objects import (
    ProteinId,
    FamilyName,
    Granularity,
    DistanceThreshold,
    SequenceSeparation,
    IC50,
)


@dataclass(frozen=True)
class ProteinStructure:
    """
    Domain representation of a protein/toxin structure assets.
    Minimal contract used across use cases without tying to persistence.
    """

    id: ProteinId
    name: str
    sequence: Optional[str] = None
    pdb_data: Optional[bytes] = None
    psf_data: Optional[bytes] = None


@dataclass(frozen=True)
class GraphConfig:
    granularity: Granularity
    distance_threshold: DistanceThreshold
    sequence_separation: SequenceSeparation


@dataclass
class Graph:
    """Wrapper for a NetworkX graph plus semantic context."""

    nx_graph: Any
    config: GraphConfig


@dataclass(frozen=True)
class GraphTopResidue:
    chain: str
    residue_name: str
    residue_number: str
    value: float


@dataclass(frozen=True)
class GraphMetrics:
    num_nodes: int
    num_edges: int
    density: float
    avg_degree: float
    avg_clustering: float
    num_components: int

    degree_top5: Tuple[GraphTopResidue, ...] = field(default_factory=tuple)
    betweenness_top5: Tuple[GraphTopResidue, ...] = field(default_factory=tuple)
    closeness_top5: Tuple[GraphTopResidue, ...] = field(default_factory=tuple)
    clustering_top5: Tuple[GraphTopResidue, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Toxin:
    id: ProteinId
    code: str
    ic50: Optional[IC50]
    sequence: Optional[str] = None
    structure: Optional[ProteinStructure] = None


@dataclass(frozen=True)
class Family:
    name: FamilyName
    toxins: Tuple[Toxin, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Dipole:
    vector: Tuple[float, float, float]
    magnitude: float
    origin: Optional[Tuple[float, float, float]] = None
