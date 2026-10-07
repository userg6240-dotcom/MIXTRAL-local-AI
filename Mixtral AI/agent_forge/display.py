import os
import sys
import uuid
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

# Supports running directly or importing from the root directory
try:
    from terminal import OllamaWorker
    from editor import ModelfileEditor
    from chat import SandboxChat
except ImportError:
    from agent_forge.terminal import OllamaWorker
    from agent_forge.editor import ModelfileEditor
    from agent_forge.chat import SandboxChat


class AgentForgeWindow(QWidget):
    # Signal emitted when returning to Home/IDE
    back_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agent Forge // Unified Sandbox")
        self.resize(1320, 840)

        # Light theme styling
        self.setStyleSheet("""
            QWidget { background-color: #F3F4F6; color: #111827; font-family: 'Segoe UI', sans-serif; }
            QSplitter::handle { background-color: #E5E7EB; }
            QSplitter::handle:hover { background-color: #6366F1; }
            QFrame[panel="true"], QWidget[panel="true"] { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; }
            QPushButton { background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 4px; padding: 6px 12px; font-weight: 600; color: #374151; }
            QPushButton:hover { background-color: #F9FAFB; border-color: #9CA3AF; }
            QComboBox { background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 4px; padding: 5px 8px; color: #111827; }
        """)

        self.current_test_hash = None
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ─── TOP BAR WITH BACK BUTTON ───
        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("← Back to Home")
        self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #E5E7EB; color: #374151; font-weight: 700;
                border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #D1D5DB; }
        """)
        self.back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # ─── MAIN SPLITTER ───
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        self.editor = ModelfileEditor()
        self.chat = SandboxChat()

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.chat)
        self.splitter.setSizes([680, 640])

        # Hook editor signals
        self.editor.test_requested.connect(self.handle_test)
        self.editor.create_requested.connect(self.handle_create)
        self.editor.pull_requested.connect(self.handle_pull)

        self.refresh_models()

    def _get_subprocess_flags(self):
        return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    def refresh_models(self):
        self.editor.status_lbl.setText("Synchronizing local models...")
        self.worker = OllamaWorker("refresh", ["ollama", "ls"])
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def handle_test(self):
        self.editor.status_lbl.setText("Compiling temporary test model...")
        self.editor.test_btn.setEnabled(False)

        # Purge existing test model if one is already running
        if self.current_test_hash:
            subprocess.run(
                ["ollama", "rm", self.current_test_hash],
                capture_output=True,
                creationflags=self._get_subprocess_flags()
            )

        self.current_test_hash = f"test_agent_{uuid.uuid4().hex[:6]}"
        modelfile_data = self.editor.get_sanitized_content()

        with open("temp_Modelfile", "w", encoding="utf-8") as f:
            f.write(modelfile_data)

        self.worker = OllamaWorker("test_create", ["ollama", "create", self.current_test_hash, "-f", "temp_Modelfile"])
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def handle_create(self, final_name: str):
        self.editor.status_lbl.setText(f"Building final agent: {final_name}...")
        self.editor.create_btn.setEnabled(False)

        modelfile_data = self.editor.get_sanitized_content()
        with open("temp_Modelfile", "w", encoding="utf-8") as f:
            f.write(modelfile_data)

        self.worker = OllamaWorker("final_create", ["ollama", "create", final_name, "-f", "temp_Modelfile"])
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def handle_pull(self, model_name: str):
        self.editor.status_lbl.setText(f"Pulling {model_name}... (This may take a while)")
        self.worker = OllamaWorker("pull", ["ollama", "pull", model_name])
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, success: bool, action: str, output: str):
        self.editor.test_btn.setEnabled(True)
        self.editor.create_btn.setEnabled(True)

        if not success:
            self.editor.status_lbl.setText("❌ Error encountered.")
            QMessageBox.critical(self, "Ollama Error", output)
            return

        if action == "refresh":
            lines = output.strip().split("\n")[1:]
            models = [line.split()[0] for line in lines if line.strip()]
            self.editor.update_models(models)
            self.editor.status_lbl.setText("Models synchronized.")

        elif action == "test_create":
            if os.path.exists("temp_Modelfile"):
                os.remove("temp_Modelfile")
            self.editor.status_lbl.setText(f"Test model '{self.current_test_hash}' active.")
            self.chat.set_active_model(self.current_test_hash)

        elif action == "final_create":
            if os.path.exists("temp_Modelfile"):
                os.remove("temp_Modelfile")

            # Clean temporary hash from disk
            if self.current_test_hash:
                subprocess.run(
                    ["ollama", "rm", self.current_test_hash],
                    capture_output=True,
                    creationflags=self._get_subprocess_flags()
                )
                self.current_test_hash = None
                self.chat.set_active_model(None)

            QMessageBox.information(self, "Success", "Agent successfully created and stored!")
            self.refresh_models()

        elif action == "pull":
            QMessageBox.information(self, "Success", "Model pulled successfully.")
            self.refresh_models()

    def closeEvent(self, event):
        # Auto-remove temporary testing images on exit
        if self.current_test_hash:
            subprocess.run(
                ["ollama", "rm", self.current_test_hash],
                capture_output=True,
                creationflags=self._get_subprocess_flags()
            )
        if os.path.exists("temp_Modelfile"):
            os.remove("temp_Modelfile")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AgentForgeWindow()
    win.show()
    sys.exit(app.exec_())