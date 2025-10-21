#!/usr/bin/env python3
"""
Exporta archivos PDB de los péptidos filtrados por el motivo (NaSpTx-like)
usando la información almacenada en la base de datos (tabla Peptides, campo
`pdb_file`).

Características:
- Reutiliza el filtro existente `extractors.toxins_filter.search_toxins` para
  seleccionar candidatos.
- Para cada peptide_id filtrado, lee de la DB: peptide_id, (accession_number o
  peptide_name) y pdb_file.
- `pdb_file` puede ser:
  - una ruta a un archivo PDB existente (se copia al destino), o
  - el contenido del PDB en texto/bytes (se escribe un .pdb nuevo).
- Los archivos se guardan con nombre estable (accession_number si existe,
  si no, peptide_name saneado; si no, "peptide_<id>") en una carpeta de salida
  configurable (por defecto: "pdbs/filtered").

Uso rápido:
  python extractors/export_filtered_pdbs.py \
    --gap-min 3 --gap-max 6 --require-pair \
    --output-dir pdbs/filtered

Requisitos:
- Base de datos SQLite accesible (por defecto database/toxins.db)
- Tabla Peptides con columnas: peptide_id, sequence, pdb_file,
  y opcionalmente accession_number y/o peptide_name.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Tuple

# Rutas base del repo para import relativo estable
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from extractors.toxins_filter import search_toxins


def _sanitize_basename(name: str) -> str:
    """Sanear nombre para usarlo como basename de archivo."""
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in name)
    return safe.strip("._") or "unnamed"


def _pick_display_name(cur: sqlite3.Cursor) -> str:
    """Selecciona una columna de nombre razonable disponible en Peptides.

    Prioriza: accession_number, peptide_name, model_source. Si no hay ninguna,
    devuelve "peptide_name" como fallback (puede no existir; el código
    llamante debe manejar None).
    """
    cur.execute("PRAGMA table_info(Peptides)")
    cols = [c[1] for c in cur.fetchall()]
    lower = [c.lower() for c in cols]
    for cand in ("accession_number", "peptide_name", "model_source"):
        if cand in lower:
            return cols[lower.index(cand)]
    return "peptide_name"


def _fetch_peptide_row(conn: sqlite3.Connection, peptide_id: int) -> Optional[Tuple[int, Optional[str], Optional[str], Optional[bytes]]]:
    """Obtiene (peptide_id, display_name, accession_number, pdb_file) de Peptides."""
    cur = conn.cursor()
    name_col = _pick_display_name(cur)
    cur.execute(
        f"""
        SELECT peptide_id, {name_col} as display_name, accession_number, pdb_file
        FROM Peptides
        WHERE peptide_id = ?
        """,
        (peptide_id,),
    )
    row = cur.fetchone()
    return row if row else None


def _resolve_output_name(peptide_id: int, display_name: Optional[str], accession_number: Optional[str]) -> str:
    if accession_number and accession_number.strip():
        return _sanitize_basename(accession_number.strip())
    if display_name and str(display_name).strip():
        return _sanitize_basename(str(display_name).strip())
    return f"peptide_{peptide_id}"


def _write_pdb_to_path(pdb_data, target_path: Path, *, overwrite: bool) -> bool:
    """Escribe/copía PDB a target_path. Acepta ruta o contenido (str/bytes).

    Retorna True si creó o sobrescribió el archivo, False si se omitió
    por existir y overwrite=False.
    """
    target_path = target_path.with_suffix(".pdb")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists() and not overwrite:
        return False

    # Si pdb_data es una ruta existente, copiar
    if isinstance(pdb_data, (str, os.PathLike)) and os.path.exists(str(pdb_data)):
        shutil.copy2(str(pdb_data), str(target_path))
        return True

    # Si es bytes o texto, escribir
    if isinstance(pdb_data, (bytes, bytearray)):
        text = pdb_data.decode("utf-8", errors="ignore")
    else:
        text = str(pdb_data) if pdb_data is not None else ""

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")
    return True


def export_filtered_pdbs(
    *,
    db_path: Path,
    output_dir: Path,
    gap_min: int = 3,
    gap_max: int = 6,
    require_pair: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
) -> Tuple[int, int, int]:
    """Exporta PDBs de los péptidos filtrados.

    Retorna tupla (n_filtrados, n_exportados, n_omitidos).
    """
    db_path = Path(db_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    hits = search_toxins(gap_min=gap_min, gap_max=gap_max, require_pair=require_pair, db_path=str(db_path))
    if verbose:
        print(f"Candidatos filtrados: {len(hits)} (gap=[{gap_min},{gap_max}], require_pair={require_pair})")

    exported = 0
    skipped = 0
    with sqlite3.connect(str(db_path)) as conn:
        for i, hit in enumerate(hits, 1):
            pid = int(hit.get("peptide_id"))
            row = _fetch_peptide_row(conn, pid)
            if not row:
                if verbose:
                    print(f"[{i}/{len(hits)}] {pid}: sin fila en DB, se omite")
                skipped += 1
                continue
            peptide_id, display_name, accession_number, pdb_file = row
            base = _resolve_output_name(peptide_id, display_name, accession_number)
            target = output_dir / f"{base}.pdb"

            created = _write_pdb_to_path(pdb_file, target, overwrite=overwrite)
            if created:
                exported += 1
                if verbose:
                    print(f"[{i}/{len(hits)}] {base}: escrito en {target}")
            else:
                skipped += 1
                if verbose:
                    print(f"[{i}/{len(hits)}] {base}: ya existía, omitido (use --overwrite para reemplazar)")

    return len(hits), exported, skipped


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Exporta PDBs de péptidos filtrados desde la base de datos.")
    parser.add_argument("--db-path", type=Path, default=ROOT_DIR / "database/toxins.db", help="Ruta a la base de datos SQLite.")
    parser.add_argument("--output-dir", type=Path, default=ROOT_DIR / "pdbs/filtered", help="Directorio de salida para los .pdb generados.")
    parser.add_argument("--gap-min", type=int, default=3, help="Gap mínimo para el motivo (S→W).")
    parser.add_argument("--gap-max", type=int, default=6, help="Gap máximo para el motivo (S→W).")
    parser.add_argument("--require-pair", action="store_true", help="Exigir par hidrofóbico antes de S.")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescribir archivos existentes.")
    parser.add_argument("--verbose", action="store_true", help="Salida detallada.")

    args = parser.parse_args(argv)

    n_hits, n_out, n_skip = export_filtered_pdbs(
        db_path=args.db_path,
        output_dir=args.output_dir,
        gap_min=args.gap_min,
        gap_max=args.gap_max,
        require_pair=args.require_pair,
        overwrite=args.overwrite,
        verbose=args.verbose,
    )

    print(f"Exportación finalizada: candidatos={n_hits} escritos={n_out} omitidos={n_skip}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
