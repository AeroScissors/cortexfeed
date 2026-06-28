# File: cortexfeed/investigation/collector/file_collector.py

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .base import PathCollector
from .models import Evidence, EvidenceChunk, EvidenceType


class FileCollector(PathCollector):
    """
    Collects evidence from files.

    Responsibilities:
    - Read files
    - Extract metadata
    - Create file evidence
    - Chunk large files
    """

    def __init__(
        self,
        path: str | Path,
        *,
        chunk_size_lines: int = 200,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(path)

        self.chunk_size_lines = chunk_size_lines
        self.encoding = encoding

    def collect(self) -> list[Evidence]:
        if not self.exists:
            raise FileNotFoundError(self.path)

        if not self.is_file:
            raise ValueError(f"Expected file, got: {self.path}")

        content = self._read_file()

        evidence = Evidence.create(
            evidence_type=EvidenceType.FILE,
            source="file_collector",
            path=str(self.path),
            content=content,
            metadata=self._build_metadata(),
        )

        return [evidence]

    def collect_chunks(self) -> list[EvidenceChunk]:
        evidence = self.collect()[0]

        lines = evidence.content.splitlines()

        if not lines:
            return []

        chunks: list[EvidenceChunk] = []

        total_chunks = (
            len(lines) + self.chunk_size_lines - 1
        ) // self.chunk_size_lines

        for chunk_index, start in enumerate(
            range(0, len(lines), self.chunk_size_lines)
        ):
            end = min(
                start + self.chunk_size_lines,
                len(lines),
            )

            chunk_content = "\n".join(lines[start:end])

            chunks.append(
                EvidenceChunk.create(
                    parent_evidence_id=evidence.evidence_id,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    content=chunk_content,
                    start_line=start + 1,
                    end_line=end,
                    metadata={
                        "path": str(self.path),
                        "extension": self.path.suffix,
                    },
                )
            )

        return chunks

    def _read_file(self) -> str:
        return self.path.read_text(
            encoding=self.encoding,
            errors="replace",
        )

    def _build_metadata(self) -> dict[str, object]:
        return {
            "filename": self.path.name,
            "extension": self.path.suffix,
            "size_bytes": self.path.stat().st_size,
            "sha256": self._calculate_hash(),
        }

    def _calculate_hash(self) -> str:
        digest = sha256()

        with self.path.open("rb") as file_handle:
            while chunk := file_handle.read(1024 * 1024):
                digest.update(chunk)

        return digest.hexdigest()