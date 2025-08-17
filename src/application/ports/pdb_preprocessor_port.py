from typing import Protocol, List

class PDBPreprocessorPort(Protocol):
    def prepare_temp_pdb(self, pdb_bytes: bytes) -> str:
        ...

    def cleanup(self, paths: List[str]) -> None:
        ...
