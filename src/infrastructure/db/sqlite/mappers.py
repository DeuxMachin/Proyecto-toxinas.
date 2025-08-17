from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

from src.domain.models.value_objects import ProteinId, FamilyName, IC50
from src.domain.models.entities import Toxin, ProteinStructure, Family


def map_structure_from_row(id_: int, name: str, pdb: Optional[bytes], psf: Optional[bytes], sequence: Optional[str] = None) -> ProteinStructure:
    return ProteinStructure(
        id=ProteinId(id_),
        name=name,
        sequence=sequence,
        pdb_data=pdb,
        psf_data=psf,
    )


def map_toxin_from_row(
    id_: int,
    code: str,
    ic50_value: Optional[float],
    ic50_unit: Optional[str],
    pdb: Optional[bytes] = None,
    psf: Optional[bytes] = None,
    sequence: Optional[str] = None,
) -> Toxin:
    ic50_obj: Optional[IC50] = None
    try:
        if ic50_value is not None and ic50_unit:
            ic50_obj = IC50.from_value_unit(ic50_value, ic50_unit)
    except Exception:
        ic50_obj = None

    structure = None
    if pdb is not None or psf is not None:
        structure = map_structure_from_row(id_, code, pdb, psf, sequence)

    return Toxin(
        id=ProteinId(id_),
        code=code,
        ic50=ic50_obj,
        sequence=sequence,
        structure=structure,
    )


def map_family_from_rows(family_prefix: str, rows: Sequence[Tuple[int, str, Optional[float], Optional[str]]]) -> Family:
    toxins = tuple(map(lambda r: map_toxin_from_row(r[0], r[1], r[2], r[3]), rows))
    return Family(name=FamilyName(family_prefix), toxins=toxins)
