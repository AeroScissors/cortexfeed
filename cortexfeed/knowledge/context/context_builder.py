# File: cortexfeed/knowledge/context/context_builder.py

from __future__ import annotations

from cortexfeed.knowledge.context.models import (
    ContextDependency,
    ContextSymbol,
    RepositoryContext,
)
from cortexfeed.knowledge.graph.v2.graph_search_v2 import (
    GraphSearchV2,
)
from cortexfeed.knowledge.ranking.v2.models import (
    EvidencePackage,
)


class KnowledgeContextBuilder:
    def __init__(
        self,
        graph_search: GraphSearchV2,
    ) -> None:
        self.graph_search = graph_search

    def build(
        self,
        issue: str,
        evidence: EvidencePackage,
    ) -> RepositoryContext:
        context = RepositoryContext(
            issue=issue,
        )

        seen_symbols: set[str] = set()
        seen_dependencies: set[str] = set()
        seen_callers: set[str] = set()
        seen_callees: set[str] = set()
        seen_routes: set[str] = set()
        seen_files: set[str] = set()
        seen_chains: set[str] = set()

        #
        # Stage 1
        # Seed Evidence
        #

        for item in evidence.files:
            if item.symbol not in seen_files:
                context.files.append(item.symbol)
                seen_files.add(item.symbol)

        for item in evidence.routes:
            if item.symbol not in seen_routes:
                context.routes.append(item.symbol)
                seen_routes.add(item.symbol)

        #
        # Stage 2
        # Symbol Expansion
        #

        all_symbols = (
            evidence.symbols
            + evidence.dependencies
            + evidence.callers
            + evidence.callees
        )

        for item in all_symbols:
            node = self.graph_search.find_node(
                item.symbol,
            )

            if not node:
                continue

            if node.name not in seen_symbols:
                context.symbols.append(
                    ContextSymbol(
                        name=node.name,
                        node_type=node.type,
                    )
                )
                seen_symbols.add(node.name)

            #
            # Dependencies
            #

            for dep in self.graph_search.get_dependencies(
                node.id,
            ):
                key = (
                    f"{node.name}|"
                    f"{dep.name}|"
                    "DEPENDS_ON"
                )

                if key in seen_dependencies:
                    continue

                context.dependencies.append(
                    ContextDependency(
                        source=node.name,
                        target=dep.name,
                        relationship="DEPENDS_ON",
                    )
                )

                seen_dependencies.add(key)

            #
            # Callers
            #

            for caller in self.graph_search.find_callers(
                node.name,
            ):
                if caller.name not in seen_callers:
                    context.callers.append(
                        caller.name,
                    )
                    seen_callers.add(
                        caller.name,
                    )

            #
            # Callees
            #

            for callee in self.graph_search.find_callees(
                node.name,
            ):
                if callee.name not in seen_callees:
                    context.callees.append(
                        callee.name,
                    )
                    seen_callees.add(
                        callee.name,
                    )

            #
            # Call Chains
            #

            chain_nodes = (
                self.graph_search.trace_call_chain(
                    node.name,
                )
            )

            if chain_nodes:
                chain = [
                    node.name,
                    *[
                        n.name
                        for n in chain_nodes
                    ],
                ]

                chain_key = "->".join(
                    chain,
                )

                if chain_key not in seen_chains:
                    context.call_chains.append(
                        chain,
                    )

                    seen_chains.add(
                        chain_key,
                    )

        #
        # Stage 3
        # Route Expansion
        #

        for route in context.routes:
            if ":" not in route:
                continue

            method, path = route.split(
                ":",
                1,
            )

            trace_nodes = (
                self.graph_search.route_trace(
                    method,
                    path,
                )
            )

            if not trace_nodes:
                continue

            chain = [
                f"Route({route})",
                *[
                    n.name
                    for n in trace_nodes
                ],
            ]

            chain_key = "->".join(
                chain,
            )

            if chain_key not in seen_chains:
                context.call_chains.append(
                    chain,
                )

                seen_chains.add(
                    chain_key,
                )

        return context