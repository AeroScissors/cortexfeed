# File: cortexfeed/tests/knowledge/test_repository_graph_builder.py

from pathlib import Path

from cortexfeed.knowledge.graph.v3.repository_graph_builder import (
    RepositoryGraphBuilder,
)


def test_build_repository_context(
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

    builder = RepositoryGraphBuilder()

    context = builder.build(
        project_root=tmp_path,
    )

    assert context.graph is not None

    assert isinstance(
        context.symbols,
        dict,
    )

    assert isinstance(
        context.routes,
        dict,
    )

    assert isinstance(
        context.project_tree,
        dict,
    )