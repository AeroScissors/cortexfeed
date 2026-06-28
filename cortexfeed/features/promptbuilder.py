import subprocess
from cortexfeed.core.context import resolve_paths, format_for_prompt
from cortexfeed.ui import menu


def copy_to_clipboard(text: str):
    try:
        subprocess.run("clip", input=text.encode("utf-8"), check=True)
        return True
    except Exception:
        return False


def multiline_input(label: str) -> str:
    print(label)
    menu.info("  (press Enter twice when done)\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def build_prompt(intent: str, file_context: str, target: str, expected: str, actual: str) -> str:
    sections = []

    sections.append(f"I am working on the following problem:\n{intent}")

    if file_context:
        sections.append(f"Here are the relevant files:\n\n{file_context}")

    if expected:
        sections.append(f"Expected behavior:\n{expected}")

    if actual:
        sections.append(f"Current behavior / what is going wrong:\n{actual}")

    sections.append(f"Please help me fix this. I am sending this to {target}.")

    return "\n\n---\n\n".join(sections)


def multiline_paste(label: str) -> str:
    """For pasting large text blocks. Type END on a new line to finish."""
    print(label)
    menu.info("  (paste your text, then type END on a new line and press Enter)\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def run_context_mode(model: str):
    """Feature 7 — paste existing conversation, build next prompt."""
    menu.separator()
    menu.info("  CONTEXT MODE — Continue an existing conversation")
    menu.separator()
    print("Paste your existing Claude/Gemini/ChatGPT conversation.")
    print("cortexfeed reads it and builds your next prompt.\n")
    
    # paste conversation
    conversation = multiline_paste("Paste the conversation below:")
    if not conversation:
        menu.warning("No conversation pasted.")
        return
        
    # what do you want next
    print()
    next_intent = multiline_input("What do you want to do NEXT in this conversation? (Enter twice when done):")
    if not next_intent:
        menu.warning("No intent given.")
        return
        
    # optional files
    print()
    attach = menu.prompt("Attach any files? (space-separated paths, or Enter to skip): ")
    file_context = ""
    if attach.strip():
        all_files = []
        for pat in attach.split():
            all_files.extend(resolve_paths(pat))
        if all_files:
            menu.info(f"  Loading {len(all_files)} file(s)...")
            file_context = format_for_prompt(all_files)
        else:
            menu.warning("  No files found.")
            
    # target
    print()
    menu.info("  Target AI:")
    print("  [1] Claude")
    print("  [2] Gemini")
    print("  [3] ChatGPT")
    print("  [4] General")
    target_choice = menu.prompt("  Pick [1-4]: ")
    targets = {
        "1": "Claude by Anthropic",
        "2": "Google Gemini",
        "3": "OpenAI ChatGPT",
        "4": "any AI assistant"
    }
    target = targets.get(target_choice, "any AI assistant")
    
    # build prompt
    sections = []
    sections.append(
        f"Here is the conversation so far:\n\n{conversation}"
    )
    sections.append(
        f"What I want to do next:\n{next_intent}"
    )
    if file_context:
        sections.append(
            f"Relevant files for context:\n\n{file_context}"
        )
    sections.append(
        f"Please continue helping me. I am sending this to {target}."
    )
    built_prompt = "\n\n---\n\n".join(sections)
    
    menu.separator()
    print(f"\n{built_prompt}\n")
    menu.separator()
    
    # actions
    print()
    menu.info("  What do you want to do?")
    print("  [1] Copy to clipboard")
    print("  [2] Copy + open Claude")
    print("  [3] Copy + open Gemini")
    print("  [4] Copy + open ChatGPT")
    print("  [6] Save to file")
    print("  [Enter] Back")
    
    action = menu.prompt("\n  Choice: ")
    if action == "1":
        if copy_to_clipboard(built_prompt):
            menu.success("  Copied! Go paste it.")
        else:
            menu.error("  Clipboard failed. Copy manually above.")
    elif action == "2":
        copy_to_clipboard(built_prompt)
        subprocess.run(["start", "https://claude.ai"], shell=True)
        menu.success("  Copied + opening Claude. Just paste!")
    elif action == "3":
        copy_to_clipboard(built_prompt)
        subprocess.run(["start", "https://gemini.google.com"], shell=True)
        menu.success("  Copied + opening Gemini. Just paste!")
    elif action == "4":
        copy_to_clipboard(built_prompt)
        subprocess.run(["start", "https://chatgpt.com"], shell=True)
        menu.success("  Copied + opening ChatGPT. Just paste!")
    elif action == "6":
        fname = f"context_prompt_{next_intent[:20].replace(' ', '_').replace(chr(10), '')}.txt"
        with open(fname, "w") as f:
            f.write(built_prompt)
        menu.success(f"  Saved to {fname}")


def run(model: str):
    menu.separator()
    menu.info("  PROMPT BUILDER")
    menu.separator()
    print("Answer a few quick questions — cortexfeed builds the prompt instantly.\n")

    while True:
        # intent
        user_intent = multiline_input("What is the problem? (press Enter twice when done):")
        if user_intent.lower() in ("back", "exit", "quit", "q", ""):
            break

        # expected
        print()
        expected = multiline_input("What SHOULD happen? (press Enter twice, or just Enter twice to skip):")

        # actual
        print()
        actual = multiline_input("What IS happening instead? (press Enter twice, or just Enter twice to skip):")

        # files
        print()
        attach = menu.prompt("Attach files? (space-separated paths, or Enter to skip): ")
        file_context = ""
        if attach.strip():
            all_files = []
            for pat in attach.split():
                all_files.extend(resolve_paths(pat))
            if all_files:
                menu.info(f"  Loading {len(all_files)} file(s)...")
                file_context = format_for_prompt(all_files)
            else:
                menu.warning("  No files found, continuing without.")

        # target
        print()
        menu.info("  Target AI:")
        print("  [1] Claude")
        print("  [2] Gemini")
        print("  [3] ChatGPT")
        print("  [4] General")
        target_choice = menu.prompt("  Pick [1-4]: ")
        targets = {
            "1": "Claude by Anthropic",
            "2": "Google Gemini",
            "3": "OpenAI ChatGPT",
            "4": "any AI assistant"
        }
        target = targets.get(target_choice, "any AI assistant")

        # build instantly — no AI needed
        built_prompt = build_prompt(user_intent, file_context, target, expected, actual)

        menu.separator()
        print(f"\n{built_prompt}\n")
        menu.separator()

        print()
        menu.info("  What do you want to do?")
        print("  [1] Copy to clipboard")
        print("  [2] Copy + open Claude")
        print("  [3] Copy + open Gemini")
        print("  [4] Copy + open ChatGPT")
        print("  [6] Save to file")
        print("  [Enter] New prompt")

        action = menu.prompt("\n  Choice: ")

        if action == "1":
            if copy_to_clipboard(built_prompt):
                menu.success("  Copied! Go paste it.")
            else:
                menu.error("  Clipboard failed. Copy manually above.")

        elif action == "2":
            copy_to_clipboard(built_prompt)
            subprocess.run(["start", "https://claude.ai"], shell=True)
            menu.success("  Copied + opening Claude. Just paste!")

        elif action == "3":
            copy_to_clipboard(built_prompt)
            subprocess.run(["start", "https://gemini.google.com"], shell=True)
            menu.success("  Copied + opening Gemini. Just paste!")

        elif action == "4":
            copy_to_clipboard(built_prompt)
            subprocess.run(["start", "https://chatgpt.com"], shell=True)
            menu.success("  Copied + opening ChatGPT. Just paste!")

        elif action == "6":
            fname = f"prompt_{user_intent[:20].replace(' ', '_').replace(chr(10), '')}.txt"
            with open(fname, "w") as f:
                f.write(built_prompt)
            menu.success(f"  Saved to {fname}")