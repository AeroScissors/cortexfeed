# File: cortexfeed/tests/knowledge/test_repository_bootstrap.py

from pathlib import Path

from cortexfeed.knowledge.graph.v3.graph_builder_v3 import (
    GraphBuilderV3,
)


def test_repository_builds_call_graph(
    tmp_path: Path,
) -> None:
    source = """
class Service:
    def login(self):
        pass

class Controller:
    def login(self):
        service = Service()
        service.login()
"""

    (tmp_path / "example.py").write_text(
        source,
        encoding="utf-8",
    )

    builder = GraphBuilderV3()

    graph = builder.build(
        project_root=tmp_path,
    )

    assert len(graph.edges) == 1

    edge = graph.edges[0]

    assert edge.source == "Controller.login"
    assert edge.target == "Service.login"