from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCursor

class CanvasPanel(QFrame):
    def __init__(self, font_family="Segoe UI"):
        super().__init__()
        self.font_family = font_family
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ─── TOP BAR ───
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        self.top_bar = top_bar
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)
        
        self.list_btn = QPushButton("▤")
        self.list_btn.setFixedSize(32, 32)
        self.list_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.title_lbl = QLabel("Canvas")
        self.title_lbl.setFont(QFont(self.font_family, 12, QFont.Bold))
        
        self.top_copy_btn = QPushButton("Copy ∨")
        self.top_copy_btn.setFixedHeight(32)
        self.top_copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.top_copy_btn.clicked.connect(self.copy_code)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        top_layout.addWidget(self.list_btn)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.title_lbl)
        top_layout.addStretch()
        top_layout.addWidget(self.top_copy_btn)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.close_btn)
        
        # ─── CODE ACTION BAR (Explain & Copy) ───
        self.action_bar = QFrame()
        action_layout = QHBoxLayout(self.action_bar)
        action_layout.setContentsMargins(16, 8, 16, 4)
        action_layout.addStretch()
        
        self.explain_btn = QPushButton("🧠 Explain")
        self.explain_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.mini_copy_btn = QPushButton("📋")
        self.mini_copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.mini_copy_btn.clicked.connect(self.copy_code)
        
        action_layout.addWidget(self.explain_btn)
        action_layout.addWidget(self.mini_copy_btn)
        
        # ─── EDITOR ───
        self.editor = QTextEdit()
        self.editor.setReadOnly(False)
        
        layout.addWidget(self.top_bar)
        layout.addWidget(self.action_bar)
        layout.addWidget(self.editor)
        
        self.apply_theme("light") # Default state
        
    def update_content(self, head, code):
        """Called by home.py to inject the AI's code into the Canvas."""
        # Grab just the filename if a language tag is attached (e.g., "script.py, python")
        self.title_lbl.setText(head.split(",")[0] if "," in head else head)
        
        # Clean up any literal escaped newlines from the JSON payload
        clean_code = code.replace("\\n", "\n").replace('\\"', '"')
        self.editor.setPlainText(clean_code)
        
    def copy_code(self):
        """Copies the editor content and gives visual feedback."""
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.top_copy_btn.setText("Copied! ✓")
        QTimer.singleShot(2000, lambda: self.top_copy_btn.setText("Copy ∨"))
        
    def apply_theme(self, mode):
        """Dynamically matches the main app's light/dark mode."""
        if mode == "light":
            self.setStyleSheet("background-color: #FFFFFF; border-left: 1px solid #E5E7EB;")
            self.top_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB; border-left: none; border-right: none; border-top: none;")
            self.action_bar.setStyleSheet("background-color: #FFFFFF; border: none;")
            
            self.list_btn.setStyleSheet("QPushButton { background: transparent; color: #6B7280; font-size: 18px; border: none; } QPushButton:hover { color: #111827; }")
            self.title_lbl.setStyleSheet("color: #111827; border: none;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #6B7280; font-size: 16px; border: none; } QPushButton:hover { color: #111827; }")
            
            self.top_copy_btn.setStyleSheet("QPushButton { background-color: #F9FAFB; color: #111827; border: 1px solid #E5E7EB; border-radius: 6px; padding: 0 12px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #F3F4F6; }")
            self.explain_btn.setStyleSheet("QPushButton { background-color: transparent; color: #6B7280; border: 1px solid #E5E7EB; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #F3F4F6; color: #111827; }")
            self.mini_copy_btn.setStyleSheet("QPushButton { background-color: transparent; color: #6B7280; border: 1px solid #E5E7EB; border-radius: 6px; padding: 4px 8px; font-size: 11px; } QPushButton:hover { background-color: #F3F4F6; color: #111827; }")
            
            self.editor.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #111827; font-family: Consolas, Monaco, monospace; font-size: 13px; border: none; padding: 16px; }")
        else:
            self.setStyleSheet("background-color: #1E1E1E; border-left: 1px solid #333333;")
            self.top_bar.setStyleSheet("background-color: #1E1E1E; border-bottom: 1px solid #333333; border-left: none; border-right: none; border-top: none;")
            self.action_bar.setStyleSheet("background-color: #1E1E1E; border: none;")
            
            self.list_btn.setStyleSheet("QPushButton { background: transparent; color: #A0A0A0; font-size: 18px; border: none; } QPushButton:hover { color: white; }")
            self.title_lbl.setStyleSheet("color: white; border: none;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #A0A0A0; font-size: 16px; border: none; } QPushButton:hover { color: white; }")
            
            self.top_copy_btn.setStyleSheet("QPushButton { background-color: #252525; color: white; border: 1px solid #333333; border-radius: 6px; padding: 0 12px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #2A2A2A; }")
            self.explain_btn.setStyleSheet("QPushButton { background-color: transparent; color: #A0A0A0; border: 1px solid #333333; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #2A2A2A; color: white; }")
            self.mini_copy_btn.setStyleSheet("QPushButton { background-color: transparent; color: #A0A0A0; border: 1px solid #333333; border-radius: 6px; padding: 4px 8px; font-size: 11px; } QPushButton:hover { background-color: #2A2A2A; color: white; }")
            
            self.editor.setStyleSheet("QTextEdit { background-color: #1E1E1E; color: #D4D4D4; font-family: Consolas, Monaco, monospace; font-size: 13px; border: none; padding: 16px; }")
