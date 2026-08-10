import os
import re
import sys
import time
import shutil
import subprocess
import requests
import webbrowser
import winreg

# --- OPTIONAL / ADVANCED DEPENDENCIES (Graceful Fallbacks) ---
try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import psutil
except ImportError:
    psutil = None

# --- CONFIGURATION ---
OLLAMA_API = "http://localhost:11434/api/generate"

# --- ALIAS GROUPS (Backwards Compatibility) ---
LAUNCH_TOOLS = ["open-app", "app-launcher", "launch-app"]
TYPING_TOOLS = ["type", "type-into-active-window", "type-text", "write-text"]
MESSAGE_TOOLS = ["message", "msg", "reply"]


# ─────────────────────────────────────────────────────────────
# CHROME DETACHED LAUNCHER
# ─────────────────────────────────────────────────────────────
def find_chrome_path() -> str | None:
    """Locate chrome.exe reliably via the registry App Paths key, falling back to common install dirs."""
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
    ]
    for hive, subkey in reg_paths:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                path, _ = winreg.QueryValueEx(key, None)
                if path and os.path.exists(path):
                    return path
        except FileNotFoundError:
            continue

    fallbacks = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in fallbacks:
        if os.path.exists(p):
            return p
    return None


def launch_chrome_detached(url: str) -> str:
    """Launches Chrome as a fully detached process, immune to console/job inheritance and pipe issues."""
    chrome_path = find_chrome_path()
    if not chrome_path:
        return "Error: chrome.exe not found on this system."

    # Strip PYTHONPATH/PYTHONHOME/VIRTUAL_ENV etc. so Chrome doesn't inherit
    # anything that could make it think it's a dev/test invocation.
    clean_env = {
        k: v for k, v in os.environ.items()
        if k.upper() not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHONSTARTUP")
    }

    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    CREATE_BREAKAWAY_FROM_JOB = 0x01000000  # escapes the parent's job object if one exists

    try:
        subprocess.Popen(
            [chrome_path, "--new-window", url],  # list form: no shell/quoting issues
            close_fds=True,
            creationflags=(
                DETACHED_PROCESS
                | CREATE_NEW_PROCESS_GROUP
                | CREATE_NO_WINDOW
                | CREATE_BREAKAWAY_FROM_JOB
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=clean_env,
            cwd=os.path.dirname(chrome_path),
        )
        return f"Opened {url} in Chrome (detached)"
    except Exception as e:
        return f"Error launching Chrome: {e}"


def sanitize_cmd(command: str) -> str:
    """
    Cleans URL formatting issues for Chrome/browsers WITHOUT stripping
    general backslashes or quotes needed for Windows file paths/scripts.
    """
    command = command.strip()

    # Target ONLY escaped/malformed URL prefixes like \"https:// or \https://
    # Fixes the leading slash/quote in front of http:// or https://
    command = re.sub(r'\\+["\']?(https?://)', r'\1', command)

    # Fixes any trailing backslash-quotes right after the URL
    command = re.sub(r'(https?://[^\s"\']+)\\+["\']?', r'\1"', command)

    # Fix Windows 'start' command when opening URLs or browser targets
    # Converts: start chrome "https://..." -> start "" chrome "https://..."
    if command.lower().startswith("start ") and '""' not in command:
        parts = command.split(" ", 1)
        command = f'{parts[0]} "" {parts[1]}'

    return command


def execute_tool(tool: str, head: str, value: str) -> str:
    """Executes the specific tool action and returns execution feedback."""
    tool = tool.lower().strip()
    head = (head or "").lower().strip()
    value = value.strip()

    print(f"\n[🛠️ TOOL TRIGGERED] Name: '{tool}' | Head: '{head}'")

    try:
        # ─────────────────────────────────────────────────────────────
        # 1. SYSTEM & OS (8 Tools)
        # ─────────────────────────────────────────────────────────────
        if tool in ["cmd_exec"] or tool in LAUNCH_TOOLS:
            clean_command = sanitize_cmd(value)

            # 1. BULLETPROOF WEB INTERCEPTOR
            url_match = re.search(r'(https?://[^\s]+)', clean_command, re.IGNORECASE)

            if url_match:
                raw_url = url_match.group(1)
                # Strip out trailing garbage
                target_url = re.sub(r'[\"\'\\]+$', '', raw_url).strip('\"\'')
                print(f"[🌐] Intercepted Web URL: {target_url}")

                if "chrome" in clean_command.lower():
                    print("[🚀] Forcing launch in Google Chrome safely...")
                    return launch_chrome_detached(target_url)

                elif "edge" in clean_command.lower():
                    print("[🚀] Forcing launch in Microsoft Edge safely...")
                    try:
                        subprocess.Popen(
                            ["powershell", "-WindowStyle", "Hidden", "-Command",
                             f"Start-Process msedge -ArgumentList '{target_url}'"]
                        )
                        return f"Opened {target_url} in Edge"
                    except Exception:
                        webbrowser.open(target_url)
                        return f"Opened {target_url} via OS default fallback"

                else:
                    webbrowser.open(target_url)
                    return f"Opened {target_url} in default browser"

            # 2. FIRE-AND-FORGET LAUNCHER (For local apps like Explorer, Arduino, etc.)
            if clean_command.lower().startswith("start "):
                print(f"[🚀] Launching app in background: {clean_command}")
                subprocess.Popen(clean_command, shell=True)
                return f"Launched process cleanly: {clean_command}"

            # 3. STANDARD COMMAND EXECUTION (For terminal commands)
            print(f"[🚀] Executing CLI Command: {clean_command}")
            res = subprocess.run(clean_command, shell=True, capture_output=True, text=True, timeout=20)
            return res.stdout if res.returncode == 0 else f"Error: {res.stderr}"

        elif tool == "sys_cpu":
            if psutil:
                usage = f"CPU Usage: {psutil.cpu_percent(interval=1)}%"
            else:
                usage = subprocess.getoutput("wmic cpu get LoadPercentage")
            print(f"[💻] {usage}")
            return usage

        elif tool == "sys_ram":
            if psutil:
                ram = psutil.virtual_memory()
                ram_info = f"RAM Usage: {ram.percent}% ({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)"
            else:
                ram_info = "RAM stats unavailable (install psutil)."
            print(f"[🧠] {ram_info}")
            return ram_info

        elif tool == "sys_gpu":
            gpu_info = subprocess.getoutput("nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader")
            print(f"[🎮] GPU Info: {gpu_info}")
            return gpu_info

        elif tool == "proc_list":
            res = subprocess.getoutput("tasklist /FO TABLE /NH")
            print("[📋] Process list retrieved.")
            return res[:2000]  # Truncate to prevent context overload

        elif tool == "proc_kill":
            res = subprocess.getoutput(f"taskkill /F /PID {value}" if value.isdigit() else f"taskkill /F /IM {value}")
            print(f"[💥] Kill result: {res}")
            return res

        # ─────────────────────────────────────────────────────────────
        # 2. FILE SYSTEM (5 Tools)
        # ─────────────────────────────────────────────────────────────
        elif tool == "fs_read":
            if os.path.exists(value):
                with open(value, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                print(f"[📖] Read {len(content)} chars from {value}")
                return content[:4000]
            return f"Error: File '{value}' not found."

        elif tool in ["fs_write", "fs_append"]:
            mode = "a" if tool == "fs_append" else "w"
            if "|" in value:
                path, content = value.split("|", 1)
            else:
                path, content = value, ""
            path = path.strip()
            with open(path, mode, encoding="utf-8") as f:
                f.write(content.lstrip())
            print(f"[📝] Written to {path}")
            return f"Successfully wrote to {path}"

        elif tool == "fs_delete":
            if os.path.isfile(value):
                os.remove(value)
            elif os.path.isdir(value):
                shutil.rmtree(value)
            print(f"[🗑️] Deleted {value}")
            return f"Deleted {value}"

        elif tool == "fs_list":
            target = value if value and value.lower() != "null" else "."
            files = os.listdir(target)
            print(f"[📁] Directory listed: {len(files)} items")
            return "\n".join(files)

        # ─────────────────────────────────────────────────────────────
        # 3. NETWORK & WEB (3 Tools)
        # ─────────────────────────────────────────────────────────────
        elif tool == "net_ping":
            res = subprocess.getoutput(f"ping -n 4 {value}")
            print(f"[🌐] Ping finished for {value}")
            return res

        elif tool == "web_search":
            print(f"[🔍] Searching Web for: '{value}'...")
            try:
                resp = requests.get(f"https://html.duckduckgo.com/html/?q={value}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                matches = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                clean_snippets = [re.sub(r'<[^>]+>', '', m).strip() for m in matches[:5]]
                output = "\n---\n".join(clean_snippets) if clean_snippets else "No search results found."
                return output
            except Exception as e:
                return f"Search Failed: {e}"

        elif tool == "web_fetch":
            print(f"[🌐] Scraping Web URL: {value}")
            url = value.strip('\"\'\\ ')
            if not url.startswith("http"):
                url = "https://" + url
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            text_only = re.sub(r'<[^>]+>', ' ', resp.text)
            return " ".join(text_only.split())[:3000]

        # ─────────────────────────────────────────────────────────────
        # 4. AUTOMATION & UI (5 Tools)
        # ─────────────────────────────────────────────────────────────
        elif tool == "ui_window":
            res = subprocess.getoutput('powershell "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object MainWindowTitle"')
            return res

        elif tool == "ui_screen":
            if pyautogui:
                pyautogui.screenshot("ultron_screenshot.png")
                return "Screenshot captured and saved to ultron_screenshot.png"
            return "pyautogui module not available."

        elif tool == "ui_mouse_move":
            if pyautogui and "," in value:
                x, y = map(int, value.split(","))
                pyautogui.moveTo(x, y)
                return f"Mouse moved to {x},{y}"
            return "Invalid mouse coordinates or pyautogui missing."

        elif tool == "ui_mouse_click":
            if pyautogui:
                btn = head if head in ["left", "right", "middle"] else "left"
                pyautogui.click(button=btn)
                return f"Mouse clicked ({btn})"
            return "pyautogui missing."

        elif tool in ["ui_key_type"] or tool in TYPING_TOOLS:
            if pyautogui:
                print(f"[⌨️] Typing text into active window...")
                if "{ENTER}" in value.upper():
                    clean_text = re.sub(r'\{enter\}', '', value, flags=re.IGNORECASE)
                    pyautogui.write(clean_text, interval=0.01)
                    pyautogui.press("enter")
                else:
                    pyautogui.write(value, interval=0.01)
                return f"Typed: {value}"
            return "pyautogui missing."

        # ─────────────────────────────────────────────────────────────
        # 5. GIT & OUTPUT (4 Tools)
        # ─────────────────────────────────────────────────────────────
        elif tool == "git_status":
            repo_path = value if os.path.exists(value) else "."
            return subprocess.getoutput(f"git -C {repo_path} status")

        elif tool == "git_commit":
            return subprocess.getoutput(f'git commit -m "{value}"')

        elif tool == "canvas":
            print(f"\n[🎨 CANVAS RENDER ({head})]:\n{value}\n")
            return "Rendered to UI Canvas."

        elif tool in MESSAGE_TOOLS:
            print(f"\n[🤖 ULTRON]: {value}\n")
            return value

        else:
            print(f"[❓] IGNORED UNKNOWN TOOL: '{tool}' with value '{value[:30]}...'")
            return f"Unknown tool '{tool}'"

    except Exception as e:
        err_msg = f"Execution Error in tool '{tool}': {e}"
        print(f"[❌] {err_msg}")
        return err_msg


def execute_protocol(ai_text: str):
    """Parses tool calls from LLM response and executes them."""
    pattern = r'/\\/\\tool="([^"]+)"(?:\s+head="([^"]*)")?\s+value="((?:[^"\\]|\\.)*)"'
    commands = re.findall(pattern, ai_text, re.DOTALL)

    if not commands:
        print("[⚠️] No valid Hexuz/Ultron protocol commands found in response.")
        return []

    results = []
    for tool, head, value in commands:
        result = execute_tool(tool, head, value)
        results.append((tool, result))

    return results


def query_mist(prompt: str, model_name: str):
    print(f"\n[⏳] Routing prompt to '{model_name}'...")
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API, json=payload)
        response.raise_for_status()
        ai_text = response.json().get("response", "")

        print(f"\n--- RAW AI OUTPUT START ---\n{ai_text}\n--- RAW AI OUTPUT END ---\n")

        execute_protocol(ai_text)
        return ai_text
    except Exception as e:
        print(f"[❌] API Error: {e}")
        return f"Error: {e}"


def stop_model(model_name: str):
    """Unloads model from system VRAM/RAM instantly."""
    print(f"[🛑] Unloading '{model_name}' from memory...")
    try:
        requests.post(OLLAMA_API, json={"model": model_name, "keep_alive": 0})
    except Exception as e:
        print(f"[⚠️] Failed to unload model: {e}")