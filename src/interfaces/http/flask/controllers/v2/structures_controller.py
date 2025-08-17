from flask import Blueprint, jsonify, Response
import os, importlib

from src.infrastructure.db.sqlite.structure_repository_sqlite import SqliteStructureRepository


structures_v2 = Blueprint("structures_v2", __name__, url_prefix="/v2/structures")
# Load central config for defaults (overridden via DI)
try:
    _cfg_mod = importlib.import_module('src.config')
    _CFG = getattr(_cfg_mod, 'load_app_config')(os.getcwd())
except Exception:
    class _CFG:  # type: ignore
        db_path = "database/toxins.db"

_structures = SqliteStructureRepository(db_path=getattr(_CFG, 'db_path', 'database/toxins.db'))


def configure_structures_dependencies(*, structures_repo: SqliteStructureRepository = None):
    global _structures
    if structures_repo is not None:
        _structures = structures_repo


@structures_v2.get("/<string:source>/<int:pid>/pdb")
def get_structure_pdb(source: str, pid: int):
    try:
        pdb_blob = _structures.get_pdb(source, pid)
        if not pdb_blob:
            return jsonify({"error": "PDB not found"}), 404
        if isinstance(pdb_blob, bytes):
            text = pdb_blob.decode("utf-8", errors="replace")
        else:
            text = str(pdb_blob)
        return Response(text, mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@structures_v2.get("/<string:source>/<int:pid>/psf")
def get_structure_psf(source: str, pid: int):
    try:
        if source != "nav1_7":
            return jsonify({"error": "PSF available only for nav1_7"}), 400
        psf_blob = _structures.get_psf(source, pid)
        if not psf_blob:
            return jsonify({"error": "PSF not found"}), 404
        if isinstance(psf_blob, bytes):
            text = psf_blob.decode("utf-8", errors="replace")
        else:
            text = str(psf_blob)
        return Response(text, mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
