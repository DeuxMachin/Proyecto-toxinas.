"""
Rutas para funcionalidades adicionales.
Este módulo contiene rutas para funcionalidades específicas como segmentación de nodos.
"""

from flask import Blueprint, jsonify, request, make_response
import traceback
import pandas as pd
import io
import re

from app.services.database_service import DatabaseService
from app.utils.graph_segmentation import generate_segment_groupings

# Crear blueprint
misc_bp = Blueprint('misc', __name__)

# Inicializar servicios
db_service = DatabaseService()


@misc_bp.route('/export_segment_nodes/<source>/<int:pid>')
def export_segment_nodes(source, pid):
    """
    Exporta segmentación de nodos agrupados para una toxina específica.
    Solo funciona con granularidad atómica.
    """
    try:
        # Obtener parámetros
        long_val = int(request.args.get('long', 5))
        threshold = float(request.args.get('threshold', 10.0))
        granularity = 'atom'  # obligatorio para nodos atómicos

        # Obtener datos de la toxina
        if source == "toxinas":
            toxin_info = db_service.get_toxin_info(source, pid)
            pdb_data = db_service.get_pdb_data(source, pid)
            toxin_name = toxin_info[0] if toxin_info else f"toxina_{pid}"
        elif source == "nav1_7":
            toxin_info = db_service.get_toxin_info(source, pid)
            pdb_data = db_service.get_pdb_data(source, pid)
            toxin_name = toxin_info[0] if toxin_info else f"nav1_7_{pid}"
        else:
            return jsonify({"error": "Invalid source"}), 400
        
        if not pdb_data:
            return jsonify({"error": "PDB not found"}), 404
        
        # Limpiar nombre para archivo Excel
        clean_name = re.sub(r'[^\w]', '_', toxin_name)[:31]

        # Crear archivo temporal
        from app.services.pdb_processor import PDBProcessor
        pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
        pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)

        try:
            # Generar segmentación usando la función del utils
            df_segmentos = generate_segment_groupings(
                pdb_path=pdb_path,
                source=source,
                protein_id=pid,
                long_range=long_val,
                threshold=threshold,
                granularity=granularity,
                toxin_name=toxin_name
            )

            if df_segmentos.empty:
                return jsonify({"error": "No se generaron segmentos"}), 500

            # Exportar a XLSX
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_segmentos.to_excel(writer, index=False, sheet_name=clean_name[:31])
            output.seek(0)

            filename = f"SegmentosAgrupados_{clean_name}.xlsx"
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        finally:
            PDBProcessor.cleanup_temp_files(pdb_path)

    except Exception as e:
        print(f"❌ Error en export_segment_nodes: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
