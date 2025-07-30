"""
Rutas principales del visor de toxinas.
Este módulo contiene las rutas básicas para navegación y datos simples.
"""

from flask import Blueprint, render_template, jsonify, request
from app.services.database_service import DatabaseService

# Crear blueprint
viewer_bp = Blueprint('viewer', __name__)

# Inicializar servicios
db_service = DatabaseService()


@viewer_bp.route("/", methods=['GET', 'POST'])
def viewer():
    """Ruta principal del visor - página de inicio."""
    # Si es una solicitud POST, simplemente devuelve un estado 200 OK
    if request.method == 'POST':
        return jsonify({"status": "ok"}), 200
    
    # Si es GET, mostrar la página normal
    try:
        toxinas = db_service.get_all_toxinas()
        nav1_7 = db_service.get_all_nav1_7()
        
        return render_template("viewer.html", toxinas=toxinas, nav1_7=nav1_7)
    except Exception as e:
        print(f"❌ Error cargando página principal: {str(e)}")
        return render_template("viewer.html", toxinas=[], nav1_7=[])


@viewer_bp.route("/get_pdb/<string:source>/<int:pid>")
def get_pdb(source, pid):
    """Obtiene datos PDB de una proteína específica."""
    try:
        pdb_data = db_service.get_pdb_data(source, pid)
        
        if not pdb_data:
            return jsonify({"error": "PDB not found"}), 404
        
        # Convertir a string para respuesta
        if isinstance(pdb_data, bytes):
            return pdb_data.decode('utf-8'), 200, {'Content-Type': 'text/plain'}
        else:
            return str(pdb_data), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return jsonify({"error": f"Error processing PDB: {str(e)}"}), 500


@viewer_bp.route("/get_psf/<string:source>/<int:pid>")
def get_psf(source, pid):
    """Obtiene archivo PSF desde la base de datos (solo para Nav1.7)."""
    if source != "nav1_7":
        return jsonify({"error": "PSF files only available for nav1_7"}), 400
    
    try:
        psf_data = db_service.get_psf_data(pid)
        
        if not psf_data:
            return jsonify({"error": "PSF not found"}), 404
        
        # Convertir a string para respuesta
        if isinstance(psf_data, bytes):
            return psf_data.decode('utf-8'), 200, {'Content-Type': 'text/plain'}
        else:
            return str(psf_data), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return jsonify({"error": f"Error processing PSF: {str(e)}"}), 500


@viewer_bp.route("/get_toxin_name/<string:source>/<int:pid>")
def get_toxin_name(source, pid):
    """Obtiene el nombre de una toxina específica."""
    try:
        toxin_info = db_service.get_toxin_info(source, pid)
        
        if toxin_info:
            return jsonify({"toxin_name": toxin_info[0]})
        else:
            return jsonify({"toxin_name": f"{source}_{pid}"})
    except Exception as e:
        print(f"❌ Error en get_toxin_name: {str(e)}")
        return jsonify({"error": str(e)}), 500
