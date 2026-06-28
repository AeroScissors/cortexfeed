# File: cortexfeed/tests/intelligence/test_repository_answering_pipeline.py

from cortexfeed.intelligence.intent_classifier import (
    IntentClassifier,
)
from cortexfeed.intelligence.repository_assistant import (
    RepositoryAssistant,
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


def _build_pipeline():
    graph_search = _build_graph_search()

    classifier = IntentClassifier()

    retriever = SemanticRetriever(
        graph_search=graph_search,
    )

    selector = EvidenceSelectorV2(
        graph_search=graph_search,
        relevance_scorer=FakeRelevanceScorer(),
    )

    context_builder = KnowledgeContextBuilder(
        graph_search=graph_search,
    )

    assistant = RepositoryAssistant()

    return (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    )


def test_end_to_end_repository_answering():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "POST /login returns 500"

    intent = classifier.classify(query)

    retrieval = retriever.retrieve(intent)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert answer.answer
    assert answer.confidence > 0.0

    assert "POST:/login" in retrieval["routes"]

    assert "POST:/login" in answer.routes

    assert "login" in answer.symbols

    assert len(answer.call_chains) > 0


def test_symbol_lookup_end_to_end():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "Where is login handled?"

    intent = classifier.classify(query)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert intent.intent == "symbol_lookup"

    assert "login" in answer.answer.lower()

    assert answer.confidence > 0.0


def test_route_information_propagates():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "POST /login returns 500"

    intent = classifier.classify(query)

    retriever.retrieve(intent)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert answer.routes == [
        "POST:/login",
    ]


def test_symbol_information_propagates():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "Where is login handled?"

    classifier.classify(query)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert "login" in answer.symbols


def test_call_chain_information_propagates():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "POST /login returns 500"

    classifier.classify(query)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert len(answer.call_chains) > 0

    chain = answer.call_chains[0]

    assert isinstance(
        chain,
        list,
    )


def test_pipeline_is_deterministic():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "POST /login returns 500"

    intent_a = classifier.classify(query)
    retriever.retrieve(intent_a)
    evidence_a = selector.select(query)

    context_a = context_builder.build(
        issue=query,
        evidence=evidence_a,
    )

    answer_a = assistant.answer(
        query=query,
        context=context_a,
    )

    intent_b = classifier.classify(query)
    retriever.retrieve(intent_b)
    evidence_b = selector.select(query)

    context_b = context_builder.build(
        issue=query,
        evidence=evidence_b,
    )

    answer_b = assistant.answer(
        query=query,
        context=context_b,
    )

    assert answer_a.answer == answer_b.answer
    assert answer_a.confidence == answer_b.confidence
    assert answer_a.routes == answer_b.routes
    assert answer_a.symbols == answer_b.symbols
    assert answer_a.call_chains == answer_b.call_chains


def test_unknown_symbol_query():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = "Where is unknown_service handled?"

    classifier.classify(query)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert isinstance(
        answer.answer,
        str,
    )

    assert answer.confidence >= 0.0


def test_empty_query():
    (
        classifier,
        retriever,
        selector,
        context_builder,
        assistant,
    ) = _build_pipeline()

    query = ""

    intent = classifier.classify(query)

    retrieval = retriever.retrieve(intent)

    evidence = selector.select(query)

    context = context_builder.build(
        issue=query,
        evidence=evidence,
    )

    answer = assistant.answer(
        query=query,
        context=context,
    )

    assert intent.intent == "general_search"

    assert retrieval == {
        "symbols": [],
        "routes": [],
        "files": [],
    }

    assert isinstance(
        answer.answer,
        str,
    )