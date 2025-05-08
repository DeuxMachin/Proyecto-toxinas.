import os
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import pickle
from Bio import PDB
from Bio.PDB import NeighborSearch, Selection, DSSP
from Bio.PDB.Polypeptide import is_aa, PPBuilder
from Bio.SeqUtils import seq3, seq1
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import to_rgb
import pandas as pd
import seaborn as sns
from scipy.spatial.distance import pdist, squareform

# Diccionarios de propiedades fisicoquímicas relevantes para interacción con Nav1.7
HYDROPHOBICITY = {'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5, 'Q': -3.5, 'E': -3.5, 
                 'G': -0.4, 'H': -3.2, 'I': 4.5, 'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 
                 'P': -1.6, 'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2}

CHARGES = {'A': 0, 'R': 1, 'N': 0, 'D': -1, 'C': 0, 'Q': 0, 'E': -1, 
           'G': 0, 'H': 0.5, 'I': 0, 'L': 0, 'K': 1, 'M': 0, 'F': 0, 
           'P': 0, 'S': 0, 'T': 0, 'W': 0, 'Y': 0, 'V': 0}

# Colores para visualización según propiedades relevantes para interacción con Nav1.7
RESIDUE_COLORS = {
    'hydrophobic': '#1E88E5',     # Azul - importante para interacciones con membrana
    'polar': '#26A69A',           # Verde azulado - estabilidad estructural
    'positive': '#D81B60',        # Rojo - crítico para interacción con VSD de Nav1.7
    'negative': '#8E24AA',        # Púrpura - importante para interacciones electrostáticas
    'cysteine': '#FFC107',        # Amarillo - esencial para puentes disulfuro en toxinas
    'other': '#78909C'            # Gris - residuos no clasificados
}

# Clasificación de residuos según su relevancia para unión a Nav1.7
def classify_residue(aa):
    """Clasifica aminoácidos según propiedades fisicoquímicas relevantes para Nav1.7"""
    if aa in "AVILMFYW":
        return "hydrophobic"
    elif aa in "STNQ":
        return "polar"
    elif aa in "KRH":
        return "positive"
    elif aa in "DE":
        return "negative"
    elif aa == "C":
        return "cysteine"
    else:
        return "other"

class Nav17ToxinGraphAnalyzer:
    def __init__(self, pdb_folder="pdbs/", db_path="database/toxins.db"):
        self.pdb_folder = pdb_folder
        self.db_path = db_path
        self.parser = PDB.PDBParser(QUIET=True)
        
    def _connect_db(self):
        return sqlite3.connect(self.db_path)
    
    def get_toxin_data(self):
        """Obtiene datos de toxinas de la base de datos para análisis estructural"""
        conn = self._connect_db()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            peptide_code, 
            sequence, 
            pharmacophore_match,
            pharmacophore_residue_count
        FROM Nav1_7_InhibitorPeptides
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        # Conversión a dataframe para análisis posterior
        df = pd.DataFrame(results, columns=[
            'peptide_code', 'sequence', 'pharmacophore', 
            'pharmacophore_count'
        ])
        
        return df
    
    def load_pdb(self, pdb_filename):
        """Carga archivo PDB de toxina para análisis estructural"""
        pdb_path = os.path.join(self.pdb_folder, pdb_filename)
        if not os.path.exists(pdb_path):
            raise FileNotFoundError(f"Archivo PDB no encontrado: {pdb_path}")
        
        structure = self.parser.get_structure('protein', pdb_path)
        return structure
    
    def load_pdb_from_blob(self, peptide_code):
        """Carga estructura PDB desde blob en base de datos (útil para toxinas Nav1.7)"""
        conn = self._connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT pdb_blob FROM Nav1_7_InhibitorPeptides WHERE peptide_code = ?", 
                      (peptide_code,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            raise ValueError(f"No se encontró blob PDB para {peptide_code}")
        
        # Escritura a archivo temporal
        temp_file = f"temp_{peptide_code}.pdb"
        with open(temp_file, "wb") as f:
            f.write(result[0])
        
        # Carga de estructura
        structure = self.parser.get_structure('protein', temp_file)
        
        # Limpieza
        os.remove(temp_file)
        
        return structure
    
    def calculate_secondary_structure(self, structure):
        """Calcula estructura secundaria mediante DSSP (relevante para identificar dominios en toxinas)"""
        model = structure[0]
        dssp = DSSP(model, structure.id, dssp='mkdssp')
        
        # Mapeo de estructura secundaria
        ss_map = {
            'H': 'helix',      # α-hélice
            'B': 'beta',       # Puente β
            'E': 'beta',       # Lámina β - común en toxinas ICK
            'G': 'helix',      # Hélice 3-10
            'I': 'helix',      # Hélice π
            'T': 'turn',       # Giro - crítico para sitios de unión de toxinas
            'S': 'bend',       # Curva - crítico para sitios de unión de toxinas
            ' ': 'loop',       # Loop/irregular
            '-': 'loop'        # Ausente
        }
        
        residue_ss = {}
        sasa_values = {}
        
        for k in dssp.keys():
            chain_id, res_id = k[0], k[1][1]
            ss = ss_map.get(dssp[k][1], 'loop')
            residue_ss[res_id] = ss
            
            # Extracción de SASA (área accesible al solvente) importante para identificar sitios de interacción
            sasa_values[res_id] = dssp[k][2]
            
        return residue_ss, sasa_values
    
    def find_disulfide_bridges(self, structure):
        """Identifica puentes disulfuro entre cisteínas (críticos para estructura de toxinas Nav1.7)"""
        cys_sg_atoms = []
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.get_resname() == "CYS":
                        for atom in residue:
                            if atom.get_name() == "SG":
                                cys_sg_atoms.append((residue.get_id()[1], atom))
        
        # Búsqueda de pares de átomos SG dentro de distancia de enlace
        disulfide_bridges = []
        ss_bond_max_distance = 2.2  # Angstroms - distancia típica en toxinas ICK
        
        for i, (res_i, atom_i) in enumerate(cys_sg_atoms):
            for j, (res_j, atom_j) in enumerate(cys_sg_atoms):
                if i < j:  # evita duplicados
                    distance = atom_i - atom_j
                    if distance < ss_bond_max_distance:
                        disulfide_bridges.append((res_i, res_j))
        
        return disulfide_bridges
    
    def calculate_dipole_moment(self, structure):
        """Calcula momento dipolar (crítico para interacciones con VSD de Nav1.7)"""
        dipole = np.zeros(3)
        
        for model in structure:
            for chain in model:
                for residue in chain:
                    if is_aa(residue):
                        try:
                            aa = seq1(residue.get_resname())
                            charge = CHARGES.get(aa, 0)
                            
                            # Uso de átomo CA para posición
                            if "CA" in residue:
                                pos = residue["CA"].get_coord()
                                dipole += charge * pos
                        except:
                            continue
        
        # Normalización del vector dipolar
        magnitude = np.linalg.norm(dipole)
        if magnitude > 0:
            dipole_norm = dipole / magnitude
        else:
            dipole_norm = np.zeros(3)
            
        return {
            'vector': dipole,
            'magnitude': magnitude,
            'normalized': dipole_norm
        }
    
    def identify_pharmacophore_residues(self, G, pharmacophore_pattern=None):
        """
        Identifica residuos que coinciden con patrón farmacofórico para toxinas Nav1.7
        """
        if not pharmacophore_pattern:
            return {}
            
        
        parts = pharmacophore_pattern.split('–')
        if len(parts) < 3:
            return {}
            
        
        target_residues = {}
        
        # Obtención de aminoácidos en orden de secuencia
        nodes = sorted(G.nodes())
        amino_acids = [G.nodes[n]['amino_acid'] for n in nodes]
        sequence = ''.join(amino_acids)
        
        # Para cada parte del farmacóforo, busca coincidencias
        for i, part in enumerate(parts):
            if len(part) > 0:
                for j in range(len(sequence) - len(part) + 1):
                    if sequence[j:j+len(part)] == part:
                        # Coincidencia encontrada, marca estos residuos
                        for k in range(len(part)):
                            residue_idx = nodes[j+k]
                            target_residues[residue_idx] = f"Parte farmacofórica {i+1}"
        
        return target_residues
    
    def identify_surface_residues(self, G, sasa_values, threshold=25):
        """
        Identifica residuos superficiales basados en valores SASA (crucial para interacción con Nav1.7)
        """
        surface_residues = {}
        for node in G.nodes():
            if node in sasa_values and sasa_values[node] > threshold:
                surface_residues[node] = sasa_values[node]
        return surface_residues
    
    def build_enhanced_graph(self, structure, cutoff_distance=8.0, pharmacophore_pattern=None):
        """Construye grafo mejorado con atributos detallados relevantes para interacciones con Nav1.7"""
        model = structure[0]
        G = nx.Graph()
        
        # Obtención de estructura secundaria y SASA si es posible
        try:
            ss_info, sasa_values = self.calculate_secondary_structure(structure)
        except Exception as e:
            print(f"Advertencia: No se pudo calcular estructura secundaria: {e}")
            ss_info, sasa_values = {}, {}
        
        # Búsqueda de puentes disulfuro (críticos para estructura de toxinas)
        disulfide_bridges = self.find_disulfide_bridges(structure)
        print(f"Encontrados {len(disulfide_bridges)} puentes disulfuro")
        
        # Cálculo de momento dipolar (crítico para interacciones con VSD)
        dipole = self.calculate_dipole_moment(structure)
        
        # Obtención de todos los átomos y átomos CA
        atoms = Selection.unfold_entities(model, 'A')
        ca_atoms = [atom for atom in atoms if atom.get_id() == 'CA' and is_aa(atom.get_parent(), standard=True)]
        
        # Adición de nodos con atributos mejorados
        for atom in ca_atoms:
            res = atom.get_parent()
            res_id = res.get_id()[1]  # Número de residuo
            resname = res.get_resname()  # Nombre de residuo de 3 letras
            
            # Conversión a código de una letra si es posible
            try:
                aa = seq1(resname)
            except:
                aa = 'X'  # 'X' para residuos no estándar
            
            # Cálculo de propiedades fisicoquímicas
            hydrophobicity = HYDROPHOBICITY.get(aa, 0)
            charge = CHARGES.get(aa, 0)
            residue_type = classify_residue(aa)
            is_in_disulfide = any(res_id in bridge for bridge in disulfide_bridges)
            secondary_structure = ss_info.get(res_id, 'unknown')
            sasa = sasa_values.get(res_id, 0)
            
            # Adición de nodo con atributos comprensivos
            G.add_node(res_id, 
                      amino_acid=aa, 
                      name=resname,
                      pos=atom.get_coord(),  # Coordenadas 3D
                      pos_2d=(atom.get_coord()[0], atom.get_coord()[1]),  # Proyección 2D
                      hydrophobicity=hydrophobicity,
                      charge=charge,
                      residue_type=residue_type,
                      secondary_structure=secondary_structure,
                      is_in_disulfide=is_in_disulfide,
                      sasa=sasa)
        
        # Adición de aristas estándar basadas en distancia
        ns = NeighborSearch(ca_atoms)
        for atom in ca_atoms:
            res_id = atom.get_parent().id[1]
            neighbors = ns.search(atom.coord, cutoff_distance, level='A')
            for neighbor in neighbors:
                neighbor_res_id = neighbor.get_parent().id[1]
                if res_id != neighbor_res_id:
                    # Cálculo de distancia real para peso de arista
                    distance = np.linalg.norm(atom.coord - neighbor.coord)
                    G.add_edge(res_id, neighbor_res_id, 
                              weight=distance,
                              type='distance',
                              interaction_strength=1.0/distance)
        
        # Adición de enlaces peptídicos (conexiones secuenciales)
        residue_ids = sorted(G.nodes())
        for i in range(len(residue_ids)-1):
            if residue_ids[i+1] - residue_ids[i] == 1:  # residuos adyacentes
                G.add_edge(residue_ids[i], residue_ids[i+1], 
                          weight=1.0,
                          type='peptide',
                          interaction_strength=5.0)  # más fuerte que basado en distancia
        
        # Adición de puentes disulfuro
        for res1, res2 in disulfide_bridges:
            if res1 in G.nodes() and res2 in G.nodes():
                G.add_edge(res1, res2, 
                          weight=1.0,
                          type='disulfide',
                          interaction_strength=10.0)  
        
        # Almacenamiento de atributos globales como atributos de grafo
        G.graph['dipole_vector'] = dipole['vector']
        G.graph['dipole_magnitude'] = dipole['magnitude'] 
        G.graph['disulfide_count'] = len(disulfide_bridges)
        
        # Identificación de residuos pharmacophore y superficiales
        pharmacophore_residues = self.identify_pharmacophore_residues(G, pharmacophore_pattern)
        surface_residues = self.identify_surface_residues(G, sasa_values)
        
        # Adición de atributos a nodos
        for node in G.nodes():
            G.nodes[node]['is_pharmacophore'] = node in pharmacophore_residues
            G.nodes[node]['is_surface'] = node in surface_residues
            G.nodes[node]['pharmacophore_part'] = pharmacophore_residues.get(node, "")
        
        return G
    
    def calculate_graph_metrics(self, G):
        """Calcula métricas de grafo centradas en características relevantes para Nav1.7"""
        if len(G) == 0:
            return {"error": "Grafo vacío"}
            
        metrics = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'avg_degree': round(sum(dict(G.degree()).values()) / len(G), 2),
            'density': round(nx.density(G), 4),
            'clustering_coefficient': round(nx.average_clustering(G), 4),
            'disulfide_count': G.graph.get('disulfide_count', 0),
            'dipole_magnitude': round(G.graph.get('dipole_magnitude', 0), 2),
        }
        
        # Cálculo de métricas de centralidad (importantes para identificar residuos clave de interacción)
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        eigenvector_centrality = nx.eigenvector_centrality_numpy(G)
        
        # Valores promedio de centralidad
        metrics['avg_degree_centrality'] = round(sum(degree_centrality.values()) / len(degree_centrality), 4)
        metrics['avg_betweenness_centrality'] = round(sum(betweenness_centrality.values()) / len(betweenness_centrality), 4)
        metrics['avg_closeness_centrality'] = round(sum(closeness_centrality.values()) / len(closeness_centrality), 4)
        metrics['avg_eigenvector_centrality'] = round(sum(eigenvector_centrality.values()) / len(eigenvector_centrality), 4)
        
        # Almacenamiento de centralidad para cada nodo
        nx.set_node_attributes(G, degree_centrality, 'degree_centrality')
        nx.set_node_attributes(G, betweenness_centrality, 'betweenness_centrality')
        nx.set_node_attributes(G, closeness_centrality, 'closeness_centrality')
        nx.set_node_attributes(G, eigenvector_centrality, 'eigenvector_centrality')
        
        # Cálculo de estadísticas de distribución de carga
        charges = [G.nodes[n]['charge'] for n in G.nodes()]
        metrics['total_charge'] = sum(charges)
        metrics['charge_std_dev'] = np.std(charges)
        
        # Cálculo de distribución de hidrofobicidad
        hydrophobicity = [G.nodes[n]['hydrophobicity'] for n in G.nodes()]
        metrics['avg_hydrophobicity'] = round(np.mean(hydrophobicity), 2)
        metrics['hydrophobicity_std_dev'] = round(np.std(hydrophobicity), 2)
        
        # Cálculo de características superficiales
        surface_nodes = [n for n, attr in G.nodes(data=True) if attr.get('is_surface', False)]
        if surface_nodes:
            surface_charges = [G.nodes[n]['charge'] for n in surface_nodes]
            surface_hydrophobicity = [G.nodes[n]['hydrophobicity'] for n in surface_nodes]
            
            metrics['surface_charge'] = sum(surface_charges)
            metrics['surface_hydrophobicity'] = round(np.mean(surface_hydrophobicity), 2)
            metrics['surface_to_total_ratio'] = round(len(surface_nodes) / len(G.nodes()), 2)
        
        # Conteo de residuos pharmacophore
        pharm_nodes = [n for n, attr in G.nodes(data=True) if attr.get('is_pharmacophore', False)]
        metrics['pharmacophore_count'] = len(pharm_nodes)
        
        
        try:
            communities = nx.algorithms.community.greedy_modularity_communities(G)
            metrics['community_count'] = len(communities)
            metrics['modularity'] = nx.algorithms.community.modularity(G, communities)
        except:
            metrics['community_count'] = 0
            metrics['modularity'] = 0
        
        return metrics
    
    def detect_structural_motifs(self, G):
        """Detecta motivos estructurales comunes en toxinas que interactúan con Nav1.7"""
        motifs = {}
        
        # Búsqueda de horquillas beta 
        beta_strands = [n for n, attr in G.nodes(data=True) 
                      if attr.get('secondary_structure') == 'beta']
        
        if len(beta_strands) >= 4:
            #  horquilla beta
            motifs['beta_hairpin'] = True
            motifs['beta_strand_count'] = len(beta_strands)
        else:
            motifs['beta_hairpin'] = False
            motifs['beta_strand_count'] = len(beta_strands)
        
        # Detección de patrón de nudo de cistina
        disulfide_nodes = [n for n, attr in G.nodes(data=True) if attr.get('is_in_disulfide', False)]
        if G.graph.get('disulfide_count', 0) >= 3 and len(disulfide_nodes) >= 6:
            # Potencial nudo de cistina 
            motifs['cystine_knot'] = True
        else:
            motifs['cystine_knot'] = False
        
        # Búsqueda de parches cargados 
        positive_nodes = [n for n, attr in G.nodes(data=True) 
                        if attr.get('charge', 0) > 0 and attr.get('is_surface', False)]
        
        if len(positive_nodes) >= 3:
            # Comprobación si forman un cluster (cercanos entre sí)
            pos = nx.get_node_attributes(G, 'pos')
            if pos:
                coordinates = np.array([pos[n] for n in positive_nodes])
                if len(coordinates) >= 2:
                    distances = pdist(coordinates)
                    if np.min(distances) < 10.0:  # Ångstroms
                        motifs['positive_patch'] = True
                    else:
                        motifs['positive_patch'] = False
                else:
                    motifs['positive_patch'] = False
            else:
                motifs['positive_patch'] = False
        else:
            motifs['positive_patch'] = False
            
        # Búsqueda de parches hidrofóbicos 
        hydrophobic_nodes = [n for n, attr in G.nodes(data=True) 
                           if attr.get('hydrophobicity', 0) > 1.0 and attr.get('is_surface', False)]
        
        if len(hydrophobic_nodes) >= 3:
            # Comprobación si forman un cluster
            pos = nx.get_node_attributes(G, 'pos')
            if pos:
                coordinates = np.array([pos[n] for n in hydrophobic_nodes])
                if len(coordinates) >= 2:
                    distances = pdist(coordinates)
                    if np.min(distances) < 10.0:  # Ångstroms
                        motifs['hydrophobic_patch'] = True
                    else:
                        motifs['hydrophobic_patch'] = False
                else:
                    motifs['hydrophobic_patch'] = False
            else:
                motifs['hydrophobic_patch'] = False
        else:
            motifs['hydrophobic_patch'] = False
            
        return motifs
    
    def visualize_enhanced_graph(self, G, title="Grafo de Toxina Nav1.7", plot_3d=False, show_labels=True, highlight_pharmacophore=True):
        """Visualización avanzada del grafo de toxina con características relevantes para Nav1.7"""
        if plot_3d:
            # Visualización 3D con características mejoradas
            fig = plt.figure(figsize=(14, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # Obtención de posiciones 3D
            pos = nx.get_node_attributes(G, 'pos')
            
            # Extracción de coordenadas x, y, z
            xs = [pos[node][0] for node in G.nodes()]
            ys = [pos[node][1] for node in G.nodes()]
            zs = [pos[node][2] for node in G.nodes()]
            
            # Obtención de atributos de nodos
            residue_types = nx.get_node_attributes(G, 'residue_type')
            is_disulfide = nx.get_node_attributes(G, 'is_in_disulfide')
            is_surface = nx.get_node_attributes(G, 'is_surface')
            is_pharmacophore = nx.get_node_attributes(G, 'is_pharmacophore')
            centrality = nx.get_node_attributes(G, 'betweenness_centrality')
            
            # Determinación de colores de nodos basados en tipo de residuo y atributos especiales
            node_colors = []
            node_sizes = []
            for node in G.nodes():
                # Color base según tipo de residuo
                res_type = residue_types.get(node, 'other')
                color = RESIDUE_COLORS.get(res_type, RESIDUE_COLORS['other'])
                
                # Modificación de color/apariencia para residuos especiales
                if highlight_pharmacophore and is_pharmacophore.get(node, False):
                    # Residuos farmacofóricos destacados con color amarillo
                    color = 'yellow'
                elif is_disulfide.get(node, False):
                    # Cisteínas con puente disulfuro más saturadas
                    r, g, b = to_rgb(color)
                    color = (r*1.2 if r*1.2 <= 1 else 1, 
                             g*1.2 if g*1.2 <= 1 else 1, 
                             b*1.2 if b*1.2 <= 1 else 1)
                
                node_colors.append(color)
                
                # Tamaño basado en centralidad y exposición superficial
                base_size = centrality.get(node, 0) * 2000 + 80
                if is_surface.get(node, False):
                    base_size *= 1.3  # Residuos superficiales más grandes
                
                node_sizes.append(base_size)
            
            # Trazado de nodos con colores y tamaños
            scatter = ax.scatter(xs, ys, zs, c=node_colors, s=node_sizes, alpha=0.8, edgecolors='black')
            
            # Dibujo de diferentes tipos de aristas con diferentes estilos
            for u, v, data in G.edges(data=True):
                x = [pos[u][0], pos[v][0]]
                y = [pos[u][1], pos[v][1]]
                z = [pos[u][2], pos[v][2]]
                
                edge_type = data.get('type', 'distance')
                
                if edge_type == 'peptide':
                    # Enlaces peptídicos como líneas sólidas
                    ax.plot(x, y, z, color='black', linewidth=1.5, alpha=0.7)
                elif edge_type == 'disulfide':
                    # Puentes disulfuro como líneas amarillas gruesas
                    ax.plot(x, y, z, color='gold', linewidth=2.5, alpha=1.0)
                else:
                    # Contactos basados en distancia como líneas grises delgadas
                    ax.plot(x, y, z, color='gray', linewidth=0.5, alpha=0.3)
            
            # Adición de etiquetas de nodos si se solicita
            if show_labels:
                for node in G.nodes():
                    # Adición de etiqueta farmacofórica si es aplicable
                    pharm_tag = " 🔑" if is_pharmacophore.get(node, False) else ""
                    ax.text(pos[node][0], pos[node][1], pos[node][2], 
                           f"{node}:{G.nodes[node]['amino_acid']}{pharm_tag}", 
                           fontsize=8, color='black')
            
            # Dibujo de vector dipolar si está disponible
            if 'dipole_vector' in G.graph and 'dipole_magnitude' in G.graph:
                dipole = G.graph['dipole_vector']
                magnitude = G.graph['dipole_magnitude']
                
                if magnitude > 0:
                    # Cálculo de centro de la estructura
                    center = np.mean(np.array([pos[node] for node in G.nodes()]), axis=0)
                    
                    # Dibujo de flecha para el dipolo
                    scaled_dipole = dipole / magnitude * min(6.0, magnitude/4)  # Escala apropiada
                    ax.quiver(center[0], center[1], center[2], 
                             scaled_dipole[0], scaled_dipole[1], scaled_dipole[2], 
                             color='red', arrow_length_ratio=0.3, linewidth=3)
                    
                    # Adición de anotación de magnitud de dipolo
                    ax.text(center[0] + scaled_dipole[0], 
                           center[1] + scaled_dipole[1], 
                           center[2] + scaled_dipole[2],
                           f"Dipolo: {magnitude:.1f} D", 
                           color='red', fontsize=10)
            
            ax.set_title(title)
            ax.set_xlabel('X (Å)')
            ax.set_ylabel('Y (Å)')
            ax.set_zlabel('Z (Å)')
            
            # Mejora del ángulo de visión 3D
            ax.view_init(elev=20, azim=135)
            plt.tight_layout()
            
        else:
            # Visualización 2D con características mejoradas
            fig, ax = plt.subplots(figsize=(14, 12))
            
            # Obtención de posiciones 2D
            pos = nx.get_node_attributes(G, 'pos_2d')
            
            # Obtención de atributos de nodos
            residue_types = nx.get_node_attributes(G, 'residue_type')
            is_disulfide = nx.get_node_attributes(G, 'is_in_disulfide')
            is_surface = nx.get_node_attributes(G, 'is_surface')
            is_pharmacophore = nx.get_node_attributes(G, 'is_pharmacophore')
            centrality = nx.get_node_attributes(G, 'betweenness_centrality')
            
            # Determinación de colores y tamaños de nodos
            node_colors = []
            node_sizes = []
            for node in G.nodes():
                # Color base según tipo de residuo
                res_type = residue_types.get(node, 'other')
                color = RESIDUE_COLORS.get(res_type, RESIDUE_COLORS['other'])
                
                # Modificación de color para residuos especiales
                if highlight_pharmacophore and is_pharmacophore.get(node, False):
                    color = 'yellow'
                
                node_colors.append(color)
                
                # Tamaño basado en centralidad y exposición superficial
                base_size = centrality.get(node, 0) * 2000 + 100
                if is_surface.get(node, False):
                    base_size *= 1.3
                
                node_sizes.append(base_size)
            
            # Creación de listas de aristas para diferentes tipos
            peptide_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'peptide']
            disulfide_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'disulfide']
            distance_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'distance']
            
            # Dibujo de nodos
            nodes = nx.draw_networkx_nodes(G, pos, 
                                         node_size=node_sizes, 
                                         node_color=node_colors, 
                                         alpha=0.8, 
                                         edgecolors='black',
                                         ax=ax)
            
            # Dibujo de diferentes tipos de aristas
            nx.draw_networkx_edges(G, pos, edgelist=peptide_edges, 
                                  width=2, edge_color='black', alpha=0.7, ax=ax)
            nx.draw_networkx_edges(G, pos, edgelist=disulfide_edges, 
                                  width=2.5, edge_color='gold', alpha=1.0, ax=ax)
            nx.draw_networkx_edges(G, pos, edgelist=distance_edges, 
                                  width=0.5, edge_color='gray', alpha=0.3, ax=ax)
            
            # Adición de etiquetas de nodos si se solicita
            if show_labels:
                # Creación de etiquetas personalizadas
                labels = {}
                for node in G.nodes():
                    # Adición de etiqueta farmacofórica si es aplicable
                    pharm_tag = " 🔑" if is_pharmacophore.get(node, False) else ""
                    surf_tag = " 📡" if is_surface.get(node, False) else ""
                    labels[node] = f"{node}:{G.nodes[node]['amino_acid']}{pharm_tag}{surf_tag}"
                
                nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_color='black', ax=ax)
            
            # Creación de labels para tipos de residuos
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor=color, markersize=10, label=res_type)
                             for res_type, color in RESIDUE_COLORS.items()]
            
            # Adición de tipos especiales a labels
            if highlight_pharmacophore:
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                               markerfacecolor='yellow', markersize=10, 
                                               label='Farmacóforo'))
            
            # Adición de tipos de arista a labels
            legend_elements.extend([
                plt.Line2D([0], [0], color='black', lw=2, label='Enlace peptídico'),
                plt.Line2D([0], [0], color='gold', lw=2.5, label='Puente disulfuro'),
                plt.Line2D([0], [0], color='gray', lw=0.5, label='Proximidad espacial')
            ])
            
            ax.legend(handles=legend_elements, loc='lower right')
            
            ax.set_title(title)
            ax.axis('off')
            plt.tight_layout()
        
        plt.show()
    
    def analyze_single_toxin(self, peptide_code, cutoff_distance=8.0, plot_3d=False):
        """Análisis completo de una sola toxina por código de péptido"""
        try:
            # Obtención de patrón pharmacophore de la base de datos
            pharmacophore_pattern = None
            conn = self._connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT pharmacophore_match FROM Nav1_7_InhibitorPeptides WHERE peptide_code = ?", 
                         (peptide_code,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                pharmacophore_pattern = result[0]
                print(f"Patrón farmacofórico encontrado: {pharmacophore_pattern}")
            
           
            try:
                structure = self.load_pdb_from_blob(peptide_code)
                print(f"Estructura cargada para {peptide_code} desde base de datos")
            except:
                
                pdb_filename = f"{peptide_code}.pdb"
                structure = self.load_pdb(pdb_filename)
                print(f"Estructura cargada para {peptide_code} desde archivo {pdb_filename}")
                
            # Extracción de secuenci 
            ppb = PPBuilder()
            for pp in ppb.build_peptides(structure):
                seq = pp.get_sequence()
                print(f"Secuencia: {seq}")
                break
                
            # Construcción de grafo 
            G = self.build_enhanced_graph(structure, cutoff_distance, pharmacophore_pattern)
            
            # Cálculo de métricas
            metrics = self.calculate_graph_metrics(G)
            
            # Detección de motivos estructurales
            motifs = self.detect_structural_motifs(G)
            
            # Impresión de resultados
            print(f"\nAnálisis de toxina {peptide_code} con distancia de corte {cutoff_distance}Å:")
            
            print("\nMétricas de Grafo:")
            for metric, value in metrics.items():
                print(f"{metric}: {value}")
                
            print("\nMotivos Estructurales:")
            for motif, present in motifs.items():
                status = "Presente" if present else "Ausente"
                print(f"{motif}: {status}")
                
            # Búsqueda de residuos clave (mayor centralidad)
            betweenness = nx.get_node_attributes(G, 'betweenness_centrality')
            key_residues = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
            
            print("\nTop 5 residuos clave por centralidad de intermediación:")
            for res_id, centrality in key_residues:
                aa = G.nodes[res_id]['amino_acid']
                res_type = G.nodes[res_id]['residue_type']
                is_pharm = "🔑 Farmacóforo" if G.nodes[res_id].get('is_pharmacophore', False) else ""
                is_surf = "📡 Superficie" if G.nodes[res_id].get('is_surface', False) else ""
                print(f"Residuo {res_id} ({aa}) - {res_type}: {centrality:.4f} {is_pharm} {is_surf}")
            
            # Visualización del grafo
            title = f"Toxina Nav1.7: {peptide_code} (corte={cutoff_distance}Å)"
            self.visualize_enhanced_graph(G, title=title, plot_3d=plot_3d, highlight_pharmacophore=True)
            
            return {
                'graph': G,
                'metrics': metrics,
                'motifs': motifs
            }
            
        except Exception as e:
            print(f"Error analizando {peptide_code}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
    def compare_toxins(self, peptide_codes, cutoff_distance=8.0):
        """Compara múltiples toxinas enfocándose en propiedades de grafo y motivos estructurales"""
        results = {}
        metrics_data = []
        motifs_data = []
        
        for peptide_code in peptide_codes:
            print(f"\nAnalizando {peptide_code}...")
            result = self.analyze_single_toxin(peptide_code, cutoff_distance, plot_3d=False)
            
            if result:
                results[peptide_code] = result
                
                # Recolección de métricas para comparación
                metrics = result['metrics']
                metrics_row = {
                    'Peptide': peptide_code,
                    'Nodes': metrics['num_nodes'],
                    'Edges': metrics['num_edges'],
                    'Avg Degree': metrics['avg_degree'],
                    'Clustering': metrics['clustering_coefficient'],
                    'Betweenness': metrics['avg_betweenness_centrality'],
                    'Dipole Magnitude': metrics['dipole_magnitude'],
                    'Disulfide Count': metrics['disulfide_count'],
                    'Total Charge': metrics.get('total_charge', 0),
                    'Avg Hydrophobicity': metrics.get('avg_hydrophobicity', 0),
                    'Pharmacophore Count': metrics.get('pharmacophore_count', 0),
                    'Surface Charge': metrics.get('surface_charge', 0),
                    'Surface Hydrophobicity': metrics.get('surface_hydrophobicity', 0),
                    'Community Count': metrics.get('community_count', 0)
                }
                metrics_data.append(metrics_row)
                
                # Recolección de datos de motivos
                motifs = result.get('motifs', {})
                if motifs:
                    motifs_row = {'Peptide': peptide_code}
                    motifs_row.update(motifs)
                    motifs_data.append(motifs_row)
        
        if not metrics_data:
            print("No hay resultados válidos para comparar")
            return
            
        # Creación de DataFrames para comparación
        metrics_df = pd.DataFrame(metrics_data)
        
        # Muestra de tabla de métricas
        print("\nComparación de métricas de toxinas:")
        print(metrics_df.to_string())
        
        # Creación de clustering jerárquico de toxinas basado en métricas de grafo
        if len(metrics_df) > 1:
            plt.figure(figsize=(14, 10))
            
            # Selección de columnas numéricas para clustering
            numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns
            
            # Normalización Z-score de los datos
            from sklearn.preprocessing import StandardScaler
            X = StandardScaler().fit_transform(metrics_df[numeric_cols])
            
            # Creación de mapa de calor con clustering jerárquico
            sns.clustermap(
                pd.DataFrame(X, columns=numeric_cols, index=metrics_df['Peptide']),
                cmap="viridis",
                standard_scale=1,  
                figsize=(14, 10),
                xticklabels=True,
                yticklabels=True
            )
            
            plt.title('Clustering Jerárquico de Toxinas Nav1.7 por Propiedades de Grafo')
            plt.tight_layout()
            plt.show()
            
        # Muestra de comparación de motivos si está disponible
        if motifs_data:
            motifs_df = pd.DataFrame(motifs_data)
            print("\nComparación de motivos estructurales:")
            print(motifs_df.to_string())
            
            # Visualización de motivos como mapa de calor
            if len(motifs_df) > 1:
                motif_columns = [col for col in motifs_df.columns if col != 'Peptide']
                if motif_columns:
                    plt.figure(figsize=(10, len(peptide_codes) * 0.5 + 2))
                    sns.heatmap(
                        motifs_df[motif_columns].astype(int), 
                        cmap="YlOrRd",
                        yticklabels=motifs_df['Peptide'],
                        annot=True,
                        fmt="d",
                        cbar_kws={'label': 'Presente (1) / Ausente (0)'}
                    )
                    plt.title('Motivos Estructurales en Toxinas Nav1.7')
                    plt.tight_layout()
                    plt.show()
                    
        return results
    
    def save_graph_to_database(self, peptide_code, G, graph_type='full_structure'):
        """Guarda un grafo en la base de datos para análisis futuro"""
        if graph_type not in ['full_structure', 'beta_hairpin', 'hydrophobic_patch', 'charge_ring']:
            graph_type = 'full_structure'
            
        graph_pickle = pickle.dumps(G)
        
        conn = self._connect_db()
        cursor = conn.cursor()
        
        column_name = f'graph_{graph_type}'
        query = f"UPDATE Nav1_7_InhibitorPeptides SET {column_name} = ? WHERE peptide_code = ?"
        
        cursor.execute(query, (graph_pickle, peptide_code))
        
        conn.commit()
        conn.close()
        print(f"Grafo {graph_type} guardado para {peptide_code} en la base de datos")

# Ejemplo de uso
if __name__ == "__main__":
    analyzer = Nav17ToxinGraphAnalyzer()
    
    # Análisis de una sola toxina
    # analyzer.analyze_single_toxin("β-TRTX-Cm1a", cutoff_distance=8.0, plot_3d=True)
    
    # Comparación de múltiples toxinas
    toxins_to_compare = [
        "β-TRTX-Cm1a",  # Toxina de araña con alta afinidad por Nav1.7
        "β-TRTX-Cm1b",  
        "β-TRTX-Cd1a",  
        "μ-TRTX-Hh2a",  
        "μ-TRTX-Hh2a_E1A_E4A_Y33W"  
    ]
    
    analyzer.compare_toxins(toxins_to_compare, cutoff_distance=8.0)