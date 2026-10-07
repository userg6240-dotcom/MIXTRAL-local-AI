from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCursor

class CanvasPanel(QFrame):
    def __init__(self, font_family="Segoe UI"):
        super().__init__()
        self.font_family = font_family
        self.setMinimumWidth(420)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ─── HEADER BAR ───
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(54)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(18, 0, 18, 0)
        
        self.list_btn = QPushButton("▤")
        self.list_btn.setFixedSize(30, 30)
        self.list_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.title_lbl = QLabel("Mixtral Canvas")
        self.title_lbl.setFont(QFont(self.font_family, 11, QFont.Bold))
        
        self.top_copy_btn = QPushButton("Copy Code")
        self.top_copy_btn.setFixedHeight(30)
        self.top_copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.top_copy_btn.clicked.connect(self.copy_code)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        top_layout.addWidget(self.list_btn)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.title_lbl)
        top_layout.addStretch()
        top_layout.addWidget(self.top_copy_btn)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.close_btn)
        
        # ─── ACTION BAR ───
        self.action_bar = QFrame()
        self.action_bar.setFixedHeight(40)
        action_layout = QHBoxLayout(self.action_bar)
        action_layout.setContentsMargins(18, 4, 18, 8)
        action_layout.addStretch()
        
        self.explain_btn = QPushButton("🧠 Explain")
        self.explain_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.mini_copy_btn = QPushButton("📋")
        self.mini_copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.mini_copy_btn.clicked.connect(self.copy_code)
        
        action_layout.addWidget(self.explain_btn)
        action_layout.addWidget(self.mini_copy_btn)
        
        # ─── CODE EDITOR ───
        self.editor = QTextEdit()
        self.editor.setReadOnly(False)
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        
        layout.addWidget(self.top_bar)
        layout.addWidget(self.action_bar)
        layout.addWidget(self.editor)
        
        self.apply_theme("light")
        
    def update_content(self, head: str, code: str):
        """Injects AI-generated code payload cleanly into the editor."""
        clean_title = head.split(",")[0].strip() if "," in head else head.strip()
        self.title_lbl.setText(clean_title if clean_title else "Mixtral Canvas")
        
        clean_code = code.replace("\\n", "\n").replace('\\"', '"').replace('\\\\', '\\')
        self.editor.setPlainText(clean_code)
        
    def copy_code(self):
        """Copies code text with active visual status feedback."""
        QApplication.clipboard().setText(self.editor.toPlainText())
        self.top_copy_btn.setText("Copied! ✓")
        QTimer.singleShot(2000, lambda: self.top_copy_btn.setText("Copy Code"))
        
    def apply_theme(self, mode: str):
        """Synchronizes color tokens with main app window."""
        if mode == "light":
            self.setStyleSheet("CanvasPanel { background-color: #FAFAFA; border-left: 1px solid #E5E7EB; }")
            self.top_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB; border-left: none; border-right: none; border-top: none;")
            self.action_bar.setStyleSheet("background-color: #FFFFFF; border: none;")
            
            self.list_btn.setStyleSheet("QPushButton { background: transparent; color: #6B7280; font-size: 15px; border: none; border-radius: 6px; } QPushButton:hover { background-color: #F3F4F6; color: #111827; }")
            self.title_lbl.setStyleSheet("color: #111827; border: none;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #6B7280; font-size: 14px; border: none; border-radius: 6px; } QPushButton:hover { background-color: #FEE2E2; color: #DC2626; }")
            
            self.top_copy_btn.setStyleSheet("QPushButton { background-color: #F3F4F6; color: #111827; border: 1px solid #E5E7EB; border-radius: 6px; padding: 0 12px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #E5E7EB; }")
            self.explain_btn.setStyleSheet("QPushButton { background-color: transparent; color: #4B5563; border: 1px solid #E5E7EB; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600; } QPushButton:hover { background-color: #F3F4F6; color: #111827; }")
            self.mini_copy_btn.setStyleSheet("QPushButton { background-color: transparent; color: #4B5563; border: 1px solid #E5E7EB; border-radius: 6px; padding: 4px 8px; font-size: 11px; } QPushButton:hover { background-color: #F3F4F6; color: #111827; }")
            
            self.editor.setStyleSheet("""
                QTextEdit {
                    background-color: #FFFFFF;
                    color: #1F2937;
                    font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
                    font-size: 13px;
                    border: none;
                    padding: 16px;
                    selection-background-color: #DBEAFE;
                }
            """)
        else:
            self.setStyleSheet("CanvasPanel { background-color: #111113; border-left: 1px solid #27272A; }")
            self.top_bar.setStyleSheet("background-color: #18181B; border-bottom: 1px solid #27272A; border-left: none; border-right: none; border-top: none;")
            self.action_bar.setStyleSheet("background-color: #18181B; border: none;")
            
            self.list_btn.setStyleSheet("QPushButton { background: transparent; color: #A1A1AA; font-size: 15px; border: none; border-radius: 6px; } QPushButton:hover { background-color: #27272A; color: #FAFAFA; }")
            self.title_lbl.setStyleSheet("color: #FAFAFA; border: none;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #A1A1AA; font-size: 14px; border: none; border-radius: 6px; } QPushButton:hover { background-color: #451A1A; color: #F87171; }")
            
            self.top_copy_btn.setStyleSheet("QPushButton { background-color: #27272A; color: #FAFAFA; border: 1px solid #3F3F46; border-radius: 6px; padding: 0 12px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #3F3F46; }")
            self.explain_btn.setStyleSheet("QPushButton { background-color: transparent; color: #A1A1AA; border: 1px solid #3F3F46; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600; } QPushButton:hover { background-color: #27272A; color: #FAFAFA; }")
            self.mini_copy_btn.setStyleSheet("QPushButton { background-color: transparent; color: #A1A1AA; border: 1px solid #3F3F46; border-radius: 6px; padding: 4px 8px; font-size: 11px; } QPushButton:hover { background-color: #27272A; color: #FAFAFA; }")
            
            self.editor.setStyleSheet("""
                QTextEdit {
                    background-color: #111113;
                    color: #E4E4E7;
                    font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
                    font-size: 13px;
                    border: none;
                    padding: 16px;
                    selection-background-color: #3F3F46;
                }
            """)