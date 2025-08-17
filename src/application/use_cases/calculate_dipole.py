from dataclasses import dataclass
from typing import Optional, Dict, Any
from src.application.ports.repositories import StructureRepository, MetadataRepository
from src.infrastructure.pdb.pdb_preprocessor_adapter import PDBPreprocessorAdapter
from src.infrastructure.graphein.dipole_adapter import DipoleAdapter


@dataclass
class CalculateDipoleInput:
    source: str
    pid: int


class CalculateDipole:
    def __init__(self, structures: StructureRepository, dipole: DipoleAdapter, metadata_repo: Optional[MetadataRepository] = None, pdb: Optional[PDBPreprocessorAdapter] = None) -> None:
        self.structures = structures
        self.dipole = dipole
        self.metadata_repo = metadata_repo
        self.pdb = pdb or PDBPreprocessorAdapter()

    def execute(self, inp: CalculateDipoleInput) -> Dict[str, Any]:
        # Obtener datos binarios prioritariamente desde repositories
        pdb_bytes = self.structures.get_pdb(inp.source, inp.pid)
        psf_bytes = self.structures.get_psf(inp.source, inp.pid)
        if not pdb_bytes:
            return {"success": False, "error": "No encontrado"}

        pdb_path = self.pdb.prepare_temp_pdb(pdb_bytes)
        psf_path = None
        if psf_bytes:
            psf_path = self.pdb.prepare_temp_psf(psf_bytes)

        try:
            result = self.dipole.calculate_dipole_from_files(pdb_path, psf_path)
            return {"success": True, "dipole": result}
        finally:
            self.pdb.cleanup([pdb_path, psf_path])
