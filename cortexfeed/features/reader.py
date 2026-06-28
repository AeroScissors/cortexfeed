from cortexfeed.core.context import resolve_paths, format_for_prompt
from cortexfeed.core import ollama
from cortexfeed.ui import menu


def run(model: str):
    menu.separator()
    menu.info("  AI READS & ASKS")
    menu.separator()
    print("Share files/folders with AI. It will analyze and ask you questions.")
    print("Examples:  src/*.py   app/   main.py config.json\n")

    pattern_input = menu.prompt("Paths to share (space-separated, globs ok): ")
    if not pattern_input:
        menu.error("No paths given.")
        return

    goal = menu.prompt("What are you trying to do? (optional): ")

    all_files = []
    for pat in pattern_input.split():
        all_files.extend(resolve_paths(pat))

    if not all_files:
        menu.error("No files found.")
        return

    menu.info(f"\nLoading {len(all_files)} file(s)...")
    context = format_for_prompt(all_files)

    prompt_text = (
        f"{'Goal: ' + goal if goal else ''}\n\n"
        f"{context}\n\n"
        f"Please:\n"
        f"1. Summarize what each file does\n"
        f"2. Identify any issues, bugs, or missing pieces\n"
        f"3. Ask me any clarifying questions you need to help me better"
    )

    menu.separator()
    menu.info(f"AI analyzing {len(all_files)} file(s)...\n")
    ai_response = ollama.ask(prompt_text, model=model,
                             system="You are an expert code reviewer. Be thorough but concise. Ask smart questions.")
    print(ai_response)
    menu.separator()

    # back and forth follow up
    print("\nAnswer AI's questions below. Type 'back' to return to menu.\n")
    history = [
        {"role": "user",      "content": prompt_text},
        {"role": "assistant", "content": ai_response}
    ]

    while True:
        user_input = menu.prompt("You: ")
        if user_input.lower() in ("back", "exit", "quit", "q", ""):
            break

        history.append({"role": "user", "content": user_input})
        menu.info("\nAI: ")
        response = ollama.chat(history, model=model)
        print(response)
        history.append({"role": "assistant", "content": response})
        print()