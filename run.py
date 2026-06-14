#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent2 — Universal Launcher
Platforms: Windows (CMD/PowerShell) | macOS | Linux

Usage:
  python run.py               — setup + start
  python run.py --web         — setup + start Web Agent
  python run.py --cli         — setup + start CLI agent
  python run.py --addapi      — add another API key
  python run.py --reset       — wipe venv and reinstall
  python run.py --uninstall   — setup + start CLI agent
  python run.py -h            — Show this help menu
"""

import os, sys, re, subprocess, platform, shutil, time, threading, itertools
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.resolve()
VENV      = ROOT / ".venv"
ENV_FILE  = ROOT / ".env"
APP_WEB   = ROOT / "agent2web.py"
APP_CLI   = ROOT / "agent2cli.py"

OS_NAME = platform.system()   # Windows | Darwin | Linux
IS_WIN  = OS_NAME == "Windows"
IS_MAC  = OS_NAME == "Darwin"

VENV_PY  = VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")
VENV_PIP = VENV / ("Scripts/pip.exe"    if IS_WIN else "bin/pip")

# (import_name, pip_name, display_label)
COMMON_PACKAGES = [
    ("google.genai",   "google-genai",   "google-genai"),
]

WEB_PACKAGES = [
    ("flask",          "flask",          "Flask"),
    ("flask_socketio", "flask-socketio", "Flask-SocketIO"),
    ("eventlet",       "eventlet",       "eventlet"),
]

CLI_PACKAGES = [
    ("rich",           "rich",           "Rich (terminal UI)"),
    ("prompt_toolkit", "prompt_toolkit", "Prompt Toolkit (terminal input)"),
]

# ── Windows console fixes ──────────────────────────────────────────────────────
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

# ── ANSI helpers ───────────────────────────────────────────────────────────────
R  = "\033[0m";   B  = "\033[1m";  D  = "\033[2m"
GR = "\033[1;32m"; CY = "\033[1;36m"; YL = "\033[1;33m"
RD = "\033[1;31m"; MG = "\033[1;35m"; WH = "\033[1;37m"

g   = lambda t: f"{GR}{t}{R}"
y   = lambda t: f"{YL}{t}{R}"
r   = lambda t: f"{RD}{t}{R}"
c   = lambda t: f"{CY}{t}{R}"
w   = lambda t: f"{WH}{B}{t}{R}"
dim = lambda t: f"{D}{t}{R}"

# ── Banner ─────────────────────────────────────────────────────────────────────
def banner():
    os.system("cls" if IS_WIN else "clear")
    print(f"{MG}")
    print(r"    _                    _   ____  ")
    print(r"   / \   __ _  ___ _ __ | |_|___ \ ")
    print(r"  / _ \ / _` |/ _ \ '_ \| __| __) |")
    print(r" / ___ \ (_| |  __/ | | | |_ / __/ ")
    print(r"/_/   \_\__, |\___|_| |_|\__|_____|")
    print(r"        |___/                      ")
    print(R)
    print(f"  {CY}{'═' * 46}{R}")
    print(f"  {w('Autonomous Terminal Agent')}  {dim('v2.1')}")
    print(f"  {dim(OS_NAME + ' ' + platform.machine() + '  |  Python ' + sys.version.split()[0])}")
    print(f"  {CY}{'═' * 46}{R}\n")

# ── Spinner ────────────────────────────────────────────────────────────────────
SPIN = ["-", "\\", "|", "/"]

def spin_run(label: str, cmd: list) -> subprocess.CompletedProcess:
    done, box = threading.Event(), [None]
    def work():
        box[0] = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace")
        done.set()
    threading.Thread(target=work, daemon=True).start()
    for f in itertools.cycle(SPIN):
        if done.is_set(): break
        print(f"\r  [{GR}{f}{R}]  {label} ...", end="", flush=True)
        time.sleep(0.10)
    print(f"\r  {g('[OK]')}  {label}        ", flush=True)
    return box[0]

# ── Step 1: Python ─────────────────────────────────────────────────────────────
def check_python():
    print(f"  {w('[ System ]')}\n")
    if sys.version_info < (3, 9):
        print(f"  {r('[ERR]')}  Python 3.9+ required (you have {sys.version.split()[0]})")
        sys.exit(1)
    print(f"  {g('[OK]')}  Python {sys.version.split()[0]}")
    print(f"  {g('[OK]')}  Platform: {OS_NAME} {platform.machine()}")

# ── Step 2: Venv ───────────────────────────────────────────────────────────────
def ensure_venv(reset=False):
    # ── 🔒 Venv Reset Guard ──────────────────────────────────────────────────
    is_running_from_venv = str(VENV).lower() in sys.executable.lower()

    if reset:
        if is_running_from_venv:
            print(f"\n  {r('[ERR]')}  It couldn't be reset in env mode.")
            print(f"         Deactivate env or try in other terminal.\n")
            sys.exit(1)
            
        if VENV.exists():
            # Function to handle Windows read-only file locks
            def remove_readonly(func, path, excinfo):
                import stat
                try:
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                except Exception: pass

            try:
                # We print the label manually since we aren't using spin_run here
                print(f"  {y('[-]')}  Removing old venv ...", end="", flush=True)
                
                shutil.rmtree(VENV, onerror=remove_readonly)
                
                time.sleep(1) # Wait for Windows file handles
                print(f"\r  {g('[OK]')}  Environment wiped.        ")
            except Exception as e:
                print(f"\n  {r('[ERR]')}  Reset failed: {e}")
                sys.exit(1)
            
            for cache in ROOT.rglob("__pycache__"):
                shutil.rmtree(cache, ignore_errors=True)

    # ── 🛠️ Venv Creation ─────────────────────────────────────────────────────
    print(f"\n  {w('[ Virtual Environment ]')}\n")
    if not VENV.exists():
        # Creation DOES use spin_run because it calls an external process
        res = spin_run("Creating fresh virtual environment",
                       [sys.executable, "-m", "venv", str(VENV)])
        if res.returncode != 0:
            print(r(f"\n  [ERR]  {res.stderr[:400]}")); sys.exit(1)
    else:
        print(f"  {g('[OK]')}  Virtual environment ready  {dim(str(VENV))}")

# ── Step 3: Packages ───────────────────────────────────────────────────────────
def pkg_ok(name: str) -> bool:
    """Explicitly check if a package can be imported in the venv."""
    return subprocess.run(
        [str(VENV_PY), "-c", f"import {name}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0

def install_deps(mode="web"):
    print(f"\n  {w('[ Dependencies ]')}\n")

    subprocess.run([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    packages = COMMON_PACKAGES[:]

    if mode == "web":
        packages += WEB_PACKAGES
    elif mode == "cli":
        packages += CLI_PACKAGES
    else:
        packages += WEB_PACKAGES + CLI_PACKAGES  # fallback (default run)

    for imp, pip_name, label in packages:
        if pkg_ok(imp):
            print(f"  {g('[OK]')}  {label} {dim('(verified)')}")
        else:
            print(f"  {y('[..]')}  Installing {label}...")
            res = spin_run(f"Installing {label}", 
                           [str(VENV_PY), "-m", "pip", "install", pip_name, "--quiet"])
            
            if res.returncode != 0:
                print(r(f"  [ERR] Failed to install {label}"))
                sys.exit(1)
            
            if pkg_ok(imp):
                print(f"  {g('[OK]')}  {label} verified in venv")
            else:
                print(r(f"  [ERR] {label} installed but not accessible"))
                sys.exit(1)

# ── Step 4: .env helpers ───────────────────────────────────────────────────────
def _read_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def _load_keys() -> list[str]:
    env = _read_env()
    keys, seen = [], set()
    placeholder = "your_gemini_api_key_here"
    for name in ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 10)]:
        v = env.get(name, "").strip()
        if v and v != placeholder and len(v) > 10 and v not in seen:
            keys.append(v); seen.add(v)
    return keys

def _write_keys(keys: list[str]):
    env = _read_env()
    for name in list(env.keys()):
        if re.match(r"^GEMINI_API_KEY", name):
            del env[name]
    for i, k in enumerate(keys):
        env_name = "GEMINI_API_KEY" if i == 0 else f"GEMINI_API_KEY_{i+1}"
        env[env_name] = k
    ENV_FILE.write_text("\n".join(f"{k}={v}" for k, v in env.items()) + "\n",
                        encoding="utf-8")
    # propagate to current process
    for k, v in env.items():
        os.environ[k] = v

def _prompt_key(num: int) -> str:
    while True:
        try:
            key = input(f"  {CY}>>>{R} API key #{num}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return ""
        if not key:
            return ""
        key = key.replace(" ", "").replace("\n", "")
        if len(key) < 15:
            print(f"  {y('[!]')}  Key too short — check and retry\n")
            continue
        return key

# ── Step 4a: Setup (first run, no keys) ───────────────────────────────────────
def ensure_keys(force_add=False):
    print(f"\n  {w('[ Gemini API Keys ]')}\n")
    keys = _load_keys()

    if keys and not force_add:
        for i, k in enumerate(keys, 1):
            print(f"  {g('[OK]')}  Key #{i}: {c(k[:14]+'...')}")
        print()
        ans = input(f"  {CY}>>>{R} Add more keys for failover? [y/N]: ").strip().lower()
        if ans != "y":
            return

    if not keys:
        print(f"  {y('[!]')}  No keys configured.")
        print(f"  {dim('  Free key:')} {c('https://aistudio.google.com/app/apikey')}\n")

    print(f"  {dim('  Enter keys one by one. Press Enter with nothing to finish.')}\n")
    num = len(keys) + 1
    while num <= 9:
        key = _prompt_key(num)
        if not key:
            break
        if key in keys:
            print(f"  {y('[!]')}  Duplicate — skipping\n"); continue
        keys.append(key)
        print(f"  {g('[OK]')}  Key #{num} saved\n")
        num += 1
        if num > 9:
            print(f"  {dim('  Maximum 9 keys.')}"); break
        ans = input(f"  {CY}>>>{R} Add another for failover? [y/N]: ").strip().lower()
        if ans != "y":
            break

    if not keys:
        print(f"  {y('[!]')}  No keys — the app will show setup instructions at runtime.")
        return
    _write_keys(keys)
    print(f"\n  {g('[OK]')}  {len(keys)} key(s) saved to .env")

# ── Step 4b: /addapi  — add key interactively, persist to .env ────────────────
def add_api():
    banner()
    print(f"  {w('[ Add Gemini API Key ]')}\n")
    keys = _load_keys()
    print(f"  {dim('Currently stored keys:')} {len(keys)}")
    for i, k in enumerate(keys, 1):
        print(f"  {g('[OK]')}  Key #{i}: {c(k[:14]+'...')}")
    print(f"\n  {dim('Free key:  https://aistudio.google.com/app/apikey')}\n")

    num = len(keys) + 1
    while num <= 9:
        key = _prompt_key(num)
        if not key:
            break
        key = key.replace(" ", "")
        if len(key) < 15:
            print(f"  {y('[!]')}  Too short\n"); continue
        if key in keys:
            print(f"  {y('[!]')}  Already saved\n"); continue
        keys.append(key)
        _write_keys(keys)
        print(f"  {g('[OK]')}  Key #{num} saved to .env\n")
        num += 1
        if num > 9:
            print(f"  {dim('  Maximum 9 keys reached.')}"); break
        ans = input(f"  {CY}>>>{R} Add another? [y/N]: ").strip().lower()
        if ans != "y":
            break

    print(f"\n  {g('[DONE]')}  Total keys in .env: {len(_load_keys())}")

def uninstall():
    """Wipe everything: .venv, .env, agent2.db, __pycache__, and global command"""
    banner()
    print(f"  {r('[ WARNING ]')}  {w('This will delete all keys, data, the environment, and global commands.')}")
    try:
        ans = input(f"  {CY}>>>{R} Are you absolutely sure? [y/N]: ").strip().lower()
    except KeyboardInterrupt:
        print(f"\n  {g('[OK]')}  Uninstall aborted.")
        return

    if ans != 'y':
        print(f"\n  {g('[OK]')}  Uninstall aborted.")
        return

    # Files to wipe
    to_delete = [VENV, ENV_FILE, ROOT / "agent2.db"]
    
    for path in to_delete:
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path, onerror=lambda func, p, _: (os.chmod(p, 0o777), func(p)))
                else:
                    path.unlink()
                print(f"  {g('[OK]')}  Deleted: {dim(path.name)}")
            except Exception as e:
                print(f"  {y('[!]')}  Could not delete {path.name}: {e}")

    # Clean up global command
    bin_dir = Path.home() / ".local" / "bin"
    if IS_WIN and not bin_dir.exists():
        import site
        bin_dir = Path(site.getuserbase()) / "Scripts"
    
    for cmd in ["agent2", "agent2.bat"]:
        cmd_path = bin_dir / cmd
        if cmd_path.exists():
            try:
                cmd_path.unlink()
                print(f"  {g('[OK]')}  Deleted global command: {dim(cmd)}")
            except Exception:
                pass

    # Clean up python caches
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

    print(f"\n  {MG}{B}Agent2 has been fully uninstalled.{R}\n")
    sys.exit(0)

# ── Step 5: Optional security tools ───────────────────────────────────────────
def check_tools():
    print(f"\n  {w('[ Optional Security Tools ]')}\n")
    tool_hints = {
        "nmap":    ("nmap",                 "brew install nmap",        "sudo apt install nmap"),
        "nikto":   ("nikto",               "brew install nikto",       "sudo apt install nikto"),
        "gobuster":("gobuster",            "brew install gobuster",    "sudo apt install gobuster"),
        "sqlmap":  ("sqlmap",              "pip install sqlmap",       "pip install sqlmap"),
        "hydra":   ("hydra",               "brew install hydra",       "sudo apt install hydra"),
    }
    for tool, (win, mac, linux) in tool_hints.items():
        if shutil.which(tool):
            print(f"  {g('[OK]')}  {tool}")
        else:
            hint = win if IS_WIN else (mac if IS_MAC else linux)
            print(f"  {y('[!]')}  {tool} {dim('not found')}  →  {dim(hint)}")

# ── Step 5b: Global Command ───────────────────────────────────────────────────
def install_global_command():
    print(f"\n  {w('[ Global Command ]')}\n")
    bin_dir = Path.home() / ".local" / "bin"
    if IS_WIN and not bin_dir.exists():
        import site
        bin_dir = Path(site.getuserbase()) / "Scripts"
    
    try:
        bin_dir.mkdir(parents=True, exist_ok=True)
        run_path = ROOT / "run.py"
        
        if IS_WIN:
            cmd_path = bin_dir / "agent2.bat"
            content = f'@echo off\nif "%~1"=="" (\n    "{sys.executable}" "{run_path}" --cli\n) else (\n    "{sys.executable}" "{run_path}" %*\n)\n'
            cmd_path.write_text(content, encoding="utf-8")
        else:
            cmd_path = bin_dir / "agent2"
            content = f'#!/usr/bin/env bash\nif [ $# -eq 0 ]; then\n    "{sys.executable}" "{run_path}" --cli\nelse\n    "{sys.executable}" "{run_path}" "$@"\nfi\n'
            cmd_path.write_text(content, encoding="utf-8")
            cmd_path.chmod(0o755)
            
        print(f"  {g('[OK]')}  Command installed: {c('agent2')} {dim('(' + str(cmd_path) + ')')}")
        print(f"         {dim('(Ensure this directory is in your PATH)')}")
    except Exception as e:
        print(f"  {y('[!]')}  Failed to install global command: {e}")

# ── Step 6: Launch ─────────────────────────────────────────────────────────────
def launch_web():
    print(f"\n  {CY}{'═' * 46}{R}")
    print(f"  {g('>>>')}  Starting Agent2 Web UI ...")
    print(f"  {c('>>>')}  {w('http://localhost:1311')}")
    print(f"  {dim('       Ctrl+C to stop')}")
    print(f"  {CY}{'═' * 46}{R}\n")
    try:
        subprocess.run([str(VENV_PY), str(APP_WEB)])
    except KeyboardInterrupt:
        print(f"\n  {dim('Stopped.')}")

def launch_cli():
    if not APP_CLI.exists():
        print(r(f"\n  [ERR]  agent2cli.py not found at {APP_CLI}"))
        print(f"  {dim('  Place agent2cli.py in the same folder as run.py.')}")
        sys.exit(1)
    print(f"\n  {CY}{'═' * 46}{R}")
    print(f"  {g('>>>')}  Starting Agent2 CLI ...")
    print(f"  {dim('       Type /help for commands  |  Ctrl+C to exit')}")
    print(f"  {CY}{'═' * 46}{R}\n")
    try:
        subprocess.run([str(VENV_PY), str(APP_CLI)])
    except KeyboardInterrupt:
        print(f"\n  {dim('Stopped.')}")

# ── Main ───────────────────────────────────────────────────────────────────────
def show_help():
    banner()
    print(f"  {w('Usage:')}  python run.py [options]\n")
    print(f"  {c('--web')}       Setup + Start Web UI (default)")
    print(f"  {c('--cli')}       Setup + Start CLI Agent")
    print(f"  {c('--addapi')}    Add a new Gemini API key")
    print(f"  {c('--reset')}     Wipe .venv and reinstall packages")
    print(f"  {c('--uninstall')} Full cleanup (deletes DB, .env, and .venv)")
    print(f"  {c('--help, -h')}  Show this help menu\n")
    sys.exit(0)

def main():
    args = sys.argv[1:]
    
    # ── Command Handlers ─────────────────────────────────────────────────────
    if "--help" in args or "-h" in args:
        show_help()
    
    if "--uninstall" in args:
        uninstall()

    do_reset  = "--reset"  in args
    do_addapi = "--addapi" in args
    do_cli    = "--cli"    in args
    do_web    = "--web"    in args

    # ── Setup Sequence ───────────────────────────────────────────────────────
    banner()
    check_python()
    ensure_venv(do_reset)
    mode = "all"
    if do_cli:
        mode = "cli"
    elif do_web:
        mode = "web"

    install_deps(mode)
    
    if do_addapi:
        ensure_keys(force_add=True)
        return

    ensure_keys()
    check_tools()
    install_global_command()

    # ── Mode Selection ───────────────────────────────────────────────────────
    if do_cli:
        launch_cli()
    elif do_web:
        launch_web()
    else:
        # Normal mode: Interactive selection with 10s timeout
        print(f"\n  {w('[ Select Mode ]')}  {dim('(Default: Web UI in 10s)')}")
        print(f"  {g('1.')}  Agent2 Web UI  {c('[Default]')}")
        print(f"  {g('2.')}  Agent2 CLI")
        print(f"  {g('3.')}  Exit")
        
        user_choice = [None]
        def get_input():
            try:
                user_choice[0] = input(f"\n  {CY}>>>{R} Choice [1-3]: ").strip()
            except EOFError: pass

        # Start input thread
        input_thread = threading.Thread(target=get_input, daemon=True)
        input_thread.start()
        
        # Wait 10 seconds
        input_thread.join(timeout=10.0)

        choice = user_choice[0]
        
        if choice is None:
            print(f"\n  {y('[timeout]')}  No response. Launching {g('Web UI')}...")
            time.sleep(1)
            launch_web()
        elif choice == '1':
            launch_web()
        elif choice == '2':
            launch_cli()
        elif choice == '3':
            print(f"\n  {dim('Goodbye.')}")
            sys.exit(0)
        else:
            print(f"\n  {y('[!]')}  Invalid choice. Defaulting to {g('Web UI')}...")
            launch_web()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  \033[2mStopped by user (Ctrl+C).\033[0m")
        sys.exit(0)
