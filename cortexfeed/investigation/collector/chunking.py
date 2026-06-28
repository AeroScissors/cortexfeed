# File: cortexfeed/investigation/collector/chunking.py

from __future__ import annotations

from math import ceil

from .models import EvidenceChunk


class TextChunker:
    """
    Generic line-based chunker.

    Used by:
    - FileCollector
    - LogCollector
    - Embedding pipeline
    - Repository indexer
    """

    def __init__(
        self,
        chunk_size_lines: int = 200,
    ) -> None:
        if chunk_size_lines <= 0:
            raise ValueError(
                "chunk_size_lines must be greater than zero"
            )

        self.chunk_size_lines = chunk_size_lines

    def chunk_text(
        self,
        *,
        parent_evidence_id: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> list[EvidenceChunk]:
        lines = content.splitlines()

        if not lines:
            return []

        total_chunks = ceil(
            len(lines) / self.chunk_size_lines
        )

        chunks: list[EvidenceChunk] = []

        for chunk_index, start in enumerate(
            range(
                0,
                len(lines),
                self.chunk_size_lines,
            )
        ):
            end = min(
                start + self.chunk_size_lines,
                len(lines),
            )

            chunk_content = "\n".join(
                lines[start:end]
            )

            chunks.append(
                EvidenceChunk.create(
                    parent_evidence_id=parent_evidence_id,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    content=chunk_content,
                    start_line=start + 1,
                    end_line=end,
                    metadata=dict(metadata or {}),
                )
            )

        return chunks

    def chunk_lines(
        self,
        *,
        parent_evidence_id: str,
        lines: list[str],
        metadata: dict[str, object] | None = None,
    ) -> list[EvidenceChunk]:
        return self.chunk_text(
            parent_evidence_id=parent_evidence_id,
            content="\n".join(lines),
            metadata=metadata,
        )