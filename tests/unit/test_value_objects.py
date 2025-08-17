import pytest

from src.domain.models import IC50, FamilyName, Granularity, DistanceThreshold, SequenceSeparation


def test_ic50_normalization():
    assert IC50.normalize_to_nm(100, 'nM') == 100
    assert IC50.normalize_to_nm(1, 'μM') == 1000
    assert IC50.normalize_to_nm(2, 'um') == 2000
    assert IC50.normalize_to_nm(3, 'mM') == 3000000
    assert IC50.normalize_to_nm(None, 'nM') is None
    assert IC50.normalize_to_nm(10, None) is None


def test_familyname_like_patterns():
    fam = FamilyName('μ-TRTX')
    like1, like2 = fam.like_patterns()
    assert like1.startswith('μ-TRTX') and like1.endswith('%')
    assert like2.startswith('mu-TRTX') and like2.endswith('%')


def test_granularity_from_string():
    assert Granularity.from_string('atom') == Granularity.ATOM
    assert Granularity.from_string('CA') == Granularity.CA
    assert Granularity.from_string('anything') == Granularity.CA


def test_distance_threshold_validation():
    with pytest.raises(ValueError):
        DistanceThreshold(0)
    with pytest.raises(TypeError):
        DistanceThreshold('10')  # type: ignore
    assert float(DistanceThreshold(8.5)) == 8.5


def test_sequence_separation_validation():
    with pytest.raises(ValueError):
        SequenceSeparation(-1)
    with pytest.raises(TypeError):
        SequenceSeparation(3.5)  # type: ignore
    assert int(SequenceSeparation(5)) == 5
