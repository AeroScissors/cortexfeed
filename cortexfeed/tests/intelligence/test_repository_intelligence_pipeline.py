# File: cortexfeed/tests/intelligence/test_repository_intelligence_pipeline.py

from cortexfeed.intelligence.intent_classifier import (
    IntentClassifier,
)
from cortexfeed.knowledge.context.context_builder import (
    KnowledgeContextBuilder,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
    GraphEdge,
    GraphNode,
)
from cortexfeed.knowledge.ranking.v2.evidence_selector_v2 import (
    EvidenceSelectorV2,
)
from cortexfeed.knowledge.retrieval.semantic_retriever import (
    SemanticRetriever,
)


class FakeRelevanceScorer:
    def score(self, issue: str):
        return {
            "files": [
                {
                    "name": "auth/service.py",
                    "score": 0.95,
                }
            ],
            "symbols": [
                {
                    "name": "login",
                    "score": 1.0,
                }
            ],
            "routes": [
                {
                    "name": "POST:/login",
                    "score": 1.0,
                }
            ],
        }


def _build_graph_search() -> GraphSearchV2:
    graph = Graph(
        nodes=[
            GraphNode(
                id="route:POST:/login",
                type="ROUTE",
                name="POST:/login",
            ),
            GraphNode(
                id="function:controller",
                type="FUNCTION",
                name="controller",
            ),
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
                id="symbol:DATABASE_URL",
                type="EXTERNAL_SYMBOL",
                name="DATABASE_URL",
            ),
        ],
        edges=[
            GraphEdge(
                source="route:POST:/login",
                target="function:login",
                relationship="CALLS",
            ),
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
                source="function:login",
                target="symbol:DATABASE_URL",
                relationship="REFERENCES",
            ),
        ],
    )

    return GraphSearchV2(graph)


def test_repository_intelligence_pipeline_end_to_end():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=FakeRelevanceScorer(),
    )

    builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    query = "POST /login returns 500"

    intent = classifier.classify(query)

    retrieval_result = retriever.retrieve(intent)

    evidence = selector.select(query)

    context = builder.build(
        issue=query,
        evidence=evidence,
    )

    assert intent.intent == "bug_investigation"

    assert "POST:/login" in retrieval_result["routes"]

    assert "login" in retrieval_result["symbols"]
    assert "validate_user" in retrieval_result["symbols"]

    assert context.issue == query

    assert "auth/service.py" in context.files
    assert "POST:/login" in context.routes

    assert "controller" in context.callers
    assert "validate_user" in context.callees

    assert len(context.call_chains) > 0


def test_symbol_lookup_pipeline():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    query = "Where is login handled?"

    intent = classifier.classify(query)

    retrieval_result = retriever.retrieve(intent)

    assert intent.intent == "symbol_lookup"

    assert "login" in retrieval_result["symbols"]


def test_route_trace_pipeline():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    query = "POST /login"

    intent = classifier.classify(query)

    retrieval_result = retriever.retrieve(intent)

    assert "POST:/login" in retrieval_result["routes"]

    assert "login" in retrieval_result["symbols"]
    assert "validate_user" in retrieval_result["symbols"]
    assert "create_token" in retrieval_result["symbols"]


def test_general_search_pipeline():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    query = "authentication"

    intent = classifier.classify(query)

    retrieval_result = retriever.retrieve(intent)

    assert intent.intent == "general_search"

    assert isinstance(
        retrieval_result,
        dict,
    )


def test_pipeline_is_deterministic():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    query = "POST /login returns 500"

    intent_a = classifier.classify(query)
    intent_b = classifier.classify(query)

    result_a = retriever.retrieve(intent_a)
    result_b = retriever.retrieve(intent_b)

    assert intent_a.intent == intent_b.intent
    assert result_a == result_b


def test_pipeline_handles_unknown_symbol():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    query = "Where is nonexistent_service handled?"

    intent = classifier.classify(query)

    retrieval_result = retriever.retrieve(intent)

    assert intent.intent == "symbol_lookup"

    assert isinstance(
        retrieval_result["symbols"],
        list,
    )


def test_pipeline_handles_empty_query():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    query = ""

    intent = classifier.classify(query)

    retrieval_result = retriever.retrieve(intent)

    assert intent.intent == "general_search"

    assert retrieval_result == {
        "symbols": [],
        "routes": [],
        "files": [],
    }