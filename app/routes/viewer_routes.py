from flask import Blueprint, render_template, request, jsonify
import sqlite3
import os

viewer_bp = Blueprint('viewer', __name__)

DB_PATH = "database/toxins.db"
PDB_DIR = "pdbs"

def fetch_peptides(group):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if group == "toxinas":
        cursor.execute("SELECT peptide_id, peptide_name FROM Peptides")
        print("Fetching peptides from Peptides table")
    elif group == "nav1_7":
        cursor.execute("SELECT id, peptide_code FROM Nav1_7_InhibitorPeptides")
    else:
        return []

    return cursor.fetchall()


@viewer_bp.route("/viewer")
def viewer():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT peptide_id, peptide_name FROM Peptides")
    toxinas = cursor.fetchall()

    cursor.execute("SELECT id, peptide_code FROM Nav1_7_InhibitorPeptides")
    nav1_7 = cursor.fetchall()

    conn.close()

    return render_template("viewer.html", toxinas=toxinas, nav1_7=nav1_7)


@viewer_bp.route("/get_pdb/<string:source>/<int:pid>")
def get_pdb(source, pid):
    print(f"[DEBUG] Solicitud PDB recibida: source={source}, pid={pid}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if source == "toxinas":
        cursor.execute("SELECT pdb_file FROM Peptides WHERE peptide_id = ?", (pid,))
    elif source == "nav1_7":
        cursor.execute("SELECT pdb_blob FROM Nav1_7_InhibitorPeptides WHERE id = ?", (pid,))
    else:
        print(f"[ERROR] Fuente inválida: {source}")
        return jsonify({"error": "Invalid source"}), 400

    result = cursor.fetchone()
    if not result:
        print(f"[ERROR] PDB no encontrado: {source}/{pid}")
        return jsonify({"error": "PDB not found"}), 404

    pdb_data = result[0]
    print(f"[DEBUG] Tipo de datos PDB: {type(pdb_data)}")

    try:
        # Decode si es binario
        if isinstance(pdb_data, bytes):
            pdb_text = pdb_data.decode('utf-8')
        else:
            pdb_text = str(pdb_data)
            
        # Inspeccionar los primeros 100 caracteres
        print(f"[DEBUG] Primeros 100 caracteres: {pdb_text[:100]}")
    except Exception as e:
        print(f"[ERROR] Fallo en decodificación: {e}")
        return jsonify({"error": "PDB decoding error"}), 500

    # Validación mejorada
    if len(pdb_text.strip()) < 100:
        print("[ERROR] PDB demasiado corto")
        return jsonify({"error": "PDB content too short"}), 500

    if not any(line.startswith("ATOM") or line.startswith("HETATM") for line in pdb_text.splitlines()):
        print("[ERROR] No se encontraron líneas ATOM o HETATM")
        return jsonify({"error": "No atomic data found"}), 500

    # OK
    print(f"[DEBUG] PDB enviado correctamente ({len(pdb_text)} caracteres)")
    # Establecer el Content-Type correcto para archivos PDB
    return pdb_text, 200, {'Content-Type': 'chemical/x-pdb'}

