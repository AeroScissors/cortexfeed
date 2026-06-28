# File: cortexfeed/investigation/models.py
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class ContextFile:
    path: str
    score: float

@dataclass(slots=True)
class ContextDependency:
    source: str
    target: str
    relationship: str

@dataclass(slots=True)
class ContextCallChain:
    chain: list[str]

@dataclass(slots=True)
class InvestigationContext:
    issue: str
    files: list[ContextFile] = field(default_factory=list)
    dependencies: list[ContextDependency] = field(default_factory=list)
    call_chains: list[ContextCallChain] = field(default_factory=list)
    routes: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)