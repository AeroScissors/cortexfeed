# File: cortexfeed/tests/knowledge/v2/test_evidence_selector_v2.py

from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.ranking.v2.evidence_selector_v2 import (
    EvidenceSelectorV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)


class FakeRelevanceScorer:
    def __init__(self, result):
        self.result = result

    def score(self, issue: str):
        return self.result


def _build_graph_search() -> GraphSearchV2:
    graph = Graph(
        nodes=[
            GraphNode(
                id="function:login",
                type="FUNCTION",
                name="login",
            ),
            GraphNode(
                id="function:validate_user",
                type="FUNCTION",
                name="validate_user",
            ),
            GraphNode(
                id="function:create_token",
                type="FUNCTION",
                name="create_token",
            ),
            GraphNode(
                id="function:controller",
                type="FUNCTION",
                name="controller",
            ),
            GraphNode(
                id="route:POST:/login",
                type="ROUTE",
                name="POST:/login",
            ),
            GraphNode(
                id="symbol:DATABASE_URL",
                type="EXTERNAL_SYMBOL",
                name="DATABASE_URL",
            ),
        ],
        edges=[
            GraphEdge(
                source="function:controller",
                target="function:login",
                relationship="CALLS",
            ),
            GraphEdge(
                source="function:login",
                target="function:validate_user",
                relationship="CALLS",
            ),
            GraphEdge(
                source="function:validate_user",
                target="function:create_token",
                relationship="CALLS",
            ),
            GraphEdge(
                source="route:POST:/login",
                target="function:login",
                relationship="CALLS",
            ),
            GraphEdge(
                source="function:login",
                target="symbol:DATABASE_URL",
                relationship="REFERENCES",
            ),
        ],
    )

    return GraphSearchV2(graph)


def test_select_returns_seed_evidence():
    scorer = FakeRelevanceScorer(
        {
            "files": [
                {
                    "name": "auth.py",
                    "score": 0.95,
                }
            ],
            "symbols": [
                {
                    "name": "login",
                    "score": 0.90,
                }
            ],
            "routes": [
                {
                    "name": "POST:/login",
                    "score": 1.0,
                }
            ],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "login bug",
    )

    assert len(package.files) == 1
    assert len(package.symbols) > 0
    assert len(package.routes) == 1

    assert package.files[0].symbol == "auth.py"
    assert package.routes[0].symbol == "POST:/login"


def test_dependency_expansion():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [
                {
                    "name": "login",
                    "score": 1.0,
                }
            ],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "login bug",
    )

    dependency_names = {
        item.symbol
        for item in package.dependencies
    }

    assert "validate_user" in dependency_names
    assert "DATABASE_URL" in dependency_names


def test_caller_expansion():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [
                {
                    "name": "login",
                    "score": 1.0,
                }
            ],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "login bug",
    )

    caller_names = {
        item.symbol
        for item in package.callers
    }

    assert "controller" in caller_names


def test_callee_expansion():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [
                {
                    "name": "login",
                    "score": 1.0,
                }
            ],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "login bug",
    )

    callee_names = {
        item.symbol
        for item in package.callees
    }

    assert "validate_user" in callee_names


def test_route_seed_expansion():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [],
            "routes": [
                {
                    "name": "POST:/login",
                    "score": 1.0,
                }
            ],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "route failure",
    )

    symbol_names = {
        item.symbol
        for item in package.symbols
    }

    assert "login" in symbol_names
    assert "validate_user" in symbol_names
    assert "create_token" in symbol_names


def test_implicit_route_detection_from_issue_text():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "POST /login returns 500",
    )

    route_names = {
        item.symbol
        for item in package.routes
    }

    assert "POST:/login" in route_names


def test_deduplication_keeps_highest_score():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [
                {
                    "name": "login",
                    "score": 1.0,
                },
                {
                    "name": "login",
                    "score": 0.5,
                },
            ],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "login issue",
    )

    login_entry = next(
        item
        for item in package.symbols
        if item.symbol == "login"
    )

    assert login_entry.score == 1.0


def test_limit_is_respected():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [
                {"name": f"symbol_{i}", "score": 100 - i}
                for i in range(50)
            ],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "large issue",
        limit=5,
    )

    assert len(package.symbols) == 5


def test_results_are_sorted_by_score():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [
                {
                    "name": "low",
                    "score": 0.1,
                },
                {
                    "name": "high",
                    "score": 0.9,
                },
                {
                    "name": "medium",
                    "score": 0.5,
                },
            ],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "ranking test",
    )

    assert package.symbols[0].symbol == "high"
    assert package.symbols[1].symbol == "medium"
    assert package.symbols[2].symbol == "low"


def test_empty_relevance_result():
    scorer = FakeRelevanceScorer(
        {
            "files": [],
            "symbols": [],
            "routes": [],
        }
    )

    selector = EvidenceSelectorV2(
        graph_search=_build_graph_search(),
        relevance_scorer=scorer,
    )

    package = selector.select(
        "nothing found",
    )

    assert package.files == []
    assert package.symbols == []
    assert package.routes == []
    assert package.dependencies == []
    assert package.callers == []
    assert package.callees == []