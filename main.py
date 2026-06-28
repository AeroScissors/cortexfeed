import sys
from cortexfeed.core import ollama
from cortexfeed.ui import menu
from cortexfeed.config import DEFAULT_MODEL
from cortexfeed.features import (
    watcher,
    terminal,
    reader,
    chat,
    promptbuilder,
    investigation,
    repository_intelligence,
)


def switch_model(current: str, available: list) -> str:
    menu.info(f"\nAvailable models: {', '.join(available)}")
    menu.info(f"Current: {current}")
    choice = menu.prompt("Enter model name (or Enter to keep current): ")
    if choice and choice in available:
        menu.success(f"Switched to: {choice}")
        return choice
    elif choice:
        menu.error(f"'{choice}' not found. Keeping {current}.")
    return current


def main():
    # check ollama
    available = ollama.check_ollama()
    if available is None:
        menu.error("ERROR: Ollama is not running.")
        menu.warning("Start it with:  ollama serve")
        menu.warning("Install from:   https://ollama.com")
        sys.exit(1)

    if not available:
        menu.error("No models found.")
        menu.warning("Pull one with:  ollama pull mistral")
        sys.exit(1)

    model = DEFAULT_MODEL
    if model not in available:
        model = available[0]

    menu.print_banner()
    menu.info(f"  Model: {model}   |   {len(available)} model(s) available\n")

    while True:
        menu.print_menu(model)
        choice = menu.prompt("Choice: ").lower()

        if choice == "1":
            watcher.run(model)
        elif choice == "2":
            terminal.run(model)
        elif choice == "3":
            reader.run(model)
        elif choice == "4":
            chat.run(model)
        elif choice == "6":
            promptbuilder.run(model)
        elif choice == "7":
            promptbuilder.run_context_mode(model)
        elif choice == "8":
            investigation.run(model)
        elif choice == "9":
            repository_intelligence.run(model)
        elif choice == "5":
            model = switch_model(model, available)
        elif choice in ("q", "quit", "exit"):
            menu.success("Bye!")
            sys.exit(0)
        else:
            menu.error("Invalid choice.")


if __name__ == "__main__":
    main()