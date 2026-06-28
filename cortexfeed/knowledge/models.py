# File: cortexfeed/knowledge/models.py
from __future__ import annotations

from dataclasses import dataclass, field

# ------------------------------------------------------------------
# V1 Symbol Models
# ------------------------------------------------------------------

@dataclass(slots=True)
class ImportSymbol:
    module: str
    imported: str | None
    line: int

@dataclass(slots=True)
class FunctionSymbol:
    name: str
    line: int
    end_line: int
    decorators: list[str] = field(default_factory=list)

@dataclass(slots=True)
class MethodSymbol:
    class_name: str
    name: str
    line: int
    end_line: int
    decorators: list[str] = field(default_factory=list)

@dataclass(slots=True)
class ClassSymbol:
    name: str
    line: int
    end_line: int
    bases: list[str] = field(default_factory=list)

@dataclass(slots=True)
class RouteSymbol:
    path: str
    method: str
    function_name: str
    line: int

@dataclass(slots=True)
class FileSymbols:
    file_path: str
    classes: list[ClassSymbol] = field(default_factory=list)
    functions: list[FunctionSymbol] = field(default_factory=list)
    methods: list[MethodSymbol] = field(default_factory=list)
    routes: list[RouteSymbol] = field(default_factory=list)
    imports: list[ImportSymbol] = field(default_factory=list)

# ------------------------------------------------------------------
# V2 Intelligence Models
# ------------------------------------------------------------------

@dataclass(slots=True)
class SymbolReference:
    symbol: str
    line: int

@dataclass(slots=True)
class FunctionCall:
    caller: str
    target: str
    line: int

@dataclass(slots=True)
class Instantiation:
    class_name: str
    line: int

@dataclass(slots=True)
class AttributeAccess:
    object_name: str
    attribute: str
    line: int

@dataclass(slots=True)
class DecoratorUsage:
    decorator: str
    line: int

@dataclass(slots=True)
class InheritanceRelation:
    class_name: str
    parent: str
    line: int

@dataclass(slots=True)
class FileSymbolsV2:
    file_path: str
    classes: list[ClassSymbol] = field(default_factory=list)
    functions: list[FunctionSymbol] = field(default_factory=list)
    methods: list[MethodSymbol] = field(default_factory=list)
    routes: list[RouteSymbol] = field(default_factory=list)
    imports: list[ImportSymbol] = field(default_factory=list)
    references: list[SymbolReference] = field(default_factory=list)
    calls: list[FunctionCall] = field(default_factory=list)
    instantiations: list[Instantiation] = field(default_factory=list)
    attributes: list[AttributeAccess] = field(default_factory=list)
    decorators: list[DecoratorUsage] = field(default_factory=list)
    inherits: list[InheritanceRelation] = field(default_factory=list)

# ------------------------------------------------------------------
# Graph Models
# ------------------------------------------------------------------

@dataclass(slots=True)
class GraphNode:
    id: str
    type: str
    name: str
    metadata: dict[str, object] = field(default_factory=dict)

@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    relationship: str
    metadata: dict[str, object] = field(default_factory=dict)

@dataclass(slots=True)
class Graph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)