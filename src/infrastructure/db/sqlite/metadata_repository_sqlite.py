from typing import Optional, Tuple, Dict, Any
import sqlite3
import importlib

class SqliteMetadataRepository:
    def __init__(self, db_path: str = "database/toxins.db") -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get_toxin_info(self, source: str, peptide_id: int) -> Optional[Tuple[str, Optional[float], Optional[str]]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            if source == 'toxinas':
                cur.execute("SELECT peptide_name FROM Peptides WHERE peptide_id = ?", (peptide_id,))
                row = cur.fetchone()
                return (row[0], None, None) if row else None
            elif source == 'nav1_7':
                cur.execute("SELECT peptide_code, ic50_value, ic50_unit FROM Nav1_7_InhibitorPeptides WHERE id = ?", (peptide_id,))
                row = cur.fetchone()
                return row if row else None
            return None
        finally:
            conn.close()

    def get_complete_toxin_data(self, source: str, peptide_id: int) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            if source == 'toxinas':
                cur.execute("SELECT pdb_file, peptide_name FROM Peptides WHERE peptide_id = ?", (peptide_id,))
                row = cur.fetchone()
                if row:
                    return {
                        'pdb_data': row[0],
                        'name': row[1],
                        'ic50_value': None,
                        'ic50_unit': None,
                        'psf_data': None,
                    }
            elif source == 'nav1_7':
                cur.execute("SELECT pdb_blob, peptide_code, ic50_value, ic50_unit, psf_blob FROM Nav1_7_InhibitorPeptides WHERE id = ?", (peptide_id,))
                row = cur.fetchone()
                if row:
                    data = {
                        'pdb_data': row[0],
                        'name': row[1],
                        'ic50_value': row[2],
                        'ic50_unit': row[3],
                        'psf_data': row[4],
                    }
                    try:
                        import importlib
                        dom = importlib.import_module('src.domain.models')
                        data['ic50'] = dom.IC50.from_value_unit(data['ic50_value'], data['ic50_unit'])
                    except Exception:
                        pass
                    return data
            return None
        finally:
            conn.close()

    # New: entity-returning helper (non-breaking)
    def get_complete_toxin_entity(self, source: str, peptide_id: int):
        """Return a domain Toxin entity when possible.

        Keeps old methods intact; this is an additive API used by v2 use cases.
        """
        conn = self._conn()
        cur = conn.cursor()
        try:
            mappers = importlib.import_module('src.infrastructure.db.sqlite.mappers')
            if source == 'toxinas':
                cur.execute(
                    "SELECT peptide_id, peptide_name, pdb_file FROM Peptides WHERE peptide_id = ?",
                    (peptide_id,),
                )
                row = cur.fetchone()
                if row:
                    # id, code/name, pdb
                    return mappers.map_toxin_from_row(row[0], row[1], None, None, pdb=row[2], psf=None, sequence=None)
            elif source == 'nav1_7':
                cur.execute(
                    """
                    SELECT id, peptide_code, ic50_value, ic50_unit, pdb_blob, psf_blob, sequence
                    FROM Nav1_7_InhibitorPeptides WHERE id = ?
                    """,
                    (peptide_id,),
                )
                row = cur.fetchone()
                if row:
                    return mappers.map_toxin_from_row(
                        id_=row[0],
                        code=row[1],
                        ic50_value=row[2],
                        ic50_unit=row[3],
                        pdb=row[4],
                        psf=row[5],
                        sequence=row[6],
                    )
            return None
        finally:
            conn.close()

    def get_family_toxins(self, family_prefix: str):
        conn = self._conn()
        cur = conn.cursor()
        try:
            try:
                import importlib
                dom = importlib.import_module('src.domain.models')
                fam = dom.FamilyName(family_prefix)
                like1, like2 = fam.like_patterns()
            except Exception:
                like1 = f"{family_prefix}%"
                like2 = f"{family_prefix.replace('μ','mu').replace('β','beta').replace('ω','omega')}%"
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

    def get_family_peptides(self, family_prefix: str):
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
                import importlib
                dom = importlib.import_module('src.domain.models')
                data['ic50'] = dom.IC50.from_value_unit(data['ic50_value'], data['ic50_unit'])
            except Exception:
                pass
            return data
        finally:
            conn.close()

    # New: entity-returning helper for WT by code
    def get_wt_toxin_entity(self, peptide_code: str):
        conn = self._conn()
        cur = conn.cursor()
        try:
            mappers = importlib.import_module('src.infrastructure.db.sqlite.mappers')
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
            return mappers.map_toxin_from_row(
                id_=row[0],
                code=row[1],
                ic50_value=row[2],
                ic50_unit=row[3],
                pdb=row[4],
                psf=None,
                sequence=row[5],
            )
        finally:
            conn.close()
