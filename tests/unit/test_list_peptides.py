import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.application.use_cases.list_peptides import ListPeptides, ListPeptidesInput

class DummyRepo:
    def __init__(self):
        self.calls = []
    def list_toxins(self):
        self.calls.append('toxins')
        return [(1, 'A'), (2, 'B')]
    def list_nav1_7(self):
        self.calls.append('nav1_7')
        return [(10, 'X')]

def test_list_peptides_toxinas():
    repo = DummyRepo()
    uc = ListPeptides(repo)
    result = uc.execute(ListPeptidesInput(source='toxinas'))
    assert result == [(1, 'A'), (2, 'B')]
    assert repo.calls == ['toxins']


def test_list_peptides_nav1_7():
    repo = DummyRepo()
    uc = ListPeptides(repo)
    result = uc.execute(ListPeptidesInput(source='nav1_7'))
    assert result == [(10, 'X')]
    assert repo.calls == ['nav1_7']


def test_list_peptides_unknown_source():
    repo = DummyRepo()
    uc = ListPeptides(repo)
    result = uc.execute(ListPeptidesInput(source='unknown'))
    assert result == []
    assert repo.calls == []
