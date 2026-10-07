import os
import sys
import subprocess
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class OllamaWorker(QThread):
    """Background thread to run CLI commands (create, rm, pull, ls)."""
    finished = pyqtSignal(bool, str, str)  # success, action_name, output/error

    def __init__(self, action_name: str, cmd_list: list):
        super().__init__()
        self.action_name = action_name
        self.cmd_list = cmd_list

    def run(self):
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                self.cmd_list,
                capture_output=True,
                text=True,
                check=True,
                creationflags=flags
            )
            self.finished.emit(True, self.action_name, result.stdout)
        except subprocess.CalledProcessError as e:
            err = e.stderr if e.stderr else e.stdout
            self.finished.emit(False, self.action_name, err or "Unknown execution error")
        except Exception as e:
            self.finished.emit(False, self.action_name, str(e))


class SandboxChatWorker(QThread):
    """Background thread that directly communicates with Ollama's API for testing."""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_name: str, messages: list):
        super().__init__()
        self.model_name = model_name
        self.messages = messages

    def run(self):
        payload = {
            "model": self.model_name,
            "messages": self.messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        try:
            res = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
            if res.status_code == 200:
                data = res.json()
                reply = data.get("message", {}).get("content", "No output received.")
                self.response_ready.emit(reply)
            else:
                self.error_occurred.emit(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            self.error_occurred.emit(f"Failed to reach Ollama API: {e}")