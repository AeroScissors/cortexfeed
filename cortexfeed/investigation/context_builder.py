# File: cortexfeed/investigation/context_builder.py
import re
from typing import Any

from cortexfeed.knowledge.graph.v2.graph_search_v2 import GraphSearchV2
from cortexfeed.investigation.models import (
    ContextFile,
    ContextDependency,
    ContextCallChain,
    InvestigationContext,
)


class ContextBuilder:
    def __init__(
        self,
        graph_search: GraphSearchV2,
        evidence_selector: Any,  # Replace 'Any' with actual EvidenceSelector type hint
    ) -> None:
        self.graph_search = graph_search
        self.evidence_selector = evidence_selector
        self._http_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}

    def _extract_routes_from_issue(self, issue: str) -> list[str]:
        routes = []
        # Basic pattern to find HTTP methods followed by a path, e.g., "GET /promise"
        pattern = r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[/\w\-]*)'
        matches = re.findall(pattern, issue, re.IGNORECASE)
        for method, path in matches:
            routes.append(f"{method.upper()}:{path}")
        return routes

    def build(self, issue: str) -> InvestigationContext:
        context = InvestigationContext(issue=issue)

        # Stage 1: Rank Evidence
        # Assuming evidence_selector.select returns a dict or object with relevant fields
        evidence = self.evidence_selector.select(issue)
        
        # Populate initial evidence (adapt property access based on actual EvidenceSelector output)
        top_files = evidence.get("files", [])
        top_symbols = evidence.get("symbols", [])
        top_routes = evidence.get("routes", [])

        for f in top_files:
            # Assuming file objects have 'path' and 'score' or can be unpacked
            path = f.get("path") if isinstance(f, dict) else getattr(f, "path", str(f))
            score = f.get("score", 1.0) if isinstance(f, dict) else getattr(f, "score", 1.0)
            context.files.append(ContextFile(path=path, score=score))

        context.symbols.extend(top_symbols)
        context.routes.extend(top_routes)

        seen_deps = set()
        seen_chains = set()

        for symbol in context.symbols:
            node = self.graph_search.find_node(symbol)
            if not node:
                continue

            # Stage 2: Dependency Discovery
            dependencies = self.graph_search.get_dependencies(node.id)
            for dep in dependencies:
                dep_key = f"{node.name}|DEPENDS_ON|{dep.name}"
                if dep_key not in seen_deps:
                    context.dependencies.append(
                        ContextDependency(
                            source=node.name,
                            target=dep.name,
                            relationship="DEPENDS_ON"
                        )
                    )
                    seen_deps.add(dep_key)

            # Stage 3: Caller Discovery
            callers = self.graph_search.find_callers(symbol)
            for caller in callers:
                dep_key = f"{caller.name}|CALLS|{node.name}"
                if dep_key not in seen_deps:
                    context.dependencies.append(
                        ContextDependency(
                            source=caller.name,
                            target=node.name,
                            relationship="CALLS"
                        )
                    )
                    seen_deps.add(dep_key)

            # Stage 4: Callee Discovery
            callees = self.graph_search.find_callees(symbol)
            for callee in callees:
                dep_key = f"{node.name}|CALLS|{callee.name}"
                if dep_key not in seen_deps:
                    context.dependencies.append(
                        ContextDependency(
                            source=node.name,
                            target=callee.name,
                            relationship="CALLS"
                        )
                    )
                    seen_deps.add(dep_key)

            # Stage 5: Call Chains
            chain_nodes = self.graph_search.trace_call_chain(symbol)
            if chain_nodes:
                chain_names = [symbol] + [n.name for n in chain_nodes]
                chain_str = "->".join(chain_names)
                if chain_str not in seen_chains:
                    context.call_chains.append(ContextCallChain(chain=chain_names))
                    seen_chains.add(chain_str)

        # Stage 6: Route Intelligence
        implicit_routes = self._extract_routes_from_issue(issue)
        all_routes = set(context.routes + implicit_routes)

        for route_str in all_routes:
            # Expected format: "METHOD:/path"
            if ":" in route_str:
                method, path = route_str.split(":", 1)
            else:
                parts = route_str.split(" ", 1)
                if len(parts) == 2:
                    method, path = parts
                else:
                    continue

            if route_str not in context.routes:
                context.routes.append(f"{method.upper()} {path}")
            
            route_trace_nodes = self.graph_search.route_trace(method, path)
            if route_trace_nodes:
                chain_names = [f"Route({method.upper()} {path})"] + [n.name for n in route_trace_nodes]
                chain_str = "->".join(chain_names)
                if chain_str not in seen_chains:
                    context.call_chains.append(ContextCallChain(chain=chain_names))
                    seen_chains.add(chain_str)

        return context