from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Support running from root or from same directory
try:
    from click_delayer import install_click_delay
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from click_delayer import install_click_delay

class SettingsPanel(QFrame):
    clear_chat_requested = pyqtSignal()
    theme_dark_requested = pyqtSignal()
    theme_light_requested = pyqtSignal()
    close_requested = pyqtSignal()
    model_changed_requested = pyqtSignal(str)

    def __init__(self, font_family="Segoe UI"):
        super().__init__()
        self.font_family = font_family
        self.setStyleSheet("background-color: transparent;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(24)

        # ── Header (Title + Close Button) ──
        header_layout = QHBoxLayout()
        
        self.title_lbl = QLabel("⚙️ Mixtral Settings")
        self.title_lbl.setFont(QFont(self.font_family, 18, QFont.Bold))
        self.title_lbl.setStyleSheet("color: white;")
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #9CA3AF; font-size: 18px; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { color: white; background-color: rgba(255, 255, 255, 0.1); }")
        self.close_btn.clicked.connect(self.close_requested.emit)
        
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        # ── Section: AI Engine ──
        self.engine_label = QLabel("Default Model Profile")
        self.engine_label.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.engine_label.setStyleSheet("color: #9CA3AF;")
        main_layout.addWidget(self.engine_label)

        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["Mixtral 8x7B (Default)", "Llama 3.1", "Qwen 2.5 Coder", "DeepSeek Reasoner"])
        self.model_dropdown.setFixedHeight(38)
        self.model_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #18181B; color: white;
                border: 1px solid #27272A; border-radius: 6px; padding: 4px 12px; font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #18181B; color: white; selection-background-color: #2563EB;
            }
        """)
        # Prevent click-through on dropdown
        install_click_delay(self.model_dropdown, delay_ms=150)
        main_layout.addWidget(self.model_dropdown)
        
        self.model_dropdown.currentTextChanged.connect(self.model_changed_requested.emit)

        # ── Section: Appearance ──
        self.theme_label = QLabel("Interface Theme")
        self.theme_label.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.theme_label.setStyleSheet("color: #9CA3AF; margin-top: 6px;")
        main_layout.addWidget(self.theme_label)

        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(12)
        
        self.btn_dark = QPushButton("🌙 Dark Theme")
        self.btn_dark.setFixedHeight(36)
        self.btn_dark.setStyleSheet("QPushButton { background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold; font-size: 12px; }")
        self.btn_dark.clicked.connect(self.theme_dark_requested.emit)
        
        self.btn_light = QPushButton("☀️ Light Theme")
        self.btn_light.setFixedHeight(36)
        self.btn_light.setStyleSheet("QPushButton { background-color: #18181B; color: #9CA3AF; border: 1px solid #27272A; border-radius: 6px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #27272A; }")
        self.btn_light.clicked.connect(self.theme_light_requested.emit)

        theme_layout.addWidget(self.btn_dark)
        theme_layout.addWidget(self.btn_light)
        main_layout.addLayout(theme_layout)

        # ── Section: Data Management ──
        self.data_label = QLabel("Data Management")
        self.data_label.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.data_label.setStyleSheet("color: #9CA3AF; margin-top: 6px;")
        main_layout.addWidget(self.data_label)

    

        self.btn_clear_chat = QPushButton("🗑️ Clear Active History")
        self.btn_clear_chat.setFixedHeight(36)
        self.btn_clear_chat.setStyleSheet("""
            QPushButton {
                background-color: #2A1717; color: #F87171;
                border: 1px solid #7F1D1D; border-radius: 6px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #7F1D1D; color: white; }
        """)
        self.btn_clear_chat.clicked.connect(self.clear_chat_requested.emit)
        main_layout.addWidget(self.btn_clear_chat)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def apply_theme(self, mode: str):
        if mode == "light":
            self.title_lbl.setStyleSheet("color: #111827;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #6B7280; font-size: 18px; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { color: #111827; background-color: #F3F4F6; }")
            self.engine_label.setStyleSheet("color: #6B7280;")
            self.theme_label.setStyleSheet("color: #6B7280; margin-top: 6px;")
            self.data_label.setStyleSheet("color: #6B7280; margin-top: 6px;")
            self.model_dropdown.setStyleSheet("""
                QComboBox { background-color: #FFFFFF; color: #111827; border: 1px solid #E5E7EB; border-radius: 6px; padding: 4px 12px; font-size: 13px; }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView { background-color: #FFFFFF; color: #111827; selection-background-color: #2563EB; }
            """)
        else:
            self.title_lbl.setStyleSheet("color: white;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #9CA3AF; font-size: 18px; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { color: white; background-color: rgba(255, 255, 255, 0.1); }")
            self.engine_label.setStyleSheet("color: #9CA3AF;")
            self.theme_label.setStyleSheet("color: #9CA3AF; margin-top: 6px;")
            self.data_label.setStyleSheet("color: #9CA3AF; margin-top: 6px;")
            self.model_dropdown.setStyleSheet("""
                QComboBox { background-color: #18181B; color: white; border: 1px solid #27272A; border-radius: 6px; padding: 4px 12px; font-size: 13px; }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView { background-color: #18181B; color: white; selection-background-color: #2563EB; }
            """)