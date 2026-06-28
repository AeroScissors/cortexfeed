# File: cortexfeed/features/investigation.py

from __future__ import annotations

import subprocess
from pathlib import Path

from cortexfeed.config.paths import ensure_data_dirs
from cortexfeed.config.settings import INVESTIGATION_SESSIONS_ROOT
from cortexfeed.investigation.orchestrator.engine import InvestigationEngine
from cortexfeed.investigation.planner.models import EvidenceType
from cortexfeed.investigation.prompts.formatter import PromptFormatter
from cortexfeed.ui import menu


def _copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run("clip", input=text.encode("utf-8"), check=True)
        return True
    except Exception:
        return False


def _collect_file_paths() -> dict:
    """Prompt user to attach files for each supported evidence type."""
    menu.info("\n  Attach evidence files (press Enter to skip each):")

    mapping = {
        EvidenceType.SERVER_LOGS:      "  Server log file path:       ",
        EvidenceType.STACK_TRACE:      "  Stack trace file path:      ",
        EvidenceType.API_ROUTES:       "  API routes file path:       ",
        EvidenceType.REPOSITORY_CODE:  "  Repository/source file:     ",
        EvidenceType.CONFIG_FILE:      "  Config file path:           ",
    }

    file_paths = {}
    for evidence_type, label in mapping.items():
        raw = menu.prompt(label)
        if raw.strip():
            p = Path(raw.strip())
            if p.exists():
                file_paths[evidence_type] = p
            else:
                menu.warning(f"  File not found, skipping: {raw.strip()}")

    return file_paths


def _collect_terminal_input() -> tuple[str | None, str, str, int]:
    """Optionally capture terminal evidence."""
    menu.info("\n  Terminal evidence (press Enter to skip):")
    cmd = menu.prompt("  Command that was run:         ")
    if not cmd.strip():
        return None, "", "", 0

    stdout = menu.prompt("  Paste stdout (or Enter):      ")
    stderr = menu.prompt("  Paste stderr (or Enter):      ")
    exit_code_raw = menu.prompt("  Exit code [default 0]:        ")

    try:
        exit_code = int(exit_code_raw.strip()) if exit_code_raw.strip() else 0
    except ValueError:
        exit_code = 0

    return cmd.strip(), stdout.strip(), stderr.strip(), exit_code


def _show_result_summary(result) -> None:
    menu.separator()
    menu.success(f"  Investigation complete")
    menu.info(f"  Project:     {result.project_name}")
    menu.info(f"  Intent:      {result.intent.investigation_type.value} / {result.intent.domain.value}")
    menu.info(f"  Confidence:  {result.intent.confidence}")
    menu.info(f"  Evidence:    {result.evidence_count}")
    menu.info(f"  Facts:       {result.fact_count}")
    menu.info(f"  Hypotheses:  {result.hypothesis_count}")
    menu.separator()


def _show_hypotheses(result) -> None:
    hypotheses = result.session.hypotheses.list()
    if not hypotheses:
        menu.warning("  No hypotheses generated.")
        return

    menu.info(f"\n  Active hypotheses ({len(hypotheses)}):")
    for i, h in enumerate(hypotheses, 1):
        menu.info(f"  [{i}] {h.statement}  [{h.status}]")


def _show_facts(result) -> None:
    facts = result.session.facts.list_facts()
    if not facts:
        menu.warning("  No facts extracted.")
        return

    menu.info(f"\n  Verified facts ({len(facts)}):")
    for i, f in enumerate(facts, 1):
        # Truncate long fact statements for display
        stmt = f.statement if len(f.statement) <= 120 else f.statement[:117] + "..."
        menu.info(f"  [{i}] {stmt}")


def _prompt_actions(formatted_prompt: str) -> None:
    print()
    menu.info("  What do you want to do with the prompt?")
    print("  [1] Copy to clipboard")
    print("  [2] Copy + open Claude")
    print("  [3] Copy + open Gemini")
    print("  [4] Copy + open ChatGPT")
    print("  [5] Print to terminal")
    print("  [6] Save to file")
    print("  [Enter] Back")

    action = menu.prompt("\n  Choice: ")

    if action == "1":
        if _copy_to_clipboard(formatted_prompt):
            menu.success("  Copied! Go paste it.")
        else:
            menu.error("  Clipboard failed. Copy manually.")

    elif action == "2":
        _copy_to_clipboard(formatted_prompt)
        subprocess.run(["start", "https://claude.ai"], shell=True)
        menu.success("  Copied + opening Claude.")

    elif action == "3":
        _copy_to_clipboard(formatted_prompt)
        subprocess.run(["start", "https://gemini.google.com"], shell=True)
        menu.success("  Copied + opening Gemini.")

    elif action == "4":
        _copy_to_clipboard(formatted_prompt)
        subprocess.run(["start", "https://chatgpt.com"], shell=True)
        menu.success("  Copied + opening ChatGPT.")

    elif action == "5":
        menu.separator()
        print(formatted_prompt)
        menu.separator()

    elif action == "6":
        safe_name = "investigation_prompt.txt"
        with open(safe_name, "w", encoding="utf-8") as f:
            f.write(formatted_prompt)
        menu.success(f"  Saved to {safe_name}")


def _list_sessions() -> None:
    engine = InvestigationEngine(sessions_root=INVESTIGATION_SESSIONS_ROOT)
    sessions = engine.list_sessions()

    if not sessions:
        menu.warning("  No investigation sessions found.")
        return

    menu.info(f"\n  Sessions ({len(sessions)}):")
    for s in sessions:
        menu.info(f"  · {s.project_name}  [updated: {s.updated_at[:19]}]")


def run(model: str) -> None:
    ensure_data_dirs()

    formatter = PromptFormatter()

    while True:
        menu.separator()
        menu.info("  INVESTIGATE")
        menu.separator()
        print("  Structured debugging investigation — collects evidence,")
        print("  extracts facts, generates hypotheses, builds AI prompt.\n")
        print("  [1] New / continue investigation")
        print("  [2] List sessions")
        print("  [q] Back\n")

        choice = menu.prompt("  Choice: ").lower()

        if choice in ("q", "back", "exit", ""):
            break

        elif choice == "2":
            _list_sessions()
            continue

        elif choice != "1":
            menu.error("  Invalid choice.")
            continue

        # ── New / continue investigation ──────────────────────
        project_name = menu.prompt("\n  Project name (e.g. trust-ledger): ").strip()
        if not project_name:
            menu.error("  Project name required.")
            continue

        request = menu.prompt("  Describe the problem: ").strip()
        if not request:
            menu.error("  Problem description required.")
            continue

        # Optional: project root for structure scan
        project_root_raw = menu.prompt("  Project root path (Enter to skip): ").strip()
        project_root = Path(project_root_raw) if project_root_raw else None
        if project_root and not project_root.exists():
            menu.warning(f"  Path not found, skipping: {project_root_raw}")
            project_root = None

        # Evidence files
        file_paths = _collect_file_paths()

        # Terminal evidence
        terminal_command, terminal_stdout, terminal_stderr, terminal_exit_code = (
            _collect_terminal_input()
        )

        # Run investigation
        menu.info("\n  Running investigation...")
        stop = menu.loading("  Analysing")

        try:
            engine = InvestigationEngine(
                sessions_root=INVESTIGATION_SESSIONS_ROOT,
                project_root=project_root,
                file_paths=file_paths if file_paths else None,
                terminal_command=terminal_command,
                terminal_stdout=terminal_stdout,
                terminal_stderr=terminal_stderr,
                terminal_exit_code=terminal_exit_code,
            )

            result = engine.investigate(
                request=request,
                project_name=project_name,
            )

        except Exception as exc:
            menu.stop_loading(stop)
            menu.error(f"\n  Investigation failed: {exc}")
            continue

        menu.stop_loading(stop)

        _show_result_summary(result)
        _show_facts(result)
        _show_hypotheses(result)

        formatted_prompt = formatter.format(result.prompt_package)
        _prompt_actions(formatted_prompt)