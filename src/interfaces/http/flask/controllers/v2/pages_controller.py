from flask import Blueprint, render_template


pages_v2 = Blueprint("pages_v2", __name__)

# Simple DI for repositories used by server-rendered pages
_tox_repo = None


def configure_pages_dependencies(*, toxin_repo=None):
    global _tox_repo
    if toxin_repo is not None:
        _tox_repo = toxin_repo


@pages_v2.get("/")
def viewer_page_v2():
    # Fetch selectable peptide lists for initial render; fall back to empty if DI missing
    toxinas = []
    nav1_7 = []
    try:
        if _tox_repo is not None:
            toxinas = _tox_repo.list_toxins()
            nav1_7 = _tox_repo.list_nav1_7()
    except Exception:
        # Keep safe defaults on any failure; JS can still fetch via API if needed
        toxinas, nav1_7 = [], []
    return render_template("viewer.html", toxinas=toxinas, nav1_7=nav1_7)


@pages_v2.get("/dipole_families")
def dipole_families_page_v2():
    return render_template("dipole_families.html")
