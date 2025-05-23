from flask import Blueprint, render_template, jsonify
import sqlite3
import tempfile
from app.services.graphein_service import build_protein_graph
import networkx as nx

graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/graph/<int:peptide_id>')
def show_graph(peptide_id):
    # Obtener PDB desde la BD
    conn = sqlite3.connect("database/toxins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pdb_file FROM Peptides WHERE peptide_id = ?", (peptide_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return "No se encontró estructura PDB", 404

    pdb_content = row[0]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.pdb', delete=False) as temp:
        temp.write(pdb_content)
        temp.flush()
        G = build_protein_graph(temp.name)

    nodes = [{"id": n, "label": G.nodes[n].get("residue", str(n))} for n in G.nodes]
    edges = [{"source": u, "target": v} for u, v in G.edges]

    return render_template("graph_view.html", nodes=nodes, edges=edges, peptide_id=peptide_id)
