from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCursor

class CanvasPanel(QFrame):
    def __init__(self, font_family="Segoe UI"):
        super().__init__()
        self.font_family = font_family
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ─── NEON TOP BAR ───
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        self.top_bar = top_bar
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        self.title_lbl = QLabel("/> SYSTEM.CANVAS")
        self.title_lbl.setFont(QFont(self.font_family, 11, QFont.Bold))
        
        self.top_copy_btn = QPushButton("📋 COPY_DATA")
        self.top_copy_btn.setFixedHeight(28)
        self.top_copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.top_copy_btn.clicked.connect(self.copy_code)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        top_layout.addWidget(self.title_lbl)
        top_layout.addStretch()
        top_layout.addWidget(self.top_copy_btn)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.close_btn)
        
        # ─── TERMINAL EDITOR ───
        self.editor = QTextEdit()
        self.editor.setReadOnly(False)
        
        layout.addWidget(self.top_bar)
        layout.addWidget(self.editor)
        
        self.apply_theme("dark") # Default to futuristic dark
        
    def update_content(self, head, code):
        self.title_lbl.setText(f"/> {head.split(',')[0].upper()}" if "," in head else f"/> {head.upper()}")
        clean_code = code.replace("\\n", "\n").replace('\\"', '"')
        self.editor.setPlainText(clean_code)
        
    def copy_code(self):
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.top_copy_btn.setText("✓ COPIED")
        QTimer.singleShot(2000, lambda: self.top_copy_btn.setText("📋 COPY_DATA"))
        
    def apply_theme(self, mode):
        if mode == "light":
            self.setStyleSheet("background-color: #F4F5F7; border-left: 1px solid #E2E8F0;")
            self.top_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; border-left: none; border-right: none; border-top: none;")
            self.title_lbl.setStyleSheet("color: #0F172A; letter-spacing: 1px;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #64748B; font-size: 16px; border: none; } QPushButton:hover { color: #EF4444; }")
            self.top_copy_btn.setStyleSheet("QPushButton { background-color: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 4px; padding: 0 10px; font-weight: bold; font-size: 10px; } QPushButton:hover { background-color: #E2E8F0; }")
            self.editor.setStyleSheet("QTextEdit { background-color: #F4F5F7; color: #0F172A; font-family: Consolas, Monaco, monospace; font-size: 13px; border: none; padding: 20px; }")
        else:
            self.setStyleSheet("background-color: #09090B; border-left: 1px solid #27272A;")
            self.top_bar.setStyleSheet("background-color: #18181B; border-bottom: 1px solid #00F0FF; border-left: none; border-right: none; border-top: none;")
            self.title_lbl.setStyleSheet("color: #00F0FF; letter-spacing: 1px;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #A1A1AA; font-size: 16px; border: none; } QPushButton:hover { color: #FF003C; }")
            self.top_copy_btn.setStyleSheet("QPushButton { background-color: #27272A; color: #00F0FF; border: 1px solid #00F0FF; border-radius: 4px; padding: 0 10px; font-weight: bold; font-size: 10px; } QPushButton:hover { background-color: rgba(0, 240, 255, 0.1); }")
            self.editor.setStyleSheet("QTextEdit { background-color: #09090B; color: #E4E4E7; font-family: Consolas, Monaco, monospace; font-size: 13px; border: none; padding: 20px; selection-background-color: rgba(0, 240, 255, 0.3); }")