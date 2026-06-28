# File: cortexfeed/knowledge/context/models.py

from dataclasses import dataclass, field


@dataclass(slots=True)
class ContextSymbol:
    name: str
    node_type: str


@dataclass(slots=True)
class ContextDependency:
    source: str
    target: str
    relationship: str


@dataclass(slots=True)
class RepositoryContext:
    issue: str

    files: list[str] = field(default_factory=list)

    symbols: list[ContextSymbol] = field(
        default_factory=list
    )

    routes: list[str] = field(
        default_factory=list
    )

    dependencies: list[ContextDependency] = field(
        default_factory=list
    )

    callers: list[str] = field(
        default_factory=list
    )

    callees: list[str] = field(
        default_factory=list
    )

    call_chains: list[list[str]] = field(
        default_factory=list
    )