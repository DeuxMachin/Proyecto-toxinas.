from Bio import PDB
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from Bio.PDB.Polypeptide import is_aa
from Bio.Data import IUPACData
import string
import networkx as nx
from Bio.PDB import NeighborSearch, Selection
import matplotlib.pyplot as plt
import sqlite3
import pickle

def calcular_caracteristicas_basicas_pdb(pdb_file_path, distancia_corte=8.0, visualizar_grafo=False):
    """
    Calcula la composición de aminoácidos, propiedades fisicoquímicas básicas y métricas del grafo de una proteína a partir de un archivo PDB.

    :param pdb_file_path: Ruta al archivo PDB.
    :param distancia_corte: Distancia máxima (en Ångströms) para considerar una interacción entre residuos.
    :param visualizar_grafo: Booleano para decidir si se visualiza el grafo.
    :return: Diccionario con la composición de aminoácidos, propiedades fisicoquímicas y métricas del grafo.
    """
    # Crear el parser de PDB
    parser = PDB.PDBParser(QUIET=True)
    
    # Parsear el archivo PDB
    estructura = parser.get_structure('proteina', pdb_file_path)
    
    # Extraer la secuencia de aminoácidos usando PPBuilder
    ppb = PDB.PPBuilder()
    secuencias = ppb.build_peptides(estructura)
    
    if not secuencias:
        raise ValueError("No se encontró una secuencia de aminoácidos en el archivo PDB.")
    
    # Asumimos la primera cadena de polipéptido
    secuencia = secuencias[0].get_sequence()
    secuencia_str = str(secuencia)
    
    # Filtrar posibles caracteres no estándar
    amino_acidos = ''.join([aa for aa in secuencia_str if aa in string.ascii_uppercase])
    
    # Verificar que la secuencia no esté vacía
    if not amino_acidos:
        raise ValueError("La secuencia de aminoácidos está vacía o contiene caracteres no estándar.")
    
    # Composición de Aminoácidos
    analisis = ProteinAnalysis(amino_acidos)
    # Recalcular composición de aminoácidos manualmente
    total_residuos = len(amino_acidos)
    composicion_contada = {aa: amino_acidos.count(aa) for aa in set(amino_acidos)}

    # Normalizar los valores para que sumen 100%
    composicion_porcentaje = {aa: round((count / total_residuos) * 100, 2) for aa, count in composicion_contada.items()}
    # Combinar conteo y porcentaje en un solo diccionario
    composicion_aa = {
        aa: {"conteo": composicion_contada[aa], "porcentaje": composicion_porcentaje[aa]}
        for aa in composicion_contada
    }
    # Propiedades Fisicoquímicas Básicas
    propiedades = {
        'masa_molecular': round(analisis.molecular_weight(), 2),  # en Da
        'pI': round(analisis.isoelectric_point(), 2),
        'hidrofobicidad_promedio': round(analisis.gravy(), 2),  # GRAVY score
        'carga_neta_pH7': round(analisis.charge_at_pH(7.0), 2)  # Carga neta a pH 7
    }
    
    # Construcción del Grafo de la Proteína
    modelo = estructura[0]
    atoms = Selection.unfold_entities(modelo, 'A')  # Todos los átomos
    # Seleccionar solo los átomos Cα para simplificar
    ca_atoms = [atom for atom in atoms if atom.get_id() == 'CA' and is_aa(atom.get_parent(), standard=True)]
    
    # Crear el grafo
    G = nx.Graph()
    
    # Agregar nodos con atributos (residuo y posición)
    for atom in ca_atoms:
        res = atom.get_parent()
        res_id = res.get_id()[1]  # Número de residuo
        resname = res.get_resname()  # Nombre del residuo (3 letras)
        # Convertir a una representación de una letra si es posible
        try:
            aa = IUPACData.protein_letters_3to1.get(resname.capitalize(), 'X')
        except KeyError:
            aa = 'X'  # 'X' para residuos no estándar
        G.add_node(res_id, amino_acido=aa, pos=atom.get_coord())
    
    # Agregar aristas basadas en la distancia_corte
    ns = NeighborSearch(ca_atoms)
    for atom in ca_atoms:
        res_id = atom.get_parent().id[1]
        vecinos = ns.search(atom.coord, distancia_corte, level='A')
        for vecino in vecinos:
            vecino_res_id = vecino.get_parent().id[1]
            if res_id != vecino_res_id:
                G.add_edge(res_id, vecino_res_id)
    
    # Métricas Básicas del Grafo
    grado_promedio = sum(dict(G.degree()).values()) / len(G) if len(G) > 0 else 0
    densidad = nx.density(G)
    centralidad = nx.degree_centrality(G)
    centralidad_promedio = sum(centralidad.values()) / len(centralidad) if len(centralidad) > 0 else 0
    
    # Otros posibles métricas
    numero_nodos = G.number_of_nodes()
    numero_aristas = G.number_of_edges()
    
    metrics_grafo = {
        'numero_nodos': numero_nodos,
        'numero_aristas': numero_aristas,
        'grado_promedio': round(grado_promedio, 2),
        'densidad': round(densidad, 4),
        'centralidad_promedio': round(centralidad_promedio, 4)
    }
    
    # Opcional: Visualizar el grafo
    if visualizar_grafo:
        plt.figure(figsize=(10, 8))
        pos = {res_id: (coord[0], coord[1]) for res_id, coord in nx.get_node_attributes(G, 'pos').items()}
        nx.draw_networkx_nodes(G, pos, node_size=100, node_color='skyblue')
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        nx.draw_networkx_labels(G, pos, labels={res_id: f"{res_id}-{G.nodes[res_id]['amino_acido']}" for res_id in G.nodes()}, font_size=8)
        plt.title('Grafo de la Proteína (Cα)')
        plt.axis('off')
        plt.show()
    
    # Combinar resultados
    resultados = {
        'secuencia': amino_acidos,
        'composicion_aminoacidos_porcentaje': composicion_porcentaje,
        'composicion_aminoacidos': composicion_contada,
        'propiedades_fisicoquimicas_basicas': propiedades,
        'metrics_grafo': metrics_grafo
    }
    
    return resultados


def obtener_pdbs_desde_bd(db_path="./database/proteins_discovery.db"):
    """Obtiene los 10 primeros archivos PDB almacenados como texto desde la base de datos."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    consulta = """
        SELECT 
            vvp.id, 
            vvp.protein_id, 
            vvp.source, 
            COALESCE(a.pdb, fad.pdb) AS pdb_file
        FROM ValidVSDProteins vvp
        LEFT JOIN Alignments a ON vvp.protein_id = a.source_id
        LEFT JOIN FoldSeekAlignmentDetails fad ON vvp.protein_id = fad.foldseek_id
        WHERE a.pdb IS NOT NULL OR fad.pdb IS NOT NULL
        LIMIT 10
    """
    
    cursor.execute(consulta)
    resultados = cursor.fetchall()
    conn.close()

    # Formatear resultados en una lista de diccionarios
    pdb_data = [
        {"vsd_protein_id": row[0], "protein_id": row[1], "source": row[2], "pdb_content": row[3]}
        for row in resultados
    ]
    
    return pdb_data

import os
import pickle
import json
from Bio import PDB

def guardar_caracteristicas_en_bd(pdb_data, db_path="./database/proteins_discovery.db"):
    """Procesa los archivos PDB y guarda sus características en la base de datos."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    parser = PDB.PDBParser(QUIET=True)

    for pdb_entry in pdb_data:
        vsd_protein_id = pdb_entry["vsd_protein_id"]
        pdb_content = pdb_entry["pdb_content"]
        
        # Crear un archivo temporal con el contenido del PDB
        temp_pdb_filename = f"temp_{vsd_protein_id}.pdb"
        with open(temp_pdb_filename, "w") as f:
            f.write(pdb_content)
        
        try:
            # Calcular características
            caracteristicas = calcular_caracteristicas_basicas_pdb(temp_pdb_filename)
            
            # Convertir los resultados a JSON para almacenamiento en TEXT
            composicion_porcentajes_json = json.dumps(caracteristicas["composicion_aminoacidos_porcentaje"])
            composicion_conteo_json = json.dumps(caracteristicas["composicion_aminoacidos"])
            
            # Serializar el grafo en binario (BLOB)
            grafo_binario = pickle.dumps(caracteristicas["metrics_grafo"])
            
            # Insertar en la base de datos
            cursor.execute('''
                INSERT INTO ProteinCalculations (
                    vsd_protein_id, composicion_porcentajes, composicion_conteo, 
                    masa_molecular, pI, hidrofobicidad_promedio, carga_neta_ph7,
                    numero_nodos, numero_aristas, grado_promedio, densidad, grafo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vsd_protein_id, composicion_porcentajes_json, composicion_conteo_json, 
                caracteristicas["propiedades_fisicoquimicas_basicas"]["masa_molecular"],
                caracteristicas["propiedades_fisicoquimicas_basicas"]["pI"],
                caracteristicas["propiedades_fisicoquimicas_basicas"]["hidrofobicidad_promedio"],
                caracteristicas["propiedades_fisicoquimicas_basicas"]["carga_neta_pH7"],
                caracteristicas["metrics_grafo"]["numero_nodos"],
                caracteristicas["metrics_grafo"]["numero_aristas"],
                caracteristicas["metrics_grafo"]["grado_promedio"],
                caracteristicas["metrics_grafo"]["densidad"],
                grafo_binario
            ))
            conn.commit()

        except Exception as e:
            print(f"Error procesando PDB {vsd_protein_id}: {e}")

        finally:
            # Eliminar el archivo temporal
            os.remove(temp_pdb_filename)

    conn.commit()
    conn.close()

# Ejemplo de uso
if __name__ == "__main__":
    
    # Obtener PDBs desde la base de datos
    pdb_data = obtener_pdbs_desde_bd()

    # Procesar y guardar los resultados en la base de datos
    guardar_caracteristicas_en_bd(pdb_data)

    print("Procesamiento completado. Los datos fueron guardados en ProteinCalculations.")
    
    """
    # Utilizaremos una estructura de ejemplo de Biopython
    # Descargaremos una estructura de ejemplo desde el PDB
    import os
    import urllib.request

    # URL de ejemplo (puedes cambiarla por cualquier PDB disponible)
    pdb_filename = './data/raw/vsd_water_bk_test.pdb'

    # Calcular características y visualizar el grafo
    try:
        caracteristicas = calcular_caracteristicas_basicas_pdb(pdb_filename, distancia_corte=8.0, visualizar_grafo=True)
        
        print("\nSecuencia de Aminoácidos:")
        print(caracteristicas['secuencia'])
        
        print("\nComposición de Aminoácidos (%)")
        for aa, porcentaje in sorted(caracteristicas['composicion_aminoacidos_porcentaje'].items()):
            print(f"{aa}: {porcentaje:.2f}%")
            
        print("\nComposición de Aminoácidos (conteo)")
        for aa, conteo in sorted(caracteristicas['composicion_aminoacidos'].items()):
            print(f"{aa}: {conteo}")
        
        print("\nPropiedades Fisicoquímicas Básicas:")
        for prop, valor in caracteristicas['propiedades_fisicoquimicas_basicas'].items():
            print(f"{prop}: {valor}")
        
        print("\nMétricas del Grafo de la Proteína:")
        for metric, value in caracteristicas['metrics_grafo'].items():
            print(f"{metric}: {value}")
    
    except Exception as e:
        print(f"Error: {e}")
        
    """