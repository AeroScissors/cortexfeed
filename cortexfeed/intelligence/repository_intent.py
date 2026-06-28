# File: cortexfeed/intelligence/repository_intent.py

from dataclasses import dataclass, field


@dataclass(slots=True)
class RepositoryIntent:
    intent: str
    confidence: float

    symbols: list[str] = field(
        default_factory=list
    )

    routes: list[str] = field(
        default_factory=list
    )

    files: list[str] = field(
        default_factory=list
    )

    keywords: list[str] = field(
        default_factory=list
    )

    raw_query: str = ""