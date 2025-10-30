import sys, os
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from src.interfaces.http.flask.presenters.graph_presenter import GraphPresenter

props = {"num_nodes": 10, "num_edges": 20}
meta = {"source": "nav1_7", "id": 7, "granularity": "CA"}
# Present output available via GraphPresenter.present(props, meta)
