from typing import Optional, Dict, Any
import os
from graphs.graph_analysis2D import Nav17ToxinGraphAnalyzer


class DipoleAdapter:
    """Adapter to compute dipole using graphs analyzer, no legacy dependency."""

    def calculate_dipole_from_files(self, pdb_path: str, psf_path: Optional[str] = None) -> Dict[str, Any]:
        analyzer = Nav17ToxinGraphAnalyzer(pdb_folder="")
        if psf_path and os.path.exists(psf_path):
            return analyzer.calculate_dipole_moment_with_psf(pdb_path, psf_path)
        structure = analyzer.load_pdb_structure(pdb_path)
        return analyzer.calculate_dipole_moment(structure)

    def process_dipole_calculation(self, pdb_data: bytes, psf_data: Optional[bytes] = None) -> Dict[str, Any]:
        # Accept raw in-memory data (legacy-style), writing to temp files transiently
        import tempfile
        pdb_fd, pdb_path = tempfile.mkstemp(suffix=".pdb")
        os.close(pdb_fd)
        with open(pdb_path, "wb") as f:
            f.write(pdb_data if isinstance(pdb_data, (bytes, bytearray)) else pdb_data.encode("utf-8"))
        psf_path = None
        if psf_data:
            psf_fd, psf_path = tempfile.mkstemp(suffix=".psf")
            os.close(psf_fd)
            with open(psf_path, "wb") as f:
                f.write(psf_data if isinstance(psf_data, (bytes, bytearray)) else psf_data.encode("utf-8"))
        try:
            dip = self.calculate_dipole_from_files(pdb_path, psf_path)
            return {"success": True, "dipole": dip}
        finally:
            try:
                os.remove(pdb_path)
            except Exception:
                pass
            if psf_path:
                try:
                    os.remove(psf_path)
                except Exception:
                    pass
