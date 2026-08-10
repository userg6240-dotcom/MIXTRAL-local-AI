from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor

class SettingsPanel(QFrame):
    clear_chat_requested = pyqtSignal()
    theme_dark_requested = pyqtSignal()
    theme_light_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, font_family="Segoe UI"):
        super().__init__()
        self.font_family = font_family
        self.setStyleSheet("background-color: transparent;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # ── Header ──
        header_layout = QHBoxLayout()
        self.title_lbl = QLabel("SYS.CONFIG")
        self.title_lbl.setFont(QFont(self.font_family, 24, QFont.Bold))
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.clicked.connect(self.close_requested.emit)
        
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        main_layout.addLayout(header_layout)

        # ── Section: UI Protocol ──
        self.theme_label = QLabel("UI PROTOCOL / THEME")
        self.theme_label.setFont(QFont(self.font_family, 11, QFont.Bold))
        main_layout.addWidget(self.theme_label)

        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(15)
        
        self.btn_dark = QPushButton("NEON VOID (DARK)")
        self.btn_dark.setFixedHeight(45)
        self.btn_dark.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_dark.clicked.connect(self.theme_dark_requested.emit)
        
        self.btn_light = QPushButton("DAYLIGHT (LIGHT)")
        self.btn_light.setFixedHeight(45)
        self.btn_light.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_light.clicked.connect(self.theme_light_requested.emit)

        theme_layout.addWidget(self.btn_dark)
        theme_layout.addWidget(self.btn_light)
        main_layout.addLayout(theme_layout)

        # ── Section: Data Core ──
        self.data_label = QLabel("MEMORY CORE")
        self.data_label.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.data_label.setStyleSheet("margin-top: 20px;")
        main_layout.addWidget(self.data_label)

        self.btn_clear_chat = QPushButton("FLUSH CONTEXT MEMORY")
        self.btn_clear_chat.setFixedHeight(45)
        self.btn_clear_chat.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_clear_chat.clicked.connect(self.clear_chat_requested.emit)
        main_layout.addWidget(self.btn_clear_chat)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def apply_theme(self, mode):
        if mode == "light":
            self.title_lbl.setStyleSheet("color: #0F172A; letter-spacing: 2px;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #64748B; font-size: 20px; font-weight: bold; border: none; } QPushButton:hover { color: #EF4444; }")
            self.theme_label.setStyleSheet("color: #64748B; letter-spacing: 1px;")
            self.data_label.setStyleSheet("color: #64748B; letter-spacing: 1px; margin-top: 20px;")
            
            self.btn_dark.setStyleSheet("QPushButton { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #E2E8F0; }")
            self.btn_light.setStyleSheet("QPushButton { background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; }")
            
            self.btn_clear_chat.setStyleSheet("QPushButton { background-color: transparent; color: #EF4444; border: 1px solid #EF4444; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #FEF2F2; }")
        else:
            self.title_lbl.setStyleSheet("color: #00F0FF; letter-spacing: 2px;")
            self.close_btn.setStyleSheet("QPushButton { background: transparent; color: #A1A1AA; font-size: 20px; font-weight: bold; border: none; } QPushButton:hover { color: #FF003C; }")
            self.theme_label.setStyleSheet("color: #A1A1AA; letter-spacing: 1px;")
            self.data_label.setStyleSheet("color: #A1A1AA; letter-spacing: 1px; margin-top: 20px;")
            
            self.btn_dark.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F0FF, stop:1 #FF003C); color: black; border-radius: 6px; font-weight: bold; border: none; }")
            self.btn_light.setStyleSheet("QPushButton { background-color: #18181B; color: #A1A1AA; border: 1px solid #27272A; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #27272A; color: white; }")
            
            self.btn_clear_chat.setStyleSheet("QPushButton { background-color: rgba(255, 0, 60, 0.05); color: #FF003C; border: 1px solid #FF003C; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 0, 60, 0.15); }")