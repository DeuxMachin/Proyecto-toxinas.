from flask import Blueprint, jsonify, request

from src.application.use_cases.list_peptides import ListPeptides, ListPeptidesInput
from src.infrastructure.db.sqlite.toxin_repository_sqlite import SqliteToxinRepository


toxins_v2 = Blueprint("toxins_v2", __name__)
_repo = SqliteToxinRepository()


def configure_toxins_dependencies(*, toxin_repo: SqliteToxinRepository = None):
    global _repo
    if toxin_repo is not None:
        _repo = toxin_repo


@toxins_v2.get("/v2/peptides")
def list_peptides_v2():
    source = request.args.get("source", "toxinas")
    usecase = ListPeptides(_repo)
    items = usecase.execute(ListPeptidesInput(source=source))
    # Normalize to a JSON-friendly shape
    result = [
        {"id": pid, "name": name}
        for (pid, name) in items
    ]
    return jsonify({"source": source, "items": result})
