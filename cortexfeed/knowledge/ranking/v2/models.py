# File: cortexfeed/knowledge/ranking/v2/models.py
from dataclasses import dataclass, field

@dataclass(slots=True)
class RankedEvidence:
    symbol: str
    score: float
    source: str

@dataclass(slots=True)
class EvidencePackage:
    files: list[RankedEvidence] = field(default_factory=list)
    symbols: list[RankedEvidence] = field(default_factory=list)
    routes: list[RankedEvidence] = field(default_factory=list)
    dependencies: list[RankedEvidence] = field(default_factory=list)
    callers: list[RankedEvidence] = field(default_factory=list)
    callees: list[RankedEvidence] = field(default_factory=list)