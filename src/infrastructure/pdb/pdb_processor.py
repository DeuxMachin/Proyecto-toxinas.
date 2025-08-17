"""
Servicio para manejar el procesamiento de archivos PDB y PSF.
Este módulo incluye funciones para cargar, preprocesar y manejar archivos de proteínas.
"""

import tempfile
import os
from typing import Optional, Tuple


class PDBProcessor:
    """Clase para procesar archivos PDB y PSF."""
    
    @staticmethod
    def preprocess_pdb_for_graphein(pdb_content: str) -> str:
        """
        Preprocesa el contenido PDB para convertir residuos no estándar a códigos reconocidos por Graphein.
        
        Args:
            pdb_content: Contenido del archivo PDB como string
            
        Returns:
            Contenido PDB procesado
        """
        # Diccionario de conversiones de residuos no estándar
        residue_conversions = {
            'HSD': 'HIS',  # Histidina delta-protonada
            'HSE': 'HIS',  # Histidina epsilon-protonada  
            'HSP': 'HIS',  # Histidina positivamente cargada
            'CYX': 'CYS',  # Cisteína en puente disulfuro
            'HIE': 'HIS',  # Otra variante de histidina
            'HID': 'HIS',  # Otra variante de histidina
            'HIP': 'HIS',  # Otra variante de histidina
            'CYM': 'CYS',  # Cisteína desprotonada
            'ASH': 'ASP',  # Ácido aspártico protonado
            'GLH': 'GLU',  # Ácido glutámico protonado
            'LYN': 'LYS',  # Lisina desprotonada
            'ARN': 'ARG',  # Arginina desprotonada
            'TYM': 'TYR',  # Tirosina desprotonada
            'MSE': 'MET',  # Selenometionina
            'PCA': 'GLU',  # Piroglutamato
            'TPO': 'THR',  # Treonina fosforilada
            'SEP': 'SER',  # Serina fosforilada
            'PTR': 'TYR',  # Tirosina fosforilada
            'SEC': 'CYS',  # Selenocisteína -> tratar como CYS
            'CYZ': 'CYS',  # Variantes de cisteína
            'CSS': 'CYS',
            'CSH': 'CYS',
            'CME': 'CYS',
            'M3L': 'LYS',  # Metil-lisina
            'MLE': 'LEU',  # Norleucina / variantes
            'HYP': 'PRO',  # Hidroxiprolina
            'SAR': 'GLY',  # Sarcosina
            'DAL': 'ALA',  # D-amino ácidos mapeados a L
            'DLY': 'LYS',
            'DPN': 'PHE',
            'DVA': 'VAL',
            'DSN': 'SER',
        }
        
        lines = pdb_content.split('\n')
        processed_lines = []
        
        for line in lines:
            if line.startswith(('ATOM', 'HETATM')):
                # El nombre del residuo está en las columnas 18-20 (0-indexed: 17-20)
                if len(line) >= 20:
                    residue_name = line[17:20].strip()
                    if residue_name in residue_conversions:
                        # Reemplazar el nombre del residuo
                        new_residue = residue_conversions[residue_name]
                        # Asegurar que tenga 3 caracteres con espacios a la derecha si es necesario
                        new_residue_padded = f"{new_residue:<3}"
                        line = line[:17] + new_residue_padded + line[20:]
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    @staticmethod
    def bytes_to_string(data) -> str:
        """
        Convierte datos de bytes o string a string.
        
        Args:
            data: Datos en bytes o string
            
        Returns:
            Contenido como string
        """
        if isinstance(data, bytes):
            return data.decode('utf-8')
        else:
            return str(data)
    
    @staticmethod
    def create_temp_pdb_file(pdb_content: str, preprocess: bool = True) -> str:
        """
        Crea un archivo temporal PDB.
        
        Args:
            pdb_content: Contenido del archivo PDB
            preprocess: Si aplicar preprocesamiento para Graphein
            
        Returns:
            Ruta del archivo temporal creado
        """
        if preprocess:
            processed_content = PDBProcessor.preprocess_pdb_for_graphein(pdb_content)
        else:
            processed_content = pdb_content
        
        with tempfile.NamedTemporaryFile(suffix='.pdb', delete=False) as temp_file:
            temp_file.write(processed_content.encode('utf-8'))
            return temp_file.name
    
    @staticmethod
    def create_temp_psf_file(psf_content) -> Optional[str]:
        """
        Crea un archivo temporal PSF.
        
        Args:
            psf_content: Contenido del archivo PSF
            
        Returns:
            Ruta del archivo temporal creado o None si no hay contenido
        """
        if not psf_content:
            return None
        
        with tempfile.NamedTemporaryFile(suffix='.psf', delete=False) as temp_file:
            if isinstance(psf_content, bytes):
                temp_file.write(psf_content)
            else:
                temp_file.write(psf_content.encode('utf-8'))
            return temp_file.name
    
    @staticmethod
    def cleanup_temp_files(*file_paths: str) -> None:
        """
        Elimina archivos temporales.
        
        Args:
            *file_paths: Rutas de archivos a eliminar
        """
        for file_path in file_paths:
            if file_path:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass  # Ignorar errores de limpieza
    
    @staticmethod
    def prepare_pdb_data(pdb_data) -> str:
        """
        Prepara datos PDB para procesamiento.
        
        Args:
            pdb_data: Datos PDB en bytes o string
            
        Returns:
            Contenido PDB como string
        """
        pdb_content = PDBProcessor.bytes_to_string(pdb_data)
        return PDBProcessor.preprocess_pdb_for_graphein(pdb_content)
    
    @staticmethod
    def create_temp_files_from_data(pdb_data, psf_data=None) -> Tuple[str, Optional[str]]:
        """
        Crea archivos temporales a partir de datos PDB y PSF.
        
        Args:
            pdb_data: Datos PDB
            psf_data: Datos PSF (opcional)
            
        Returns:
            Tupla (ruta_pdb, ruta_psf)
        """
        # Procesar PDB
        pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
        pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)
        
        # Procesar PSF si existe
        psf_path = None
        if psf_data:
            psf_path = PDBProcessor.create_temp_psf_file(psf_data)
        
        return pdb_path, psf_path


class FileUtils:
    """Utilidades para manejo de archivos."""
    
    @staticmethod
    def clean_filename(name: str, max_length: int = 31) -> str:
        """
        Limpia un nombre para usarlo como nombre de archivo.
        
        Args:
            name: Nombre original
            max_length: Longitud máxima permitida
            
        Returns:
            Nombre limpio
        """
        import unicodedata
        import re
        
        # Normalizar Unicode
        normalized_name = unicodedata.normalize('NFKD', name)
        
        # Convertir caracteres griegos especiales a ASCII
        clean_name = (normalized_name
                     .replace('μ', 'mu')
                     .replace('β', 'beta')
                     .replace('ω', 'omega')
                     .replace('δ', 'delta'))
        
        # Remover caracteres no ASCII alfanuméricos, guiones o guiones bajos
        clean_name = re.sub(r'[^\w\-_]', '', clean_name, flags=re.ASCII)
        
        # Truncar si es necesario
        if len(clean_name) > max_length:
            clean_name = clean_name[:max_length]
        
        return clean_name if clean_name else "unknown"
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
        """
        Valida que un archivo tenga una extensión permitida.
        
        Args:
            filename: Nombre del archivo
            allowed_extensions: Lista de extensiones permitidas (ej: ['.pdb', '.psf'])
            
        Returns:
            True si la extensión es válida
        """
        if not filename:
            return False
        
        extension = os.path.splitext(filename.lower())[1]
        return extension in [ext.lower() for ext in allowed_extensions]
