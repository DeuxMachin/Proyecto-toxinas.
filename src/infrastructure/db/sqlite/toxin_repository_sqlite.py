from typing import List, Tuple, Optional, Dict, Any
import sqlite3
import importlib

class SqliteToxinRepository:
    """Lightweight read-only repository for peptide listings and PDB fetch.

    This replaces the legacy DatabaseService usage with direct sqlite queries
    to avoid cross-layer dependency from infrastructure to legacy app services.
    """

    def __init__(self, db_path: str = "database/toxins.db") -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def list_toxins(self) -> List[Tuple[int, str]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            cur.execute("SELECT peptide_id, peptide_name FROM Peptides ORDER BY peptide_name")
            return cur.fetchall()
        finally:
            conn.close()

    def list_nav1_7(self) -> List[Tuple[int, str]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, peptide_code FROM Nav1_7_InhibitorPeptides ORDER BY peptide_code")
            return cur.fetchall()
        finally:
            conn.close()

    def get_pdb(self, source: str, peptide_id: int) -> Optional[bytes]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            if source == "toxinas":
                cur.execute("SELECT pdb_file FROM Peptides WHERE peptide_id = ?", (peptide_id,))
            elif source == "nav1_7":
                cur.execute("SELECT pdb_blob FROM Nav1_7_InhibitorPeptides WHERE id = ?", (peptide_id,))
            else:
                return None
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_complete(self, source: str, peptide_id: int) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            if source == "toxinas":
                cur.execute("SELECT pdb_file, peptide_name FROM Peptides WHERE peptide_id = ?", (peptide_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "pdb_data": row[0],
                        "name": row[1],
                        "ic50_value": None,
                        "ic50_unit": None,
                        "psf_data": None,
                    }
            elif source == "nav1_7":
                cur.execute(
                    "SELECT pdb_blob, peptide_code, ic50_value, ic50_unit, psf_blob FROM Nav1_7_InhibitorPeptides WHERE id = ?",
                    (peptide_id,),
                )
                row = cur.fetchone()
                if row:
                    data = {
                        "pdb_data": row[0],
                        "name": row[1],
                        "ic50_value": row[2],
                        "ic50_unit": row[3],
                        "psf_data": row[4],
                    }
                    try:
                        import importlib
                        dom = importlib.import_module('src.domain.models')
                        data["ic50"] = dom.IC50.from_value_unit(data["ic50_value"], data["ic50_unit"])
                    except Exception:
                        pass
                    return data
            return None
        finally:
            conn.close()

    # New: entity-returning helper for toxin
    def get_complete_entity(self, source: str, peptide_id: int):
        conn = self._conn()
        cur = conn.cursor()
        try:
            mappers = importlib.import_module('src.infrastructure.db.sqlite.mappers')
            if source == "toxinas":
                cur.execute("SELECT peptide_id, peptide_name, pdb_file FROM Peptides WHERE peptide_id = ?", (peptide_id,))
                row = cur.fetchone()
                if row:
                    return mappers.map_toxin_from_row(row[0], row[1], None, None, pdb=row[2])
            elif source == "nav1_7":
                cur.execute(
                    "SELECT id, peptide_code, ic50_value, ic50_unit, pdb_blob, psf_blob, sequence FROM Nav1_7_InhibitorPeptides WHERE id = ?",
                    (peptide_id,),
                )
                row = cur.fetchone()
                if row:
                    return mappers.map_toxin_from_row(row[0], row[1], row[2], row[3], pdb=row[4], psf=row[5], sequence=row[6])
            return None
        finally:
            conn.close()
