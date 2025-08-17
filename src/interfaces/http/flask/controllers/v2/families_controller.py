from flask import Blueprint, jsonify
import os, importlib
from typing import Dict, Any

from src.infrastructure.db.sqlite.family_repository_sqlite import SqliteFamilyRepository
from src.infrastructure.db.sqlite.structure_repository_sqlite import SqliteStructureRepository
from src.infrastructure.graphein.dipole_adapter import DipoleAdapter


families_v2 = Blueprint("families_v2", __name__)
# Load central config for defaults (overridden via DI)
try:
    _cfg_mod = importlib.import_module('src.config')
    _CFG = getattr(_cfg_mod, 'load_app_config')(os.getcwd())
except Exception:
    class _CFG:  # type: ignore
        db_path = "database/toxins.db"

_families = SqliteFamilyRepository(db_path=getattr(_CFG, 'db_path', 'database/toxins.db'))
_structures = SqliteStructureRepository(db_path=getattr(_CFG, 'db_path', 'database/toxins.db'))
_dipole = DipoleAdapter()


def configure_families_dependencies(
    *,
    families_repo: SqliteFamilyRepository = None,
    structures_repo: SqliteStructureRepository = None,
    dipole_service: DipoleAdapter = None,
):
    global _families, _structures, _dipole
    if families_repo is not None:
        _families = families_repo
    if structures_repo is not None:
        _structures = structures_repo
    if dipole_service is not None:
        _dipole = dipole_service


@families_v2.get("/v2/families")
def list_families_v2():
    try:
        # Keep same curated set as legacy UI
        families = [
            {"value": "μ-TRTX-Hh2a", "text": "μ-TRTX-Hh2a (Familia Hh2a)", "count": 0},
            {"value": "μ-TRTX-Hhn2b", "text": "μ-TRTX-Hhn2b (Familia Hhn2b)", "count": 0},
            {"value": "β-TRTX", "text": "β-TRTX (Familia Beta)", "count": 0},
            {"value": "ω-TRTX-Gr2a", "text": "ω-TRTX-Gr2a (Familia Omega)", "count": 0},
        ]

        for fam in families:
            try:
                peptides = _families.get_family_peptides(fam["value"])  # list of dict rows
                fam["count"] = len(peptides)
            except Exception:
                fam["count"] = 0

        return jsonify({"success": True, "families": families})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@families_v2.get("/v2/family-peptides/<string:family_name>")
def get_family_peptides_v2(family_name: str):
    try:
        peptides = _families.get_family_peptides(family_name)

        if family_name == "β-TRTX":
            payload: Dict[str, Any] = {
                "family_name": family_name,
                "family_type": "multiple_originals",
                "all_peptides": peptides,
                "total_count": len(peptides),
                "original_peptide": None,
                "modified_peptides": [],
            }
        else:
            original = None
            modified = []
            for p in peptides:
                if p.get("peptide_type") == "original":
                    original = p
                else:
                    modified.append(p)
            payload = {
                "family_name": family_name,
                "family_type": "original_plus_modified",
                "original_peptide": original,
                "modified_peptides": modified,
                "total_count": len(peptides),
                "modified_count": len(modified),
            }

        return jsonify({"success": True, "data": payload})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@families_v2.get("/v2/family-dipoles/<string:family_name>")
def get_family_dipoles_v2(family_name: str):
    """Calculate dipoles for all peptides in a family using DB-held PDB/PSF."""
    try:
        peptides = _families.get_family_peptides(family_name)

        dipole_results = []
        calculation_errors = []

        for peptide in peptides:
            try:
                pid = peptide["id"]
                pdb_data = _structures.get_pdb("nav1_7", pid)
                psf_data = _structures.get_psf("nav1_7", pid)

                if not pdb_data:
                    calculation_errors.append({
                        "peptide_code": peptide.get("peptide_code"),
                        "error": "No se encontraron datos PDB",
                    })
                    continue

                result = _dipole.process_dipole_calculation(pdb_data, psf_data)
                if not result.get("success"):
                    calculation_errors.append({
                        "peptide_code": peptide.get("peptide_code"),
                        "error": result.get("error", "Error desconocido en cálculo dipolar"),
                    })
                    continue

                # Ensure PDB/PSF are strings for frontend viewers
                pdb_text = pdb_data.decode("utf-8") if isinstance(pdb_data, (bytes, bytearray)) else pdb_data
                psf_text = None
                if psf_data is not None:
                    psf_text = psf_data.decode("utf-8") if isinstance(psf_data, (bytes, bytearray)) else psf_data

                dipole_results.append({
                    "peptide_id": pid,
                    "peptide_code": peptide.get("peptide_code"),
                    "ic50_value": peptide.get("ic50_value"),
                    "ic50_unit": peptide.get("ic50_unit"),
                    "pdb_data": pdb_text,
                    "psf_data": psf_text,
                    "dipole_data": result["dipole"],
                })
            except Exception as ex:
                calculation_errors.append({
                    "peptide_code": peptide.get("peptide_code"),
                    "error": f"Error procesando péptido: {str(ex)}",
                })

        if dipole_results:
            magnitudes = [r["dipole_data"]["magnitude"] for r in dipole_results]
            summary = {
                "total_proteins": len(dipole_results),
                "avg_magnitude": sum(magnitudes) / len(magnitudes),
                "min_magnitude": min(magnitudes),
                "max_magnitude": max(magnitudes),
                "calculation_errors": len(calculation_errors),
            }
        else:
            summary = {
                "total_proteins": 0,
                "avg_magnitude": 0,
                "min_magnitude": 0,
                "max_magnitude": 0,
                "calculation_errors": len(calculation_errors),
            }

        return jsonify({
            "success": True,
            "data": {
                "family": family_name,
                "dipole_results": dipole_results,
                "summary": summary,
                "errors": calculation_errors,
            },
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
