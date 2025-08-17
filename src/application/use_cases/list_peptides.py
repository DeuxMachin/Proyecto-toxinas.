from dataclasses import dataclass
from typing import List, Tuple
from src.application.ports.repositories import ToxinRepository

@dataclass
class ListPeptidesInput:
    source: str  # 'toxinas' | 'nav1_7'

class ListPeptides:
    def __init__(self, repo: ToxinRepository) -> None:
        self.repo = repo

    def execute(self, inp: ListPeptidesInput) -> List[Tuple[int, str]]:
        if inp.source == 'toxinas':
            return self.repo.list_toxins()
        elif inp.source == 'nav1_7':
            return self.repo.list_nav1_7()
        else:
            return []
