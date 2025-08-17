from typing import Optional, List, Tuple, Dict, Any
import sqlite3
import importlib


class SqliteStructureRepository:
    def __init__(self, db_path: str = "database/toxins.db") -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get_pdb(self, source: str, peptide_id: int) -> Optional[bytes]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            if source == 'toxinas':
                cur.execute("SELECT pdb_file FROM Peptides WHERE peptide_id = ?", (peptide_id,))
            elif source == 'nav1_7':
                cur.execute("SELECT pdb_blob FROM Nav1_7_InhibitorPeptides WHERE id = ?", (peptide_id,))
            else:
                return None
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else None
        finally:
            conn.close()

    def get_psf(self, source: str, peptide_id: int) -> Optional[bytes]:
        if source != 'nav1_7':
            return None
        conn = self._conn()
        cur = conn.cursor()
        try:
            cur.execute("SELECT psf_blob FROM Nav1_7_InhibitorPeptides WHERE id = ?", (peptide_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] else None
        finally:
            conn.close()

    # Convenience queries to support family/WT flows
    def list_family_members(self, family_prefix: str) -> List[Tuple[int, str, Optional[float], Optional[str]]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            # Normalize using domain VO (import lazily to avoid hard dependency during linting)
            try:
                import importlib
                dom = importlib.import_module('src.domain.models')
                fam = dom.FamilyName(family_prefix)
                like1, like2 = fam.like_patterns()
            except Exception:
                like1, like2 = (f"{family_prefix}%", f"{family_prefix.replace('μ','mu').replace('β','beta').replace('ω','omega')}%")
            cur.execute(
                """
                SELECT id, peptide_code, ic50_value, ic50_unit
                FROM Nav1_7_InhibitorPeptides
                WHERE peptide_code LIKE ? OR peptide_code LIKE ?
                """,
                (like1, like2),
            )
            return cur.fetchall()
        finally:
            conn.close()

    def get_wt_by_code(self, peptide_code: str) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, peptide_code, ic50_value, ic50_unit, pdb_blob, sequence
                FROM Nav1_7_InhibitorPeptides
                WHERE peptide_code = ?
                """,
                (peptide_code,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                'id': row[0],
                'name': row[1],
                'ic50_value': row[2],
                'ic50_unit': row[3],
                'pdb_data': row[4],
                'sequence': row[5],
            }
        finally:
            conn.close()

    # New: entity-returning helper
    def get_structure_entity(self, source: str, peptide_id: int):
        conn = self._conn()
        cur = conn.cursor()
        try:
            if source == 'toxinas':
                cur.execute("SELECT peptide_id, peptide_name, pdb_file FROM Peptides WHERE peptide_id = ?", (peptide_id,))
                row = cur.fetchone()
                if not row:
                    return None
                mappers = importlib.import_module('src.infrastructure.db.sqlite.mappers')
                return mappers.map_structure_from_row(row[0], row[1], row[2], None, None)
            elif source == 'nav1_7':
                cur.execute(
                    "SELECT id, peptide_code, pdb_blob, psf_blob, sequence FROM Nav1_7_InhibitorPeptides WHERE id = ?",
                    (peptide_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                mappers = importlib.import_module('src.infrastructure.db.sqlite.mappers')
                return mappers.map_structure_from_row(row[0], row[1], row[2], row[3], row[4])
            return None
        finally:
            conn.close()
