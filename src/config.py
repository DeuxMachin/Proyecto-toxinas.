from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    db_path: str
    pdb_dir: str
    psf_dir: str
    wt_reference_path: str


def _resolve(base: Optional[str], path: str) -> str:
    if os.path.isabs(path):
        return path
    if base:
        return os.path.abspath(os.path.join(base, path))
    return os.path.abspath(path)


def load_app_config(project_root: Optional[str] = None) -> AppConfig:
    """Load application configuration for v2 from environment with sane defaults.

    Environment variables:
      - TOXINS_DB_PATH: path to SQLite DB (default: database/toxins.db)
      - PDB_DIR: directory where PDB files live (default: pdbs)
      - PSF_DIR: directory where PSF files live (default: psfs)
      - WT_REFERENCE_PATH: default WT reference PDB (default: pdbs/WT/hwt4_Hh2a_WT.pdb)
    """
    db_path = os.getenv('TOXINS_DB_PATH', 'database/toxins.db')
    pdb_dir = os.getenv('PDB_DIR', 'pdbs')
    psf_dir = os.getenv('PSF_DIR', 'psfs')
    wt_reference_path = os.getenv('WT_REFERENCE_PATH', os.path.join(pdb_dir, 'WT', 'hwt4_Hh2a_WT.pdb'))

    base = project_root or os.getenv('PROJECT_ROOT')
    return AppConfig(
        db_path=_resolve(base, db_path),
        pdb_dir=_resolve(base, pdb_dir),
        psf_dir=_resolve(base, psf_dir),
        wt_reference_path=_resolve(base, wt_reference_path),
    )
