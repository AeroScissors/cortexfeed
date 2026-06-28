# File: cortexfeed/intelligence/capabilities/models.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CapabilityResult:
    capability: str
    confidence: float

    summary: str

    symbols: list[str] = field(
        default_factory=list,
    )

    files: list[str] = field(
        default_factory=list,
    )

    routes: list[str] = field(
        default_factory=list,
    )

    callers: list[str] = field(
        default_factory=list,
    )

    callees: list[str] = field(
        default_factory=list,
    )

    execution_path: list[str] = field(
        default_factory=list,
    )

    metadata: dict = field(
        default_factory=dict,
    )