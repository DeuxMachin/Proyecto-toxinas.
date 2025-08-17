from flask import Blueprint, jsonify
import os, importlib

from src.infrastructure.db.sqlite.metadata_repository_sqlite import SqliteMetadataRepository


metadata_v2 = Blueprint("metadata_v2", __name__)
# Load central config for defaults (overridden via DI)
try:
    _cfg_mod = importlib.import_module('src.config')
    _CFG = getattr(_cfg_mod, 'load_app_config')(os.getcwd())
except Exception:
    class _CFG:  # type: ignore
        db_path = "database/toxins.db"

_meta_repo = SqliteMetadataRepository(db_path=getattr(_CFG, 'db_path', 'database/toxins.db'))


def configure_metadata_dependencies(*, metadata_repo: SqliteMetadataRepository = None):
    global _meta_repo
    if metadata_repo is not None:
        _meta_repo = metadata_repo


@metadata_v2.get("/v2/metadata/toxin_name/<string:source>/<int:pid>")
def get_toxin_name_v2(source: str, pid: int):
    """Return the display name for a toxin/structure in a v2 endpoint.

    Shape mirrors legacy route but under /v2. Falls back to f"{source}_{pid}" if not found.
    """
    try:
        info = _meta_repo.get_toxin_info(source, pid)
        if info:
            return jsonify({"toxin_name": info[0]})
        return jsonify({"toxin_name": f"{source}_{pid}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
