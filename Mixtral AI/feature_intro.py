import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor, QColor

STATE_FILE = "intro_state.json"

INTRO_DATA = {
    "forge": {
        "badge": "⚡ AGENT FORGE SANDBOX",
        "title": "Welcome to Agent Forge",
        "tagline": "Design, fine-tune, and sandbox custom local LLM personalities.",
        "icon": "⚒️",
        "features": [
            ("Custom Modelfile Architecture", "Configure base models, system prompts, parameters (temperature, top_p), and custom adapters."),
            ("Real-Time Isolated Testing", "Spins up lightweight, temporary test instances without modifying your permanent model library."),
            ("Split-Pane Sandbox", "Tweak system instructions on the left and immediately stress-test token responses on the right."),
            ("One-Click Compilation", "Build and export the final verified agent directly into Ollama for use across the MaxDev ecosystem.")
        ],
        "button_text": "Enter Agent Forge"
    },
    "ide": {
        "badge": "💻 AUTONOMOUS WORKSPACE",
        "title": "Welcome to MaxDev IDE",
        "tagline": "An agentic programming environment built for local-first software delivery.",
        "icon": "🚀",
        "features": [
            ("Project Workspace Scanner", "Direct filesystem tree navigation with live file reading and multi-file editing."),
            ("Astral Autonomous Agent", "Direct disk-writing AI agent capable of planning, coding, and fixing bugs autonomously."),
            ("Integrated Shell Console", "Execute background compilers, spin up local web servers, and inspect live stdout output."),
            ("Full-Stack Portability", "Scaffold React, Node, Python, and native desktop workflows side-by-side.")
        ],
        "button_text": "Launch MaxDev Studio"
    }
}

def load_intro_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_intro_state(feature_key: str):
    state = load_intro_state()
    state[feature_key] = True
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[Intro] Warning: Could not save intro state: {e}")


class FeatureIntroDialog(QDialog):
    def __init__(self, feature_key: str, parent=None):
        super().__init__(parent)
        self.feature_key = feature_key
        self.data = INTRO_DATA.get(feature_key, INTRO_DATA["forge"])

        # Frameless modal window with alpha transparency for rounded drop shadows
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(620, 560)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Card container
        card = QFrame()
        card.setStyleSheet("""
            QFrame#card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }
        """)
        card.setObjectName("card")

        # Soft drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 45))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # ─── HEADER ROW ───
        header_row = QHBoxLayout()
        badge_lbl = QLabel(self.data["badge"])
        badge_lbl.setStyleSheet("""
            background-color: #EEF2FF; color: #4F46E5;
            font-size: 10px; font-weight: 800; letter-spacing: 1px;
            padding: 4px 10px; border-radius: 6px;
        """)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #9CA3AF; border: none; font-size: 15px; font-weight: bold; }
            QPushButton:hover { color: #111827; }
        """)
        close_btn.clicked.connect(self.accept)

        header_row.addWidget(badge_lbl)
        header_row.addStretch()
        header_row.addWidget(close_btn)
        card_layout.addLayout(header_row)

        # Title & Tagline
        title_lbl = QLabel(f"{self.data['icon']}  {self.data['title']}")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #111827; border: none;")
        card_layout.addWidget(title_lbl)

        tagline_lbl = QLabel(self.data["tagline"])
        tagline_lbl.setStyleSheet("font-size: 13px; color: #6B7280; border: none;")
        tagline_lbl.setWordWrap(True)
        card_layout.addWidget(tagline_lbl)

        # Separator line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #F3F4F6; border: none;")
        card_layout.addWidget(sep)

        # ─── FEATURE LIST ───
        features_container = QVBoxLayout()
        features_container.setSpacing(14)

        for heading, desc in self.data["features"]:
            item_box = QVBoxLayout()
            item_box.setSpacing(2)

            item_title = QLabel(f"•  {heading}")
            item_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #1F2937;")

            item_desc = QLabel(f"    {desc}")
            item_desc.setStyleSheet("font-size: 12px; color: #6B7280;")
            item_desc.setWordWrap(True)

            item_box.addWidget(item_title)
            item_box.addWidget(item_desc)
            features_container.addLayout(item_box)

        card_layout.addLayout(features_container)
        card_layout.addStretch()

        # ─── FOOTER ACTIONS ───
        footer_layout = QHBoxLayout()

        self.dont_show_cb = QCheckBox("Don't show this intro again")
        self.dont_show_cb.setChecked(True)
        self.dont_show_cb.setStyleSheet("""
            QCheckBox { font-size: 12px; color: #6B7280; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #D1D5DB; }
            QCheckBox::indicator:checked { background-color: #4F46E5; border-color: #4F46E5; }
        """)

        action_btn = QPushButton(self.data["button_text"])
        action_btn.setCursor(QCursor(Qt.PointingHandCursor))
        action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
                color: #FFFFFF; font-weight: 700; font-size: 13px;
                border-radius: 8px; padding: 10px 22px; border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4F46E5, stop:1 #4338CA);
            }
        """)
        action_btn.clicked.connect(self.on_start)

        footer_layout.addWidget(self.dont_show_cb)
        footer_layout.addStretch()
        footer_layout.addWidget(action_btn)
        card_layout.addLayout(footer_layout)

        main_layout.addWidget(card)

    def on_start(self):
        if self.dont_show_cb.isChecked():
            save_intro_state(self.feature_key)
        self.accept()


def show_intro_if_needed(parent, feature_key: str):
    """Triggers the introductory modal if it has not yet been dismissed permanently."""
    state = load_intro_state()
    if not state.get(feature_key, False):
        dialog = FeatureIntroDialog(feature_key, parent=parent)
        dialog.exec_()