from typing import List, Tuple, Optional, Dict, Any
import sqlite3
import importlib


class SqliteFamilyRepository:
    def __init__(self, db_path: str = "database/toxins.db") -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _family_like_patterns(self, family_prefix: str) -> Tuple[str, str]:
        try:
            dom = importlib.import_module('src.domain.models')
            fam = dom.FamilyName(family_prefix)
            return fam.like_patterns()
        except Exception:
            return (
                f"{family_prefix}%",
                f"{family_prefix.replace('μ','mu').replace('β','beta').replace('ω','omega')}%",
            )

    def get_family_toxins(self, family_prefix: str) -> List[Tuple[int, str, Optional[float], Optional[str]]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            like1, like2 = self._family_like_patterns(family_prefix)
            cur.execute(
                """
                SELECT id, peptide_code, ic50_value, ic50_unit
                FROM Nav1_7_InhibitorPeptides
                WHERE peptide_code LIKE ? OR peptide_code LIKE ?
                ORDER BY peptide_code
                """,
                (like1, like2),
            )
            return cur.fetchall()
        finally:
            conn.close()

    def get_family_peptides(self, family_prefix: str) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            if family_prefix == 'β-TRTX':
                cur.execute(
                    """
                    SELECT id, peptide_code, ic50_value, ic50_unit, sequence, 'original' as peptide_type
                    FROM Nav1_7_InhibitorPeptides
                    WHERE peptide_code LIKE 'β-TRTX-%'
                    ORDER BY peptide_code ASC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, peptide_code, ic50_value, ic50_unit, sequence,
                           CASE WHEN peptide_code = ? THEN 'original' ELSE 'modified' END as peptide_type
                    FROM Nav1_7_InhibitorPeptides
                    WHERE peptide_code = ? OR peptide_code LIKE ?
                    ORDER BY peptide_type ASC, peptide_code ASC
                    """,
                    (family_prefix, family_prefix, f"{family_prefix}_%"),
                )
            rows = cur.fetchall()
            return [
                {
                    'id': r[0],
                    'peptide_code': r[1],
                    'ic50_value': r[2],
                    'ic50_unit': r[3],
                    'sequence': r[4],
                    'peptide_type': r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()

    # New: entity-returning helper assembling a Family from DB rows
    def get_family_entity(self, family_prefix: str):
        conn = self._conn()
        cur = conn.cursor()
        try:
            like1, like2 = self._family_like_patterns(family_prefix)
            cur.execute(
                """
                SELECT id, peptide_code, ic50_value, ic50_unit
                FROM Nav1_7_InhibitorPeptides
                WHERE peptide_code LIKE ? OR peptide_code LIKE ?
                ORDER BY peptide_code
                """,
                (like1, like2),
            )
            rows = cur.fetchall()
            mappers = importlib.import_module('src.infrastructure.db.sqlite.mappers')
            return mappers.map_family_from_rows(family_prefix, rows)
        finally:
            conn.close()

    # FamilyRepository (ports) compatibility: provide list_* aliases
    def list_family_toxins(self, family_prefix: str) -> List[Tuple[int, str, Optional[float], Optional[str]]]:
        """Alias to get_family_toxins to satisfy FamilyRepository port naming."""
        return self.get_family_toxins(family_prefix)

    def list_family_peptides(self, family_prefix: str) -> List[Dict[str, Any]]:
        """Alias to get_family_peptides to satisfy FamilyRepository port naming."""
        return self.get_family_peptides(family_prefix)

    def get_wt_toxin_data(self, peptide_code: str) -> Optional[Dict[str, Any]]:
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
            data: Dict[str, Any] = {
                'id': row[0],
                'name': row[1],
                'ic50_value': row[2],
                'ic50_unit': row[3],
                'pdb_data': row[4],
                'sequence': row[5],
            }
            try:
                dom = importlib.import_module('src.domain.models')
                data['ic50'] = dom.IC50.from_value_unit(data['ic50_value'], data['ic50_unit'])
            except Exception:
                pass
            return data
        finally:
            conn.close()
