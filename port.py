import os
import re
import sys
import time
import json
import shutil
import subprocess
import requests
import webbrowser
import winreg
import ctypes
import urllib.parse
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# 1. NATIVE WIN32 HARDWARE HOOKS
# ─────────────────────────────────────────────────────────────
sys.coinit_flags = 2  
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

try:
    import psutil
except ImportError:
    psutil = None

VK_MAP = {
    "win": 0x5B, "winleft": 0x5B, "winright": 0x5C,
    "ctrl": 0x11, "ctrlleft": 0x11, "ctrlright": 0x11,
    "alt": 0x12, "altleft": 0x12, "altright": 0x12,
    "shift": 0x10, "shiftleft": 0x10, "shiftright": 0x10,
    "enter": 0x0D, "return": 0x0D,
    "tab": 0x09, "space": 0x20, "esc": 0x1B, "escape": 0x1B,
    "backspace": 0x08, "delete": 0x2E, "del": 0x2E,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
    "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B
}

def win32_key_down(vk_code: int): user32.keybd_event(vk_code, 0, 0, 0)
def win32_key_up(vk_code: int): user32.keybd_event(vk_code, 0, 2, 0)
def win32_tap_key(vk_code: int):
    win32_key_down(vk_code)
    time.sleep(0.01)
    win32_key_up(vk_code)

def win32_send_hotkey(keys_str: str):
    keys = [k.strip().lower() for k in keys_str.split(",")]
    vk_sequence = []
    for k in keys:
        if k in VK_MAP:
            vk_sequence.append(VK_MAP[k])
        elif len(k) == 1:
            vk = user32.VkKeyScanW(ord(k)) & 0xFF
            vk_sequence.append(vk)

    for vk in vk_sequence:
        win32_key_down(vk)
        time.sleep(0.02)
    time.sleep(0.03)
    for vk in reversed(vk_sequence):
        win32_key_up(vk)
        time.sleep(0.02)

def win32_type_text(text: str):
    tokens = re.split(r'(\{[^}]+\})', text)
    for token in tokens:
        if not token: continue
        if token.startswith('{') and token.endswith('}'):
            key_name = token[1:-1].lower()
            if key_name in VK_MAP:
                win32_tap_key(VK_MAP[key_name])
                time.sleep(0.03)
        else:
            for char in token:
                res = user32.VkKeyScanW(ord(char))
                vk = res & 0xFF
                shift = (res >> 8) & 1
                if shift: win32_key_down(0x10)
                win32_tap_key(vk)
                if shift: win32_key_up(0x10)
                time.sleep(0.01)

# ─────────────────────────────────────────────────────────────
# 2. CONFIGURATION & MEMORY ENGINE
# ─────────────────────────────────────────────────────────────
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_CHAT_API = "http://localhost:11434/api/chat"

LAUNCH_TOOLS = ["open-app", "app-launcher", "launch-app", "app_launch"]
TYPING_TOOLS = ["type", "type-into-active-window", "type-text", "write-text", "ui_key_type"]
MESSAGE_TOOLS = ["message", "msg", "reply"]

CHAT_LOG_FILE = "Chat.txt"
MODEL_CONFIG_FILE = "model_config.json"
ACTIVE_SESSION_ID = None

def get_next_session_id() -> int:
    """Reads Chat.txt to find the highest session ID and returns the next available."""
    if not os.path.exists(CHAT_LOG_FILE):
        return 1
    with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    ids = re.findall(r'^(\d+)>', content, re.MULTILINE)
    if not ids:
        return 1
    return max(map(int, ids)) + 1

def log_chat_header(session_id: int, title: str):
    """Appends a new session header to Chat.txt"""
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%H:%M:%S")
    entry = f"{session_id}>{title}@{date_str}/\\{time_str}\n"
    with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def log_chat_message(session_id: int, role: str, message: str):
    """Logs a message to Chat.txt using JSON encoding."""
    entry = f"{session_id}>>{role}: {json.dumps(message, ensure_ascii=False)}\n"
    with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def _decode_logged_message(raw: str) -> str:
    """Decodes a message body written by log_chat_message."""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw.strip('"').replace(' \\n ', '\n')

def get_recent_messages(session_id: int, limit: int = 8) -> list:
    """Parses Chat.txt into a native Ollama message history array."""
    if not os.path.exists(CHAT_LOG_FILE):
        return []
    
    with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    messages = []
    prefix = f"{session_id}>>"
    
    for line in lines:
        if line.startswith(prefix):
            content_str = line[len(prefix):].rstrip("\n")
            
            if content_str.startswith("User:"):
                msg = _decode_logged_message(content_str[5:])
                messages.append({"role": "user", "content": msg})
                
            elif content_str.startswith("AI:"):
                msg = _decode_logged_message(content_str[3:])
                messages.append({"role": "assistant", "content": msg})
                
    return messages[-limit:]

def get_all_sessions() -> list:
    """Reads Chat.txt and returns all recorded sessions (supports legacy headers)."""
    if not os.path.exists(CHAT_LOG_FILE):
        return []
    sessions = []
    with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r'^(\d+)>(?!>)([^@\n]+)(?:@(.*))?$', line.strip())
            if match:
                sess_id = int(match.group(1))
                title = match.group(2).strip() or f"Session {sess_id}"
                timestamp = match.group(3).strip() if match.group(3) else "Legacy Session"
                sessions.append({
                    "id": sess_id,
                    "title": title,
                    "timestamp": timestamp
                })
    return sessions

def rename_session(session_id: int, new_title: str):
    """Updates the title of a specific session in Chat.txt."""
    if not os.path.exists(CHAT_LOG_FILE):
        return
    with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    updated_lines = []
    prefix = f"{session_id}>"
    for line in lines:
        # Match session header like "1>Old Title@24/08/2026/\10:30:00"
        if line.startswith(prefix) and not line.startswith(f"{session_id}>>"):
            parts = line.strip().split("@", 1)
            timestamp = f"@{parts[1]}" if len(parts) > 1 else ""
            updated_lines.append(f"{session_id}>{new_title.strip()}{timestamp}\n")
        else:
            updated_lines.append(line)
            
    with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

def delete_session(session_id: int):
    """Deletes a session header and all associated messages from Chat.txt."""
    if not os.path.exists(CHAT_LOG_FILE):
        return
    with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    header_prefix = f"{session_id}>"
    msg_prefix = f"{session_id}>>"
    
    updated_lines = [
        line for line in lines
        if not (line.startswith(header_prefix) or line.startswith(msg_prefix))
    ]
    
    with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

def get_session_history(session_id: int) -> list:
    """Returns all messages for a specific session as [(sender, text), ...]."""
    if not os.path.exists(CHAT_LOG_FILE):
        return []
    history = []
    prefix = f"{session_id}>>"
    with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith(prefix):
                content_str = line[len(prefix):].rstrip("\n")
                if content_str.startswith("User:"):
                    msg = _decode_logged_message(content_str[5:])
                    history.append(("user", msg))
                elif content_str.startswith("AI:"):
                    msg = _decode_logged_message(content_str[3:])
                    history.append(("mist", msg))
    return history

def save_last_model(tag: str, title: str):
    """Persists the most recently selected model so it survives app restarts."""
    try:
        with open(MODEL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"tag": tag, "title": title}, f)
    except Exception as e:
        print(f"[⚠️] Could not save last model: {e}")

def load_last_model() -> dict | None:
    """Returns {'tag': ..., 'title': ...} for the last used model, or None."""
    if not os.path.exists(MODEL_CONFIG_FILE):
        return None
    try:
        with open(MODEL_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and data.get("tag"):
                return data
    except Exception as e:
        print(f"[⚠️] Could not load last model: {e}")
    return None

# ─────────────────────────────────────────────────────────────
# 3. DETACHED BROWSER & SYSTEM HELPERS
# ─────────────────────────────────────────────────────────────
def find_chrome_path() -> str | None:
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
        if os.path.exists(p): return p
    return None

def launch_chrome_detached(url: str) -> str:
    chrome_path = find_chrome_path()
    if not chrome_path:
        webbrowser.open(url)
        return f"Chrome not found; opened {url} in default browser."
    clean_env = {k: v for k, v in os.environ.items() if k.upper() not in ("PYTHONPATH", "PYTHONHOME")}
    try:
        subprocess.Popen(
            [chrome_path, "--new-window", url],
            close_fds=True,
            creationflags=0x00000008 | 0x00000200 | 0x08000000 | 0x01000000,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=clean_env, cwd=os.path.dirname(chrome_path),
        )
        return f"Opened {url} in Chrome (detached)"
    except Exception as e:
        return f"Error launching Chrome: {e}"

def sanitize_cmd(command: str) -> str:
    command = os.path.expandvars(command.strip())
    command = re.sub(r'\\+["\']?(https?://)', r'\1', command)
    command = re.sub(r'(https?://[^\s"\']+)\\+["\']?', r'\1"', command)
    if command.lower().startswith("start ") and '""' not in command:
        parts = command.split(" ", 1)
        command = f'{parts[0]} "" {parts[1]}'
    return command

# ─────────────────────────────────────────────────────────────
# 4. MASTER TOOL DISPATCHER
# ─────────────────────────────────────────────────────────────
def execute_tool(tool: str, head: str, value: str) -> str:
    global ACTIVE_SESSION_ID
    tool = tool.lower().strip()
    head = (head or "").lower().strip()
    value = os.path.expandvars(value.strip())

    print(f"\n[🛠️ TOOL TRIGGERED] Name: '{tool}' | Head: '{head}' | Payload: '{value[:60]}...'")

    try:
        if tool == "generate-head":
            log_chat_header(ACTIVE_SESSION_ID, value)
            return f"Session title set to: {value}"

        elif tool in MESSAGE_TOOLS:
            return value

        elif tool == "canvas":
            return "Rendered to UI Canvas."

        elif tool == "verify_step":
            if head == "process_exists":
                output = subprocess.getoutput(f'tasklist /FI "IMAGENAME eq {value}"')
                return f"Process '{value}' running = {value.lower() in output.lower()}"
            elif head == "file_exists":
                return f"Path '{value}' exists = {os.path.exists(value)}"
            return "Verification complete."

        elif tool in ["cmd_exec"] or tool in LAUNCH_TOOLS:
            clean_command = sanitize_cmd(value)
            timeout_match = re.search(r'timeout\s+(?:/t\s+)?(\d+)', clean_command, re.IGNORECASE)
            if timeout_match:
                secs = int(timeout_match.group(1))
                time.sleep(secs)
                return f"Waited {secs} seconds."

            if url_match := re.search(r'(https?://[^\s]+)', clean_command, re.IGNORECASE):
                raw_url = url_match.group(1).rstrip('"\'\\')
                if "chrome" in clean_command.lower():
                    return launch_chrome_detached(raw_url)
                webbrowser.open(raw_url)
                return f"Opened {raw_url} in browser"

            if clean_command.lower().startswith("start "):
                subprocess.Popen(clean_command, shell=True)
                return f"Launched process cleanly: {clean_command}"

            res = subprocess.run(clean_command, shell=True, capture_output=True, text=True)
            return res.stdout if res.returncode == 0 else f"Error: {res.stderr}"

        elif tool == "powershell_exec":
            res = subprocess.run(["powershell", "-NoProfile", "-Command", value], capture_output=True, text=True)
            return res.stdout if res.returncode == 0 else f"PowerShell Error: {res.stderr}"

        elif tool == "proc_list":
            if head == "filter" and value != "none":
                return subprocess.getoutput(f'tasklist /FI "IMAGENAME eq *{value}*" /FO TABLE /NH')[:2500]
            return subprocess.getoutput("tasklist /FO TABLE /NH")[:2500]
            
        elif tool == "proc_kill":
            flag = "/PID" if value.isdigit() else "/IM"
            return subprocess.getoutput(f"taskkill /F {flag} {value}")

        elif tool == "sys_cpu":
            if psutil: return f"CPU: {psutil.cpu_percent(interval=0.5)}% across {psutil.cpu_count(logical=True)} cores"
            return subprocess.getoutput("wmic cpu get LoadPercentage")
            
        elif tool == "sys_ram":
            if psutil: 
                r = psutil.virtual_memory()
                return f"RAM: {r.percent}% ({r.used // (1024**2)}MB / {r.total // (1024**2)}MB)"
            return subprocess.getoutput("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value")
            
        elif tool == "sys_gpu":
            res = subprocess.getoutput("nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader")
            if "not recognized" in res or "error" in res.lower():
                res = subprocess.getoutput("wmic path win32_VideoController get name")
            return res
            
        elif tool == "sys_disk":
            target = value if value and ":" in value else "C:"
            if psutil:
                u = psutil.disk_usage(target)
                return f"Disk {target} Used: {u.percent}% | Free: {u.free // (1024**3)}GB / {u.total // (1024**3)}GB"
            return subprocess.getoutput(f"fsutil volume diskfree {target}")

        elif tool == "sys_power":
            if value == "lock": user32.LockWorkStation(); return "Workstation locked."
            elif value == "sleep": os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"); return "Sleeping."
            elif value == "restart": os.system("shutdown /r /t 5"); return "Restarting in 5s."
            elif value == "shutdown": os.system("shutdown /s /t 5"); return "Shutting down in 5s."
            return f"Unknown power command: {value}"

        elif tool == "fs_read":
            if os.path.exists(value):
                with open(value, "r", encoding="utf-8", errors="ignore") as f: return f.read()[:5000]
            return f"Error: File '{value}' not found."
            
        elif tool in ["fs_write", "fs_append"]:
            mode = "a" if tool == "fs_append" else "w"
            path, content = value.split("|", 1) if "|" in value else (value, "")
            path = os.path.expandvars(path.strip())
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, mode, encoding="utf-8") as f: f.write(content.lstrip())
            return f"File operation successful: {path}"
            
        elif tool == "fs_delete":
            if os.path.isfile(value): os.remove(value); return f"Deleted file: {value}"
            elif os.path.isdir(value): shutil.rmtree(value); return f"Deleted directory: {value}"
            return f"Target '{value}' does not exist."
            
        elif tool == "fs_list":
            target = value if value and value != "none" else "."
            return "\n".join(os.listdir(target)[:100]) if os.path.exists(target) else f"Dir '{target}' not found."
            
        elif tool in ["fs_move", "fs_copy"]:
            src, dst = [os.path.expandvars(x.strip()) for x in value.split("|", 1)]
            if tool == "fs_move": shutil.move(src, dst)
            elif os.path.isdir(src): shutil.copytree(src, dst)
            else: shutil.copy(src, dst)
            return f"{'Moved' if tool == 'fs_move' else 'Copied'} {src} to {dst}"
            
        elif tool == "fs_find":
            root_dir, pattern = value.split("|", 1) if "|" in value else (".", value)
            root_dir = os.path.expandvars(root_dir.strip())
            matches = [os.path.join(r, f) for r, _, fs in os.walk(root_dir) for f in fs if pattern.strip().replace("*", "") in f][:20]
            return "\n".join(matches) if matches else "No matching files found."

        elif tool == "reg_read":
            hive_str, rest = value.split("\\", 1); subkey, val_name = rest.rsplit("|", 1)
            hives = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}
            with winreg.OpenKey(hives.get(head.upper(), winreg.HKEY_CURRENT_USER), subkey) as k:
                val, _ = winreg.QueryValueEx(k, val_name)
                return f"Reg Value [{val_name}]: {val}"
                
        elif tool == "reg_write":
            key_path, val_name, val_data = value.split("|", 2)
            return subprocess.getoutput(f'reg add "{key_path}" /v "{val_name}" /d "{val_data}" /f')

        elif tool == "ui_screen":
            out_file = value if value and value != "auto" else "ultron_screenshot.png"
            out_file = os.path.expandvars(out_file)
            return subprocess.getoutput(f'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\'{{PRTSC}}\')"')

        elif tool in TYPING_TOOLS:
            win32_type_text(value)
            return f"Injected keys: {value}"

        elif tool == "ui_hotkey":
            win32_send_hotkey(value)
            return f"Triggered native hotkey: {value}"

        elif tool == "ui_window_list":
            cmd = 'Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object Id, ProcessName, MainWindowTitle | Format-Table -AutoSize'
            return subprocess.getoutput(f'powershell -NoProfile -Command "{cmd}"')
            
        elif tool == "ui_window_focus":
            cmd = f"$w=Get-Process|Where-Object {{$_.MainWindowTitle -like '*{value}*'}} | Select-Object -First 1; if ($w) {{(New-Object -ComObject WScript.Shell).AppActivate($w.Id)}}"
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd])
            return f"Focused window matching: {value}"

        elif tool == "media_volume":
            def tap_vk(code): user32.keybd_event(code, 0, 0, 0); user32.keybd_event(code, 0, 2, 0)
            if head == "mute" or "mute" in value.lower(): tap_vk(0xAD); return "Mute toggled."
            elif head in ["up", "down"]:
                vk = 0xAF if head == "up" else 0xAE
                steps = max(1, int(re.search(r'\d+', value).group(0))) if re.search(r'\d+', value) else 5
                for _ in range(steps // 2 or 1): tap_vk(vk); time.sleep(0.02)
                return f"Volume {head} by {steps}%."
            elif head == "set" or value.isdigit():
                target = max(0, min(100, int(re.search(r'\d+', value).group(0)) if re.search(r'\d+', value) else 50))
                for _ in range(50): tap_vk(0xAE)
                time.sleep(0.05)
                for _ in range(target // 2): tap_vk(0xAF); time.sleep(0.01)
                return f"Master volume set to ~{target}%."
            return f"Volume command: {head} {value}"

        elif tool == "media_key":
            vk = {"playpause": 0xB3, "play": 0xB3, "pause": 0xB3, "nexttrack": 0xB0, "prevtrack": 0xB1, "stop": 0xB2}.get(value.lower().strip(), 0xB3)
            user32.keybd_event(vk, 0, 0, 0); user32.keybd_event(vk, 0, 2, 0)
            return f"Triggered media key: {value}"

        elif tool == "net_ping":
            return subprocess.getoutput(f"ping -n 3 {value}")

        elif tool == "web_open":
            clean_url = value.strip('\"\'\\ ')
            return launch_chrome_detached(clean_url) if head == "chrome" else webbrowser.open(clean_url)

        elif tool == "automation":
            return f"Automation signal: {head} ({value})"

        else:
            return f"Unknown tool '{tool}'"

    except Exception as e:
        err = f"Execution Error in '{tool}': {str(e)}"
        print(f"[❌] {err}")
        return err

# ─────────────────────────────────────────────────────────────
# 5. PROTOCOL PARSER
# ─────────────────────────────────────────────────────────────
def execute_protocol(ai_text: str):
    pattern = r'[/\\]{2,4}tool=["\']([^"\']+)["\'](?:\s+head=["\']([^"\']*)["\'])?\s+value=["\']((?:[^"\'\\]|\\.)*)["\']'
    commands = re.findall(pattern, ai_text, re.DOTALL | re.IGNORECASE)

    if not commands:
        return []

    results = []
    for tool, head, value in commands:
        clean_val = value.replace('\\"', '"').replace('\\\\', '\\').strip()

        res = execute_tool(tool, head, clean_val)
        results.append((tool, res))

        # Pacing Engine
        tool_lower = tool.lower()
        if tool_lower in LAUNCH_TOOLS:
            time.sleep(1.5)
        elif tool_lower in ["cmd_exec", "powershell_exec"]:
            if "timeout" not in clean_val.lower():
                time.sleep(0.5)
        elif tool_lower == "ui_hotkey":
            time.sleep(0.4)
        elif tool_lower in TYPING_TOOLS:
            if "{enter}" in clean_val.lower():
                time.sleep(1.0)
            else:
                time.sleep(0.3)
        else:
            time.sleep(0.2)

    return results

# ─────────────────────────────────────────────────────────────
# 6. THE MASE PIPELINE (SEARCH & EVALUATION)
# ─────────────────────────────────────────────────────────────
def mase_evaluate(prompt: str) -> str:
    """Asks the MASE model if a web search is needed."""
    payload = {
        "model": "MASE",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0} # Zero temp for strict keyword generation
    }
    try:
        res = requests.post(OLLAMA_API, json=payload, timeout=10).json()
        response = res.get("response", "").strip()
        if "NULL?" in response or not response:
            return "NULL?"
        return response
    except Exception as e:
        print(f"[⚠️] MASE Evaluation Error: {e}")
        return "NULL?"

def perform_web_search(query: str) -> str:
    """Built-in lightweight web scraper using DuckDuckGo HTML."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        safe_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={safe_query}"
        res = requests.get(url, headers=headers, timeout=5)
        
        # Scrape snippets from search results
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', res.text, re.IGNORECASE | re.DOTALL)
        if snippets:
            # Clean HTML tags and join top 3 results
            clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]
            return " | ".join(clean_snippets).replace('"', "'")
        return "No relevant search results found."
    except Exception as e:
        print(f"[⚠️] Web Search Error: {e}")
        return "Search failed."

# ─────────────────────────────────────────────────────────────
# 7. EXECUTION BRIDGES & UI CONNECTORS
# ─────────────────────────────────────────────────────────────
def query_mist(prompt: str, model_name: str = "7K", session_id: int = None):
    """Entry point for the UI: Intercepts via MASE, fetches context, and calls 7K."""
    global ACTIVE_SESSION_ID
    
    if session_id is not None:
        ACTIVE_SESSION_ID = session_id
    elif ACTIVE_SESSION_ID is None:
        ACTIVE_SESSION_ID = get_next_session_id()
        
    session_id = ACTIVE_SESSION_ID
    
    # 1. THE MASE INTERCEPT
    print(f"\n[🧠] MASE evaluating prompt...")
    mase_query = mase_evaluate(prompt)
    search_data = "NULL?"
    
    if mase_query != "NULL?":
        print(f"[🔍] MASE Triggered Search: {mase_query}")
        search_data = perform_web_search(mase_query)
        print(f"[✅] Search Results Acquired.")
    else:
        print(f"[⚡] MASE Bypassed (Local Execution).")

    # 2. Format payload for 7K
    formatted_prompt = f'search="{search_data}" query="{prompt}"'
    
    messages = get_recent_messages(session_id, limit=8)
    
    # Log the CLEAN prompt to the UI history so the chat looks normal
    log_chat_message(session_id, "User", prompt)
    
    if not messages:
        formatted_prompt += "\n\n[SYSTEM] NEW CHAT. Output generate-head first."
        
    messages.append({"role": "user", "content": formatted_prompt})
    
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "num_predict": 2048,
            "temperature": 0.1
        }
    }

    print(f"\n[DIAGNOSTIC] Session {session_id} Final Payload to {model_name}:\n{formatted_prompt}\n")

    try:
        res = requests.post(OLLAMA_CHAT_API, json=payload, timeout=None).json()
        ai_reply = res.get("message", {}).get("content", "")
    except Exception as e:
        return f"API Error: {e}"
        
    log_chat_message(session_id, "AI", ai_reply)
    
    # Execute the background OS macros
    execute_protocol(ai_reply)
    
    # Return RAW AI text so home.py can parse canvas and messages itself
    return ai_reply

def run_macro_session(initial_prompt: str, model_name: str = "7K", session_id: int = None):
    """Terminal/CLI fallback testing loop."""
    print(f"\n[🚀 STARTING MACRO TEST]")
    result = query_mist(initial_prompt, model_name, session_id)
    print(f"\n[UI OUTPUT]: {result}")
    return result

def stop_model(model_name: str = "7K"):
    """Flushes model weights from VRAM."""
    print(f"[🛑] Flushing '{model_name}' from VRAM...")
    try:
        requests.post(OLLAMA_API, json={"model": model_name, "keep_alive": 0}, timeout=5)
    except Exception as e:
        print(f"[⚠️] Could not flush VRAM: {e}")

if __name__ == "__main__":
    run_macro_session("What is the current price of Bitcoin?", session_id=1)
