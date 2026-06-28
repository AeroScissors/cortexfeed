from datetime import datetime
from cortexfeed.core.context import resolve_paths, read_file, run_command, format_for_prompt
from cortexfeed.core import ollama
from cortexfeed.ui import menu


HELP = """
  /file <path>   — attach a file to your next message
  /run <cmd>     — run a command, attach output
  /clear         — clear chat history
  /save          — save chat to a .txt file
  /help          — show this help
  back           — return to menu
"""


def run(model: str):
    menu.separator()
    menu.info("  CHAT")
    menu.separator()
    print("Full chat with file and terminal context support.")
    print(HELP)

    history = []
    attached: list = []

    while True:
        try:
            label = f"You [{len(history)//2} msgs]: "
            user_input = menu.prompt(label)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input.lower() in ("back", "exit", "quit", "q"):
            break

        # ── slash commands ──────────────────────────────────────
        if user_input.startswith("/file "):
            path = user_input[6:].strip()
            files = resolve_paths(path)
            if not files:
                menu.error(f"No files found: {path}")
                continue
            for f in files:
                content = read_file(f)
                attached.append(f"=== FILE: {f} ===\n{content}")
            menu.success(f"  Attached {len(files)} file(s) — will send with next message.")
            continue

        if user_input.startswith("/run "):
            cmd = user_input[5:].strip()
            menu.info(f"  Running: {cmd}")
            stdout, stderr, code = run_command(cmd)
            out = f"$ {cmd}\n[exit {code}]\n{stdout}\n{stderr}".strip()
            attached.append(f"=== TERMINAL OUTPUT ===\n{out}")
            menu.success(f"  Output captured — will send with next message.")
            continue

        if user_input == "/clear":
            history.clear()
            attached.clear()
            menu.success("  Chat history cleared.")
            continue

        if user_input == "/save":
            fname = f"cortexfeed_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(fname, "w") as f:
                for m in history:
                    f.write(f"[{m['role'].upper()}]\n{m['content']}\n\n")
            menu.success(f"  Chat saved to {fname}")
            continue

        if user_input == "/help":
            print(HELP)
            continue

        # ── build message ───────────────────────────────────────
        full_content = user_input
        if attached:
            full_content = "\n\n".join(attached) + f"\n\n{user_input}"
            attached.clear()

        history.append({"role": "user", "content": full_content})

        menu.separator()
        response = ollama.chat(history, model=model)
        print(f"\n{response}\n")
        history.append({"role": "assistant", "content": response})
        menu.separator()