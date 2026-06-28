from datetime import datetime
from cortexfeed.core.context import run_command
from cortexfeed.core import ollama
from cortexfeed.ui import menu


def run(model: str):
    menu.separator()
    menu.info("  RUN TERMINAL")
    menu.separator()
    print("Type a shell command to run. AI will analyze the output.")
    print("Examples:  python main.py   npm test   git log --oneline -10")
    print("Type 'back' to return to menu.\n")

    while True:
        cmd = menu.prompt("\n$ ")

        if cmd.lower() in ("back", "exit", "quit", "q", ""):
            break

        menu.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running: {cmd}")
        stdout, stderr, code = run_command(cmd)

        menu.separator()
        if stdout:
            print(stdout[:3000])
        if stderr:
            menu.warning(f"[stderr]\n{stderr[:1000]}")
        menu.info(f"[exit code: {code}]")
        menu.separator()

        question = menu.prompt("Ask AI about this output (Enter to skip): ")
        if not question:
            continue

        prompt_text = (
            f"Command: {cmd}\n"
            f"Exit code: {code}\n"
            f"Stdout:\n{stdout[:3000]}\n"
            f"Stderr:\n{stderr[:1000]}\n\n"
            f"Question: {question}"
        )

        menu.separator()
        ollama.stream(prompt_text, model=model,
                      system="You are a helpful coding assistant. Analyze command output and answer concisely.")
        menu.separator()