import os
import numpy as np
from Bio.PDB import PDBParser, DSSP, ShrakeRupley
import MDAnalysis as mda

# Definir residuos hidrofóbicos y cargados
hidrofobicos = {'ALA', 'VAL', 'LEU', 'ILE', 'MET', 'PHE', 'TRP', 'PRO'}
cargados = {'ARG', 'LYS', 'HIS', 'ASP', 'GLU'}

# Ruta al primer archivo PDB en la carpeta 'pdbs'
pdb_folder = "pdbs"
pdb_files = [f for f in os.listdir(pdb_folder) if f.endswith(".pdb")]
if not pdb_files:
    raise FileNotFoundError("No se encontró ningún archivo .pdb en la carpeta 'pdbs'.")
pdb_path = os.path.join(pdb_folder, pdb_files[0])
print(f"Analizando archivo: {pdb_path}") 

# Analizar estructura con Biopython
parser = PDBParser(QUIET=True)
estructura = parser.get_structure('proteina', pdb_path)
modelo = estructura[0]

# Calcular SASA con ShrakeRupley
sr = ShrakeRupley()
sr.compute(modelo, level="R")  # Nivel de residuo

# Detectar parches hidrofóbicos
parches_hidrofobicos = []
for cadena in modelo:
    for residuo in cadena:
        if residuo.get_resname() in hidrofobicos:
            sasa = getattr(residuo, 'sasa', 0.0)
            if sasa > 30.0:  # Umbral ajustable
                parches_hidrofobicos.append((cadena.id, residuo.id[1], residuo.get_resname(), sasa))

# Asignar estructuras secundarias con DSSP
dssp = DSSP(modelo, pdb_path)
beta_strands = []
for k in dssp.keys():
    try:
        chain_id, res_id = k[0], k[1][1]
        ss = dssp[k][2]
        if ss == 'E':
            beta_strands.append(((chain_id, res_id), ss))
    except Exception as e:
        print(f"Saltando clave inválida {k}: {e}")
beta_hairpins = []
for i in range(len(beta_strands) - 1):
    r1 = beta_strands[i][0][1]  # resseq del primero
    r2 = beta_strands[i+1][0][1]  # resseq del segundo
    if abs(r2 - r1) <= 6:
        beta_hairpins.append((r1, r2))

# Analizar estructura con MDAnalysis
u = mda.Universe(pdb_path)
residuos_cargados = sorted(
    [res for res in u.select_atoms("protein").residues if res.resname in cargados],
    key=lambda r: r.resid
)

# Detectar anillos de carga consecutivos (mínimo 3)
anillos_de_carga = []
grupo_actual = []

for i in range(len(residuos_cargados)):
    if not grupo_actual:
        grupo_actual.append(residuos_cargados[i])
    else:
        previo = grupo_actual[-1].resid
        actual = residuos_cargados[i].resid
        if actual == previo + 1:
            grupo_actual.append(residuos_cargados[i])
        else:
            if len(grupo_actual) >= 3:
                anillos_de_carga.append([r.resid for r in grupo_actual])
            grupo_actual = [residuos_cargados[i]]

# Verificar el último grupo
if len(grupo_actual) >= 3:
    anillos_de_carga.append([r.resid for r in grupo_actual])

# Mostrar resultados
print("Parches hidrofóbicos detectados:")
for parche in parches_hidrofobicos:
    print(f"Cadena {parche[0]}, Residuo {parche[1]} ({parche[2]}), SASA: {parche[3]:.2f}")

print("\nβ-hairpins detectados:")
for hairpin in beta_hairpins:
    print(f"Desde residuo {hairpin[0]} hasta residuo {hairpin[1]}")

print("\nAnillos de carga detectados:")
for grupo in anillos_de_carga:
    print(f"Residuos consecutivos cargados: {grupo}")
