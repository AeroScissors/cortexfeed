# cortexfeed

Local AI context feeder — free, offline, powered by Ollama.
Feed your files and terminal output directly to AI without copy-pasting.

---

## Features

- **Watch files** — auto-detect file changes and stream AI analysis
- **Run terminal** — execute commands and ask AI about the output
- **AI reads & asks** — dump your project files, AI reviews and asks questions
- **Chat** — full terminal chat with `/file` and `/run` context injection

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

---

## Setup

    # 1. install dependencies
    pip install -r requirements.txt

    # 2. pull a model
    ollama pull mistral

    # 3. start ollama
    ollama serve

    # 4. run cortexfeed
    python main.py

---

## Chat Commands

| Command | What it does |
|---------|--------------|
| `/file <path>` | Attach a file to your next message |
| `/run <cmd>` | Run a command, attach output |
| `/clear` | Clear chat history |
| `/save` | Save chat to a .txt file |
| `/help` | Show help |
| `back` | Return to main menu |

---

## Config

Edit `.env` to change defaults:

    OLLAMA_URL=http://localhost:11434
    DEFAULT_MODEL=mistral
    WATCH_INTERVAL=2
    MAX_FILE_KB=200

---

## Models

Switch models anytime from the main menu.
Popular options: `mistral`, `llama3`, `codellama`, `phi3`