# File: cortexfeed/investigation/orchestrator/exceptions.py

from __future__ import annotations


class InvestigationError(Exception):
    """
    Base exception for the investigation orchestration layer.
    """


class SessionResolutionError(InvestigationError):
    """
    Raised when a session cannot be created or loaded.
    """


class PlanningError(InvestigationError):
    """
    Raised when intent analysis or evidence planning fails.
    """


class CollectionError(InvestigationError):
    """
    Raised when evidence collection fails.
    """


class AnalysisError(InvestigationError):
    """
    Raised when fact extraction or hypothesis generation fails.
    """


class PromptGenerationError(InvestigationError):
    """
    Raised when prompt composition fails.
    """


class UnsupportedEvidenceTypeError(CollectionError):
    """
    Raised when no collector is available for an evidence type.
    """

    def __init__(self, evidence_type: object) -> None:
        super().__init__(
            f"No collector registered for evidence type: {evidence_type}"
        )


class InvalidInvestigationRequestError(InvestigationError):
    """
    Raised when an investigation request is empty or invalid.
    """


class CollectorConfigurationError(CollectionError):
    """
    Raised when collector configuration is incomplete.
    """


class AdapterError(InvestigationError):
    """
    Raised when a domain model cannot be converted
    between subsystems.
    """


class PersistenceError(InvestigationError):
    """
    Raised when session persistence fails.
    """