# File: cortexfeed/tests/intelligence/test_bootstrap.py

from pathlib import Path

from cortexfeed.intelligence.bootstrap import (
    build_repository_intelligence,
)
from cortexfeed.intelligence.facade import (
    RepositoryIntelligenceFacade,
)


def test_builds_facade(
    tmp_path: Path,
):
    project_file = (
        tmp_path / "sample.py"
    )

    project_file.write_text(
        """
def login():
    return True
""",
        encoding="utf-8",
    )

    facade = build_repository_intelligence(
        tmp_path,
    )

    assert isinstance(
        facade,
        RepositoryIntelligenceFacade,
    )


def test_facade_operational(
    tmp_path: Path,
):
    project_file = (
        tmp_path / "sample.py"
    )

    project_file.write_text(
        """
def login():
    return True
""",
        encoding="utf-8",
    )

    facade = build_repository_intelligence(
        tmp_path,
    )

    result = facade.ask(
        "Where is login handled?",
    )

    assert result is not None
    assert hasattr(
        result,
        "capability",
    )


def test_deterministic_construction(
    tmp_path: Path,
):
    project_file = (
        tmp_path / "sample.py"
    )

    project_file.write_text(
        """
def login():
    return True
""",
        encoding="utf-8",
    )

    facade_a = (
        build_repository_intelligence(
            tmp_path,
        )
    )

    facade_b = (
        build_repository_intelligence(
            tmp_path,
        )
    )

    result_a = facade_a.ask(
        "Where is login handled?",
    )

    result_b = facade_b.ask(
        "Where is login handled?",
    )

    assert result_a == result_b


def test_dependencies_wired_correctly(
    tmp_path: Path,
):
    project_file = (
        tmp_path / "sample.py"
    )

    project_file.write_text(
        """
def login():
    return True
""",
        encoding="utf-8",
    )

    facade = build_repository_intelligence(
        tmp_path,
    )

    assert hasattr(
        facade,
        "repository_service",
    )

    assert hasattr(
        facade.repository_service,
        "query_router",
    )