import os
import sqlite3

import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from extractors.cortar_pdb import PDBHandler
class PDBCutterInserter:
    def __init__(self, db_path: str = "database/toxins.db", pdb_folder: str = "pdbs/"):
        self.db_path = db_path
        self.pdb_folder = pdb_folder
        os.makedirs(self.pdb_folder, exist_ok=True)

    def _connect_db(self):
        return sqlite3.connect(self.db_path)

    def fetch_peptides(self):
        """Obtiene peptide_code y sequence desde Nav1_7_InhibitorPeptides."""
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT peptide_code, sequence FROM Nav1_7_InhibitorPeptides")
        peptides = cursor.fetchall()
        conn.close()
        return peptides

    def find_pdb_file(self, peptide_code: str) -> str:
        """Busca el archivo PDB correspondiente a un peptide_code."""
        pdb_path = os.path.join(self.pdb_folder, f"{peptide_code}.pdb")
        if not os.path.isfile(pdb_path):
            raise FileNotFoundError(f"No se encontró el archivo PDB: {pdb_path}")
        return pdb_path

    def cut_pdb_if_needed(self, pdb_path: str, expected_sequence: str) -> bytes:
        """
        Compara la secuencia del PDB con la esperada y corta si es necesario.
        Retorna el contenido binario del PDB final.
        """
        pdb_sequence = PDBHandler.extract_primary_sequence(pdb_path)

        if expected_sequence in pdb_sequence:
            start_index = pdb_sequence.index(expected_sequence) + 1
            end_index = start_index + len(expected_sequence) - 1

            cut_pdb_path = pdb_path.replace(".pdb", "_cut.pdb")
            PDBHandler.cut_pdb_by_residue_indices(pdb_path, cut_pdb_path, start_index, end_index)

            with open(cut_pdb_path, "rb") as f:
                pdb_data = f.read()
            os.remove(cut_pdb_path)
            return pdb_data
        else:
            print(f"[!] Secuencia no encontrada exactamente, guardando archivo completo: {os.path.basename(pdb_path)}")
            with open(pdb_path, "rb") as f:
                return f.read()

    def update_pdb_in_database(self, peptide_code: str, pdb_blob: bytes):
        """Actualiza el campo pdb_blob para un peptide_code."""
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Nav1_7_InhibitorPeptides
            SET pdb_blob = ?
            WHERE peptide_code = ?
        """, (pdb_blob, peptide_code))
        conn.commit()
        conn.close()

    def process_all_peptides(self):
        peptides = self.fetch_peptides()
        print(f"[•] Procesando {len(peptides)} péptidos...")

        for peptide_code, sequence in peptides:
            try:
                print(f"→ Procesando {peptide_code}...")
                pdb_path = self.find_pdb_file(peptide_code)
                pdb_blob = self.cut_pdb_if_needed(pdb_path, sequence)
                self.update_pdb_in_database(peptide_code, pdb_blob)
                print(f"  [✓] {peptide_code} actualizado en la base de datos.")
            except Exception as e:
                print(f"  [!] Error en {peptide_code}: {str(e)}")

if __name__ == "__main__":
    cutter_inserter = PDBCutterInserter(db_path="database/toxins.db", pdb_folder="pdbs/")
    cutter_inserter.process_all_peptides()
