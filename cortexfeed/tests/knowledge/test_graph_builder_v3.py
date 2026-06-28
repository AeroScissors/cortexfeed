# File: cortexfeed/tests/knowledge/test_graph_builder_v3.py

from pathlib import Path

from cortexfeed.knowledge.graph.v3.graph_builder_v3 import (
    GraphBuilderV3,
)


def test_build_graph_contains_call_edges(
    tmp_path: Path,
) -> None:
    source = """
class A:
    def a(self):
        self.b()

    def b(self):
        pass
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

    assert edge.source == "A.a"
    assert edge.target == "A.b"