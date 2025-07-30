"""
Rutas para análisis comparativo de toxinas.
Este módulo maneja comparaciones entre toxinas WT y de referencia.
"""

from flask import Blueprint, jsonify, request, send_file
import traceback
import pandas as pd

from app.services.database_service import DatabaseService
from app.services.comparison_service import ToxinComparisonService
from app.services.export_service import ExportService

# Crear blueprint
comparison_bp = Blueprint('comparison', __name__)

# Inicializar servicios
db_service = DatabaseService()


@comparison_bp.route("/export_wt_comparison_xlsx/<string:wt_family>")
def export_wt_comparison_xlsx(wt_family):
    """
    Exporta comparación entre toxina WT y toxina de referencia.
    
    Parámetros URL:
    - long: Umbral de interacciones largas (default: 5)
    - threshold: Umbral de distancia (default: 10.0)
    - granularity: Granularidad del grafo ('CA' o 'atom', default: 'CA')
    - export_type: Tipo de exportación ('residues' o 'segments_atomicos', default: 'residues')
    """
    try:
        # Obtener parámetros
        long_threshold = int(request.args.get('long', 5))
        distance_threshold = float(request.args.get('threshold', 10.0))
        granularity = request.args.get('granularity', 'CA')
        export_type = request.args.get('export_type', 'residues')
        
        print(f"Procesando comparación WT para {wt_family} con parámetros: long={long_threshold}, dist={distance_threshold}, granularity={granularity}, tipo={export_type}")
        
        # Validación para segmentación atómica
        if export_type == 'segments_atomicos' and granularity != 'atom':
            return jsonify({"error": "La segmentación atómica requiere granularidad atómica"}), 400
        
        # Validar familia WT
        if not ToxinComparisonService.validate_wt_family(wt_family):
            return jsonify({"error": f"Unrecognized WT family: {wt_family}"}), 400
        
        # Obtener mapeo y código de péptido WT
        wt_mapping = ToxinComparisonService.get_wt_mapping()
        wt_peptide_code = wt_mapping[wt_family]
        
        # Obtener datos de la toxina WT desde la base de datos
        wt_result = db_service.get_wt_toxin_by_code(wt_peptide_code)
        if not wt_result:
            return jsonify({"error": f"WT toxin not found: {wt_peptide_code}"}), 404
        
        wt_id, wt_code, wt_ic50, wt_unit, wt_pdb_data = wt_result
        print(f"WT toxin found: {wt_code} (IC₅₀: {wt_ic50} {wt_unit})")
        
        # Cargar toxina de referencia desde archivo
        reference_path = ToxinComparisonService.get_reference_file_path()
        ref_pdb_content = ToxinComparisonService.load_reference_toxin(reference_path)
        
        if not ref_pdb_content:
            return jsonify({"error": f"Reference file not found: {reference_path}"}), 404
        
        print(f"Reference file found: {reference_path}")
        
        # === PROCESAR TOXINA WT ===
        print(f"Procesando toxina WT: {wt_code}")
        wt_data = ToxinComparisonService.process_single_toxin_for_comparison(
            pdb_data=wt_pdb_data,
            toxin_name=wt_code,
            ic50_value=wt_ic50,
            ic50_unit=wt_unit,
            granularity=granularity,
            long_threshold=long_threshold,
            distance_threshold=distance_threshold,
            toxin_type="WT_Target",
            export_type=export_type
        )
        
        # === PROCESAR TOXINA DE REFERENCIA ===
        print(f"Procesando toxina de referencia: hwt4_Hh2a_WT")
        ref_data = ToxinComparisonService.process_single_toxin_for_comparison(
            pdb_data=ref_pdb_content,
            toxin_name="hwt4_Hh2a_WT",
            ic50_value=None,
            ic50_unit=None,
            granularity=granularity,
            long_threshold=long_threshold,
            distance_threshold=distance_threshold,
            toxin_type="Reference",
            export_type=export_type
        )
        
        # Preparar dataframes para comparación
        comparison_dataframes = {}
        
        if wt_data is not None:
            if export_type == 'segments_atomicos':
                # Para segmentación atómica, wt_data ya es un DataFrame
                comparison_dataframes['WT_Target'] = wt_data
            else:
                # Para análisis por residuos, convertir lista a DataFrame
                comparison_dataframes['WT_Target'] = pd.DataFrame(wt_data)
        
        if ref_data is not None:
            if export_type == 'segments_atomicos':
                # Para segmentación atómica, ref_data ya es un DataFrame
                comparison_dataframes['Reference'] = ref_data
            else:
                # Para análisis por residuos, convertir lista a DataFrame
                comparison_dataframes['Reference'] = pd.DataFrame(ref_data)
        
        # Crear metadatos completos
        from datetime import datetime
        metadata = {
            'Toxina_WT': wt_code,
            'Toxina_Referencia': 'hwt4_Hh2a_WT',
            'Familia': wt_family,
            'Tipo_Analisis': 'Segmentación Atómica' if export_type == 'segments_atomicos' else 'Análisis por Residuos',
            'IC50_WT': f"{wt_ic50} {wt_unit}" if wt_ic50 and wt_unit else "No disponible",
            'Granularidad': granularity,
            'Umbral_Distancia': distance_threshold,
            'Umbral_Interaccion_Larga': long_threshold,
            'Fecha_Exportacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Crear hoja de resumen comparativo si ambas toxinas fueron procesadas
        if 'WT_Target' in comparison_dataframes and 'Reference' in comparison_dataframes:
            wt_df = comparison_dataframes['WT_Target']
            ref_df = comparison_dataframes['Reference']
            
            # Crear DataFrame de resumen
            summary_df = ExportService.create_summary_comparison_dataframe(
                wt_df, ref_df, wt_code, export_type
            )
            comparison_dataframes['Resumen_Comparativo'] = summary_df
        
        # Generar archivo Excel
        excel_data, excel_filename = ExportService.generate_comparison_excel(
            comparison_dataframes, wt_family, metadata, export_type, granularity
        )
        
        # Retornar archivo Excel
        return send_file(
            excel_data,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
