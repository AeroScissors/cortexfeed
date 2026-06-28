# File: cortexfeed/investigation/planner/models.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InvestigationType(str, Enum):
    DEBUGGING = "debugging"
    ROOT_CAUSE = "root_cause"
    FEATURE_ANALYSIS = "feature_analysis"
    ARCHITECTURE_REVIEW = "architecture_review"
    PERFORMANCE = "performance"
    SECURITY = "security"
    TEST_FAILURE = "test_failure"
    UNKNOWN = "unknown"


class InvestigationDomain(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    MOBILE = "mobile"
    DATABASE = "database"
    API = "api"
    AUTH = "auth"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


@dataclass(slots=True, frozen=True)
class InvestigationIntent:
    raw_request: str
    investigation_type: InvestigationType
    domain: InvestigationDomain
    confidence: float


class EvidenceType(str, Enum):
    SERVER_LOGS = "server_logs"
    STACK_TRACE = "stack_trace"
    API_ROUTES = "api_routes"
    REPOSITORY_CODE = "repository_code"
    DATABASE_SCHEMA = "database_schema"
    CONFIG_FILE = "config_file"
    NETWORK_TRACE = "network_trace"
    TERMINAL_OUTPUT = "terminal_output"
    TEST_RESULTS = "test_results"
    PROJECT_STRUCTURE = "project_structure"


@dataclass(slots=True, frozen=True)
class EvidenceRequirement:
    evidence_type: EvidenceType
    reason: str


@dataclass(slots=True)
class EvidencePlan:
    required: list[EvidenceRequirement]
    missing: list[EvidenceRequirement]
    collection_order: list[EvidenceRequirement]


@dataclass(slots=True)
class QuestionBundle:
    questions: list[str]
    combined_prompt: str