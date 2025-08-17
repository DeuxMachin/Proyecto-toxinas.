import sys, os
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from src.infrastructure.pdb.pdb_preprocessor_adapter import PDBPreprocessorAdapter
from src.infrastructure.fs.temp_file_service import TempFileService

pdb_text = """
ATOM      1  N   HSD A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  HSD A   1      12.560  13.456   8.410  1.00 20.00           C
END
""".encode('utf-8')

pdb = PDBPreprocessorAdapter()
tmp = pdb.prepare_temp_pdb(pdb_text)
print('TMP', tmp, os.path.exists(tmp))

TempFileService().cleanup([tmp])
print('CLEANED', not os.path.exists(tmp))
