import os
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QFont, QTextCursor, QCursor

class TerminalTextEdit(QPlainTextEdit):
    def __init__(self, terminal_parent):
        super().__init__()
        self.terminal_parent = terminal_parent

    def keyPressEvent(self, event):
        # Handle Ctrl+C: Copy if text is selected, otherwise send keyboard interrupt (\x03)
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.textCursor().hasSelection():
                self.copy()
                event.accept()
                return
            else:
                if self.terminal_parent.process.state() == QProcess.Running:
                    self.terminal_parent.process.write(b"\x03")
                event.accept()
                return
        
        cursor = self.textCursor()
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            
            all_text = self.toPlainText()
            lines = all_text.splitlines()
            last_line = lines[-1] if lines else ""
            
            if ">" in last_line:
                cmd = last_line.split(">", 1)[1].strip()
            else:
                cmd = last_line.strip()

            self.appendPlainText("")
            if cmd:
                self.terminal_parent.dispatch_command(cmd)
            else:
                self.terminal_parent.process.write(b"\n")
            event.accept()
        else:
            super().keyPressEvent(event)


class VSCodeTerminal(QWidget):
    def __init__(self, workspace_path=None, parent=None):
        super().__init__(parent)
        self.workspace_path = workspace_path or os.getcwd()
        self.current_dir = self.workspace_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Mini Top Toolbar with Stop Button
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #121215; border-bottom: 1px solid #1C1C21;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 2, 8, 2)

        lbl = QLabel("TERMINAL")
        lbl.setStyleSheet("color: #71717A; font-size: 10px; font-weight: bold; border: none;")

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.stop_btn.setFixedHeight(20)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #27272A; color: #FAFAFA; font-size: 10px; font-weight: bold;
                border: none; border-radius: 3px; padding: 0 8px;
            }
            QPushButton:hover { background-color: #EF4444; color: #FFFFFF; }
        """)
        self.stop_btn.clicked.connect(self.stop_process)

        tb_layout.addWidget(lbl)
        tb_layout.addStretch()
        tb_layout.addWidget(self.stop_btn)

        layout.addWidget(toolbar)

        # Terminal Text Editor View
        self.editor = TerminalTextEdit(self)
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0A0A0C;
                color: #A1A1AA;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.editor)

        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.current_dir)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        
        shell = "powershell.exe" if sys.platform.startswith("win") else "bash"
        self.process.start(shell)

        self.editor.appendPlainText(f"PS {self.current_dir}> ")
        self.editor.moveCursor(QTextCursor.End)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.editor.insertPlainText(data)
        self.editor.moveCursor(QTextCursor.End)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        self.editor.insertPlainText(data)
        self.editor.moveCursor(QTextCursor.End)

    def dispatch_command(self, cmd: str):
        stripped = cmd.strip()
        if stripped.lower().startswith("cd ") or stripped.lower() == "cd":
            parts = stripped.split(" ", 1)
            if len(parts) > 1:
                target = parts[1].strip().strip('"\'')
                if os.path.isabs(target):
                    new_dir = target
                else:
                    new_dir = os.path.abspath(os.path.join(self.current_dir, target))
                
                if os.path.isdir(new_dir):
                    self.current_dir = new_dir
                    self.process.setWorkingDirectory(self.current_dir)

        if not cmd.endswith("\n"):
            cmd += "\n"
        self.process.write(cmd.encode("utf-8"))

    def stop_process(self):
        if self.process.state() == QProcess.Running:
            # Send keyboard interrupt signal (\x03)
            self.process.write(b"\x03")

    def shutdown(self):
        if self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished(1000)