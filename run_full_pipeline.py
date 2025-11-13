#!/usr/bin/env python3
"""
Pipeline maestro (interactivo/CLI) UniProt → DB → artefactos:

Flujo por defecto:
    1) Crear/verificar DB
    2) Buscar accessions y descargar XML + insertar Proteins
    3) Extraer/descargar/cortar péptidos → Peptides
    4) Insertar dataset Nav1.7 curado
    5) Adjuntar blobs PDB/PSF locales a Nav1.7
    6) Exportar PDBs filtrados (skip si existen y no --overwrite)
    7) Generar PSF/PDB para filtrados (skip si existen y no --overwrite; omitir con --no-psf)
    8) Construir JSON IA (skip si existe y no --overwrite; omitir con --no-ai)
    9) Resumen de tiempos

CLI:
    python run_full_pipeline.py [--query "..."] [--gap-min 3 --gap-max 6 --require-pair]
                                                            [--no-psf] [--no-ai] [--overwrite]

Requisitos: requests, aiohttp, biopython, mdanalysis, certifi, VMD/psfgen (para PSF), configuración IA.
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import argparse

try:
    from database.create_db import create_database, DB_PATH as DEFAULT_DB_PATH
    from extractors.uniprot import UniProtPipeline
    from extractors.peptide_extractor import PeptideExtractor
    from loaders.instert_Nav1_7 import insert_peptides as insert_nav1_7_peptides
    from loaders.instert_Nav1_7_pdb_psf import PDBAndPSFInserter
    # Extensiones offline del pipeline
    from extractors.export_filtered_pdbs import export_filtered_pdbs as export_filtered_pdbs_cli
    from extractors.generate_filtered_psfs import FilteredPSFGenerator
    from tools.export_filtered_accessions_nav1_7 import (
        process_filtered_hits as process_ai_filtered_hits,
    )
except ModuleNotFoundError as e:
    print(f"Error importando módulos del proyecto: {e}")
    sys.exit(1)


def human_time(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.1f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{int(m)}m {s:.1f}s"
    h, m = divmod(m, 60)
    return f"{int(h)}h {int(m)}m {s:.1f}s"


def ensure_database(db_path: str):
    """Crea la base de datos si no existe (idempotente)."""
    first_time = not os.path.exists(db_path)
    create_database()
    if first_time:
        print(f"[DB] Creada base de datos en {db_path}")


async def run_peptide_stage(xml_path: str, db_path: str, concurrency: int = 5) -> Dict[str, Any]:
    """Ejecuta extracción/corte de péptidos y devuelve métricas."""
    peptide_extractor = PeptideExtractor(db_path=db_path)
    t0 = time.perf_counter()
    peptide_ids = await peptide_extractor.process_xml_file(xml_path, max_concurrent=concurrency)
    return {
        "peptides_inserted": len(peptide_ids),
        "peptide_ids": peptide_ids,
        "time_seconds": time.perf_counter() - t0
    }


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Pipeline completo UniProt→DB→Artefactos")
    parser.add_argument("--query", help="Query para UniProt (si falta, se pedirá por consola)")
    parser.add_argument("--gap-min", type=int, default=3, help="Gap mínimo del motivo")
    parser.add_argument("--gap-max", type=int, default=6, help="Gap máximo del motivo")
    parser.add_argument("--require-pair", action="store_true", help="Exigir par hidrofóbico")
    parser.add_argument("--no-psf", action="store_true", help="No generar PSF/PDB filtrados")
    parser.add_argument("--no-ai", action="store_true", help="No construir JSON IA")
    parser.add_argument("--overwrite", action="store_true", help="Recalcular/reescribir artefactos existentes")

    args = parser.parse_args(argv)

    print("[PIPELINE] Inicio del proceso completo")
    query = args.query or input("🔍 Ingresa una query para buscar proteínas en UniProt: ").strip()
    if not query:
        print("No se ingresó una query. Saliendo.")
        return

    # Parámetros base del motivo
    gap_min = args.gap_min
    gap_max = args.gap_max
    require_pair = args.require_pair

    timings = {}
    t_global_start = time.perf_counter()

    # 1. Base de datos
    t0 = time.perf_counter()
    ensure_database(DEFAULT_DB_PATH)
    timings['create_database'] = time.perf_counter() - t0

    # 2. Accessions
    pipeline = UniProtPipeline(db_path=DEFAULT_DB_PATH)
    t1 = time.perf_counter()
    accessions, name_prefix = pipeline.fetch_accessions(query)
    timings['fetch_accessions'] = time.perf_counter() - t1
    if not accessions:
        print("No se obtuvieron accessions. Saliendo.")
        return

    # 3. Descarga XML + inserción Proteins
    xml_path = f"data/processed/{name_prefix}_data.xml"
    t2 = time.perf_counter()
    asyncio.run(pipeline.fetch_all_async(accessions, xml_path))
    timings['download_and_insert_proteins'] = time.perf_counter() - t2

    # 4. Péptidos (extracción + descarga + corte)
    print(f"[PEPTIDES] Procesando péptidos desde {xml_path}")
    t3 = time.perf_counter()
    peptide_stage = asyncio.run(run_peptide_stage(xml_path, DEFAULT_DB_PATH, concurrency=5))
    timings['extract_and_insert_peptides'] = peptide_stage['time_seconds']
    timings['peptides_inserted'] = peptide_stage['peptides_inserted']

    # 5. Insertar dataset Nav1.7
    t4 = time.perf_counter()
    try:
        insert_nav1_7_peptides()
        timings['insert_nav1_7'] = time.perf_counter() - t4
    except Exception as e:
        print(f"[Nav1.7][ERROR] Falló inserción de péptidos Nav1.7: {e}")
        timings['insert_nav1_7'] = time.perf_counter() - t4

    # 6. Actualizar blobs PDB/PSF para Nav1.7
    t5 = time.perf_counter()
    try:
        inserter = PDBAndPSFInserter(db_path=DEFAULT_DB_PATH, pdb_folder="pdbs/", psf_folder="psfs/")
        inserter.process_all_peptides()
        timings['update_nav1_7_blobs'] = time.perf_counter() - t5
    except Exception as e:
        print(f"[Nav1.7][ERROR] Falló actualización de blobs PDB/PSF: {e}")
        timings['update_nav1_7_blobs'] = time.perf_counter() - t5

    # 7. Exportar PDBs de péptidos filtrados (útil para inspección)
    t6 = time.perf_counter()
    try:
        n_hits, n_out, n_skip = export_filtered_pdbs_cli(
            db_path=Path(DEFAULT_DB_PATH),
            output_dir=Path("pdbs/filtered"),
            gap_min=gap_min,
            gap_max=gap_max,
            require_pair=require_pair,
            overwrite=args.overwrite,
            verbose=False,
        )
        timings['export_filtered_pdbs'] = time.perf_counter() - t6
        timings['export_filtered_pdbs_counts'] = (n_hits, n_out, n_skip)
        print(f"[FILTERED PDBs] candidatos={n_hits} escritos={n_out} omitidos={n_skip}")
    except Exception as e:
        print(f"[FILTERED PDBs][ERROR] Exportación falló: {e}")
        timings['export_filtered_pdbs'] = time.perf_counter() - t6

    # 8. Generar PSF/PDB para filtrados (salida consumida por la UI de dipolos)
    t7 = time.perf_counter()
    if args.no_psf:
        print("[PSF] Omitido por --no-psf")
        timings['generate_filtered_psfs'] = 0.0
    else:
        try:
            gen = FilteredPSFGenerator(
                db_path=DEFAULT_DB_PATH,
                output_base="pdbs/filtered_psfs",
                default_chain="PROA",
                disulfide_cutoff=2.3,
            )

            # En lugar de regenerar todo, saltar existentes salvo --overwrite
            hits = gen.get_filtered_peptides(gap_min=gap_min, gap_max=gap_max, require_pair=require_pair)
            total = len(hits)
            ok_count = 0
            skipped = 0
            for i, hit in enumerate(hits, 1):
                pid = hit.get("peptide_id") if isinstance(hit, dict) else hit
                pdata = gen.get_peptide_data(pid)
                if not pdata:
                    continue
                out_prefix = (gen.output_base / pdata["accession_number"]).resolve()
                psf_path = out_prefix.with_suffix(".psf")
                pdb_out = out_prefix.with_suffix(".pdb")
                if (not args.overwrite) and psf_path.exists() and pdb_out.exists():
                    skipped += 1
                    continue
                ok, _log = gen.generate_psf_for_peptide_subprocess(pdata, verbose=False)
                if ok:
                    ok_count += 1

            timings['generate_filtered_psfs'] = time.perf_counter() - t7
            print(f"[PSF] OK={ok_count} SKIP={skipped} TOTAL={total}")
        except Exception as e:
            print(f"[PSF][ERROR] Generación PSF/PDB falló: {e} (verifica VMD/psfgen y resources/*)")
            timings['generate_filtered_psfs'] = time.perf_counter() - t7

    # 9. Construir JSON con análisis IA de accessions filtrados
    t8 = time.perf_counter()
    if args.no_ai:
        print("[AI] Omitido por --no-ai")
        timings['ai_analysis'] = 0.0
        timings['ai_items'] = 0
    else:
        try:
            out_json = Path("exports/filtered_accessions_nav1_7_analysis.json")
            # Si existe y no --overwrite, saltar
            if out_json.exists() and not args.overwrite and out_json.stat().st_size > 10:
                print(f"[AI] Saltado: {out_json} ya existe (use --overwrite para recalcular)")
                timings['ai_analysis'] = time.perf_counter() - t8
                # Contar items existentes para el resumen
                try:
                    existing = json.loads(out_json.read_text(encoding="utf-8"))
                    timings['ai_items'] = len(existing) if isinstance(existing, list) else 0
                except Exception:
                    timings['ai_items'] = 0
            else:
                log_path = "exports/process_log.txt"
                ai_results = process_ai_filtered_hits(
                    db_path=DEFAULT_DB_PATH,
                    gap_min=gap_min,
                    gap_max=gap_max,
                    require_pair=require_pair,
                    log_path=log_path,
                )
                out_json.parent.mkdir(parents=True, exist_ok=True)
                with out_json.open("w", encoding="utf-8") as f:
                    json.dump(ai_results, f, ensure_ascii=False, indent=2)
                timings['ai_analysis'] = time.perf_counter() - t8
                timings['ai_items'] = len(ai_results) if ai_results else 0
                print(f"[AI] JSON generado en {out_json} (items={timings['ai_items']})")
        except Exception as e:
            print(f"[AI][ERROR] Proceso IA falló: {e}")
            timings['ai_analysis'] = time.perf_counter() - t8

    # 10. Métricas finales
    timings['total_time_seconds'] = time.perf_counter() - t_global_start

    # 11. Resumen
    print("\n===== RESUMEN DEL PIPELINE =====")
    print(f"Query: {query}")
    print(f"Accession numbers recuperados: {len(accessions)}")
    print(f"Tiempo crear/verificar BD: {human_time(timings['create_database'])}")
    print(f"Tiempo fetch accessions: {human_time(timings['fetch_accessions'])}")
    print(f"Tiempo XML + insert Proteins: {human_time(timings['download_and_insert_proteins'])}")
    print(f"Tiempo péptidos UniProt: {human_time(timings['extract_and_insert_peptides'])} (n={timings.get('peptides_inserted', 0)})")
    if 'insert_nav1_7' in timings:
        print(f"Tiempo insertar Nav1.7: {human_time(timings['insert_nav1_7'])}")
    if 'update_nav1_7_blobs' in timings:
        print(f"Tiempo blobs PDB/PSF Nav1.7: {human_time(timings['update_nav1_7_blobs'])}")
    if 'export_filtered_pdbs' in timings:
        c = timings.get('export_filtered_pdbs_counts', (0, 0, 0))
        print(f"PDBs filtrados: {c[1]}/{c[0]} escritos, omitidos={c[2]} en {human_time(timings['export_filtered_pdbs'])}")
    if 'generate_filtered_psfs' in timings:
        print(f"PSF/PDB filtrados: {human_time(timings['generate_filtered_psfs'])} (salida: pdbs/filtered_psfs)")
    if 'ai_analysis' in timings:
        print(f"Análisis IA filtrados: {human_time(timings['ai_analysis'])} (items={timings.get('ai_items', 0)})")
    print(f"Tiempo TOTAL: {human_time(timings['total_time_seconds'])}")
    print("================================\n")

if __name__ == '__main__':
    main()
