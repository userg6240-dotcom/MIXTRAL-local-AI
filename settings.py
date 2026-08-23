from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class SettingsPanel(QFrame):
    clear_chat_requested = pyqtSignal()
    theme_dark_requested = pyqtSignal()
    theme_light_requested = pyqtSignal()
    close_requested = pyqtSignal() # 🌟 NEW: Signal for the X button

    def __init__(self, font_family="Segoe UI"):
        super().__init__()
        self.font_family = font_family
        self.setStyleSheet("background-color: transparent;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # ── Header (Title + Close Button) ──
        header_layout = QHBoxLayout()
        
        self.title_lbl = QLabel("⚙️ Dex Configuration")
        self.title_lbl.setFont(QFont(self.font_family, 22, QFont.Bold))
        self.title_lbl.setStyleSheet("color: white;")
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #A0A0A0; font-size: 20px; font-weight: bold; border: none; } QPushButton:hover { color: white; }")
        self.close_btn.clicked.connect(self.close_requested.emit)
        
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        # ── Section: AI Engine ──
        self.engine_label = QLabel("Language Model")
        self.engine_label.setFont(QFont(self.font_family, 12, QFont.Bold))
        self.engine_label.setStyleSheet("color: #A0A0A0;")
        main_layout.addWidget(self.engine_label)

        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["Dex Core (Default)", "Llama 3", "Mistral", "DeepSeek"])
        self.model_dropdown.setFixedHeight(40)
        self.model_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #252525; color: white;
                border: 1px solid #333333; border-radius: 8px; padding: 5px 15px; font-size: 14px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #252525; color: white; selection-background-color: #E8510A;
            }
        """)
        main_layout.addWidget(self.model_dropdown)

        # ── Section: Appearance ──
        self.theme_label = QLabel("Appearance")
        self.theme_label.setFont(QFont(self.font_family, 12, QFont.Bold))
        self.theme_label.setStyleSheet("color: #A0A0A0; margin-top: 10px;")
        main_layout.addWidget(self.theme_label)

        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(15)
        
        self.btn_dark = QPushButton("🌙 Dark Mode")
        self.btn_dark.setFixedHeight(40)
        self.btn_dark.setStyleSheet("QPushButton { background-color: #E8510A; color: white; border-radius: 8px; font-weight: bold; }")
        self.btn_dark.clicked.connect(self.theme_dark_requested.emit)
        
        self.btn_light = QPushButton("☀️ Light Mode")
        self.btn_light.setFixedHeight(40)
        self.btn_light.setStyleSheet("QPushButton { background-color: #252525; color: #A0A0A0; border-radius: 8px; font-weight: bold; } QPushButton:hover { background-color: #333; }")
        self.btn_light.clicked.connect(self.theme_light_requested.emit)

        theme_layout.addWidget(self.btn_dark)
        theme_layout.addWidget(self.btn_light)
        main_layout.addLayout(theme_layout)

        # ── Section: Data Management ──
        self.data_label = QLabel("Data Management")
        self.data_label.setFont(QFont(self.font_family, 12, QFont.Bold))
        self.data_label.setStyleSheet("color: #A0A0A0; margin-top: 10px;")
        main_layout.addWidget(self.data_label)

        self.btn_clear_chat = QPushButton("🗑️ Clear Chat History")
        self.btn_clear_chat.setFixedHeight(40)
        self.btn_clear_chat.setStyleSheet("""
            QPushButton {
                background-color: #3A1E1E; color: #FF6B6B;
                border: 1px solid #FF6B6B; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #FF6B6B; color: white; }
        """)
        self.btn_clear_chat.clicked.connect(self.clear_chat_requested.emit)
        main_layout.addWidget(self.btn_clear_chat)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def apply_theme(self, mode):
        if mode == "light":
            self.title_lbl.setStyleSheet("color: #111827;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #6B7280; font-size: 20px; font-weight: bold; border: none; } QPushButton:hover { color: #111827; }")
            self.engine_label.setStyleSheet("color: #6B7280;")
            self.theme_label.setStyleSheet("color: #6B7280; margin-top: 10px;")
            self.data_label.setStyleSheet("color: #6B7280; margin-top: 10px;")
            self.model_dropdown.setStyleSheet("""
                QComboBox { background-color: #FFFFFF; color: #111827; border: 1px solid #D1D5DB; border-radius: 8px; padding: 5px 15px; font-size: 14px; }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView { background-color: #FFFFFF; color: #111827; selection-background-color: #E8510A; }
            """)
        else:
            self.title_lbl.setStyleSheet("color: white;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #A0A0A0; font-size: 20px; font-weight: bold; border: none; } QPushButton:hover { color: white; }")
            self.engine_label.setStyleSheet("color: #A0A0A0;")
            self.theme_label.setStyleSheet("color: #A0A0A0; margin-top: 10px;")
            self.data_label.setStyleSheet("color: #A0A0A0; margin-top: 10px;")
            self.model_dropdown.setStyleSheet("""
                QComboBox { background-color: #252525; color: white; border: 1px solid #333333; border-radius: 8px; padding: 5px 15px; font-size: 14px; }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView { background-color: #252525; color: white; selection-background-color: #E8510A; }
            """)
