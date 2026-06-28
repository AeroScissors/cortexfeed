# File: cortexfeed/knowledge/ranking/v2/evidence_selector_v2.py
import re
from typing import Any

from cortexfeed.knowledge.graph.v2.graph_search_v2 import GraphSearchV2
from cortexfeed.knowledge.ranking.v2.models import RankedEvidence, EvidencePackage


class EvidenceSelectorV2:
    def __init__(
        self,
        graph_search: GraphSearchV2,
        relevance_scorer: Any,
    ) -> None:
        self.graph_search = graph_search
        self.relevance_scorer = relevance_scorer

    def select(self, issue: str, limit: int = 20) -> EvidencePackage:
        # Deduplication Tracker
        self._seen: dict[str, float] = {}
        self._sources: dict[str, str] = {}

        def _add_evidence(symbol: str, score: float, source: str) -> None:
            if symbol not in self._seen or score > self._seen[symbol]:
                self._seen[symbol] = score
                self._sources[symbol] = source

        # Stage 1: Initial Ranking
        seed_evidence = self.relevance_scorer.score(issue)
        
        seed_files = seed_evidence.get("files", [])
        seed_symbols = seed_evidence.get("symbols", [])
        seed_routes = seed_evidence.get("routes", [])

        for sf in seed_files:
            name = sf.get("name") if isinstance(sf, dict) else getattr(sf, "name", str(sf))
            score = sf.get("score", 1.0) if isinstance(sf, dict) else getattr(sf, "score", 1.0)
            _add_evidence(name, score, "file")

        for sym in seed_symbols:
            name = sym.get("name") if isinstance(sym, dict) else getattr(sym, "name", str(sym))
            score = sym.get("score", 1.0) if isinstance(sym, dict) else getattr(sym, "score", 1.0)
            _add_evidence(name, score, "symbol")

        for rt in seed_routes:
            name = rt.get("name") if isinstance(rt, dict) else getattr(rt, "name", str(rt))
            score = rt.get("score", 1.0) if isinstance(rt, dict) else getattr(rt, "score", 1.0)
            _add_evidence(name, score, "route")

        # Snapshot seed symbols for the expansion loops
        current_symbols = {k: v for k, v in self._seen.items() if self._sources[k] == "symbol"}

        for sym_name, base_score in current_symbols.items():
            node = self.graph_search.find_node(sym_name)
            if not node:
                continue

            # Stage 2: Dependency Expansion
            for dep in self.graph_search.get_dependencies(node.id):
                _add_evidence(dep.name, base_score * 0.75, "dependency")

            # Stage 3: Caller Expansion
            for caller in self.graph_search.find_callers(sym_name):
                _add_evidence(caller.name, base_score * 0.85, "caller")

            # Stage 4: Callee Expansion
            for callee in self.graph_search.find_callees(sym_name):
                _add_evidence(callee.name, base_score * 0.80, "callee")

        # Stage 5: Route Expansion
        # Combine explicit seed routes with implicit ones found in the issue text
        pattern = r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[/\w\-]*)'
        implicit_routes = [f"{m.upper()}:{p}" for m, p in re.findall(pattern, issue, re.IGNORECASE)]
        all_routes = set([k for k, v in self._sources.items() if v == "route"] + implicit_routes)

        for route_str in all_routes:
            if ":" in route_str:
                method, path = route_str.split(":", 1)
            elif " " in route_str:
                method, path = route_str.split(" ", 1)
            else:
                continue
                
            route_trace = self.graph_search.route_trace(method, path)
            for node in route_trace:
                # Boost all members of the execution path
                _add_evidence(node.name, 0.95, "symbol")
            
            # Ensure the route itself is tracked
            _add_evidence(f"{method.upper()}:{path}", 1.0, "route")

        # Stage 6 & 7: Deduplication & Final Ranking
        package = EvidencePackage()

        def _get_ranked(source_type: str) -> list[RankedEvidence]:
            items = [
                RankedEvidence(symbol=k, score=v, source=self._sources[k])
                for k, v in self._seen.items() if self._sources[k] == source_type
            ]
            return sorted(items, key=lambda x: x.score, reverse=True)[:limit]

        package.files = _get_ranked("file")
        package.symbols = _get_ranked("symbol")
        package.routes = _get_ranked("route")
        package.dependencies = _get_ranked("dependency")
        package.callers = _get_ranked("caller")
        package.callees = _get_ranked("callee")

        return package