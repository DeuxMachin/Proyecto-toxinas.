from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class Granularity(str, Enum):
    CA = "CA"
    ATOM = "atom"

    @classmethod
    def from_string(cls, value: str) -> "Granularity":
        v = (value or "").strip().lower()
        return cls.ATOM if v == "atom" else cls.CA


@dataclass(frozen=True)
class DistanceThreshold:
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError("DistanceThreshold must be a number")
        if self.value <= 0:
            raise ValueError("DistanceThreshold must be > 0")

    def __float__(self) -> float:
        return float(self.value)


@dataclass(frozen=True)
class SequenceSeparation:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise TypeError("SequenceSeparation must be an int")
        if self.value < 0:
            raise ValueError("SequenceSeparation must be >= 0")

    def __int__(self) -> int:
        return int(self.value)


@dataclass(frozen=True)
class ProteinId:
    source: str
    pid: int


@dataclass(frozen=True)
class FamilyName:
    raw: str

    def normalized_ascii(self) -> str:
        # Replace common Greek letters used in dataset with ascii equivalents
        return (
            self.raw
            .replace("μ", "mu")
            .replace("β", "beta")
            .replace("ω", "omega")
        )

    def like_patterns(self) -> Tuple[str, str]:
        # Returns tuple of (original_like, normalized_like)
        return (f"{self.raw}%", f"{self.normalized_ascii()}%")


class IC50Unit(str, Enum):
    NM = "nM"
    UM = "μM"
    MM = "mM"

    @classmethod
    def from_string(cls, unit: Optional[str]) -> Optional["IC50Unit"]:
        if not unit:
            return None
        u = unit.strip()
        low = u.lower()
        if low in ("nm",):
            return cls.NM
        if low in ("μm", "um"):
            return cls.UM
        if low in ("mm",):
            return cls.MM
        # Unknown unit; keep original spelling but not as Enum
        return None


@dataclass(frozen=True)
class IC50:
    value: Optional[float]
    unit: Optional[str]

    def to_nm(self) -> Optional[float]:
        return IC50.normalize_to_nm(self.value, self.unit)

    @staticmethod
    def normalize_to_nm(ic50_value: Optional[float], ic50_unit: Optional[str]) -> Optional[float]:
        if ic50_value is None or ic50_unit is None:
            return None
        unit_enum = IC50Unit.from_string(ic50_unit)
        if unit_enum == IC50Unit.NM:
            return float(ic50_value)
        if unit_enum == IC50Unit.UM:
            return float(ic50_value) * 1000.0
        if unit_enum == IC50Unit.MM:
            return float(ic50_value) * 1000000.0
        # Unknown unit: return original number (best-effort)
        return float(ic50_value)

    @classmethod
    def from_value_unit(cls, value: Optional[float], unit: Optional[str]) -> "IC50":
        return cls(value=value, unit=unit)
