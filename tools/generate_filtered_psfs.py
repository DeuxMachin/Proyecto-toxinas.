#!/usr/bin/env python3
"""
Genera PSF/PDB para los péptidos filtrados (tabla Peptides) y guarda los archivos
en tools/filtered nombrados por accession_number. Captura logs por péptido y
reintenta los fallidos al final mostrando el tail del log para depurar.

Extensión: permite generar PSF/PDB directamente desde un archivo PDB arbitrario
pasado por CLI, útil para procesar proteínas sueltas (ej. wild type) y dejar la
salida en una carpeta `generated` junto al archivo original.
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Rutas base
root_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root_dir))

# Import filtro de toxinas
try:
    from extractors.toxins_filter import search_toxins
except Exception as e:
    print(f"ERROR importando search_toxins: {e}")
    sys.exit(1)

# Fallback para crear PDB temporal desde texto/bytes
def create_temp_pdb_file(content: str) -> str:
    fd, tmp = tempfile.mkstemp(suffix=".pdb", prefix="peptide_", text=True)
    os.close(fd)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp

def tail_text(text: str, n: int = 60) -> str:
    lines = text.strip().splitlines()
    return "\n".join(lines[-n:]) if len(lines) > n else text

class FilteredPSFGenerator:
    def __init__(self,
                 db_path="database/toxins.db",
                 tcl_script_path="resources/psf_gen.tcl",
                 topology_files=None,
                 output_base="tools/filtered",
                 default_chain="PROA",
                 disulfide_cutoff=2.3):
        # Rutas absolutas
        self.db_path = (root_dir / db_path).resolve()
        self.tcl_script_path = (root_dir / tcl_script_path).resolve()
        self.output_base = (root_dir / output_base).resolve()
        self.logs_dir = self.output_base / "logs"
        self.default_chain = default_chain
        self.disulfide_cutoff = disulfide_cutoff

        if topology_files is None:
            topology_files = ["resources/top_all36_prot.rtf"]
        self.topology_files = [(root_dir / f).resolve() for f in topology_files]

        # Directorios
        self.output_base.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Verificación
        self._verify_files()

    def _verify_files(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"No existe la base de datos: {self.db_path}")
        if not self.tcl_script_path.exists():
            raise FileNotFoundError(f"No existe el script Tcl: {self.tcl_script_path}")
        for top in self.topology_files:
            if not top.exists():
                raise FileNotFoundError(f"No existe topología: {top}")
        if not shutil.which("vmd"):
            print("Advertencia: no se encontró 'vmd' en PATH. Asegúrate de tener VMD instalado.")

    def get_filtered_peptides(self, gap_min=3, gap_max=6, require_pair=False):
        hits = search_toxins(
            gap_min=gap_min,
            gap_max=gap_max,
            require_pair=require_pair,
            db_path=str(self.db_path)
        )
        return hits

    def get_peptide_data(self, peptide_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT p.peptide_id, p.peptide_name, p.pdb_file, p.accession_number
                FROM Peptides p
                WHERE p.peptide_id = ?
            """, (peptide_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "peptide_id": row[0],
                "peptide_name": row[1],
                "pdb_data": row[2],
                "accession_number": row[3] or f"UNK_{row[0]}",
            }
        finally:
            conn.close()

    def _run_vmd_subprocess(
        self,
        pdb_path: Path,
        out_prefix: Path,
        chain: Optional[str] = None,
        disulfide_cutoff: Optional[float] = None,
    ) -> Tuple[bool, str]:
        # Script TCL por peptide
        tops_tcl = "{" + " ".join(f'"{t}"' for t in self.topology_files) + "}"
        chain_id = chain or self.default_chain
        cutoff = disulfide_cutoff or self.disulfide_cutoff
        tcl_body = f"""
package require psfgen
source "{self.tcl_script_path}"
set res [build_psf_with_disulfides "{pdb_path}" {tops_tcl} "{out_prefix}" "{chain_id}" {cutoff}]
puts "PSF_OUT:[lindex $res 0]"
puts "PDB_OUT:[lindex $res 1]"
exit
"""
        # Archivo TCL temporal
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tcl", delete=False) as tmp_tcl:
            tmp_tcl.write(tcl_body)
            tcl_path = Path(tmp_tcl.name)

        try:
            # Ejecutar VMD capturando stdout/err
            completed = subprocess.run(
                ["vmd", "-dispdev", "text", "-e", str(tcl_path)],
                capture_output=True,
                text=True,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            ok = completed.returncode == 0
            # Retornar estado y stdout+stderr
            return ok, stdout + ("\n" + stderr if stderr else "")
        finally:
            try:
                tcl_path.unlink(missing_ok=True)
            except Exception:
                pass

    def generate_psf_for_peptide_subprocess(self, peptide_data, verbose=False):
        accession = peptide_data["accession_number"]
        pdb_data = peptide_data["pdb_data"]

        if not pdb_data:
            return False, f"{accession}: sin PDB"

        # Crear PDB temporal si es contenido; si es path existente, úsalo
        created_temp = False
        tmp_pdb = None
        try:
            if isinstance(pdb_data, str) and os.path.exists(pdb_data):
                tmp_pdb = Path(pdb_data).resolve()
            else:
                content = (
                    pdb_data.decode("utf-8", errors="ignore")
                    if isinstance(pdb_data, (bytes, bytearray))
                    else str(pdb_data)
                )
                tmp_pdb = Path(create_temp_pdb_file(content)).resolve()
                created_temp = True

            out_prefix = (self.output_base / accession).resolve()
            ok, out_text = self._run_vmd_subprocess(tmp_pdb, out_prefix)

            # Guardar log
            log_path = self.logs_dir / f"{accession}.log"
            log_path.write_text(out_text, encoding="utf-8")

            # Verificar archivos
            psf = Path(str(out_prefix) + ".psf")
            pdb = Path(str(out_prefix) + ".pdb")
            success = ok and psf.exists() and pdb.exists()

            if verbose:
                print(tail_text(out_text, 80))

            return success, str(log_path)
        finally:
            if created_temp and tmp_pdb:
                try:
                    tmp_pdb.unlink(missing_ok=True)
                except Exception:
                    pass

    def generate_psf_from_local_pdb(
        self,
        pdb_file: Path,
        output_dir: Optional[Path] = None,
        *,
        chain: Optional[str] = None,
        disulfide_cutoff: Optional[float] = None,
        verbose: bool = False,
    ) -> Dict[str, object]:
        """Genera PSF/PDB a partir de un archivo PDB local.

        Retorna un diccionario con rutas de salida y estado.
        """
        pdb_path = Path(pdb_file).expanduser().resolve()
        if not pdb_path.exists():
            raise FileNotFoundError(f"No existe el archivo PDB: {pdb_path}")

        if output_dir is None:
            output_base = pdb_path.parent / "generated"
        else:
            output_base = Path(output_dir).expanduser().resolve()

        output_base.mkdir(parents=True, exist_ok=True)
        logs_dir = (output_base / "logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        out_prefix = (output_base / pdb_path.stem).resolve()
        ok, out_text = self._run_vmd_subprocess(
            pdb_path,
            out_prefix,
            chain=chain,
            disulfide_cutoff=disulfide_cutoff,
        )

        log_path = logs_dir / f"{pdb_path.stem}.log"
        log_path.write_text(out_text, encoding="utf-8")

        psf_path = out_prefix.with_suffix(".psf")
        pdb_out_path = out_prefix.with_suffix(".pdb")

        if verbose:
            print(tail_text(out_text, 80))

        return {
            "ok": ok and psf_path.exists() and pdb_out_path.exists(),
            "psf": psf_path,
            "pdb": pdb_out_path,
            "log": log_path,
            "stdout": out_text,
        }

    def process_all_filtered(self, gap_min=3, gap_max=6, require_pair=False):
        hits = self.get_filtered_peptides(gap_min, gap_max, require_pair)
        total = len(hits)
        print(f"Filtrados: {total}")

        successes = []
        failures = []

        for i, hit in enumerate(hits, 1):
            peptide_id = hit.get("peptide_id") if isinstance(hit, dict) else hit
            pdata = self.get_peptide_data(peptide_id)
            if not pdata:
                print(f"[{i}/{total}] {peptide_id}: sin datos")
                failures.append((peptide_id, "sin_datos", None))
                continue

            accession = pdata["accession_number"]
            print(f"[{i}/{total}] {accession}: generando...", end="", flush=True)
            ok, log_path = self.generate_psf_for_peptide_subprocess(pdata, verbose=False)
            if ok:
                successes.append(accession)
                print(" OK")
            else:
                failures.append((peptide_id, accession, log_path))
                print(" FAIL")

        print(f"\nResumen: OK={len(successes)} FAIL={len(failures)}")
        if failures:
            print("Reintentando fallidos en modo verbose...")
            for idx, (peptide_id, accession, log_path) in enumerate(failures, 1):
                pdata = self.get_peptide_data(peptide_id)
                if not pdata:
                    continue
                print(f"\n[Retry {idx}/{len(failures)}] {accession}")
                ok, retry_log = self.generate_psf_for_peptide_subprocess(pdata, verbose=True)
                print(f"Log: {retry_log}")
                if ok:
                    print("Retry OK")
                else:
                    print("Retry FAIL")

        print(f"\nLogs: {self.logs_dir}")
        print(f"Outputs: {self.output_base}")
        return successes, failures

    def find_toxin_for_comparison(self, target_peptide_code="μ-TRTX-Cg4a"):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, peptide_code, sequence, ic50_value, ic50_unit
                FROM Nav1_7_InhibitorPeptides
                WHERE peptide_code = ?
            """, (target_peptide_code,))
            row = cur.fetchone()
            if row:
                print(f"Referencia: {row[1]} (ID {row[0]}) IC50={row[3]} {row[4]}")
        finally:
            conn.close()

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera PSF/PDB desde la base de datos o desde un archivo PDB suelto."
    )
    parser.add_argument("--pdb-file", type=Path, help="Ruta a un archivo PDB a procesar directamente.")
    parser.add_argument("--output-dir", type=Path, help="Directorio de salida opcional para el modo --pdb-file.")
    parser.add_argument("--chain", default="PROA", help="ID de cadena a usar en psfgen (default: PROA).")
    parser.add_argument("--disulfide-cutoff", type=float, default=2.3,
                        help="Distancia de corte para detectar puentes disulfuro (Å).")
    parser.add_argument("--gap-min", type=int, default=3, help="Gap mínimo para el filtro de toxinas.")
    parser.add_argument("--gap-max", type=int, default=6, help="Gap máximo para el filtro de toxinas.")
    parser.add_argument("--require-pair", action="store_true", help="Requiere par hidrofóbico en el filtro.")
    parser.add_argument("--skip-reference", action="store_true", help="Omitir impresión de toxina de referencia.")
    parser.add_argument("--verbose", action="store_true", help="Mostrar tail de logs en consola.")

    args = parser.parse_args(argv)

    gen = FilteredPSFGenerator(
        default_chain=args.chain,
        disulfide_cutoff=args.disulfide_cutoff,
    )

    if args.pdb_file:
        result = gen.generate_psf_from_local_pdb(
            args.pdb_file,
            args.output_dir,
            chain=args.chain,
            disulfide_cutoff=args.disulfide_cutoff,
            verbose=args.verbose,
        )

        psf_status = "OK" if result["ok"] else "FAIL"
        print(f"[{psf_status}] PDB: {args.pdb_file}")
        print(f"  • PSF: {result['psf']}")
        print(f"  • PDB: {result['pdb']}")
        print(f"  • Log: {result['log']}")
        return 0 if result["ok"] else 1

    if not args.skip_reference:
        gen.find_toxin_for_comparison("μ-TRTX-Cg4a")

    gen.process_all_filtered(
        gap_min=args.gap_min,
        gap_max=args.gap_max,
        require_pair=args.require_pair,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())