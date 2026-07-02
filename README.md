# cortexfeed

**Give your AI the full picture — automatically.**

cortexfeed reads your active AI conversation, detects which files in your project are relevant, and injects them as context — all with one click. No copy-pasting. No manual file hunting. Free and offline.

---

## How it works

1. You're debugging in ChatGPT, Claude, or Gemini
2. Click the cortexfeed extension icon
3. It reads your conversation and finds the relevant files in your project
4. You see a preview of the full prompt (with file contents attached)
5. Click **Paste Now** — cortexfeed injects it directly into the AI chat

> Your code never leaves your machine. Everything runs locally via Ollama.

---

## Works with

- [ChatGPT](https://chatgpt.com)
- [Claude](https://claude.ai)
- [Gemini](https://gemini.google.com)

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- Google Chrome

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Pull a model

```bash
ollama pull mistral
```

### 3. Start the cortexfeed server

```bash
python server.py
```

You should see:

```
cortexfeed server starting on http://localhost:5050
Chrome extension can now connect.
```

Keep this terminal open while you use cortexfeed.

### 4. Install the Chrome extension

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `extension/` folder from this repo

The cortexfeed icon will appear in your toolbar.

---

## First use

1. Open ChatGPT (or Claude / Gemini) and start a conversation about your code
2. Click the cortexfeed icon
3. Enter your project folder path when prompted (e.g. `C:\Users\You\Projects\myapp`)
4. Click **Build + Paste**
5. Review the prompt in the preview — you'll see your files attached at the bottom
6. Click **Paste Now**

---

## Keyboard shortcuts

| Shortcut | What it does |
|----------|--------------|
| `Alt+C` | Build + paste into the current AI tab (no popup needed) |
| `Alt+Shift+C` | Classify your task, open the best AI, paste automatically |

---

## Config

Edit `.env` to change defaults:

```
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=mistral
MAX_FILE_KB=256
```

### Supported models

Switch models anytime from the extension popup.
Popular options: `mistral`, `llama3`, `codellama`, `phi3`

---

## FAQ

**Does this send my code anywhere?**
No. cortexfeed runs entirely on your machine. Ollama is local. The server is local. Nothing is sent to any external service.

**Does it work without internet?**
Yes, fully offline once Ollama and the model are installed.

**Which files does it pick?**
cortexfeed reads your AI conversation, extracts mentioned filenames and keywords, and scores files in your project folder by relevance. You can include or exclude specific files before pasting.

**The extension says "server offline" — what do I do?**
Make sure `python server.py` is running in a terminal. Check that Ollama is also running (`ollama serve`).

---

## Project structure

```
cortexfeed/
├── server.py              # Flask server (run this)
├── extension/             # Chrome extension (load this in Chrome)
│   ├── popup.js
│   ├── content.js
│   └── background.js
├── server/
│   ├── routes/            # API routes (analyze, classify, files)
│   └── ai/                # File detection and prompt building
└── cortexfeed/            # CLI and config
```

---

## License

MIT
