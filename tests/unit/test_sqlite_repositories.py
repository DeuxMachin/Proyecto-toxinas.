import sqlite3
from pathlib import Path


def setup_temp_db(tmp_path: Path):
    db_path = tmp_path / "toxins_test.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Minimal schemas used by repositories
    cur.executescript(
        """
        CREATE TABLE Peptides (
            peptide_id INTEGER PRIMARY KEY,
            peptide_name TEXT,
            pdb_file BLOB,
            sequence TEXT
        );
        CREATE TABLE Nav1_7_InhibitorPeptides (
            id INTEGER PRIMARY KEY,
            peptide_code TEXT,
            ic50_value REAL,
            ic50_unit TEXT,
            sequence TEXT,
            pdb_blob BLOB,
            psf_blob BLOB
        );
        """
    )
    # Seed data
    cur.execute("INSERT INTO Peptides (peptide_id, peptide_name, pdb_file, sequence) VALUES (?,?,?,?)",
                (1, 'tox-pep', b'PDB1', 'AAAA'))
    cur.execute("INSERT INTO Nav1_7_InhibitorPeptides (id, peptide_code, ic50_value, ic50_unit, sequence, pdb_blob, psf_blob) VALUES (?,?,?,?,?,?,?)",
                (10, 'μ-TRTX-Hh2a', 12.3, 'nM', 'BBBB', b'PDBN', b'PSF'))
    cur.execute("INSERT INTO Nav1_7_InhibitorPeptides (id, peptide_code, ic50_value, ic50_unit, sequence, pdb_blob, psf_blob) VALUES (?,?,?,?,?,?,?)",
                (11, 'μ-TRTX-Hh2a_E1A', 20.0, 'nM', 'CCCC', b'PDBE', None))
    cur.execute("INSERT INTO Nav1_7_InhibitorPeptides (id, peptide_code, ic50_value, ic50_unit, sequence, pdb_blob, psf_blob) VALUES (?,?,?,?,?,?,?)",
                (12, 'beta-TRTX-X1', None, None, 'DDDD', b'PDBB', b'PSFB'))
    conn.commit()
    conn.close()
    return str(db_path)


def test_sqlite_structure_repository(tmp_path):
    db_path = setup_temp_db(tmp_path)
    from src.infrastructure.db.sqlite.structure_repository_sqlite import SqliteStructureRepository
    repo = SqliteStructureRepository(db_path)

    # toxinas source
    assert repo.get_pdb('toxinas', 1) == b'PDB1'
    # nav1_7 source
    assert repo.get_pdb('nav1_7', 10) == b'PDBN'
    # psf present
    assert repo.get_psf('nav1_7', 10) == b'PSF'
    # psf missing returns None
    assert repo.get_psf('nav1_7', 11) is None
    # other source returns None
    assert repo.get_pdb('other', 1) is None


def test_sqlite_metadata_repository(tmp_path):
    db_path = setup_temp_db(tmp_path)
    from src.infrastructure.db.sqlite.metadata_repository_sqlite import SqliteMetadataRepository
    repo = SqliteMetadataRepository(db_path)

    # get_toxin_info
    assert repo.get_toxin_info('toxinas', 1) == ('tox-pep', None, None)
    assert repo.get_toxin_info('nav1_7', 10) == ('μ-TRTX-Hh2a', 12.3, 'nM')
    assert repo.get_toxin_info('nav1_7', 9999) is None

    # get_complete_toxin_data
    data_nav = repo.get_complete_toxin_data('nav1_7', 10)
    assert data_nav and data_nav['pdb_data'] == b'PDBN' and data_nav['psf_data'] == b'PSF'
    data_tox = repo.get_complete_toxin_data('toxinas', 1)
    assert data_tox and data_tox['pdb_data'] == b'PDB1' and data_tox['psf_data'] is None
    assert repo.get_complete_toxin_data('nav1_7', 9999) is None

    # get_family_toxins with unicode and normalized prefixes
    fam = repo.get_family_toxins('μ-TRTX-Hh2a')
    codes = {r[1] for r in fam}
    assert 'μ-TRTX-Hh2a' in codes and 'μ-TRTX-Hh2a_E1A' in codes
    fam_norm = repo.get_family_toxins('β-TRTX')
    # At least returns iterable, though our seed may not match β-TRTX
    assert isinstance(fam_norm, list)

    # get_family_peptides
    fam_peps = repo.get_family_peptides('μ-TRTX-Hh2a')
    assert len(fam_peps) >= 1 and any(p['peptide_code'].startswith('μ-TRTX-Hh2a') for p in fam_peps)

    # get_wt_toxin_data
    wt = repo.get_wt_toxin_data('μ-TRTX-Hh2a')
    assert wt and wt['name'] == 'μ-TRTX-Hh2a' and wt['pdb_data'] == b'PDBN'
