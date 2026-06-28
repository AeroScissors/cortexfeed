# File: cortexfeed/knowledge/graph/v3/call_models.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CallRelationship:
    """
    Represents a resolved method/function call.

    Example:

    Controller.login
        ↓
    AuthService.login
    """

    caller_symbol: str
    callee_symbol: str

    caller_file: str
    callee_file: str

    line_number: int


@dataclass(slots=True)
class CallTrace:
    """
    Represents a multi-hop execution chain.

    Example:

    Controller.login
        ↓
    AuthService.login
        ↓
    UserRepository.find_user
    """

    path: list[str]

    @property
    def depth(self) -> int:
        return len(self.path)