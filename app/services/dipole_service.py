"""
Servicio para análisis de momento dipolar de toxinas.
Este módulo maneja los cálculos de momento dipolar usando archivos PDB y PSF.
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple

# Agregar el path para importar el analizador
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'graphs'))


class DipoleAnalysisService:
    """Servicio para análisis de momento dipolar."""
    
    def __init__(self):
        """Inicializa el servicio de análisis dipolar."""
        try:
            from graphs.graph_analysis2D import Nav17ToxinGraphAnalyzer
            self.analyzer = Nav17ToxinGraphAnalyzer()
        except ImportError as e:
            print(f"Error importando Nav17ToxinGraphAnalyzer: {e}")
            self.analyzer = None
    
    def calculate_dipole_from_files(self, pdb_path: str, psf_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula el momento dipolar a partir de archivos PDB y PSF.
        
        Args:
            pdb_path: Ruta del archivo PDB
            psf_path: Ruta del archivo PSF (opcional)
            
        Returns:
            Datos del momento dipolar
        """
        if not self.analyzer:
            raise RuntimeError("Analizador de toxinas no disponible")
        
        try:
            return self.analyzer.calculate_dipole_moment_with_psf(pdb_path, psf_path)
        except Exception as e:
            raise RuntimeError(f"Error calculando momento dipolar: {str(e)}")
    
    def process_dipole_calculation(self, pdb_data, psf_data=None) -> Dict[str, Any]:
        """
        Procesa el cálculo de momento dipolar desde datos en memoria.
        
        Args:
            pdb_data: Datos PDB en bytes o string
            psf_data: Datos PSF en bytes o string (opcional)
            
        Returns:
            Resultado del cálculo dipolar
        """
        from app.services.pdb_processor import PDBProcessor
        
        # Crear archivos temporales
        pdb_path, psf_path = PDBProcessor.create_temp_files_from_data(pdb_data, psf_data)
        
        try:
            # Calcular momento dipolar
            dipole_data = self.calculate_dipole_from_files(pdb_path, psf_path)
            
            return {
                'success': True,
                'dipole': dipole_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Limpiar archivos temporales
            PDBProcessor.cleanup_temp_files(pdb_path, psf_path)
    
    def validate_dipole_inputs(self, pdb_data, psf_data=None) -> Tuple[bool, str]:
        """
        Valida los datos de entrada para el cálculo dipolar.
        
        Args:
            pdb_data: Datos PDB
            psf_data: Datos PSF (opcional)
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not pdb_data:
            return False, "No se proporcionaron datos PDB"
        
        # Verificar que el analizador esté disponible
        if not self.analyzer:
            return False, "Servicio de análisis dipolar no disponible"
        
        return True, ""
