# File: cortexfeed/intelligence/facade.py

from __future__ import annotations

from cortexfeed.intelligence.repository_service import (
    RepositoryAnswer,
    RepositoryService,
)


class RepositoryIntelligenceFacade:
    def __init__(
        self,
        repository_service: RepositoryService,
    ) -> None:
        self.repository_service = (
            repository_service
        )

    def ask(
        self,
        query: str,
    ) -> RepositoryAnswer:
        return self.repository_service.answer(
            query,
        )

    def search(
        self,
        query: str,
    ) -> RepositoryAnswer:
        return self.ask(
            query,
        )

    def explain(
        self,
        query: str,
    ) -> RepositoryAnswer:
        return self.ask(
            query,
        )

    def trace(
        self,
        query: str,
    ) -> RepositoryAnswer:
        return self.ask(
            query,
        )

    def impact(
        self,
        query: str,
    ) -> RepositoryAnswer:
        return self.ask(
            query,
        )