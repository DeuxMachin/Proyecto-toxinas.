from typing import List, Union, Optional
from src.infrastructure.pdb.pdb_processor import PDBProcessor


class PDBPreprocessorAdapter:
    def __init__(self, pdb_dir: Optional[str] = None, psf_dir: Optional[str] = None) -> None:
        # Optional directories for future filesystem-based operations
        self.pdb_dir = pdb_dir
        self.psf_dir = psf_dir
    def prepare_temp_pdb(self, pdb_bytes: bytes) -> str:
        pdb_str = PDBProcessor.bytes_to_string(pdb_bytes)
        return PDBProcessor.create_temp_pdb_file(pdb_str, preprocess=True)

    def prepare_temp_pdb_from_any(self, pdb_data: Union[bytes, str]) -> str:
        """Accepts bytes or str; uses legacy prepare_pdb_data to normalize and writes a temp file."""
        content = PDBProcessor.prepare_pdb_data(pdb_data)
        return PDBProcessor.create_temp_pdb_file(content)

    def prepare_temp_psf(self, psf_data: Union[bytes, str]) -> str:
        """Creates a temp PSF file from bytes or string."""
        if isinstance(psf_data, str):
            psf_data = psf_data.encode('utf-8', errors='ignore')
        return PDBProcessor.create_temp_psf_file(psf_data)

    def cleanup(self, paths: List[str]) -> None:
        for p in paths:
            if p:
                PDBProcessor.cleanup_temp_files(p)
