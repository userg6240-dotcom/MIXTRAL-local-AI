import os
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeView, QFileSystemModel, QTabWidget, QLabel,
    QPushButton, QFrame, QFileDialog, QInputDialog, QPlainTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QKeySequence
from PyQt5.QtWidgets import QShortcut

from code_editor import CodeEditor
from terminal import VSCodeTerminal
from astral_chat import AstralChatPanel

STATE_FILE = os.path.join(os.path.expanduser("~"), ".maxdev_state.json")

def load_persisted_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"workspace_dir": os.getcwd(), "open_files": [], "active_file": ""}

def save_persisted_state(state_data):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=4)
    except Exception:
        pass


class MaxDevStudio(QWidget):  # Changed from QMainWindow to QWidget
    switch_to_chat = pyqtSignal()  # Signal to swap back to Chat

    def __init__(self):
        super().__init__()
        
        self.state = load_persisted_state()
        self.workspace_dir = self.state.get("workspace_dir", os.getcwd())
        if not os.path.exists(self.workspace_dir):
            self.workspace_dir = os.getcwd()

        self.setStyleSheet("""
            QWidget { background-color: #000000; }
            QSplitter::handle { background-color: #0F0F12; }
            QSplitter::handle:hover { background-color: #6366F1; }
            QFrame[panel="true"] { background-color: #0A0A0C; border: 1px solid #1C1C21; border-radius: 8px; }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        # ─── TOP RUNNER BAR ───
        top_bar = QFrame()
        top_bar.setFixedHeight(34)
        top_bar.setStyleSheet("background-color: #0A0A0C; border: 1px solid #1C1C21; border-radius: 6px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 0, 10, 0)

        self.breadcrumb_lbl = QLabel(f"Workspace > {os.path.basename(self.workspace_dir)}")
        self.breadcrumb_lbl.setStyleSheet("color: #71717A; font-size: 11px; border: none;")

        self.chat_toggle_btn = QPushButton("💬 Chat")
        self.chat_toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.chat_toggle_btn.setFixedHeight(22)
        self.chat_toggle_btn.setStyleSheet("QPushButton { background-color: #3F3F46; color: #FAFAFA; font-weight: bold; font-size: 11px; border: none; border-radius: 4px; padding: 0 10px; } QPushButton:hover { background-color: #6366F1; }")
        self.chat_toggle_btn.clicked.connect(self.switch_to_chat.emit)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.setFixedHeight(22)
        self.save_btn.setStyleSheet("QPushButton { background-color: #27272A; color: #FAFAFA; font-weight: bold; font-size: 11px; border: none; border-radius: 4px; padding: 0 10px; } QPushButton:hover { background-color: #3F3F46; }")
        self.save_btn.clicked.connect(self.save_current_file)

        self.run_btn = QPushButton("▶ Run")
        self.run_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.run_btn.setFixedHeight(22)
        self.run_btn.setStyleSheet("QPushButton { background-color: #10B981; color: #000000; font-weight: bold; font-size: 11px; border: none; border-radius: 4px; padding: 0 12px; } QPushButton:hover { background-color: #34D399; }")
        self.run_btn.clicked.connect(self.run_current_file)

        top_layout.addWidget(self.breadcrumb_lbl)
        top_layout.addStretch()
        top_layout.addWidget(self.chat_toggle_btn)
        top_layout.addSpacing(6)
        top_layout.addWidget(self.save_btn)
        top_layout.addSpacing(6)
        top_layout.addWidget(self.run_btn)
        root_layout.addWidget(top_bar)

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_current_file)

        # ─── SPLITTER WORKSPACE ───
        self.main_h_splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(self.main_h_splitter)

        explorer_panel = QFrame()
        explorer_panel.setProperty("panel", "true")
        exp_layout = QVBoxLayout(explorer_panel)
        exp_layout.setContentsMargins(8, 8, 8, 8)
        exp_layout.setSpacing(6)

        exp_header = QHBoxLayout()
        exp_title = QLabel("EXPLORER")
        exp_title.setStyleSheet("color: #71717A; font-weight: bold; font-size: 10px; border: none;")
        
        btn_style = "QPushButton { background: #121215; color: #A1A1AA; border: 1px solid #1F1F24; border-radius: 3px; font-size: 11px; } QPushButton:hover { background: #1F1F24; color: white; }"
        btn_open = QPushButton("📁")
        btn_open.setFixedSize(24, 22)
        btn_open.setStyleSheet(btn_style)
        btn_open.clicked.connect(self.open_folder_dialog)

        btn_new = QPushButton("+📄")
        btn_new.setFixedSize(26, 22)
        btn_new.setStyleSheet(btn_style)
        btn_new.clicked.connect(self.create_new_file)

        exp_header.addWidget(exp_title)
        exp_header.addStretch()
        exp_header.addWidget(btn_open)
        exp_header.addWidget(btn_new)
        exp_layout.addLayout(exp_header)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.workspace_dir)

        self.tree = QTreeView()
        self.tree.setModel(self.file_model)
        self.tree.setRootIndex(self.file_model.index(self.workspace_dir))
        self.tree.hideColumn(1); self.tree.hideColumn(2); self.tree.hideColumn(3)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet("QTreeView { background-color: transparent; color: #A1A1AA; border: none; font-size: 12px; } QTreeView::item:hover { background-color: #121215; color: #FFFFFF; } QTreeView::item:selected { background-color: #1F1F26; color: #818CF8; }")
        self.tree.doubleClicked.connect(lambda idx: self.open_file(self.file_model.filePath(idx)))
        exp_layout.addWidget(self.tree)
        self.main_h_splitter.addWidget(explorer_panel)

        self.center_v_splitter = QSplitter(Qt.Vertical)

        self.editor_frame = QFrame()
        self.editor_frame.setProperty("panel", "true")
        editor_layout = QVBoxLayout(self.editor_frame)
        editor_layout.setContentsMargins(4, 4, 4, 4)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda idx: self.tabs.removeTab(idx))
        self.tabs.currentChanged.connect(self.on_tab_switched)
        self.tabs.setStyleSheet("QTabWidget::pane { border: none; background-color: transparent; } QTabBar::tab { background-color: #0A0A0C; color: #71717A; padding: 6px 14px; font-size: 11px; margin-right: 2px; } QTabBar::tab:selected { background-color: #121215; color: #FAFAFA; border-bottom: 2px solid #6366F1; }")
        editor_layout.addWidget(self.tabs)
        self.center_v_splitter.addWidget(self.editor_frame)

        self.terminal_frame = QFrame()
        self.terminal_frame.setProperty("panel", "true")
        term_layout = QVBoxLayout(self.terminal_frame)
        term_layout.setContentsMargins(4, 4, 4, 4)

        self.terminal = VSCodeTerminal(self.workspace_dir)
        term_layout.addWidget(self.terminal)
        self.center_v_splitter.addWidget(self.terminal_frame)

        self.center_v_splitter.setSizes([550, 220])
        self.main_h_splitter.addWidget(self.center_v_splitter)

        self.astral = AstralChatPanel(self.workspace_dir)
        self.astral.run_code_requested.connect(self.handle_run_code_signal)
        self.astral.file_create_requested.connect(self.open_file)
        self.astral.file_edit_requested.connect(self.handle_file_edit_signal)
        self.astral.terminal_exec_requested.connect(self.terminal.dispatch_command)
        
        self.main_h_splitter.addWidget(self.astral)
        self.main_h_splitter.setSizes([220, 880, 380])
        self.restore_previous_session()

    def restore_previous_session(self):
        open_files = self.state.get("open_files", [])
        active_file = self.state.get("active_file", "")
        for fpath in open_files:
            if os.path.exists(fpath):
                self.open_file(fpath, set_active=False)
        if active_file and os.path.exists(active_file):
            for i in range(self.tabs.count()):
                if self.tabs.tabToolTip(i) == active_file:
                    self.tabs.setCurrentIndex(i)
                    break

    def save_current_file(self):
        idx = self.tabs.currentIndex()
        if idx == -1:
            return
        path = self.tabs.tabToolTip(idx)
        widget = self.tabs.widget(idx)
        if isinstance(widget, QPlainTextEdit):
            with open(path, "w", encoding="utf-8") as f:
                f.write(widget.toPlainText())
            self.breadcrumb_lbl.setText(f"Saved: {os.path.basename(path)}")

    def open_file(self, path: str, set_active: bool = True):
        if not os.path.isfile(path):
            return
        filename = os.path.basename(path)
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == path:
                if set_active:
                    self.tabs.setCurrentIndex(i)
                return

        editor = CodeEditor(file_path=path)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                editor.setPlainText(f.read())
        except Exception as e:
            editor.setPlainText(f"Error loading file: {e}")

        idx = self.tabs.addTab(editor, filename)
        self.tabs.setTabToolTip(idx, path)
        if set_active:
            self.tabs.setCurrentIndex(idx)

    def on_tab_switched(self, index):
        if index != -1:
            self.breadcrumb_lbl.setText(f"Workspace > {self.tabs.tabToolTip(index)}")
        else:
            self.breadcrumb_lbl.setText(f"Workspace > {os.path.basename(self.workspace_dir)}")

    def handle_run_code_signal(self, filename: str):
        target_path = filename
        if not os.path.isabs(target_path):
            target_path = os.path.join(self.workspace_dir, filename)
        
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == target_path:
                widget = self.tabs.widget(i)
                if isinstance(widget, QPlainTextEdit):
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(widget.toPlainText())
                break

        if os.path.exists(target_path):
            self.open_file(target_path)
            ext = os.path.splitext(target_path)[1].lower()
            clean_path = f'"{os.path.abspath(target_path)}"'
            runner_map = {
                ".py": f"python {clean_path}",
                ".js": f"node {clean_path}",
                ".cpp": f"g++ {clean_path} -o temp_exec; .\\temp_exec",
                ".ps1": f"powershell -ExecutionPolicy Bypass -File {clean_path}"
            }
            cmd = runner_map.get(ext, f"python {clean_path}")
            self.terminal.dispatch_command(cmd)

    def handle_file_edit_signal(self, full_path: str, new_content: str):
        os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == full_path:
                widget = self.tabs.widget(i)
                if isinstance(widget, QPlainTextEdit):
                    widget.setPlainText(new_content)
                break
        else:
            self.open_file(full_path)

    def run_current_file(self):
        idx = self.tabs.currentIndex()
        if idx == -1:
            return
        self.save_current_file()
        self.handle_run_code_signal(self.tabs.tabToolTip(idx))

    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Workspace", self.workspace_dir)
        if folder:
            self.workspace_dir = folder
            self.tree.setRootIndex(self.file_model.setRootPath(folder))
            self.terminal.workspace_path = folder
            self.terminal.process.setWorkingDirectory(folder)
            self.astral.workspace_path = folder
            self.breadcrumb_lbl.setText(f"Workspace > {os.path.basename(folder)}")

    def create_new_file(self):
        name, ok = QInputDialog.getText(self, "New File", "File Name (e.g., app.py):")
        if ok and name.strip():
            target = os.path.join(self.workspace_dir, name.strip())
            with open(target, "w", encoding="utf-8") as f:
                f.write("")
            self.open_file(target)

    def closeEvent(self, event):
        open_files_list = []
        for i in range(self.tabs.count()):
            fpath = self.tabs.tabToolTip(i)
            if fpath and fpath not in open_files_list:
                open_files_list.append(fpath)
        
        active_fpath = ""
        current_idx = self.tabs.currentIndex()
        if current_idx != -1:
            active_fpath = self.tabs.tabToolTip(current_idx)

        state_data = {
            "workspace_dir": self.workspace_dir,
            "open_files": open_files_list,
            "active_file": active_fpath
        }
        save_persisted_state(state_data)
        self.terminal.shutdown()
        event.accept()