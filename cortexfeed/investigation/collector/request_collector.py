# File: cortexfeed/investigation/collector/request_collector.py

from __future__ import annotations

from .models import Evidence, EvidenceType


class RequestCollector:
    """
    Collects the original investigation request as evidence.

    Purpose:
    - Preserve the user's problem statement
    - Feed the problem statement into fact extraction
    - Enable hypothesis generation from reported failures

    Example:

        User:
            GET /promise returns 404

        Evidence:
            GET /promise returns 404

        Fact:
            GET /promise returns 404

        Hypothesis:
            Requested route is not registered
            Request path is incorrect
    """

    def __init__(
        self,
        request: str,
    ) -> None:
        self.request = request.strip()

    def collect(self) -> list[Evidence]:
        if not self.request:
            return []

        return [
            Evidence.create(
                evidence_type=EvidenceType.USER_REPORTED_PROBLEM,
                source="request_collector",
                content=self.request,
                metadata={
                    "source": "user_request",
                },
            )
        ]