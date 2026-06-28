# File: cortexfeed/tests/intelligence/test_capability_registry.py

from cortexfeed.intelligence.capabilities.call_chain import (
    CallChainCapability,
)
from cortexfeed.intelligence.capabilities.impact_analysis import (
    ImpactAnalysisCapability,
)
from cortexfeed.intelligence.capabilities.registry import (
    CapabilityRegistry,
)
from cortexfeed.intelligence.capabilities.route_trace import (
    RouteTraceCapability,
)
from cortexfeed.intelligence.capabilities.where_is_symbol import (
    WhereIsSymbolCapability,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.models import (
    Graph,
)


def _build_graph_search() -> GraphSearchV2:
    graph = Graph(
        nodes=[],
        edges=[],
    )

    return GraphSearchV2(graph)


def test_lists_all_capabilities():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    capabilities = registry.list_capabilities()

    assert capabilities == [
        "call_chain",
        "impact_analysis",
        "route_trace",
        "where_is_symbol",
    ]


def test_returns_where_is_symbol():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    capability = registry.get(
        "where_is_symbol",
    )

    assert isinstance(
        capability,
        WhereIsSymbolCapability,
    )


def test_returns_route_trace():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    capability = registry.get(
        "route_trace",
    )

    assert isinstance(
        capability,
        RouteTraceCapability,
    )


def test_returns_impact_analysis():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    capability = registry.get(
        "impact_analysis",
    )

    assert isinstance(
        capability,
        ImpactAnalysisCapability,
    )


def test_returns_call_chain():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    capability = registry.get(
        "call_chain",
    )

    assert isinstance(
        capability,
        CallChainCapability,
    )


def test_unknown_capability_returns_none():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    capability = registry.get(
        "unknown_capability",
    )

    assert capability is None


def test_registry_is_deterministic():
    registry = CapabilityRegistry(
        _build_graph_search(),
    )

    first = registry.list_capabilities()
    second = registry.list_capabilities()

    assert first == second