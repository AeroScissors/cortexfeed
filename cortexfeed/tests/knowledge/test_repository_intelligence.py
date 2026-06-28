# File: cortexfeed/tests/knowledge/test_repository_intelligence.py

from pathlib import Path

from cortexfeed.knowledge.graph.v3.repository_intelligence import (
    RepositoryIntelligence,
)


def test_build_graph_from_repository(
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

    intelligence = RepositoryIntelligence()

    graph = intelligence.build_graph(
        project_root=tmp_path,
    )

    assert len(graph.edges) == 1