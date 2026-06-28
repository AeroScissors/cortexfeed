# File: cortexfeed/investigation/collector/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .models import Evidence


class BaseCollector(ABC):
    """
    Base contract for all investigation collectors.

    Collectors are responsible for gathering raw evidence and
    normalizing it into Evidence objects.
    """

    @abstractmethod
    def collect(self) -> list[Evidence]:
        """
        Collect evidence.

        Returns:
            list[Evidence]
        """
        raise NotImplementedError


class PathCollector(BaseCollector):
    """
    Base collector for collectors that operate on filesystem paths.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def is_file(self) -> bool:
        return self.path.is_file()

    @property
    def is_directory(self) -> bool:
        return self.path.is_dir()


class RepositoryCollector(BaseCollector):
    """
    Base collector for collectors that operate on repositories
    or project roots.
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)

    @property
    def exists(self) -> bool:
        return self.project_root.exists()

    def validate_root(self) -> None:
        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {self.project_root}"
            )

        if not self.project_root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {self.project_root}"
            )