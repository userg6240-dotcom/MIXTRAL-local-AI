import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QLineEdit, QPushButton, QFrame, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QCursor


class ForgeChatWorker(QThread):
    """Direct local HTTP chat worker using MaxDev mechanics."""
    finished = pyqtSignal(str)

    def __init__(self, prompt: str, history: list, model_name: str):
        super().__init__()
        self.prompt = prompt
        # Clone history and append the latest prompt
        self.messages = list(history)
        self.messages.append({"role": "user", "content": self.prompt})
        self.model_name = model_name

    def run(self):
        payload = {
            "model": self.model_name,
            "messages": self.messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        try:
            res = requests.post("http://localhost:11434/api/chat", json=payload, timeout=90)
            if res.status_code == 200:
                data = res.json()
                reply = data.get("message", {}).get("content", "").strip()
                if not reply:
                    reply = "(Model returned an empty response)"
            else:
                reply = f"⚠️ Ollama Error (HTTP {res.status_code}): {res.text}"
        except Exception as e:
            reply = f"⚠️ Connection error to Ollama: {e}"

        self.finished.emit(reply)


class SandboxChat(QWidget):
    def __init__(self):
        super().__init__()
        self.setProperty("panel", "true")
        self.active_model = None
        self.chat_history = []
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ─── HEADER STATUS ───
        self.header = QLabel("🧪 Sandbox Chat (No active test agent)")
        self.header.setStyleSheet("color: #4F46E5; font-weight: 700; font-size: 13px; border: none;")
        layout.addWidget(self.header)

        # ─── SCROLLABLE CHAT CONTAINER ───
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_layout.setSpacing(10)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        # ─── INPUT CONTROLS ───
        input_box = QHBoxLayout()
        input_box.setSpacing(8)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Test your agent here...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF; border: 1px solid #D1D5DB;
                border-radius: 6px; padding: 8px 12px; font-size: 12px; color: #111827;
            }
            QLineEdit:focus { border: 1px solid #6366F1; }
        """)
        self.chat_input.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5; color: white; font-weight: 700;
                border: none; border-radius: 6px; padding: 8px 16px;
            }
            QPushButton:hover { background-color: #4338CA; }
        """)
        self.send_btn.clicked.connect(self.send_message)

        input_box.addWidget(self.chat_input)
        input_box.addWidget(self.send_btn)
        layout.addLayout(input_box)

        # Initial placeholder hint
        self.append_bubble("Click '⚙️ Test Model' on the left to compile and connect a test agent.", sender="system")

    def set_active_model(self, model_name: str):
        self.active_model = model_name
        self.chat_history.clear()
        self._clear_bubbles()

        if model_name:
            self.header.setText(f"🧪 Sandbox Chat (Connected: {model_name})")
            self.append_bubble(f"Session established with '{model_name}'. Send a prompt to test behavior.", sender="system")
        else:
            self.header.setText("🧪 Sandbox Chat (No active test agent)")
            self.append_bubble("Agent disconnected. Build a new test model to resume.", sender="system")

    def _clear_bubbles(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def append_bubble(self, text: str, sender: str = "agent"):
        """Direct frame widget injection matching MaxDev mechanics."""
        bubble = QFrame()

        if sender == "user":
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #EEF2FF;
                    border: 1px solid #C7D2FE;
                    border-radius: 8px;
                }
            """)
            tag_text = "👤 You"
            tag_color = "#4F46E5"
            msg_color = "#1E1B4B"
        elif sender == "system":
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #F9FAFB;
                    border: 1px dashed #D1D5DB;
                    border-radius: 8px;
                }
            """)
            tag_text = "⚙️ System"
            tag_color = "#6B7280"
            msg_color = "#4B5563"
        else:  # Agent response
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                }
            """)
            tag_text = f"🤖 {self.active_model or 'Agent'}"
            tag_color = "#10B981"
            msg_color = "#111827"

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        # Sender identifier tag
        tag_lbl = QLabel(tag_text)
        tag_lbl.setStyleSheet(f"color: {tag_color}; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        bubble_layout.addWidget(tag_lbl)

        # Message body
        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg_lbl.setStyleSheet(f"color: {msg_color}; font-size: 12px; background: transparent; border: none;")
        bubble_layout.addWidget(msg_lbl)

        # Directly add the frame widget to chat layout
        self.chat_layout.addWidget(bubble)

        # Force scroll update
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_message(self):
        query = self.chat_input.text().strip()
        if not query or self.worker is not None:
            return

        if not self.active_model:
            self.append_bubble("⚠️ No active test agent. Compile your model first using '⚙️ Test Model'.", sender="system")
            return

        # Show user message immediately
        self.append_bubble(query, sender="user")
        self.chat_input.clear()
        self.chat_input.setEnabled(False)

        # Dispatch background worker
        self.worker = ForgeChatWorker(query, self.chat_history, self.active_model)
        self.worker.finished.connect(self._handle_response)
        self.worker.start()

    def _handle_response(self, reply: str):
        # Update history for persistent multi-turn conversation
        self.chat_history.append({"role": "user", "content": self.worker.prompt})
        self.chat_history.append({"role": "assistant", "content": reply})

        self.append_bubble(reply, sender="agent")

        self.chat_input.setEnabled(True)
        self.chat_input.setFocus()
        self.worker = None