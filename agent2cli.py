#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent2cli.py  —  Agent 2 CLI
────────────────────────────
Run via:  python run.py --cli
      or: venv/bin/python agent2cli.py   (after run.py setup)

Keys are loaded ONLY from .env in the same folder as this script.
Key rotation: if one key hits quota, the next is tried automatically.

Commands:
  /help          show all commands
  /addapi        add an API key to .env
  /model [name]  switch model
  /mode  [name]  switch mode (fast | pro | thinking)
  /clear         clear conversation (start fresh)
  /shrink        summarize & shrink history manually
  /scan <path>   scan and analyze entire project
  /history       show recent messages
  /clearhistory  clear message history
  /memory        list saved memories
  /addmem <txt>  add a memory
  /run <cmd>     run a shell command directly
  /read <file>   read a file
  /search <q>    web search
  /exit          quit
"""

import os, sys, re, json, shutil, threading, time, platform
import subprocess, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime

# ── Locate project root (.env lives next to run.py / agent2cli.py) ────────────
ROOT     = Path(__file__).parent.resolve()
ENV_FILE = ROOT / ".env"
DATA_DIR = Path.home() / ".agent2"
HST_FILE = DATA_DIR / "history.json"
MEM_FILE = DATA_DIR / "memories.json"
PT_HISTORY = DATA_DIR / "cli_history.txt"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Windows console fixes ──────────────────────────────────────────────────────
OS_NAME = platform.system()
IS_WIN  = OS_NAME == "Windows"
IS_MAC  = OS_NAME == "Darwin"

if IS_WIN:
    os.system("chcp 65001 >nul 2>&1")
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception: pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# ── Rich (installed by run.py) ─────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box as rbox
    _RICH = True
    _con  = Console(highlight=False)
except ImportError:
    _RICH = False
    _con  = None

# ── prompt_toolkit ─────────────────────────────────────────────────────────────
# Imported lazily/optionally so commands like `--help` and `/addapi` can still
# work on a fresh machine before optional CLI dependencies are installed.
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
    _PTK = True
    _PTK_IMPORT_ERROR = None
except ImportError as ex:
    PromptSession = FileHistory = HTML = Style = None
    _PTK = False
    _PTK_IMPORT_ERROR = ex

# ── Gemini ─────────────────────────────────────────────────────────────────────
# Do not exit at import time. This lets `python agent2cli.py --help` work even
# when google-genai has not been installed yet. Agent calls validate this later.
try:
    import google.genai as genai
    from google.genai import types as gtypes
    _GENAI = True
    _GENAI_IMPORT_ERROR = None
except ImportError as ex:
    genai = None
    gtypes = None
    _GENAI = False
    _GENAI_IMPORT_ERROR = ex

# ── ANSI colour helpers ────────────────────────────────────────────────────────
R  = "\033[0m"; B  = "\033[1m"; D  = "\033[2m"
PU = "\033[38;5;135m"; CY = "\033[38;5;81m";  GR = "\033[38;5;83m"
YW = "\033[38;5;221m"; RD = "\033[38;5;203m"; WH = "\033[38;5;255m"
MG = "\033[38;5;177m"

def _p(col, text): return f"{col}{text}{R}"
def ok(t):   return _p(GR, t)
def warn(t): return _p(YW, t)
def err(t):  return _p(RD, t)
def dim(t):  return _p(D,  t)
def pu(t):   return _p(PU, t)
def cy(t):   return _p(CY, t)

# ── Platform ───────────────────────────────────────────────────────────────────
def detect_shell():
    if IS_WIN:
        ps = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        if ps: return ps, "PowerShell", "-Command"
        return "cmd.exe", "CMD", "/c"
    sh = os.environ.get("SHELL", "")
    for s in [sh, "/bin/bash", "/bin/zsh", "/bin/sh"]:
        if s and shutil.which(s):
            return s, Path(s).name.upper(), "-c"
    return "/bin/sh", "SH", "-c"

SHELL_BIN, SHELL_LABEL, SHELL_FLAG = detect_shell()

def shell_argv(cmd: str) -> list:
    if IS_WIN and SHELL_BIN.lower().endswith("cmd.exe"):
        return ["cmd.exe", "/c", cmd]
    return [SHELL_BIN, SHELL_FLAG, cmd]

# ── Models & modes ─────────────────────────────────────────────────────────────
MODELS = {
    "2.5-flash-lite": "gemini-2.5-flash-lite",
    "2.5-flash":      "gemini-2.5-flash",
    "2.5-pro":        "gemini-2.5-pro",
    "3.1-flash-lite": "gemini-3.1-flash-lite",
    "3.1-flash":      "gemini-3.1-flash",
    "3.1-pro":        "gemini-3.1-pro",
}
DEFAULT_MODEL = "2.5-flash-lite"

MODES = {
    "fast":     {"icon": "⚡", "max_tokens": 2048,  "thinking": False},
    "pro":      {"icon": "★",  "max_tokens": 8192,  "thinking": False},
    "thinking": {"icon": "🧠", "max_tokens": 16384, "thinking": True, "thinking_budget": 8000},
}
DEFAULT_MODE = "pro"

# ── .env key management ────────────────────────────────────────────────────────
def _read_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def _write_env(env: dict):
    ENV_FILE.write_text(
        "\n".join(f"{k}={v}" for k, v in env.items()) + "\n",
        encoding="utf-8"
    )

def load_keys() -> list[dict]:
    """Return list of {key, label, active, errs} from .env."""
    env = _read_env()
    keys, seen = [], set()
    placeholder = "your_gemini_api_key_here"
    for i, name in enumerate(["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{j}" for j in range(2, 10)]):
        v = env.get(name, "").strip()
        if v and v != placeholder and len(v) > 10 and v not in seen:
            keys.append({"key": v, "label": str(i + 1), "active": True, "errs": 0})
            seen.add(v)
    return keys

def save_key_to_env(new_key: str) -> tuple[bool, str]:
    """Append a new key to .env. Returns (success, label)."""
    new_key = new_key.strip().replace(" ", "")
    if len(new_key) < 15:
        return False, "key too short"
    existing_vals = [k["key"] for k in load_keys()]
    if new_key in existing_vals:
        return False, "already exists"
    env = _read_env()
    # Find the next free slot: GEMINI_API_KEY, GEMINI_API_KEY_2, ...
    used_names = {n for n in env if re.match(r"^GEMINI_API_KEY(?:_\d+)?$", n)}
    slot = 1
    while True:
        name = "GEMINI_API_KEY" if slot == 1 else f"GEMINI_API_KEY_{slot}"
        if name not in used_names:
            break
        slot += 1
    env[name] = new_key
    _write_env(env)
    return True, str(slot)

# ── Key rotator (in-memory, seeded from .env) ──────────────────────────────────
class KeyRotator:
    _lock = threading.Lock()

    def __init__(self):
        self._entries: list[dict] = []
        self.reload()

    def reload(self):
        with self._lock:
            self._entries = load_keys()

    def get(self) -> tuple:
        """Return (client, raw_key, label) — picks first active key."""
        if not _GENAI:
            return None, None, None
        with self._lock:
            active = [e for e in self._entries if e["active"]]
            if not active:
                # reset all and retry once
                for e in self._entries:
                    e["active"] = True
                    e["errs"] = 0
                active = self._entries
            if not active:
                return None, None, None
            e = active[0]
            return genai.Client(api_key=e["key"]), e["key"], e["label"]

    def fail(self, key: str, quota: bool = False):
        with self._lock:
            for e in self._entries:
                if e["key"] == key:
                    e["errs"] += 1
                    if quota or e["errs"] >= 3:
                        e["active"] = False
                    break

    def next_active(self, current_key: str) -> tuple:
        """After a failure, get the next different active key."""
        if not _GENAI:
            return None, None, None
        with self._lock:
            active = [e for e in self._entries if e["active"] and e["key"] != current_key]
            if not active:
                return None, None, None
            e = active[0]
            return genai.Client(api_key=e["key"]), e["key"], e["label"]

    def status(self) -> list[dict]:
        with self._lock:
            return [{"label": e["label"], "preview": e["key"][:14] + "…",
                     "active": e["active"]} for e in self._entries]

_rotator = KeyRotator()

# ── Memories ───────────────────────────────────────────────────────────────────
def load_mems() -> list:
    if MEM_FILE.exists():
        try: return json.loads(MEM_FILE.read_text(encoding="utf-8"))
        except: pass
    return []

def save_mems(mems: list):
    MEM_FILE.write_text(json.dumps(mems, indent=2, ensure_ascii=False), encoding="utf-8")

def add_mem(content: str, importance: int = 5, tags: list = None):
    mems = load_mems()
    mems.append({"id": f"{time.time():.0f}", "content": content.strip(),
                 "importance": importance, "tags": tags or [],
                 "created": datetime.now().isoformat()})
    save_mems(mems)

# ── History ────────────────────────────────────────────────────────────────────
def load_history() -> list:
    if HST_FILE.exists():
        try: return json.loads(HST_FILE.read_text(encoding="utf-8"))[-60:]
        except: pass
    return []

def save_history(h: list):
    HST_FILE.write_text(json.dumps(h[-100:], indent=2, ensure_ascii=False), encoding="utf-8")

# ── Terminal width ─────────────────────────────────────────────────────────────
def tw() -> int:
    return min(shutil.get_terminal_size((100, 30)).columns, 120)

# ── Print helpers ──────────────────────────────────────────────────────────────
def hr(char="─", col=D):
    print(f"{col}{char * (tw() - 2)}{R}")

def status_line(msg: str, kind: str = "info"):
    sym  = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}.get(kind, "•")
    _col = {"info": CY, "success": GR, "warning": YW, "error": RD}.get(kind, D)
    if _RICH:
        style = {"info":"#60b8ff","success":"#3ddc84","warning":"#f0c060","error":"#ff5555"}.get(kind,"dim")
        _con.print(f"  [{style}]{sym}[/] {msg}")
    else:
        print(f"  {_col}{sym}{R} {msg}")

def print_banner():
    os.system("cls" if IS_WIN else "clear")
    keys = _rotator.status()
    if _RICH:
        title = Text()
        title.append("  ⚡ ", style="bold yellow")
        title.append("Agent 2 CLI", style="bold #7c6af7")
        title.append(f"  {OS_NAME}/{SHELL_LABEL}", style="dim")
        _con.print(Panel(title, border_style="#1e1e30", padding=(0, 1)))
        for k in keys:
            st = "[bold #3ddc84]●[/]" if k["active"] else "[bold #ff5555]●[/]"
            _con.print(f"  {st} Key #{k['label']}: [dim]{k['preview']}[/]")
        if not keys:
            _con.print("  [bold #ff5555]⚠[/] No API keys — run [bold]/addapi[/]")
    else:
        w = min(tw(), 56)
        print(f"{PU}{'═' * w}{R}")
        print(f"{PU}{B}  ⚡ Agent 2 CLI{R}  {D}{OS_NAME}/{SHELL_LABEL}{R}")
        for k in keys:
            col = GR if k["active"] else RD
            print(f"  {col}●{R}  Key #{k['label']}: {D}{k['preview']}{R}")
        if not keys:
            print(f"  {YW}⚠  No API keys — type /addapi{R}")
        print(f"{PU}{'═' * w}{R}")
    print()

def print_help():
    cmds = [
        ("/help",             "Show this help"),
        ("/addapi",           "Add a Gemini API key to .env"),
        ("/model [name]",     "Switch model  (2.5-flash-lite | 2.5-flash | 2.5-pro | 3.1-*)"),
        ("/mode [name]",      "Switch mode   (fast ⚡ | pro ★ | thinking 🧠)"),
        ("/clear",            "Clear conversation (start fresh)"),
        ("/shrink",           "Summarize and shrink history manually"),
        ("/scan <path>",      "Scan and analyze entire project directory"),
        ("/history",          "Show last 10 messages"),
        ("/clearhistory",     "Clear message history"),
        ("/memory",           "List all saved memories"),
        ("/addmem <text>",    "Save a memory manually"),
        ("/run <cmd>",        "Run a shell command directly"),
        ("/read <file>",      "Read a file's contents"),
        ("/search <query>",   "Web search (DuckDuckGo)"),
        ("/keys",             "Show API key status"),
        ("/exit  or  Ctrl+C", "Quit"),
    ]
    if _RICH:
        t = Table(show_header=True, header_style="bold #7c6af7",
                  box=rbox.SIMPLE_HEAD, border_style="dim")
        t.add_column("Command",     style="#60b8ff", no_wrap=True)
        t.add_column("Description", style="#c4c4dc")
        for cmd, desc in cmds:
            t.add_row(cmd, desc)
        _con.print(t)
    else:
        print(f"\n{PU}{B}  Commands:{R}")
        for cmd, desc in cmds:
            print(f"  {CY}{cmd:<28}{R}{D}{desc}{R}")
        print()

def print_agent_reply(text: str):
    """Render agent markdown reply."""
    if _RICH:
        hr_style = "#1e1e30"
        _con.rule(style=hr_style)
        _con.print(f"  [bold #7c6af7]⚡ Agent 2[/]  [dim]{datetime.now().strftime('%H:%M')}[/]")
        _con.print()
        _con.print(Markdown(text), style="#c4c4dc")
        _con.print()
    else:
        hr()
        print(f"  {PU}{B}⚡ Agent 2{R}  {D}{datetime.now().strftime('%H:%M')}{R}")
        print()
        _render_markdown_plain(text)
        print()

def _render_markdown_plain(text: str):
    in_code = False
    lang    = ""
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            lang = line[3:].strip() if in_code else ""
            if in_code:  print(f"  {D}┌{'─' * 50}{R}")
            else:        print(f"  {D}└{'─' * 50}{R}")
            continue
        if in_code:
            print(f"  {YW}│ {line}{R}"); continue
        if   line.startswith("# "):   print(f"\n  {WH}{B}{line[2:]}{R}")
        elif line.startswith("## "):  print(f"\n  {CY}{B}{line[3:]}{R}")
        elif line.startswith("### "): print(f"  {PU}{line[4:]}{R}")
        elif re.match(r"^[-*] ", line): print(f"  {D}•{R} {line[2:]}")
        elif re.match(r"^\d+\. ", line):
            n, rest = line.split(". ", 1); print(f"  {PU}{n}.{R} {rest}")
        else:
            line = re.sub(r"\*\*(.+?)\*\*", f"{WH}{B}\\1{R}", line)
            line = re.sub(r"`(.+?)`",        f"{YW}\\1{R}", line)
            print(f"  {line}")

def print_tool_call(name: str, desc: str, detail: str = ""):
    icons = {"run_command":"⚙️","read_file":"📄","write_file":"✏️",
             "scan_project":"🔍","multi_edit_files":"✂️",
             "web_search":"🌐","save_memory":"🧠","emit_plan":"📋"}
    icon = icons.get(name, "🔧")
    if _RICH:
        body = Text()
        body.append(f" {icon} ", style="bold")
        body.append(name, style="bold #f0c060")
        body.append(f"  {desc}", style="dim")
        if detail: body.append(f"\n   $ {detail}", style="#f0c060")
        _con.print(Panel(body, border_style="#2a2a40", padding=(0, 1)))
    else:
        print(f"\n  {YW}▶ {name}{R}  {D}{desc}{R}")
        if detail: print(f"  {YW}$ {detail}{R}")

def print_plan(title: str, steps: list):
    if _RICH:
        body = Text()
        body.append(f"{title}\n\n", style="bold white")
        for i, s in enumerate(steps, 1):
            body.append(f"  {i}. ", style="bold #7c6af7")
            body.append(f"{s}\n",   style="#c4c4dc")
        _con.print(Panel(body, title="[bold #7c6af7]📋 Plan[/]",
                         border_style="#3a2a70", padding=(0, 1)))
    else:
        print(f"\n  {PU}{B}📋 {title}{R}")
        for i, s in enumerate(steps, 1):
            print(f"  {PU}{i}.{R} {s}")
        print()

# ── Esc Interrupter ────────────────────────────────────────────────────────────
import _thread

class EscInterrupter:
    """Listens for ESC key in the background to interrupt processing."""
    def __init__(self):
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._listen, daemon=True)

    def start(self):
        self._t.start()

    def stop(self):
        self._stop.set()

    def _listen(self):
        if not IS_WIN: return
        import msvcrt
        while not self._stop.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b'\x1b', b'\x03'):  # ESC or Ctrl+C
                    _thread.interrupt_main()
                    break
            time.sleep(0.05)

# ── Spinner ────────────────────────────────────────────────────────────────────
class Spinner:
    _frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, msg: str = "Thinking"):
        self._msg  = msg
        self._stop = threading.Event()
        self._t    = None
        self._prog = None

    def start(self):
        if _RICH:
            self._prog = Progress(SpinnerColumn(), TextColumn("[dim]{task.description}"),
                                  transient=True, console=_con)
            self._prog.start()
            self._prog.add_task(self._msg)
        else:
            self._t = threading.Thread(target=self._spin, daemon=True)
            self._t.start()

    def stop(self):
        self._stop.set()
        if _RICH and self._prog:
            self._prog.stop()
        if self._t:
            self._t.join(timeout=0.5)
        if not _RICH:
            print(f"\r{' ' * (tw() - 2)}\r", end="", flush=True)

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            print(f"\r  {PU}{self._frames[i % len(self._frames)]}{R} {D}{self._msg}…{R}",
                  end="", flush=True)
            i += 1
            time.sleep(0.08)

# ── Run command (streaming) ────────────────────────────────────────────────────
def run_cmd_stream(cmd: str, cwd: str | None = None) -> tuple[str, int]:
    work_dir = str(Path(cwd).expanduser()) if cwd else str(Path.cwd())
    output   = []
    if _RICH:
        _con.print(f"  [dim]$ {cmd}[/]")
    else:
        print(f"  {D}$ {cmd}{R}")
    try:
        proc = subprocess.Popen(
            shell_argv(cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True,
            env=os.environ.copy(), cwd=work_dir,
        )
        for line in proc.stdout:
            output.append(line)
            stripped = line.rstrip("\n")
            if _RICH: _con.print(f"  [dim]│[/] {stripped}")
            else:     print(f"  {D}│{R} {stripped}")
        proc.wait()
        rc  = proc.returncode
        sym = "✓" if rc == 0 else "✗"
        col_r = GR if rc == 0 else RD
        if _RICH:
            style = "bold #3ddc84" if rc == 0 else "bold #ff5555"
            _con.print(f"  [{style}]{sym} exit {rc}[/]")
        else:
            print(f"  {col_r}{B}{sym} exit {rc}{R}")
        return "".join(output), rc
    except Exception as ex:
        msg = str(ex)
        if _RICH: _con.print(f"  [bold #ff5555]✗ {msg}[/]")
        else:     print(f"  {RD}✗ {msg}{R}")
        return msg, -1

# ── Tool implementations (same logic as web app) ───────────────────────────────
MAX_FILE = 64_000
_SKIP    = {"__pycache__", ".git", "node_modules", ".venv", "venv", "env",
            "dist", "build", ".next", "target", ".DS_Store"}

def _impl_read(args: dict) -> dict:
    p = Path(args["path"]).expanduser()
    s = args.get("start_line"); e = args.get("end_line")
    try:
        if not p.exists(): return {"error": f"Not found: {p}"}
        with open(p, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total = len(lines)
        sl, el = (s - 1 if s else 0), (e if e else total)
        content = "".join(lines[sl:el])
        if len(content) > MAX_FILE:
            content = content[:MAX_FILE] + "\n…[truncated]"
        return {"content": content, "total_lines": total, "path": str(p)}
    except Exception as ex: return {"error": str(ex)}

def _impl_write(args: dict) -> dict:
    p = Path(args.get("path", "")).expanduser()
    content = args.get("content", "")
    if not content: return {"error": "content is required"}
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        lines = content.count("\n") + 1
        return {"success": True, "path": str(p), "lines": lines}
    except Exception as ex: return {"error": str(ex)}



def _impl_search(args: dict) -> dict:
    q = args.get("query", "")
    try:
        url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(
            {"q": q, "format": "json", "no_html": "1", "skip_disambig": "1"})
        req = urllib.request.Request(url, headers={"User-Agent": "Agent 2CLI/2.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        if data.get("AbstractText"):
            results.append({"title": data.get("Heading",""), "snippet": data["AbstractText"][:400]})
        for t in data.get("RelatedTopics", [])[:4]:
            if isinstance(t, dict) and t.get("Text"):
                results.append({"title": t["Text"][:80], "snippet": t["Text"][:300]})
        return {"query": q, "results": results[:5]} if results else {"query": q, "results": [], "note": "No results"}
    except Exception as ex:
        return {"error": str(ex), "query": q}

def _impl_save_mem(args: dict) -> dict:
    c = args.get("content", "").strip()
    if not c: return {"error": "content required"}
    imp  = min(10, max(1, int(args.get("importance", 5))))
    tags = [t.strip() for t in args.get("tags", "").split(",") if t.strip()]
    add_mem(c, imp, tags)
    return {"saved": True}

def _impl_plan(args: dict) -> dict:
    title = args.get("title", "Plan")
    try:    steps = json.loads(args.get("steps", "[]"))
    except: steps = [args.get("steps", "")]
    print_plan(title, steps)
    return {"plan_emitted": True}


def _impl_scan_project(args: dict) -> dict:
    raw = args.get("path", ".")
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path(os.getcwd()) / p
    p = p.resolve()
    if not p.exists() or not p.is_dir(): return {"error": f"Invalid directory: {p}"}
    
    important_exts = {".py", ".js", ".html", ".css", ".json", ".md", ".txt", ".ts", ".tsx",
                      ".jsx", ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".rb",
                      ".php", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env", ".sql",
                      ".sh", ".bat", ".ps1", ".xml", ".svg", ".lock"}
    skip_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
                 ".next", "target", ".DS_Store", ".idea", ".vscode", "coverage", ".cache"}
    
    # Build a file tree first
    tree_lines = [f"Project root: {p}"]
    contents = []
    total_size = 0
    
    import os as _os
    for root, dirs, files in _os.walk(p):
        dirs[:] = sorted([d for d in dirs if d not in skip_dirs])
        level = len(Path(root).relative_to(p).parts)
        indent = "  " * level
        tree_lines.append(f"{indent}{Path(root).name}/")
        for fname in sorted(files):
            fp = Path(root) / fname
            if fp.suffix in important_exts:
                tree_lines.append(f"{indent}  {fname}  ({fp.stat().st_size} bytes)")
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                    if len(text) > 50000: text = text[:50000] + "\n...[truncated]"
                    contents.append(f"\n{'='*60}\n FILE: {fp.relative_to(p)}\n{'='*60}\n{text}")
                    total_size += len(text)
                    if total_size > 300000:
                        contents.append("\n--- [TRUNCATED: Project too large, remaining files skipped] ---")
                        break
                except Exception:
                    pass
        if total_size > 300000:
            break
    
    file_tree = "\n".join(tree_lines)
    file_contents = "\n".join(contents) if contents else "No important text files found."
    return {"file_tree": file_tree, "file_count": len(contents), "project_contents": file_contents}

def _impl_multi_edit(args: dict) -> dict:
    edits = args.get("edits", [])
    results = []
    for edit in edits:
        p = Path(edit.get("path", "")).expanduser()
        old_text = edit.get("old_text", "")
        new_text = edit.get("new_text", "")
        if not p.exists():
            results.append(f"{p}: File not found")
            continue
        try:
            c = p.read_text(encoding="utf-8")
            if old_text not in c:
                results.append(f"{p}: old_text not found")
            else:
                p.write_text(c.replace(old_text, new_text), encoding="utf-8")
                results.append(f"{p}: Successfully edited")
        except Exception as e:
            results.append(f"{p}: Error {e}")
    return {"results": "\n".join(results)}

def dispatch_tool(name: str, args: dict) -> dict:
    if name == "read_file":        return _impl_read(args)
    if name == "write_file":       return _impl_write(args)
    if name == "web_search":       return _impl_search(args)
    if name == "save_memory":      return _impl_save_mem(args)
    if name == "emit_plan":        return _impl_plan(args)
    if name == "scan_project":     return _impl_scan_project(args)
    if name == "multi_edit_files": return _impl_multi_edit(args)
    return {"error": f"Unknown tool: {name}"}

# ── Gemini tool declarations ────────────────────────────────────────────────────
def _build_tools():
    S = gtypes.Schema; T = gtypes.Type
    return gtypes.Tool(function_declarations=[
        gtypes.FunctionDeclaration(name="run_command",
            description=f"Execute a shell command on {OS_NAME} ({SHELL_LABEL}). Use for running scripts, installs, scans, builds.",
            parameters=S(type=T.OBJECT, properties={
                "command":     S(type=T.STRING),
                "description": S(type=T.STRING),
                "cwd":         S(type=T.STRING),
            }, required=["command","description"])),
        gtypes.FunctionDeclaration(name="read_file",
            description="Read a file's contents. Always read before editing.",
            parameters=S(type=T.OBJECT, properties={
                "path":       S(type=T.STRING),
                "start_line": S(type=T.INTEGER),
                "end_line":   S(type=T.INTEGER),
            }, required=["path"])),
        gtypes.FunctionDeclaration(name="write_file",
            description="Create or overwrite a file with the given content. Use for creating new files. Parent directories are created automatically.",
            parameters=S(type=T.OBJECT, properties={
                "path":    S(type=T.STRING),
                "content": S(type=T.STRING),
            }, required=["path","content"])),
        gtypes.FunctionDeclaration(name="web_search",
            description="Search the web for CVEs, docs, error messages, latest info.",
            parameters=S(type=T.OBJECT, properties={
                "query":       S(type=T.STRING),
                "max_results": S(type=T.INTEGER),
            }, required=["query"])),
        gtypes.FunctionDeclaration(name="save_memory",
            description="Save an important fact to long-term memory (persists across sessions).",
            parameters=S(type=T.OBJECT, properties={
                "content":    S(type=T.STRING),
                "importance": S(type=T.INTEGER),
                "tags":       S(type=T.STRING),
            }, required=["content"])),
        gtypes.FunctionDeclaration(name="emit_plan",
            description="Show a step-by-step plan before a complex multi-step task.",
            parameters=S(type=T.OBJECT, properties={
                "title": S(type=T.STRING),
                "steps": S(type=T.STRING),
            }, required=["title","steps"])),
        gtypes.FunctionDeclaration(name="scan_project",
            description="Recursively scan a project directory and return a file tree + content of ALL code/config files. Use this AUTOMATICALLY whenever the user mentions a project, asks to check code, add features, or fix bugs. Pass the project path.",
            parameters=S(type=T.OBJECT, properties={
                "path": S(type=T.STRING),
            }, required=["path"])),
        gtypes.FunctionDeclaration(name="multi_edit_files",
            description="Edit multiple files at once by replacing exact text snippets. Each edit has path, old_text (exact match), new_text (replacement). Use for renaming, refactoring, or patching across files.",
            parameters=S(type=T.OBJECT, properties={
                "edits": S(type=T.ARRAY, items=S(type=T.OBJECT, properties={
                    "path": S(type=T.STRING),
                    "old_text": S(type=T.STRING),
                    "new_text": S(type=T.STRING)
                }))
            }, required=["edits"])),
    ])

# ── System prompt ──────────────────────────────────────────────────────────────
def build_sys_prompt() -> str:
    if IS_WIN:
        plat = ("PLATFORM: Windows / CMD+PowerShell\n"
                "ipconfig | dir | type | python | pip | ping -n 4 | winget/choco for packages")
    elif IS_MAC:
        plat = "PLATFORM: macOS / zsh\nifconfig | ls | python3 | pip3 | brew install"
    else:
        plat = "PLATFORM: Linux / bash\nip addr | ls | python3 | pip3 | apt/dnf/pacman"

    mems = load_mems()
    mem_block = ""
    if mems:
        top = sorted(mems, key=lambda x: -x.get("importance", 5))[:20]
        mem_block = "\n\n## MEMORIES:\n" + "\n".join(
            f"- [{m['importance']}/10] {m['content']}" for m in top)

    return f"""You are Agent 2 — an elite autonomous AI development and security agent running in a terminal.

{plat}

## YOUR TOOLS (use these — do NOT just print code)
1. **run_command** — Execute any shell command. Translate user intent to platform commands automatically:
   - User says "ls" or "ls -a" on Windows → run `dir` or `dir /a`
   - User says "cat file" on Windows → run `type file`
   - User says "mkdir" → use the correct platform command
   - ALWAYS translate Linux/Mac commands to Windows equivalents and vice versa. NEVER tell the user to "use dir instead" — just DO it.
2. **read_file** — Read a file's contents (optionally specific line range)
3. **write_file** — Create or overwrite a file with content. Use this to ACTUALLY write code to disk. Do NOT just show code in chat — call write_file to create the file.
4. **scan_project** — Recursively scan a project directory. Returns file tree + all source code. Use this AUTOMATICALLY when the user:
   - Says "check my project", "look at my code", "scan this", "add a feature to my project"
   - Mentions any project or codebase by name or path
   - Asks to fix bugs, refactor, or add functionality to existing code
   - You do NOT need the user to type /scan — just call it yourself
5. **multi_edit_files** — Precisely edit multiple files at once using find-and-replace. Each edit: {{path, old_text, new_text}}. Use for renaming, refactoring, or patching across files.
6. **web_search** — Search the web for docs, errors, CVEs, latest info
7. **save_memory** — Persist important facts across sessions
8. **emit_plan** — Show a step-by-step plan before complex tasks (3+ steps)

## CRITICAL RULES
- **NEVER just show code in chat and expect the user to copy-paste it.** Always use `write_file` to create files and `multi_edit_files` to edit existing files. You are an AGENT — you DO things, not just suggest things.
- **When creating a project** (e.g. "make an e-commerce site"), use `emit_plan` first, then `write_file` for EVERY file. Create proper directory structure. Write ALL the code to disk.
- **When editing a project**, use `scan_project` first to understand the full codebase (language, framework, DB, structure), then use `multi_edit_files` or `write_file` to make changes.
- **When fixing bugs or testing**, `scan_project` first, deeply analyze all files for logic errors, security vulnerabilities (XSS, SQLi, CSRF, etc.), and edge cases, then fix them using `multi_edit_files`. You have full cybersecurity analysis capabilities.
- **When asked to perform security testing**, use `run_command` to execute tools like nmap, sqlmap, nikto, or write custom testing scripts to verify vulnerabilities.
- **When user asks to "shrink memory/history"**, that is handled by the /shrink command — tell them to use `/shrink`.
- **Translate commands automatically.** If user says `ls`, run `dir`. If user says `cat`, run `type`. NEVER refuse or say "you should use X instead" — just run the right command.
- **Task with 3+ steps** → call `emit_plan` FIRST to show the plan, then execute it step by step.

## RESPONSE STYLE
- Use markdown: headers, **bold**, `code`, tables
- Always include language tag on code blocks: ```python, ```bash
- Summarize command output clearly
- After finishing: confirm what was done + suggest next steps{mem_block}
"""


# ── Shrink History ─────────────────────────────────────────────────────────────
def shrink_history_agent(history: list, model_key: str, keep: int = 10, manual: bool = False) -> list:
    if not manual and len(history) < 100:
        return history
    
    if manual:
        status_line("Manually shrinking history...", "info")
    else:
        status_line("History reached 100 messages. Summarizing to save tokens...", "info")
        
    client, key, label = _rotator.get()
    if not client: return history[-50:] # fallback
    
    api_model = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    
    text_to_summarize = ""
    for h in history[:-keep]:
        role = "User" if h["role"] == "user" else "Agent"
        text_to_summarize += f"{role}: {h['content']}\n\n"
        
    prompt = f"Please provide a concise but comprehensive summary of the following conversation history. Retain key facts, decisions, and context.\n\n{text_to_summarize}"
    
    try:
        resp = client.models.generate_content(model=api_model, contents=prompt)
        summary = resp.text
        
        new_history = [{"role": "assistant", "content": f"**[System: History Summary]**\n{summary}", "ts": datetime.now().isoformat()}]
        new_history.extend(history[-keep:])
        return new_history
    except Exception as ex:
        status_line(f"Failed to shrink history: {ex}", "warning")
        return history[-50:] # fallback

# ── Agent loop ─────────────────────────────────────────────────────────────────
def run_agent(
    user_msg:  str,
    history:   list,
    model_key: str,
    mode_key:  str,
) -> list:
    """One full agentic turn. Returns updated history."""

    if not _GENAI:
        status_line("google-genai is not installed. Run: pip install google-genai", "error")
        return history

    client, key, label = _rotator.get()
    if not client:
        status_line("No API keys found. Run:  python run.py --addapi  or type /addapi", "error")
        return history

    api_model = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    mode_cfg  = MODES.get(mode_key,  MODES[DEFAULT_MODE])

    # Generation config
    cfg_kw: dict = dict(
        system_instruction=build_sys_prompt(),
        tools=[_build_tools()],
        tool_config=gtypes.ToolConfig(
            function_calling_config=gtypes.FunctionCallingConfig(mode="AUTO")
        ),
        max_output_tokens=mode_cfg["max_tokens"],
    )
    if mode_cfg.get("thinking") and model_key in ("2.5-pro","3.1-flash","3.1-pro","3.1-flash-lite","2.5-flash","2.5-flash-lite"):
        try:
            cfg_kw["thinking_config"] = gtypes.ThinkingConfig(
                thinking_budget=mode_cfg.get("thinking_budget", 8000))
        except Exception: pass

    gen_cfg = gtypes.GenerateContentConfig(**cfg_kw)

    # Build context from history (last 20 turns)
    context = []
    for h in history[-20:]:
        if   h["role"] == "user":      context.append(gtypes.Content(role="user",  parts=[gtypes.Part(text=h["content"])]))
        elif h["role"] == "assistant": context.append(gtypes.Content(role="model", parts=[gtypes.Part(text=h["content"])]))

    context.append(gtypes.Content(role="user", parts=[gtypes.Part(text=user_msg)]))
    history.append({"role": "user", "content": user_msg, "ts": datetime.now().isoformat()})

    total_tokens = 0

    for _iteration in range(12):
        mode_icon = mode_cfg["icon"]
        spin_msg  = f"Agent 2  [{model_key} / {mode_key} {mode_icon}]  key #{label}"
        spin = Spinner(spin_msg)
        spin.start()

        try:
            resp = client.models.generate_content(model=api_model, contents=context, config=gen_cfg)
        except KeyboardInterrupt:
            spin.stop()
            print()
            status_line("Interrupted.", "warning")
            return history
        except Exception as exc:
            spin.stop()
            es = str(exc)
            is_quota  = "429" in es or "quota" in es.lower() or "exhausted" in es.lower()
            is_model  = any(k in es.lower() for k in ("not found","invalid","unsupported","model"))
            _rotator.fail(key, quota=is_quota)

            if is_quota:
                # try next key
                c2, k2, l2 = _rotator.next_active(key)
                if c2:
                    status_line(f"Quota hit on key #{label} — switching to key #{l2}", "warning")
                    client, key, label = c2, k2, l2
                    continue
            hint = "\n  Tip: /model 2.5-flash-lite" if is_model else ""
            status_line(f"API Error ({model_key}): {es}{hint}", "error")
            return history
        finally:
            spin.stop()

        # Parse response
        try:
            candidate = resp.candidates[0] if resp.candidates else None
            if not candidate or not candidate.content:
                fr = getattr(candidate, "finish_reason", "?") if candidate else "none"
                status_line(f"Empty response (finish_reason={fr}). Try /model 2.5-flash-lite", "warning")
                return history
            parts = candidate.content.parts or []
        except Exception as ex:
            status_line(f"Parse error: {ex}", "error")
            return history

        func_calls: list = []
        texts:      list = []
        for p in parts:
            try:
                if p.function_call and p.function_call.name: func_calls.append(p.function_call)
                elif p.text: texts.append(p.text)
            except Exception: pass

        # Tokens
        try:    tok = getattr(resp.usage_metadata, "total_token_count", 0) or 0
        except: tok = 0
        total_tokens += tok
        if tok:
            if _RICH: _con.print(f"  [dim]tokens: {total_tokens:,}[/]")
            else:     print(f"  {D}tokens: {total_tokens:,}{R}")

        # Interim text (before tool calls)
        if texts and func_calls:
            print()
            for t in texts: print(f"  {D}{t[:200]}{R}")

        # Tool calls
        if func_calls:
            context.append(gtypes.Content(role="model",
                parts=[gtypes.Part(function_call=fc) for fc in func_calls]))
            tool_result_parts = []

            for fc in func_calls:
                name = fc.name
                args = dict(fc.args)
                print()

                if name == "run_command":
                    cmd  = args.get("command", "")
                    desc = args.get("description", "Running…")
                    cwd  = args.get("cwd", None)
                    print_tool_call(name, desc, cmd)
                    out, rc = run_cmd_stream(cmd, cwd)
                    result  = {"output": out[:3000], "returncode": rc, "success": rc == 0}
                else:
                    labels = {
                        "read_file":        f"Reading {args.get('path','?')}",
                        "write_file":       f"Writing {args.get('path','?')}",
                        "scan_project":     f"Scanning {args.get('path','?')}",
                        "multi_edit_files": f"Editing {len(args.get('edits',[])) if isinstance(args.get('edits'), list) else '?'} file(s)",
                        "web_search":       f"Searching: {args.get('query','?')}",
                        "save_memory":      f"Saving memory",
                        "emit_plan":        f"Planning: {args.get('title','?')}",
                    }
                    print_tool_call(name, labels.get(name, name))
                    result = dispatch_tool(name, args)

                    # Pretty display
                    if name == "read_file" and "content" in result:
                        preview = result["content"][:600]
                        lang    = Path(args.get("path","")).suffix.lstrip(".")
                        if _RICH:
                            try:   _con.print(Syntax(preview, lang or "text", theme="monokai", line_numbers=True))
                            except: _con.print(f"[dim]{preview}[/]")
                        else: print(f"{YW}{preview}{R}")
                    elif name == "write_file" and result.get("success"):
                        status_line(f"Written \u2192 {result.get('path','?')}  ({result.get('lines',0)} lines)", "success")
                    elif name == "scan_project" and "file_tree" in result:
                        tree = result["file_tree"][:2000]
                        cnt  = result.get("file_count", 0)
                        status_line(f"Scanned {cnt} files", "success")
                        if _RICH: _con.print(f"[dim]{tree}[/]")
                        else:     print(f"{D}{tree}{R}")
                    elif name == "multi_edit_files" and "results" in result:
                        for line in result["results"].split("\n"):
                            if "Successfully" in line:
                                status_line(line, "success")
                            elif "not found" in line or "Error" in line:
                                status_line(line, "error")
                            else:
                                status_line(line, "info")
                    elif name == "web_search" and "results" in result:
                        for res in result["results"][:3]:
                            if _RICH: _con.print(f"  [bold #60b8ff]{res.get('title','')[:70]}[/]\n  [dim]{res.get('snippet','')[:220]}[/]\n")
                            else:     print(f"  {CY}{res.get('title','')[:70]}{R}\n  {D}{res.get('snippet','')[:220]}{R}\n")
                    elif name == "save_memory" and result.get("saved"):
                        status_line("Memory saved", "success")
                    elif "error" in result:
                        status_line(f"Tool error: {result['error']}", "error")

                tool_result_parts.append(gtypes.Part(function_response=gtypes.FunctionResponse(
                    name=name, response=result)))

            context.append(gtypes.Content(role="user", parts=tool_result_parts))

        else:
            # Final text response
            final = "\n".join(texts) or "Done."
            print_agent_reply(final)
            history.append({"role": "assistant", "content": final,
                            "ts": datetime.now().isoformat()})
            return history

    status_line(f"Reached max iterations (12).", "warning")
    return history

# ── /addapi command (interactive, writes to .env) ──────────────────────────────
def cmd_addapi():
    keys = load_keys()
    print()
    if _RICH:
        _con.print(Panel("[bold #7c6af7]Add Gemini API Key[/]\nFree: [link=https://aistudio.google.com/app/apikey]aistudio.google.com/app/apikey[/link]",
                         border_style="#3a2a70"))
    else:
        print(f"  {PU}{B}Add Gemini API Key{R}")
        print(f"  Free key: https://aistudio.google.com/app/apikey\n")

    status_line(f"Keys currently in .env: {len(keys)}", "info")
    for k in keys:
        col = GR if k["active"] else RD
        print(f"    {col}●{R}  #{k['label']}: {D}{k['key'][:14]}…{R}")
    print()

    while True:
        try:
            raw = input(f"  {PU}paste key (or Enter to cancel):{R} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if not raw:
            return
        raw = raw.replace(" ", "").replace("\n", "")
        ok_save, msg = save_key_to_env(raw)
        if ok_save:
            _rotator.reload()
            status_line(f"Key saved as #{msg}", "success")
            status_line(f"Total keys in .env: {len(load_keys())}", "info")
            ans = input(f"  Add another? [y/N]: ").strip().lower()
            if ans != "y":
                break
        else:
            status_line(f"Could not save key: {msg}", "error")

# ── Read multi-line input helper ───────────────────────────────────────────────
def read_input(prompt_str: str) -> str:
    """Read one line, stripping leading/trailing whitespace."""
    try:
        if _RICH:
            return _con.input(prompt_str)
        else:
            return input(prompt_str)
    except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt


def get_prompt_style(mode: str):
    mode_color = {
        "fast": "#00ff9c",     # neon green
        "pro": "#7c6af7",      # purple
        "thinking": "#ff9f43"  # orange
    }.get(mode, "#7c6af7")

    return Style.from_dict({
        "user": f"{mode_color} bold",
        "meta": "#888888",
        "arrow": f"{mode_color} bold",
    })

# ── Main interactive loop ──────────────────────────────────────────────────────
def main():
    import argparse
    ap = argparse.ArgumentParser(description="Agent 2 CLI — autonomous dev agent")
    ap.add_argument("message", nargs="?", help="One-shot message (no REPL)")
    ap.add_argument("--model", default=None, choices=list(MODELS.keys()))
    ap.add_argument("--mode",  default=None, choices=list(MODES.keys()))
    ap.add_argument("--clear", action="store_true", help="Start with fresh chats")
    args = ap.parse_args()

    # Session state
    model     = args.model or DEFAULT_MODEL
    mode      = args.mode  or DEFAULT_MODE
    history   = [] if args.clear else load_history()

    # One-shot mode (like `gemini -m flash "hello"`)
    if args.message:
        _rotator.reload()
        history = run_agent(args.message, history, model, mode)
        save_history(history)
        return

    # Interactive REPL
    if not _PTK:
        print("\n  [ERR]  prompt-toolkit not installed.")
        print("         Run:  pip install prompt-toolkit\n")
        return

    print_banner()
    status_line(f"Model: {model}  Mode: {mode}  Shell: {SHELL_LABEL}", "info")
    status_line("Type /help for commands.  Ctrl+C or /exit to quit.", "info")
    if not _GENAI:
        status_line("google-genai is missing — install it before chatting: pip install google-genai", "warning")
    if not load_keys():
        status_line("No API keys — type /addapi to add one.", "warning")
    if history:
        status_line(f"Restored {len(history)} messages from last session.  /clearhistory to start fresh.", "info")

    session = PromptSession(history=FileHistory(str(PT_HISTORY)))
    
    while True:
        # Build prompt line
        mo_icon   = MODES[mode]["icon"]
        style = get_prompt_style(mode)

        prompt = HTML(
            f'<user>you</user> '
            f'<meta>[{SHELL_LABEL}|{model}|{mo_icon} ]</meta>'
            f'<arrow>></arrow> '
        )

        try:
            print()
            user_input = session.prompt(prompt, style=style).strip()
        except KeyboardInterrupt:
            print()
            status_line("Goodbye.", "info")
            save_history(history)
            break

        if not user_input:
            continue

        low = user_input.lower()

        # ── Slash commands ─────────────────────────────────────────────────────
        if low in ("/exit", "/quit", "exit", "quit"):
            status_line("Goodbye.", "info")
            save_history(history)
            break

        elif low == "/help":
            print_help()

        elif low == "/addapi":
            cmd_addapi()

        elif low == "/keys":
            for k in _rotator.status():
                sym = ok("●") if k["active"] else err("●")
                print(f"  {sym}  Key #{k['label']}: {D}{k['preview']}{R}")

        elif low.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 1:
                if _RICH:
                    t = Table(show_header=False, box=rbox.SIMPLE)
                    t.add_column(); t.add_column()
                    for k in MODELS:
                        cur = "[bold #7c6af7]← current[/]" if k == model else ""
                        t.add_row(f"[#60b8ff]{k}[/]", cur)
                    _con.print(t)
                else:
                    for k in MODELS:
                        print(f"  {CY}{k}{R}{'  ← current' if k==model else ''}")
            else:
                m = parts[1].strip()
                if m in MODELS:
                    model = m
                    status_line(f"Model → {m}", "success")
                else:
                    status_line(f"Unknown model. Options: {', '.join(MODELS)}", "error")

        elif low.startswith("/mode"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 1:
                for k, v in MODES.items():
                    print(f"  {YW}{k}{R}  {D}{v['max_tokens']} tokens{R}{'  ← current' if k==mode else ''}")
            else:
                m = parts[1].strip()
                if m in MODES:
                    mode = m
                    status_line(f"Mode → {m}  {MODES[m]['icon']}", "success")
                else:
                    status_line(f"Unknown mode. Options: {', '.join(MODES)}", "error")

        elif low == "/clear":
            history = []
            save_history(history)
            os.system("cls" if IS_WIN else "clear")
            print_banner()
            status_line("Conversation cleared.", "success")
        elif low == "/clearhistory":
            history = []
            save_history(history)
            status_line("Message history cleared.", "success")

        elif low == "/shrink":
            history = shrink_history_agent(history, model, keep=5, manual=True)
            save_history(history)
            status_line("History shrunk.", "success")

        elif low == "/history":
            if not history:
                status_line("No history.", "info")
            else:
                for h in history[-10:]:
                    col = CY if h["role"] == "user" else PU
                    sym = "you" if h["role"] == "user" else " a2"
                    ts  = h.get("ts","")[-8:][:5]
                    print(f"  {col}{sym}{R}  {D}{ts}{R}  {h['content'][:90]}")

        elif low == "/memory":
            mems = load_mems()
            if not mems:
                status_line("No memories saved yet.", "info")
            else:
                if _RICH:
                    t = Table(show_header=True, header_style="bold #7c6af7", box=rbox.SIMPLE_HEAD)
                    t.add_column("#", width=3, style="dim")
                    t.add_column("Imp", width=5)
                    t.add_column("Content")
                    t.add_column("Tags", style="dim")
                    for i, m in enumerate(sorted(mems, key=lambda x: -x.get("importance", 5)), 1):
                        t.add_row(str(i), f"{m.get('importance',5)}/10",
                                  m["content"][:80],
                                  ", ".join(m.get("tags", [])))
                    _con.print(t)
                else:
                    for i, m in enumerate(sorted(mems, key=lambda x: -x.get("importance", 5)), 1):
                        print(f"  {D}{i}.{R}  {YW}[{m.get('importance',5)}/10]{R}  {m['content'][:80]}")

        elif low.startswith("/addmem"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                add_mem(parts[1].strip())
                status_line("Memory saved.", "success")
            else:
                status_line("Usage: /addmem <text>", "warning")

        elif low.startswith("/run "):
            cmd = user_input[5:].strip()
            if cmd: run_cmd_stream(cmd)

        elif low.startswith("/read "):
            path = user_input[6:].strip()
            result = _impl_read({"path": path})
            if "error" in result:
                status_line(result["error"], "error")
            else:
                lang = Path(path).suffix.lstrip(".")
                if _RICH:
                    try:   _con.print(Syntax(result["content"][:3000], lang or "text", theme="monokai", line_numbers=True))
                    except: _con.print(result["content"][:3000])
                else:
                    print(f"{YW}{result['content'][:3000]}{R}")

        elif low.startswith("/search "):
            q = user_input[8:].strip()
            result = _impl_search({"query": q})
            for res in result.get("results", [])[:5]:
                print()
                if _RICH: 
                    _con.print(f"  [bold #60b8ff]{res.get('title','')[:70]}[/]\n  [dim]{res.get('snippet','')[:250]}[/]\n")
                else:     
                    print(f"  {CY}{res.get('title','')[:70]}{R}\n  {D}{res.get('snippet','')[:250]}{R}\n")
            if not result.get("results"):
                status_line("No results.", "info")

        elif low.startswith("/scan"):
            # Extract path and feed to agent as an explicit scan request
            scan_path = user_input[5:].strip() or "."
            user_input = f"Scan the project at path: {scan_path} — use the scan_project tool on that path. Show the file tree and analyze the tech stack (languages, frameworks, DB, etc)."
            esc_killer = EscInterrupter()
            esc_killer.start()
            try:
                history = run_agent(user_input, history, model, mode)
                history = shrink_history_agent(history, model)
                save_history(history)
            except KeyboardInterrupt:
                print()
                status_line("Interrupted.", "warning")
            finally:
                esc_killer.stop()

        elif low.startswith("/"):
            status_line(f"Unknown command: {user_input}  →  /help", "warning")

        # ── Agent call ─────────────────────────────────────────────────────────
        else:
            esc_killer = EscInterrupter()
            esc_killer.start()
            try:
                history = run_agent(user_input, history, model, mode)
                history = shrink_history_agent(history, model)
                save_history(history)
            except KeyboardInterrupt:
                print()
                status_line("Interrupted.", "warning")
            finally:
                esc_killer.stop()

if __name__ == "__main__":
    main()
