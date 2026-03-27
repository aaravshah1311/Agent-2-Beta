<h1 align="center">⚡ Agent-2-Beta</h1>

<p align="center">
  <em>A self-hosted autonomous AI development agent powered by Google Gemini —<br>
  coding assistant, terminal agent, security tester, and persistent memory in one interface.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-Web_Framework-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini-AI_Engine-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/CLI-Agent2_CLI-7c6af7?style=for-the-badge&logo=gnubash&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Beta-f97316?style=for-the-badge" />
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-installation">Install</a> •
  <a href="#️-run-modes">Run</a> •
  <a href="#-managing-api-keys">Keys</a> •
  <a href="#️-cli-commands-reference">CLI</a> •
  <a href="#-troubleshooting">Troubleshoot</a> •
  <a href="#-agent-2-pro">Pro Version</a> •
  <a href="#-contributing">Contribute</a>
</p>

---

## 🚀 Overview

**Agent-2-Beta** is a self-hosted autonomous AI agent powered by Google Gemini. It ships in two modes:

| Mode | Entry point | Description |
|------|-------------|-------------|
| 🌐 **Web UI** | `agent2web.py` | Browser interface — workspaces, multi-tab terminals, Three.js 3D welcome, real-time streaming |
| ⚡ **CLI** | `agent2cli.py` | Terminal-native agent — same brain, tools, and memory as the web UI |

Both modes share the same **8 agentic tools**, persistent memory engine, and `.env`-based API key rotation.

---

## ✨ Core Features

| | Feature | Description |
|-|---------|-------------|
| 🗂️ | **Workspaces** | Claude Projects-style context — path browser, per-workspace memory, framework detection |
| 🤖 | **8 Agent Tools** | Shell, file R/W, directory tree, project analyzer, web search, memory, planner |
| 🧠 | **Persistent Memory** | Global, workspace-scoped, and auto-extracted memories across sessions |
| 💻 | **Multi-tab Terminals** | Live streaming, stdin injection, ↑↓ command history, 2-stage kill |
| 🔑 | **API Key Rotation** | Multiple keys, auto-rotate on quota, pin a key, per-key usage stats |
| 🔒 | **Security Testing** | nmap, nikto, gobuster, sqlmap, hydra, metasploit — built-in workflows |
| 🌐 | **Web Search** | DuckDuckGo instant answers — no extra API key required |
| ✏️ | **Message Editing** | Edit any past message and re-run the agent from that point |
| ⏹️ | **Stop Generation** | Cancel agent mid-flight at any time |
| 📎 | **File Attachments** | Attach code, images, PDFs as context |
| ▶️ | **One-click Run** | Click ▶ on any tool block to instantly run that command in the active terminal |
| 🎨 | **3D Welcome Screen** | Three.js — neural particles, torus knot, rotating wireframes, octahedron |
| 📦 | **Project Auto-Setup** | Detect framework → install deps → run project automatically |

---

## 🖼️ Screenshots

<div align="center">
  <img src="pic/img1.png" alt="Agent2 Web Interface" width="49%" />
  <img src="pic/img2.png" alt="Agent2 Installation" width="49%" />
</div>
<p align="center"><sub><strong>Left:</strong> Web Interface &nbsp;•&nbsp; <strong>Right:</strong> Installation &amp; Setup</sub></p>

<br>

<div align="center">
  <img src="pic/img3.png" alt="Agent2 CLI" width="80%" />
</div>
<p align="center"><sub><strong>Agent2 CLI</strong> — Rich UI, key rotation, ↑↓ history, and all 8 tools in the terminal</sub></p>

---

## 🧱 Project Structure

```text
agent2/
├── run.py                  ← Universal launcher — setup, run, manage keys
├── agent2web.py            ← Web UI entry point
├── agent2cli.py            ← CLI agent entry point
├── .env                    ← API keys  (auto-created on first run)
├── agent2.db               ← SQLite database  (auto-created)
└── agent2/
    ├── __init__.py
    ├── config.py           ← Platform detection, models, modes, constants
    ├── database.py         ← SQLite helpers + schema + migrations
    ├── memory.py           ← Memory engine (auto-extract, workspace-scoped)
    ├── tools.py            ← 8 tool implementations
    ├── keys.py             ← KeyRotator: rotation, pinning, usage tracking
    ├── terminal.py         ← stream_command, stdin, kill, stop events
    ├── agent.py            ← system_prompt, context builder, run_agent loop
    ├── routes.py           ← All /api/* REST endpoints
    ├── sockets.py          ← All Socket.IO event handlers
    └── ui.py               ← HTML/CSS/JS single-page frontend  (89 KB)
```

---

## ⚙️ Installation

### 1 — Clone

```bash
git https://github.com/aaravshah1311/Agent-2-Beta.git
cd Agent-2-Beta
```

### 2 — Run the launcher

```bash
python run.py
```

`run.py` will automatically:
- ✅ Create a virtual environment
- ✅ Install all dependencies (`flask`, `flask-socketio`, `google-genai`, `rich`, …)
- ✅ Prompt for your Gemini API key and save it to `.env`
- ✅ Start the web server

> 🔑 **Free Gemini API key →** https://aistudio.google.com/app/apikey

---

## ▶️ Run Modes

### `run.py` — all flags at a glance

```
python run.py                 setup + start Web UI  (default)
python run.py --web           setup + start Web UI
python run.py --cli           setup + start CLI agent
python run.py --addapi        add / manage API keys
python run.py --reset         wipe venv and reinstall everything
python run.py --uninstall     completely remove Agent2 and its venv
python run.py -h              show this help menu
```

---

### 🌐 Web UI

```bash
python run.py
# or explicitly
python run.py --web
```

Opens at → **http://localhost:1311**

---

### ⚡ CLI Agent

```bash
python run.py --cli
```

Or call directly after first setup:

```bash
# macOS / Linux
venv/bin/python agent2cli.py

# Windows
venv\Scripts\python agent2cli.py
```

**One-shot mode** (pipe-friendly, just like `gemini -m flash "..."`):

```bash
venv/bin/python agent2cli.py "portscan 10.10.1.1"
venv/bin/python agent2cli.py --model 2.5-flash "explain this error"
venv/bin/python agent2cli.py --mode thinking "design this architecture"
venv/bin/python agent2cli.py --clear "start a fresh session"
```

---

## 🔑 Managing API Keys

### Via `run.py` — recommended

```bash
python run.py --addapi
```

Walks you through adding keys interactively and saves them to `.env`.  
Keys are stored as `GEMINI_API_KEY`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3` … and **auto-rotated** when one exhausts its quota. No downtime — the next key is picked up on the very next request.

### Inside a CLI session

```
/addapi
```

Paste a new key without leaving the session — saved to `.env` immediately and active on the next call.

### Reset everything

```bash
python run.py --reset
```

Wipes `venv/` and reinstalls all dependencies. Use when packages break or Python is upgraded.

### Full uninstall

```bash
python run.py --uninstall
```

Removes the virtual environment and generated files, leaving source code intact.

---

## 🗂️ First Run — Workspace Setup (Web UI)

1. Open **http://localhost:1311**
2. Click **+ Create Workspace** in the sidebar
3. Enter a name and optionally a project path — leave blank to auto-create a folder
4. Click the workspace → **New Chat** → start working

Every chat belongs to a workspace. The agent always knows your project path, detected framework, and accumulated workspace memories.

---

## ⌨️ CLI Commands Reference

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/addapi` | Add a Gemini API key to `.env` |
| `/keys` | Show current API key status and usage |
| `/model [name]` | Switch model (`2.5-flash-lite` · `2.5-flash` · `2.5-pro` · `3.1-*`) |
| `/mode [name]` | Switch mode (`fast ⚡` · `pro ★` · `thinking 🧠`) |
| `/clear` | Clear current conversation and start fresh |
| `/history` | Show last 10 messages |
| `/memory` | List all saved memories with importance scores |
| `/addmem <text>` | Save a memory manually |
| `/workspace [path]` | Show or set working directory for commands |
| `/run <cmd>` | Run a shell command directly in the current workspace |
| `/read <file>` | Read and display a file's contents |
| `/write <file>` | Write text to a file (prompts for content) |
| `/ls [path]` | Display a recursive directory tree |
| `/analyze <path>` | Detect framework / language / dependencies / run command |
| `/search <query>` | Web search via DuckDuckGo (no key required) |
| `/exit` · `Ctrl+C` | Quit |

---

## 🧪 Setup Checklist

- [ ] Python 3.10+ installed
- [ ] `python run.py` completed without errors
- [ ] Gemini API key saved to `.env`
- [ ] Web UI → server starts at **http://localhost:1311**, first workspace created
- [ ] CLI → prompt `you [no-ws|2.5-flash-lite|★]>` appears

---

## 🤖 Models Available

| Key | Model | Group |
|-----|-------|-------|
| `2.5-flash-lite` | Gemini 2.5 Flash Lite | 2.5 |
| `2.5-flash` | Gemini 2.5 Flash | 2.5 |
| `2.5-pro` | Gemini 2.5 Pro | 2.5 |
| `3.1-flash-lite` | Gemini 3.1 Flash Lite | 3.1 |
| `3.1-flash` | Gemini 3.1 Flash | 3.1 |
| `3.1-pro` | Gemini 3.1 Pro | 3.1 |

## ⚡ Reasoning Modes

| Mode | Max Tokens | Best for |
|------|-----------|----------|
| ⚡ Fast | 2 048 | Quick answers, simple commands — lowest cost |
| ★ Pro | 8 192 | Most tasks — balanced speed and quality |
| 🧠 Thinking | 16 384 | Complex reasoning, architecture, hard bugs *(2.5 / 3.1 only)* |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask, Flask-SocketIO |
| AI Engine | Google Gemini (`google-genai`) |
| Database | SQLite (stdlib `sqlite3`) |
| Terminal | `subprocess.Popen` — live stdout streaming |
| Web frontend | Vanilla JS, xterm.js, marked.js, highlight.js, Three.js |
| 3D scene | Three.js r128 — particles, torus knot, icosahedra, octahedron |
| CLI UI | Rich — panels, markdown, syntax highlight, spinner |
| Memory | Auto-extraction via background Gemini call after each reply |
| Web search | DuckDuckGo Instant Answer API — no key required |

---

## 🔒 Security Testing Workflows

Agent-2-Beta is purpose-built for security research and CTF work:

```bash
portscan 10.10.1.1
enumerate http://target:8080 with gobuster
run sqlmap on http://target/login?id=1
check for open ports on localhost
scan for vulnerabilities on 192.168.1.0/24
brute force SSH on 10.10.1.5 with hydra
```

Supports: `nmap`, `nikto`, `gobuster`, `ffuf`, `sqlmap`, `hydra`, `metasploit`,
`searchsploit`, `theharvester`, `binwalk`, `strings`, `volatility`, and more.

---

## 📌 Troubleshooting

| Problem | Solution |
|---------|----------|
| `No API keys configured` | `python run.py --addapi` or type `/addapi` in the CLI |
| Key quota exhausted | Keys rotate automatically. Add more: `python run.py --addapi` |
| Model returns empty response | Switch to **2.5 Flash Lite**: `/model 2.5-flash-lite` |
| Terminal not showing output | Refresh the browser tab and reconnect |
| `python` not found on Windows | Use `py run.py` or install from the Microsoft Store |
| Port 1311 already in use | Change `port=1311` in `agent2web.py` to another port |
| Broken venv / import errors | `python run.py --reset` — wipes and reinstalls cleanly |
| CLI spinner frozen | `Ctrl+C` — cancels the request and returns to prompt |
| `rich` not installed | `python run.py --reset` — `rich` is included in the install list |
| Want to start completely fresh | `python run.py --uninstall` then `python run.py` |

---

## 🚀 Agent-2-Pro

> **Unlock the full power of autonomous AI engineering.**

**Agent-2-Pro** is the professional-grade evolution of Agent-2-Beta — a proper **Software Engineer** and **Brutal Pentester** in one agent.

<div align="center">

| | Agent-2-Beta | Agent-2-Pro |
|-|:---:|:---:|
| Workspaces | ✅ | ✅ |
| 8 Agent Tools | ✅ | ✅ Extended |
| Memory Engine | ✅ | ✅ Advanced |
| Multi-tab Terminals | ✅ | ✅ |
| **Full-project generation from one prompt** | ❌ | ✅ |
| **Software Engineering mode** | ❌ | ✅ |
| **DeepDive — task decomposition** | ❌ | ✅ |
| **Brutal Penetration Testing** | ❌ | ✅ |
| **QA & automated test generation** | ❌ | ✅ |
| **Project Space** | ❌ | ✅ |

</div>

### Pro Feature Highlights

**🏗️ Software Engineering Mode**
Analyzes your prompt, architects the full solution, and engineers a complete multi-file project in a series of precise, self-correcting steps. One prompt → production-ready codebase.

**🎯 DeepDive**
Breaks a single complex task into multiple focused sub-tasks, solves each with precision, then assembles the final result. Dramatically higher accuracy on hard problems.

**🔴 Brutal Pentester**
Goes far beyond basic scanning — full kill-chain automation: recon → enumeration → exploitation → post-exploitation → report generation, all in one session.

**🧪 QA Mode**
Automatically generates unit tests, integration tests, and edge-case coverage for any codebase it builds or is given.

### Get Agent-2-Pro

📧 **Contact:** [aaravprogrammers@gmail.com](mailto:aaravprogrammers@gmail.com)
🐙 **GitHub:** [github.com/aaravshah1311](https://github.com/aaravshah1311)

---

## 🤝 Contributing

Contributions are welcome and appreciated! Agent-2-Beta is open to improvements in any area.

### How to contribute

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make** your changes and commit with a clear message
   ```bash
   git commit -m "feat: add your feature description"
   ```
4. **Push** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open** a Pull Request against `main`

### What we're looking for

- 🐛 **Bug fixes** — especially edge cases on Windows/Mac/Linux
- 🌐 **New tools** — additional agent capabilities
- 🎨 **UI improvements** — frontend polish, accessibility
- 📚 **Documentation** — clearer explanations, more examples
- 🔒 **Security workflows** — new pentest automation patterns
- ⚡ **Performance** — faster startup, lower memory, better streaming
- 🌍 **Portability** — improvements for different platforms or Python versions

### Guidelines

- Keep changes focused — one PR per feature/fix
- Follow the existing code style in each file
- Test on at least one platform before submitting
- Add a brief description in the PR explaining *what* and *why*

### Report issues

Found a bug or have a feature request? [Open an issue](https://github.com/aaravshah1311/Agent-2-Beta/issues) — please include your OS, Python version, and the exact error message.

---

## 👤 Authors

**Aarav Shah**
[![GitHub](https://img.shields.io/badge/GitHub-aaravshah1311-181717?style=flat&logo=github)](https://github.com/aaravshah1311/)
[![Portfolio](https://img.shields.io/badge/Portfolio-aaravshah1311.is--great.net-0ea5e9?style=flat)](https://aaravshah1311.is-great.net)
[![Email](https://img.shields.io/badge/Email-aaravprogrammers%40gmail.com-EA4335?style=flat&logo=gmail)](mailto:aaravprogrammers@gmail.com)

**Naitik Soni**
[![GitHub](https://img.shields.io/badge/GitHub-Naitiksoni--123-181717?style=flat&logo=github)](https://github.com/Naitiksoni-123/)
[![Email](https://img.shields.io/badge/Email-naitiksoni1417%40gmail.com-EA4335?style=flat&logo=gmail)](mailto:naitiksoni1417@gmail.com)

---

<div align="center">

**⭐ Star this repo if Agent-2-Beta helps you build or break things.**

<br>

<sub>Built for developers, security researchers, and anyone who wants an AI that actually does things.</sub>

</div>
