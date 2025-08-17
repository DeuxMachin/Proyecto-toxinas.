from flask import Blueprint, jsonify, request
import os, importlib

from src.infrastructure.pdb.pdb_preprocessor_adapter import PDBPreprocessorAdapter
from src.infrastructure.fs.temp_file_service import TempFileService
from src.interfaces.http.flask.presenters.dipole_presenter import DipolePresenter
from src.application.use_cases.calculate_dipole import CalculateDipole, CalculateDipoleInput
from src.infrastructure.db.sqlite.structure_repository_sqlite import SqliteStructureRepository
from src.infrastructure.db.sqlite.metadata_repository_sqlite import SqliteMetadataRepository
from src.infrastructure.graphein.dipole_adapter import DipoleAdapter


dipole_v2 = Blueprint("dipole_v2", __name__)
# Load central config for defaults (overridden via DI)
try:
    _cfg_mod = importlib.import_module('src.config')
    _CFG = getattr(_cfg_mod, 'load_app_config')(os.getcwd())
except Exception:
    class _CFG:  # type: ignore
        db_path = "database/toxins.db"

_dip = DipoleAdapter()
_pdb = PDBPreprocessorAdapter()
_tmp = TempFileService()
_structures = SqliteStructureRepository(db_path=getattr(_CFG, 'db_path', 'database/toxins.db'))
_metadata = SqliteMetadataRepository(db_path=getattr(_CFG, 'db_path', 'database/toxins.db'))
_dipole_uc = CalculateDipole(_structures, _dip, _metadata)


def configure_dipole_dependencies(
    *,
    dipole_service: DipoleAdapter = None,
    pdb_preprocessor: PDBPreprocessorAdapter = None,
    temp_files: TempFileService = None,
    structures_repo: SqliteStructureRepository = None,
    metadata_repo: SqliteMetadataRepository = None,
    use_case: CalculateDipole = None,
):
    global _dip, _pdb, _tmp, _structures, _metadata, _dipole_uc
    if dipole_service is not None:
        _dip = dipole_service
    if pdb_preprocessor is not None:
        _pdb = pdb_preprocessor
    if temp_files is not None:
        _tmp = temp_files
    if structures_repo is not None:
        _structures = structures_repo
    if metadata_repo is not None:
        _metadata = metadata_repo
    if use_case is not None:
        _dipole_uc = use_case


@dipole_v2.post("/v2/dipole/<string:source>/<int:pid>")
def calculate_dipole_v2(source, pid):
    try:
        if source != 'nav1_7':
            return jsonify({"error": "Dipole solo disponible para nav1_7"}), 400

        res = _dipole_uc.execute(CalculateDipoleInput(source=source, pid=pid))
        if not res.get("success"):
            return jsonify({"error": res.get("error", "unknown")}), 404
        meta = {"source": source, "pid": pid}
        return jsonify(DipolePresenter.present(res, meta))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
