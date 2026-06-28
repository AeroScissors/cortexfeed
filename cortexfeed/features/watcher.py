from datetime import datetime
from cortexfeed.core.context import resolve_paths, format_for_prompt, file_hash
from cortexfeed.core import ollama
from cortexfeed.ui import menu
from cortexfeed.config import WATCH_INTERVAL
import time


def run(model: str):
    menu.separator()
    menu.info("  WATCH FILES")
    menu.separator()
    print("Enter file paths / globs to watch (space-separated)")
    print("Examples:  src/*.py   app/   config.json\n")

    pattern_input = menu.prompt("Paths: ")
    if not pattern_input:
        menu.error("No paths given.")
        return

    question = menu.prompt("What should AI do when a file changes?\n[default: explain changes and flag issues]\n> ")
    if not question:
        question = "Explain what changed in this file and flag any obvious bugs or issues."

    patterns = pattern_input.split()
    hashes: dict = {}

    # initial scan
    all_files = []
    for pat in patterns:
        all_files.extend(resolve_paths(pat))

    if not all_files:
        menu.error("No files found matching those paths.")
        return

    for f in all_files:
        hashes[f] = file_hash(f)

    menu.success(f"\nWatching {len(all_files)} file(s). Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(WATCH_INTERVAL)
            changed = []

            # check for modifications
            for f in list(hashes.keys()):
                new_h = file_hash(f)
                if new_h != hashes[f]:
                    hashes[f] = new_h
                    changed.append(f)

            # check for new files
            for pat in patterns:
                for f in resolve_paths(pat):
                    if f not in hashes:
                        hashes[f] = file_hash(f)
                        changed.append(f)

            if changed:
                menu.separator()
                menu.info(f"[{datetime.now().strftime('%H:%M:%S')}] Changed: {', '.join(changed)}")
                menu.separator()
                context = format_for_prompt(changed)
                prompt_text = f"{question}\n\n{context}"
                ollama.stream(prompt_text, model=model)
                menu.separator()

    except KeyboardInterrupt:
        menu.warning("\nStopped watching.")