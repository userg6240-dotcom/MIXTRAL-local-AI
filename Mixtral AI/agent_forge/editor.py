from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QPlainTextEdit, QFileDialog, QInputDialog,
    QMessageBox, QDialog, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor, QColor

# Support running from root or from agent_forge directory
try:
    from click_delayer import install_click_delay
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from click_delayer import install_click_delay

PLACEHOLDER_TEXT = "Put how you want the model to behave here"
FALLBACK_TEXT = "You are an model made by Mixtral Inc"

class DarkenedUploadModal(QDialog):
    """Frosted/darkened background overlay for uploading modelfiles."""
    file_loaded = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if parent:
            self.resize(parent.size())
        else:
            self.resize(900, 600)

        # Full overlay root
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setContentsMargins(0, 0, 0, 0)

        # Darkened back-panel simulating blurred border effect
        bg_frame = QWidget()
        bg_frame.setStyleSheet("background-color: rgba(15, 23, 42, 0.72);")
        bg_layout = QVBoxLayout(bg_frame)
        bg_layout.setAlignment(Qt.AlignCenter)

        # Center Card
        card = QWidget()
        card.setFixedSize(480, 260)
        card.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel("Upload Modelfile")
        title.setStyleSheet("font-weight: 700; font-size: 15px; color: #111827; border: none;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("QPushButton { border: none; font-size: 14px; color: #9CA3AF; } QPushButton:hover { color: #111827; }")
        close_btn.clicked.connect(self.reject)
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(close_btn)
        card_layout.addLayout(top_row)

        desc = QLabel("Select a local Modelfile to load it directly into your Forge workspace.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6B7280; font-size: 12px; border: none;")
        card_layout.addWidget(desc)

        card_layout.addSpacing(6)

        upload_box = QPushButton("📁  Browse File")
        upload_box.setCursor(QCursor(Qt.PointingHandCursor))
        upload_box.setFixedHeight(44)
        upload_box.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6; border: 1px dashed #6366F1;
                border-radius: 8px; font-weight: 600; color: #4F46E5; font-size: 13px;
            }
            QPushButton:hover { background-color: #EEF2FF; border-color: #4F46E5; }
        """)
        upload_box.clicked.connect(self._browse)
        card_layout.addWidget(upload_box)
        card_layout.addStretch()

        bg_layout.addWidget(card)
        overlay_layout.addWidget(bg_frame)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Modelfile", "", "All Files (*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.file_loaded.emit(f.read())
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")


class ModelfileEditor(QWidget):
    test_requested = pyqtSignal()
    create_requested = pyqtSignal(str)
    pull_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setProperty("panel", "true")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Toolbar
        tools = QHBoxLayout()
        tools.setSpacing(8)

        self.base_combo = QComboBox()
        self.base_combo.setMinimumWidth(160)
        self.base_combo.currentTextChanged.connect(self.on_base_model_changed)
        # Prevent click-through on dropdown
        install_click_delay(self.base_combo, delay_ms=150)

        self.plugin_btn = QPushButton("🔌 Plugin")
        self.plugin_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.plugin_btn.clicked.connect(self.open_plugin_modal)

        self.test_btn = QPushButton("⚙️ Test Model")
        self.test_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5; color: white; font-weight: 700;
                border: none; border-radius: 4px; padding: 6px 14px;
            }
            QPushButton:hover { background-color: #4338CA; }
        """)
        self.test_btn.clicked.connect(self.test_requested.emit)

        self.create_btn = QPushButton("🚀 Create Final")
        self.create_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; font-weight: 700;
                border: none; border-radius: 4px; padding: 6px 14px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.create_btn.clicked.connect(self.prompt_create)

        tools.addWidget(QLabel("Base:"))
        tools.addWidget(self.base_combo)
        tools.addStretch()
        tools.addWidget(self.plugin_btn)
        tools.addWidget(self.test_btn)
        tools.addWidget(self.create_btn)
        layout.addLayout(tools)

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(self.status_lbl)

        # Code Editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #FAFAFA; border: 1px solid #D1D5DB;
                border-radius: 6px; padding: 12px; color: #111827; font-family: 'Consolas', monospace;
            }
        """)
        layout.addWidget(self.editor)

    def on_base_model_changed(self, model_name: str):
        if not model_name:
            return
        template = (
            f"FROM {model_name}\n\n"
            f"PARAMETER temperature 0.7\n\n"
            f'SYSTEM """\n{PLACEHOLDER_TEXT}\n"""\n'
        )
        self.editor.setPlainText(template)

    def open_plugin_modal(self):
        modal = DarkenedUploadModal(self.window())
        modal.file_loaded.connect(self.editor.setPlainText)
        modal.exec_()

    def prompt_create(self):
        existing = [self.base_combo.itemText(i) for i in range(self.base_combo.count())]
        name, ok = QInputDialog.getText(self, "Create Final Agent", "Enter unique model name:")
        if not ok or not name.strip():
            return
        clean_name = name.strip()
        if clean_name in existing:
            QMessageBox.warning(self, "Conflict", f"Model '{clean_name}' already exists.")
            return
        self.create_requested.emit(clean_name)

    def get_sanitized_content(self) -> str:
        raw = self.editor.toPlainText()
        # Fallback to default identity if placeholder wasn't customized
        if PLACEHOLDER_TEXT in raw:
            raw = raw.replace(PLACEHOLDER_TEXT, FALLBACK_TEXT)
        return raw

    def update_models(self, models: list):
        self.base_combo.blockSignals(True)
        self.base_combo.clear()
        self.base_combo.addItems(models)
        self.base_combo.blockSignals(False)
        if models:
            self.on_base_model_changed(models[0])