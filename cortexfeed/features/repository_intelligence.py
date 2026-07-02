# File: cortexfeed/features/repository_intelligence.py

from __future__ import annotations

from pathlib import Path

from cortexfeed.intelligence.bootstrap import (
    build_repository_intelligence,
)
from cortexfeed.ui import menu


def run(model: str | None = None) -> None:
    menu.info("\nRepository Intelligence")

    default = Path.cwd()
    raw = menu.prompt(f"  Project path [{default}]: ").strip()
    project_root = Path(raw) if raw else default

    if not project_root.exists():
        menu.error(f"Path not found: {project_root}")
        return

    try:
        facade = build_repository_intelligence(
            project_root,
        )
    except Exception as exc:
        menu.error(
            f"Failed to initialize repository intelligence: {exc}"
        )
        return

    menu.success(
        f"Repository loaded: {project_root.name} ({project_root})"
    )

    while True:
        query = menu.prompt(
            "\nQuestion (or 'back'): "
        ).strip()

        if not query:
            continue

        if query.lower() in {
            "back",
            "exit",
            "quit",
            "q",
        }:
            return

        try:
            result = facade.ask(
                query,
            )

            print()
            print("=" * 60)

            print(
                f"Capability:\n{result.capability}"
            )

            print()
            print(
                f"Answer:\n{result.answer}"
            )

            if result.evidence:
                print()
                print("Evidence:")

                for item in result.evidence:
                    print(
                        f"- {item}"
                    )

            print()
            print(
                f"Confidence:\n{result.confidence:.2f}"
            )

            print("=" * 60)

        except Exception as exc:
            menu.error(
                f"Query failed: {exc}"
            )