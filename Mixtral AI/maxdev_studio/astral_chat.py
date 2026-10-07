import os
import re
import sys
import time
import ctypes
import subprocess
import requests

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QLineEdit, QPushButton, QComboBox, QScrollArea, QWidget,
    QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QCursor, QColor

from astral_parser import parse_protocol

# Support running from root or from maxdev_studio directory
try:
    from click_delayer import install_click_delay
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from click_delayer import install_click_delay

# ═══════════════════════════════════════════════════════════════
# WIN32 INPUT AUTOMATION HOOKS
# ═══════════════════════════════════════════════════════════════
IS_WINDOWS = sys.platform.startswith("win")
user32 = ctypes.windll.user32 if IS_WINDOWS else None

VK_MAP = {
    "win": 0x5B, "ctrl": 0x11, "alt": 0x12, "shift": 0x10,
    "enter": 0x0D, "tab": 0x09, "space": 0x20, "esc": 0x1B,
    "backspace": 0x08, "delete": 0x2E, "up": 0x26, "down": 0x28,
    "left": 0x25, "right": 0x27, "f1": 0x70, "f2": 0x71
}

def win32_send_hotkey(keys_str: str):
    if not user32:
        return
    keys = [k.strip().lower() for k in keys_str.split(",")]
    vk_seq = [VK_MAP[k] for k in keys if k in VK_MAP]
    for vk in vk_seq:
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.02)
    time.sleep(0.04)
    for vk in reversed(vk_seq):
        user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.02)

def win32_type_text(text: str):
    if not user32:
        return
    tokens = re.split(r'(\{[^}]+\})', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('{') and token.endswith('}'):
            k = token[1:-1].lower()
            if k in VK_MAP:
                user32.keybd_event(VK_MAP[k], 0, 0, 0)
                time.sleep(0.02)
                user32.keybd_event(VK_MAP[k], 0, 2, 0)
        else:
            for char in token:
                res = user32.VkKeyScanW(ord(char))
                vk = res & 0xFF
                shift = (res >> 8) & 1
                if shift:
                    user32.keybd_event(0x10, 0, 0, 0)
                user32.keybd_event(vk, 0, 0, 0)
                time.sleep(0.01)
                user32.keybd_event(vk, 0, 2, 0)
                if shift:
                    user32.keybd_event(0x10, 0, 2, 0)
                time.sleep(0.01)


# ═══════════════════════════════════════════════════════════════
# WORKER THREAD
# ═══════════════════════════════════════════════════════════════
class AstralWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, prompt: str, messages: list, model_name: str):
        super().__init__()
        self.prompt = prompt
        self.messages = list(messages)
        self.model_name = model_name

    def run(self):
        self.messages.append({"role": "user", "content": self.prompt})
        payload = {
            "model": self.model_name,
            "messages": self.messages,
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 8192}
        }
        try:
            res = requests.post("http://localhost:11434/api/chat", json=payload, timeout=None).json()
            reply = res.get("message", {}).get("content", "")
        except Exception as e:
            reply = f'//tool="message" value="Connection error to local model: {e}"'
        self.finished.emit(reply)


# ═══════════════════════════════════════════════════════════════
# ASTRAL CHAT PANEL
# ═══════════════════════════════════════════════════════════════
class AstralChatPanel(QFrame):
    run_code_requested = pyqtSignal(str)
    file_create_requested = pyqtSignal(str)
    file_edit_requested = pyqtSignal(str, str)
    terminal_exec_requested = pyqtSignal(str)
    session_title_changed = pyqtSignal(str)

    def __init__(self, workspace_path: str = None):
        super().__init__()
        self.workspace_path = workspace_path or os.getcwd()
        self.worker = None
        self.chat_history = []
        self.first_message = True

        self.setStyleSheet("QFrame { background-color: #0A0A0C; border: 1px solid #1C1C21; border-radius: 8px; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Header Bar
        header = QHBoxLayout()
        title = QLabel("✨ Astral")
        title.setStyleSheet("color: #818CF8; font-size: 13px; font-weight: bold; border: none;")

        self.model_combo = QComboBox()
        self.model_combo.addItems(["Astral", "Astral-gemma"])
        self.model_combo.setFixedHeight(24)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #18181B; color: #FAFAFA;
                border: 1px solid #27272A; border-radius: 4px; padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #18181B; color: #FAFAFA; selection-background-color: #6366F1; }
        """)
        # Prevent click-through on dropdown
        install_click_delay(self.model_combo, delay_ms=150)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.model_combo)
        main_layout.addLayout(header)

        # Scrollable Chat Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area)

        # Input Controls
        input_container = QHBoxLayout()
        input_container.setSpacing(6)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask Astral about your workspace code...")
        self.input_box.setStyleSheet("QLineEdit { background-color: #121215; color: #FAFAFA; border: 1px solid #1F1F24; border-radius: 5px; padding: 6px 10px; font-size: 12px; } QLineEdit:focus { border: 1px solid #6366F1; }")
        self.input_box.returnPressed.connect(self.send_prompt)

        input_container.addWidget(self.input_box)
        main_layout.addLayout(input_container)

        self.append_chat("Astral Engine Active. Workspace files will be automatically included in context.", sender="system")

    def append_chat(self, text: str, sender: str = "astral"):
        bubble = QFrame()
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {'#18181B' if sender == 'user' else '#121215'};
                border: 1px solid {'#27272A' if sender == 'user' else '#1C1C21'};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(10, 8, 10, 8)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet(f"color: {'#FAFAFA' if sender == 'user' else '#D4D4D4'}; background: transparent; border: none; font-size: 12px;")
        layout.addWidget(lbl)

        self.chat_layout.addWidget(bubble)
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_prompt(self):
        raw_text = self.input_box.text().strip()
        if not raw_text or self.worker is not None:
            return

        # Automatically gather all text/code files from the workspace directory
        final_prompt_payload = ""
        allowed_exts = {'.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.cpp', '.c', '.h', '.txt', '.ps1', '.sh'}
        
        for root, dirs, files in os.walk(self.workspace_path):
            # Prune hidden or heavy system directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'build', 'dist')]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in allowed_exts:
                    fpath = os.path.join(root, file)
                    relpath = os.path.relpath(fpath, self.workspace_path)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        # Include file contents if under 40,000 characters to prevent context overflow
                        if len(content) < 40000:
                            final_prompt_payload += f"\n[WORKSPACE FILE: {relpath}]\n```\n{content}\n```\n"
                    except Exception:
                        pass

        final_prompt_payload += f'\nsearch="NULL?" query="{raw_text}"'
        if self.first_message:
            final_prompt_payload += "\n\n[SYSTEM] NEW CHAT. Output generate-head first."
            self.first_message = False

        self.append_chat(raw_text, sender="user")
        self.input_box.clear()
        self.input_box.setEnabled(False)

        selected_model = self.model_combo.currentText()
        self.worker = AstralWorker(final_prompt_payload, self.chat_history, selected_model)
        self.worker.finished.connect(self._handle_response)
        self.worker.start()

    def _handle_response(self, response: str):
        self.chat_history.append({"role": "assistant", "content": response})
        items = parse_protocol(response)

        for item in items:
            if item[0] == 'tool':
                _, tool, head, val = item
                self.dispatch_tool(tool, head, val)
            elif item[0] == 'text' and item[1].strip():
                self.append_chat(item[1].strip(), sender="astral")

        self.input_box.setEnabled(True)
        self.input_box.setFocus()
        self.worker = None

    def dispatch_tool(self, tool: str, head: str, value: str):
        t = tool.lower().strip()
        if t == "run_code":
            self.append_chat(f"⚙️ [Runner]: Executing '{value}'...", sender="system")
            self.run_code_requested.emit(value)
        elif t == "file_create":
            full_path = os.path.join(self.workspace_path, value) if not os.path.isabs(value) else value
            os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
            if not os.path.exists(full_path):
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("")
            self.append_chat(f"📄 [File]: Created '{value}'", sender="system")
            self.file_create_requested.emit(full_path)
        elif t == "file_edit":
            target = head if head else "script.py"
            full_path = os.path.join(self.workspace_path, target) if not os.path.isabs(target) else target
            os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(value)
            self.append_chat(f"✍️ [File]: Saved updates to '{target}'", sender="system")
            self.file_edit_requested.emit(full_path, value)
        elif t == "terminal_exec":
            self.append_chat(f"💻 [Terminal]: {value}", sender="system")
            self.terminal_exec_requested.emit(value)
        elif t in ["message", "msg", "reply"]:
            self.append_chat(value, sender="astral")
        elif t == "generate-head":
            self.session_title_changed.emit(value)
            self.append_chat(f"🏷️ Session: {value}", sender="system")