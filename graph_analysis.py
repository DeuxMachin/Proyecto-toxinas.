import os
import networkx as nx
import matplotlib.pyplot as plt
from Bio import PDB
from Bio.PDB import NeighborSearch, Selection
from Bio.PDB.Polypeptide import is_aa
from Bio.Data import IUPACData
from Bio.SeqUtils.ProtParam import ProteinAnalysis
import string
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

class ProteinGraphAnalyzer:
    def __init__(self, pdb_folder="pdbs/"):
        self.pdb_folder = pdb_folder
        self.parser = PDB.PDBParser(QUIET=True)
    
    def load_pdb(self, pdb_filename):
        """Load a PDB file and return the structure."""
        pdb_path = os.path.join(self.pdb_folder, pdb_filename)
        if not os.path.exists(pdb_path):
            raise FileNotFoundError(f"PDB file not found: {pdb_path}")
        
        structure = self.parser.get_structure('protein', pdb_path)
        return structure
    
    def extract_sequence(self, structure):
        """Extract the amino acid sequence from a structure."""
        ppb = PDB.PPBuilder()
        sequences = ppb.build_peptides(structure)
        
        if not sequences:
            raise ValueError("No amino acid sequence found in the PDB file.")
        
        # Using the first polypeptide chain
        sequence = sequences[0].get_sequence()
        sequence_str = str(sequence)
        
        # Filter non-standard characters
        amino_acids = ''.join([aa for aa in sequence_str if aa in string.ascii_uppercase])
        
        if not amino_acids:
            raise ValueError("Empty amino acid sequence or contains non-standard characters.")
        
        return amino_acids
    
    def calculate_aa_composition(self, amino_acids):
        """Calculate amino acid composition and properties."""
        analysis = ProteinAnalysis(amino_acids)
        
        # Count amino acids
        total_residues = len(amino_acids)
        aa_counts = {aa: amino_acids.count(aa) for aa in set(amino_acids)}
        
        # Calculate percentages
        aa_percentages = {aa: round((count / total_residues) * 100, 2) 
                         for aa, count in aa_counts.items()}
        
        # Basic physicochemical properties
        properties = {
            'molecular_weight': round(analysis.molecular_weight(), 2),  # Da
            'pI': round(analysis.isoelectric_point(), 2),
            'hydrophobicity': round(analysis.gravy(), 2),  # GRAVY score
            'net_charge_pH7': round(analysis.charge_at_pH(7.0), 2)
        }
        
        return {
            'sequence': amino_acids,
            'aa_counts': aa_counts,
            'aa_percentages': aa_percentages,
            'properties': properties
        }
    
    def build_residue_graph(self, structure, cutoff_distance=8.0):
        """Build a graph where nodes are residues and edges are based on distance."""
        model = structure[0]  # First model
        
        # Get all atoms
        atoms = Selection.unfold_entities(model, 'A')
        
        # Select only CA atoms of standard amino acids
        ca_atoms = [atom for atom in atoms if atom.get_id() == 'CA' and is_aa(atom.get_parent(), standard=True)]
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes with attributes
        for atom in ca_atoms:
            res = atom.get_parent()
            res_id = res.get_id()[1]  # Residue number
            resname = res.get_resname()  # 3-letter residue name
            
            # Convert to one-letter code if possible
            try:
                aa = IUPACData.protein_letters_3to1.get(resname.capitalize(), 'X')
            except KeyError:
                aa = 'X'  # 'X' for non-standard residues
                
            # Add node with attributes
            G.add_node(res_id, 
                       amino_acid=aa, 
                       pos=atom.get_coord(),  # 3D coordinates
                       pos_2d=(atom.get_coord()[0], atom.get_coord()[1]),  # 2D projection
                       name=resname)
        
        # Add edges based on cutoff distance
        ns = NeighborSearch(ca_atoms)
        for atom in ca_atoms:
            res_id = atom.get_parent().id[1]
            neighbors = ns.search(atom.coord, cutoff_distance, level='A')
            for neighbor in neighbors:
                neighbor_res_id = neighbor.get_parent().id[1]
                if res_id != neighbor_res_id:
                    # Calculate actual distance for edge weight
                    distance = np.linalg.norm(atom.coord - neighbor.coord)
                    G.add_edge(res_id, neighbor_res_id, weight=distance)
        
        return G
    
    def calculate_graph_metrics(self, G):
        """Calculate various graph metrics."""
        if len(G) == 0:
            return {"error": "Empty graph"}
            
        metrics = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'avg_degree': round(sum(dict(G.degree()).values()) / len(G), 2),
            'density': round(nx.density(G), 4),
            'clustering_coefficient': round(nx.average_clustering(G), 4),
        }
        
        # Add centrality metrics
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        
        metrics['avg_degree_centrality'] = round(sum(degree_centrality.values()) / len(degree_centrality), 4)
        metrics['avg_betweenness_centrality'] = round(sum(betweenness_centrality.values()) / len(betweenness_centrality), 4)
        metrics['avg_closeness_centrality'] = round(sum(closeness_centrality.values()) / len(closeness_centrality), 4)
        
        # Store centrality for each node
        nx.set_node_attributes(G, degree_centrality, 'degree_centrality')
        nx.set_node_attributes(G, betweenness_centrality, 'betweenness_centrality')
        nx.set_node_attributes(G, closeness_centrality, 'closeness_centrality')
        
        return metrics
    
    def visualize_graph(self, G, title="Protein Residue Graph", plot_3d=False):
        """Visualize the protein graph."""
        if plot_3d:
            # 3D visualization
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Get 3D positions
            pos = nx.get_node_attributes(G, 'pos')
            
            # Extract x, y, z coordinates
            xs = [pos[node][0] for node in G.nodes()]
            ys = [pos[node][1] for node in G.nodes()]
            zs = [pos[node][2] for node in G.nodes()]
            
            # Plot nodes
            sc = ax.scatter(xs, ys, zs, s=100, c='skyblue', edgecolors='black')
            
            # Plot edges
            for u, v in G.edges():
                x = [pos[u][0], pos[v][0]]
                y = [pos[u][1], pos[v][1]]
                z = [pos[u][2], pos[v][2]]
                ax.plot(x, y, z, 'gray', alpha=0.5)
            
            # Add node labels
            for node in G.nodes():
                ax.text(pos[node][0], pos[node][1], pos[node][2], 
                    f"{node}:{G.nodes[node]['amino_acid']}", 
                    fontsize=8)
            
            ax.set_title(title)
            plt.tight_layout()
            
        else:
            # 2D visualization
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Get 2D positions
            pos = nx.get_node_attributes(G, 'pos_2d')
            
            # Calculate node sizes based on betweenness centrality
            betweenness = nx.get_node_attributes(G, 'betweenness_centrality')
            node_sizes = [v * 2000 + 50 for v in betweenness.values()]
            
            # Calculate node colors based on degree centrality
            degree_cent = nx.get_node_attributes(G, 'degree_centrality')
            node_colors = [v for v in degree_cent.values()]
            
            # Create a normalization for the colorbar
            norm = plt.Normalize(min(node_colors), max(node_colors))
            
            # Draw the graph
            nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, 
                                cmap=plt.cm.viridis, alpha=0.8, ax=ax)
            edges = nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.5, ax=ax)
            
            # Add node labels
            labels = {node: f"{node}:{G.nodes[node]['amino_acid']}" for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_color='black', ax=ax)
            
            # Create the colorbar with the right mappable object
            sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='Degree Centrality')
            
            ax.set_title(title)
            ax.axis('off')
            plt.tight_layout()
        
        plt.show()
        
    def analyze_pdb(self, pdb_filename, cutoff_distance=8.0, plot_3d=False):
        """Full analysis of a PDB file."""
        try:
            # Load structure
            structure = self.load_pdb(pdb_filename)
            
            # Extract sequence and calculate composition
            amino_acids = self.extract_sequence(structure)
            composition = self.calculate_aa_composition(amino_acids)
            
            # Build graph and calculate metrics
            G = self.build_residue_graph(structure, cutoff_distance)
            metrics = self.calculate_graph_metrics(G)
            
            # Print results
            print(f"\nAnalysis of {pdb_filename} with cutoff distance {cutoff_distance}Å:")
            
            print("\nAmino Acid Sequence:")
            print(composition['sequence'])
            
            print("\nAmino Acid Composition (%):")
            for aa, percentage in sorted(composition['aa_percentages'].items()):
                print(f"{aa}: {percentage:.2f}%")
            
            print("\nPhysicochemical Properties:")
            for prop, value in composition['properties'].items():
                print(f"{prop}: {value}")
            
            print("\nGraph Metrics:")
            for metric, value in metrics.items():
                print(f"{metric}: {value}")
            
            # Visualize the graph
            self.visualize_graph(G, 
                               title=f"Residue Graph: {pdb_filename} (cutoff={cutoff_distance}Å)", 
                               plot_3d=plot_3d)
            
            return {
                'composition': composition,
                'graph': G,
                'metrics': metrics
            }
            
        except Exception as e:
            print(f"Error analyzing {pdb_filename}: {str(e)}")
            return None
    
    def analyze_all_pdbs(self, cutoff_distance=8.0, plot_3d=False):
        """Analyze all PDB files in the folder."""
        results = {}
        
        for pdb_file in os.listdir(self.pdb_folder):
            if pdb_file.endswith('.pdb'):
                print(f"\nProcessing {pdb_file}...")
                result = self.analyze_pdb(pdb_file, cutoff_distance, plot_3d)
                if result:
                    results[pdb_file] = result
        
        return results

# Example usage
if __name__ == "__main__":
    analyzer = ProteinGraphAnalyzer()
    
    # Analyze a specific PDB
    results = analyzer.analyze_pdb("β-TRTX-Cd1a.pdb", cutoff_distance=8.0, plot_3d=False)
    
    # To analyze all PDBs in the folder:
    """
    analyzer.analyze_all_pdbs(cutoff_distance=8.0, plot_3d=False)
    """