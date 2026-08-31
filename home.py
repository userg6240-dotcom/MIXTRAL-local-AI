import sys
import os
import re
import random
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QScrollArea, QApplication,
    QSizePolicy, QTextEdit, QSplitter, QMenu, QInputDialog,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QTimer, QPoint
from PyQt5.QtGui import QFontDatabase, QFont, QPixmap, QCursor, QColor

from port import (
    query_mixtral, stop_model, get_all_sessions, get_session_history,
    get_next_session_id, save_last_model, load_last_model,
    rename_session, delete_session
)
from settings import SettingsPanel
from model_menu import ModelMenu
from canvas import CanvasPanel
from protocol_parser import build_display_text, split_protocol

# ══════════════════════════════════════════════════════
#  DESIGN TOKENS
#  Centralized so the whole app reads from one palette instead of
#  scattered hex literals. Two themes: "light" and "dark".
# ══════════════════════════════════════════════════════
THEME = {
    "light": {
        "bg":              "#FAFBFC",
        "side_bg":         "#FFFFFF",
        "text_main":       "#18181B",
        "text_muted":      "#71717A",
        "text_faint":      "#A1A1AA",
        "border":          "#E4E4E7",
        "border_soft":     "#EFEFF1",
        "bar_bg":          "#FFFFFF",
        "btn_active_bg":   "#F4F4F5",
        "btn_hover_bg":    "#EBEBED",
        "accent_1":        "#4F46E5",
        "accent_2":        "#6366F1",
        "accent_soft_bg":  "#EEF2FF",
        "accent_text":     "#4338CA",
        "send_idle":       "#18181B",
        "send_hover":      "#4F46E5",
        "user_bubble_bg":  "#F4F4F6",
        "user_bubble_text":"#18181B",
        "shadow_alpha":    28,
        "code_bg":         "#F8F8F9",
        "code_border":     "#E4E4E7",
        "code_top_bg":     "#F1F1F3",
    },
    "dark": {
        "bg":              "#0A0A0C",
        "side_bg":         "#111114",
        "text_main":       "#FAFAFA",
        "text_muted":      "#A1A1AA",
        "text_faint":      "#71717A",
        "border":          "#232326",
        "border_soft":     "#1C1C1F",
        "bar_bg":          "#18181B",
        "btn_active_bg":   "#1F1F23",
        "btn_hover_bg":    "#27272A",
        "accent_1":        "#6366F1",
        "accent_2":        "#818CF8",
        "accent_soft_bg":  "#1E1B4B",
        "accent_text":     "#A5B4FC",
        "send_idle":       "#6366F1",
        "send_hover":      "#818CF8",
        "user_bubble_bg":  "#6366F1",
        "user_bubble_text":"#FFFFFF",
        "shadow_alpha":    110,
        "code_bg":         "#121214",
        "code_border":     "#27272A",
        "code_top_bg":     "#18181B",
    },
}


# ══════════════════════════════════════════════════════
#  CUSTOM WIDGET: CODE BLOCK WITH COPY BUTTON
# ══════════════════════════════════════════════════════
class CodeBlockWidget(QFrame):
    def __init__(self, language: str, code: str, mono_font: str = "Consolas", theme: str = "dark"):
        super().__init__()
        self.code_text = code
        self.mono_font = mono_font
        t = THEME[theme]

        self.setStyleSheet(f"""
            CodeBlockWidget {{
                background-color: {t['code_bg']};
                border-radius: 10px;
                border: 1px solid {t['code_border']};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            background-color: {t['code_top_bg']};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 1px solid {t['code_border']};
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 8, 10, 8)
        top_layout.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {t['accent_2']}; font-size: 9px; background: transparent; border: none;")

        lang_label = QLabel(language.upper() if language else "CODE")
        lang_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px; font-weight: 600; background: transparent; border: none; letter-spacing: 1px;")

        self.copy_btn = QPushButton("⧉  Copy")
        self.copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text_muted']}; font-size: 11px;
                border: none; font-weight: 600; padding: 3px 8px; border-radius: 6px;
            }}
            QPushButton:hover {{ color: {t['text_main']}; background-color: {t['btn_hover_bg']}; }}
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        top_layout.addWidget(dot)
        top_layout.addWidget(lang_label)
        top_layout.addStretch()
        top_layout.addWidget(self.copy_btn)

        self.text_area = QTextEdit()
        self.text_area.setPlainText(code)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {t['text_main']};
                font-family: "{self.mono_font}", 'JetBrains Mono', Consolas, monospace;
                font-size: 13px;
                border: none;
                padding: 14px;
            }}
        """)

        line_count = len(code.split('\n'))
        calc_height = min(max(line_count * 20 + 24, 64), 420)
        self.text_area.setMinimumHeight(calc_height)

        layout.addWidget(top_bar)
        layout.addWidget(self.text_area)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.code_text)
        self.copy_btn.setText("✓  Copied")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("⧉  Copy"))


# ══════════════════════════════════════════════════════
#  BACKGROUND WORKER THREAD
# ══════════════════════════════════════════════════════
class Worker7K(QThread):
    finished = pyqtSignal(str)

    def __init__(self, prompt: str, model_name: str, session_id: int = None):
        super().__init__()
        self.prompt = prompt
        self.model_name = model_name
        self.session_id = session_id

    def run(self):
        response = query_mixtral(self.prompt, self.model_name, self.session_id)
        self.finished.emit(response)


# ══════════════════════════════════════════════════════
#  MAIN APPLICATION UI
# ══════════════════════════════════════════════════════
class HomeScreen(QWidget):
    def __init__(self, username="guest user"):
        super().__init__()

        self.current_user = str(username) if not isinstance(username, list) else str(username[0])

        self.setWindowTitle("Mixtral AI Assistant")
        self.worker = None
        self.first_message_sent = False
        self.current_theme = "light"
        self.current_model_tag = "llama3.1"
        self.current_session_id = None

        self.nav_buttons = []
        self.history_buttons = []

        # ─── 1. BASE APP FONTS ───
        font_path = "assets/GoogleSans-VariableFont_GRAD,opsz,wght.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Segoe UI"

        mono_path = "assets/GoogleSansCode-VariableFont_MONO,wght.ttf"
        mono_id = QFontDatabase.addApplicationFont(mono_path)
        self.mono_family = QFontDatabase.applicationFontFamilies(mono_id)[0] if mono_id != -1 else "Consolas"

        app_font = QFont(self.font_family, 10)
        QApplication.setFont(app_font)

        # ─── 2. SPLASH SCREEN FONTS & PHRASES ───
        splash_font_files = [
            "assets/SourGummy-VariableFont_wdth,wght.ttf",
            "assets/Outfit-VariableFont_wght.ttf",
            "assets/Michroma-Regular.ttf",
            "assets/Honk-Regular-VariableFont_MORF,SHLN.ttf"
        ]
        self.splash_fonts = []
        for f_path in splash_font_files:
            f_id = QFontDatabase.addApplicationFont(f_path)
            if f_id != -1:
                fams = QFontDatabase.applicationFontFamilies(f_id)
                if fams:
                    self.splash_fonts.append(fams[0])
        if not self.splash_fonts:
            self.splash_fonts = [self.font_family]

        self.splash_phrases = [
            "Where should we start?",
            "Any new ideas to explore?",
            "What are we building today?",
            "Ready when you are.",
            "It's a late-night jam session.",
            "Got a tough problem to solve?",
            "Let's make some magic.",
            "What's on your mind?",
            "Time to build the future.",
            "Explore a brand new thought."
        ]

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ══════════════════════════════════════════════════════
        #  SIDEBAR
        # ══════════════════════════════════════════════════════
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(224)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(16, 18, 16, 16)
        side_layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(9)

        self.logo_box = QLabel()
        self.logo_box.setFixedSize(30, 30)
        self.logo_box.setAlignment(Qt.AlignCenter)

        logo_pixmap = QPixmap("wolf.png")
        if not logo_pixmap.isNull():
            self.logo_box.setPixmap(logo_pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.logo_box.setStyleSheet("background: transparent;")
        else:
            self.logo_box.setText("M")
            self.logo_box.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                color: white; border-radius: 8px; font-weight: 700; font-size: 14px;
            """)

        self.vibe_label = QLabel("Mixtral")
        self.vibe_label.setFont(QFont(self.font_family, 14, QFont.Bold))

        header_layout.addWidget(self.logo_box)
        header_layout.addWidget(self.vibe_label)
        header_layout.addStretch()

        self.icon_search = QPushButton("⌕")
        self.icon_search.setFixedSize(28, 28)
        self.icon_search.setCursor(QCursor(Qt.PointingHandCursor))
        self.icon_search.setStyleSheet("background: transparent; border: none; font-size: 16px; font-weight: bold; color: #9CA3AF;")

        self.icon_panel = QPushButton("▦")
        self.icon_panel.setFixedSize(28, 28)
        self.icon_panel.setCursor(QCursor(Qt.PointingHandCursor))
        self.icon_panel.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #9CA3AF;")

        header_layout.addWidget(self.icon_search)
        header_layout.addWidget(self.icon_panel)
        side_layout.addLayout(header_layout)
        side_layout.addSpacing(14)

        toggle_frame = QFrame()
        toggle_frame.setFixedHeight(36)
        toggle_frame.setStyleSheet("background-color: transparent;")
        toggle_layout = QHBoxLayout(toggle_frame)
        toggle_layout.setContentsMargins(2, 2, 2, 2)
        toggle_layout.setSpacing(2)

        self.chat_btn = QPushButton("Chat")
        self.chat_btn.setFixedHeight(30)
        self.chat_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.chat_btn.clicked.connect(self.show_chat)

        self.work_btn = QPushButton("Work")
        self.work_btn.setFixedHeight(30)
        self.work_btn.setCursor(QCursor(Qt.PointingHandCursor))

        toggle_layout.addWidget(self.chat_btn)
        toggle_layout.addWidget(self.work_btn)
        side_layout.addWidget(toggle_frame)
        side_layout.addSpacing(8)

        nav_items = [("＋", "New Chat", True), ("◇", "Agents", False), ("▤", "Context", False)]

        for icon, name, active in nav_items:
            btn = QPushButton(f"   {icon}    {name}")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            if active:
                btn.clicked.connect(self.clear_chat_history)
            self.nav_buttons.append(btn)
            side_layout.addWidget(btn)

        side_layout.addSpacing(18)

        proj_row = QHBoxLayout()
        self.proj_lbl = QLabel("PROJECTS")
        self.proj_plus = QPushButton("+")
        self.proj_plus.setCursor(QCursor(Qt.PointingHandCursor))
        self.proj_plus.setFixedSize(20, 20)
        self.proj_plus.setStyleSheet("QPushButton { background: transparent; color: #9CA3AF; border: none; font-size: 15px; } QPushButton:hover { color: #111827; }")
        proj_row.addWidget(self.proj_lbl)
        proj_row.addStretch()
        proj_row.addWidget(self.proj_plus)
        side_layout.addLayout(proj_row)
        side_layout.addSpacing(6)

        self.chats_lbl = QLabel("RECENTS")
        side_layout.addWidget(self.chats_lbl)
        side_layout.addSpacing(6)

        # Dynamic History Container
        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(2)
        side_layout.addWidget(self.history_container)

        side_layout.addStretch()

        profile_frame = QFrame()
        profile_frame.setStyleSheet("background: transparent;")
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(4, 0, 4, 0)
        profile_layout.setSpacing(9)

        avatar_text = (self.current_user[:2].upper() if len(self.current_user) >= 2 else "GU")
        avatar = QLabel(avatar_text)
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #6366F1, stop:1 #4F46E5);
            color: white; border-radius: 9px; font-weight: 700; font-size: 11px;
        """)

        user_col = QVBoxLayout()
        user_col.setSpacing(1)

        self.name_lbl = QLabel(self.current_user.lower())
        self.tier_lbl = QLabel("FREE")
        self.tier_lbl.setFixedHeight(15)
        user_col.addWidget(self.name_lbl)
        user_col.addWidget(self.tier_lbl)

        self.swap_btn = QPushButton("⇅")
        self.swap_btn.setFixedSize(24, 24)
        self.swap_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.swap_btn.setStyleSheet("background: transparent; border: none; color: #9CA3AF; font-size: 13px;")

        profile_layout.addWidget(avatar)
        profile_layout.addLayout(user_col)
        profile_layout.addStretch()
        profile_layout.addWidget(self.swap_btn)
        side_layout.addWidget(profile_frame)

        action_row = QFrame()
        action_row.setStyleSheet("background: transparent;")
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(2, 10, 2, 2)
        action_layout.setSpacing(8)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.toggle_settings)

        self.update_frame = QFrame()
        update_layout = QHBoxLayout(self.update_frame)
        update_layout.setContentsMargins(10, 0, 10, 0)

        self.up_text = QLabel(f"{self.current_user.capitalize()}")
        update_layout.addWidget(self.up_text)

        self.toggle_pill = QLabel(" ● ")
        self.toggle_pill.setFixedSize(28, 20)
        self.toggle_pill.setAlignment(Qt.AlignCenter)

        action_layout.addWidget(self.settings_btn)
        action_layout.addWidget(self.update_frame, 1)
        action_layout.addWidget(self.toggle_pill)

        side_layout.addWidget(action_row)

        # ══════════════════════════════════════════════════════
        #  MAIN CONTENT AREA & SPLITTER
        # ══════════════════════════════════════════════════════
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")

        self.content = QFrame()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(40, 20, 40, 40)
        self.content_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.hide()

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(0, 8, 0, 8)
        self.chat_layout.setSpacing(14)

        self.scroll_area.setWidget(self.chat_container)
        self.content_layout.addWidget(self.scroll_area)

        self.mascot_label = QLabel(self.content)
        self.mascot_label.setAlignment(Qt.AlignCenter)
        self.mascot_label.setStyleSheet("background: transparent;")
        pixmap = QPixmap("wolf.png")
        if not pixmap.isNull():
            self.mascot_label.setPixmap(pixmap.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.mascot_label.setText("🐺")
            self.mascot_label.setStyleSheet("font-size: 48px; background: transparent;")
        self.mascot_label.adjustSize()

        self.welcome_label = QLabel(self.content)
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.randomize_welcome_phrase()

        self.center_bar = QFrame(self.content)
        self.center_bar.setMaximumWidth(700)
        self.center_bar.setMinimumWidth(480)
        self.center_bar.setFixedHeight(54)

        self.input_layout = QHBoxLayout(self.center_bar)
        self.input_layout.setContentsMargins(12, 6, 10, 6)
        self.input_layout.setSpacing(9)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.plus_btn.setFixedSize(32, 32)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Message Mixtral...")

        self.fast_btn = QPushButton("Mixtral ⌄")
        self.fast_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.model_dropdown = ModelMenu(self)
        self.model_dropdown.model_changed.connect(self.switch_model)
        self.fast_btn.setMenu(self.model_dropdown)

        last_model = load_last_model()
        if last_model:
            self.current_model_tag = last_model.get("tag", self.current_model_tag)
            last_title = last_model.get("title") or "Mixtral"
            short_name = last_title.split(" ")[0] if last_title else "Mixtral"
            self.fast_btn.setText(f"{short_name} ⌄")

        self.send_btn = QPushButton("↑")
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.setFixedSize(34, 34)

        self.send_btn.clicked.connect(self.send_prompt)
        self.search_bar.returnPressed.connect(self.send_prompt)

        self.input_layout.addWidget(self.plus_btn)
        self.input_layout.addWidget(self.search_bar)
        self.input_layout.addWidget(self.fast_btn)
        self.input_layout.addWidget(self.send_btn)

        self.settings_panel = SettingsPanel(font_family=self.font_family)
        self.settings_panel.clear_chat_requested.connect(self.clear_chat_history)
        self.settings_panel.theme_dark_requested.connect(lambda: self.apply_theme("dark"))
        self.settings_panel.theme_light_requested.connect(lambda: self.apply_theme("light"))
        self.settings_panel.close_requested.connect(self.show_chat)

        self.content_layout.addWidget(self.settings_panel)
        self.settings_panel.hide()

        self.splitter.addWidget(self.content)

        self.canvas_panel = CanvasPanel(font_family=self.font_family)
        self.canvas_panel.close_btn.clicked.connect(self.canvas_panel.hide)
        self.splitter.addWidget(self.canvas_panel)
        self.canvas_panel.hide()

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.splitter)

        self.apply_theme("light")
        self.refresh_history_sidebar()

    # ──────────────────────────────────────────────
    #  SHADOW HELPER (depth = the difference between
    #  "app" and "website in a window")
    # ──────────────────────────────────────────────
    def _make_shadow(self, blur=32, x=0, y=10, alpha=None):
        t = THEME[self.current_theme]
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setOffset(x, y)
        shadow.setColor(QColor(0, 0, 0, alpha if alpha is not None else t["shadow_alpha"]))
        return shadow

    def randomize_welcome_phrase(self):
        phrase = random.choice(self.splash_phrases)
        chosen_font = random.choice(self.splash_fonts)
        self.welcome_label.setText(phrase)
        self.welcome_label.setFont(QFont(chosen_font, 23, QFont.Bold))
        self.welcome_label.adjustSize()

    def refresh_history_sidebar(self):
        self._clear_layout(self.history_layout)
        self.history_buttons.clear()

        sessions = get_all_sessions()

        for sess in reversed(sessions):
            sess_id = sess["id"]
            title = sess["title"]
            display_title = title if len(title) <= 18 else title[:15] + "..."

            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)

            btn = QPushButton(display_title)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setToolTip(f"{title} ({sess['timestamp']})")
            btn.clicked.connect(lambda checked, s_id=sess_id: self.load_session(s_id))

            dots_btn = QPushButton("⋮")
            dots_btn.setFixedSize(22, 22)
            dots_btn.setCursor(QCursor(Qt.PointingHandCursor))
            t = THEME[self.current_theme]
            dots_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {t['text_faint']}; font-weight: bold; border: none; border-radius: 5px; }}
                QPushButton:hover {{ background-color: {t['btn_hover_bg']}; color: {t['text_main']}; }}
            """)

            def show_options_menu(pos, s_id=sess_id, current_title=title, sender_btn=dots_btn):
                menu = QMenu(self)
                mt = THEME[self.current_theme]
                menu.setStyleSheet(f"""
                    QMenu {{ background-color: {mt['bar_bg']}; color: {mt['text_main']}; border: 1px solid {mt['border']}; border-radius: 10px; padding: 6px; }}
                    QMenu::item {{ padding: 7px 16px; border-radius: 6px; font-size: 12px; }}
                    QMenu::item:selected {{ background-color: {mt['accent_1']}; color: white; }}
                """)
                edit_action = menu.addAction("✎  Rename")
                delete_action = menu.addAction("🗑  Delete")

                action = menu.exec_(sender_btn.mapToGlobal(pos))
                if action == edit_action:
                    self.prompt_rename_session(s_id, current_title)
                elif action == delete_action:
                    self.prompt_delete_session(s_id)

            dots_btn.clicked.connect(lambda _, d_btn=dots_btn, s_id=sess_id, t=title: show_options_menu(QPoint(0, 22), s_id, t, d_btn))

            row_layout.addWidget(btn, 1)
            row_layout.addWidget(dots_btn, 0)

            self.history_buttons.append(btn)
            self.history_layout.addWidget(row_widget)

        self.apply_theme(self.current_theme)

    def prompt_rename_session(self, session_id: int, old_title: str):
        new_title, ok = QInputDialog.getText(self, "Edit Chat Name", "Enter new chat title:", text=old_title)
        if ok and new_title.strip():
            rename_session(session_id, new_title.strip())
            self.refresh_history_sidebar()

    def prompt_delete_session(self, session_id: int):
        delete_session(session_id)
        self.refresh_history_sidebar()
        if self.current_session_id == session_id:
            self.clear_chat_history()

    def load_session(self, session_id: int):
        self.current_session_id = session_id
        self._clear_layout(self.chat_layout)

        history = get_session_history(session_id)
        if not history:
            return

        if not self.first_message_sent:
            self.first_message_sent = True
            self.animate_prompt_bar()

        for sender, raw_text in history:
            if sender == "mixtral":
                display_text = build_display_text(raw_text, fallback="✓ Task completed.")
            else:
                display_text = raw_text

            self.add_message(display_text, sender=sender)

        self.show_chat()

    # ══════════════════════════════════════════════════════
    #  THEME ENGINE
    # ══════════════════════════════════════════════════════
    def apply_theme(self, mode: str):
        self.current_theme = mode
        t = THEME[mode]

        is_light = mode == "light"

        self.settings_panel.btn_light.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent_2']}, stop:1 {t['accent_1']}); color: white; border-radius: 9px; font-weight: 700; }}"
            if is_light else
            f"QPushButton {{ background-color: {t['btn_active_bg']}; color: {t['text_muted']}; border: 1px solid {t['border']}; border-radius: 9px; font-weight: 700; }}"
        )
        self.settings_panel.btn_dark.setStyleSheet(
            f"QPushButton {{ background-color: {t['btn_active_bg']}; color: {t['text_muted']}; border: 1px solid {t['border']}; border-radius: 9px; font-weight: 700; }}"
            if is_light else
            f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent_2']}, stop:1 {t['accent_1']}); color: white; border-radius: 9px; font-weight: 700; }}"
        )

        self.content.setStyleSheet(f"background-color: {t['bg']};")
        self.sidebar.setStyleSheet(f"background-color: {t['side_bg']}; border-right: 1px solid {t['border']};")

        self.welcome_label.setStyleSheet(f"color: {t['text_main']}; background: transparent;")
        self.vibe_label.setStyleSheet(f"color: {t['text_main']}; background: transparent;")
        self.name_lbl.setStyleSheet(f"color: {t['text_main']}; font-size: 13px; font-weight: 700; background: transparent;")
        self.tier_lbl.setStyleSheet(f"""
            color: {t['accent_text']}; font-size: 9px; font-weight: 700; letter-spacing: 1px;
            background-color: {t['accent_soft_bg']}; border-radius: 4px; padding: 1px 5px; max-width: 34px;
        """)
        self.proj_lbl.setStyleSheet(f"color: {t['text_faint']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;")
        self.chats_lbl.setStyleSheet(f"color: {t['text_faint']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;")

        accent_label_color = t['accent_1'] if is_light else t['accent_2']
        self.up_text.setText(f"Workspace: <b style='color:{accent_label_color};'>{self.current_user.capitalize()}</b>")
        self.toggle_pill.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent_2']}, stop:1 {t['accent_1']});
            border-radius: 10px; color: white; font-size: 10px; font-weight: 700;
        """)

        self.center_bar.setStyleSheet(f"""
            QFrame {{ background-color: {t['bar_bg']}; border: 1px solid {t['border']}; border-radius: 16px; }}
        """)
        self.center_bar.setGraphicsEffect(self._make_shadow(blur=40, y=14, alpha=t['shadow_alpha']))

        self.search_bar.setStyleSheet(f"""
            QLineEdit {{ background-color: transparent; color: {t['text_main']}; font-size: 13px; border: none; padding: 0px 4px; }}
        """)
        self.plus_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {t['btn_active_bg']}; color: {t['text_muted']}; border-radius: 8px; font-size: 17px; border: none; }}
            QPushButton:hover {{ background-color: {t['btn_hover_bg']}; }}
        """)
        self.fast_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {t['accent_text'] if not is_light else t['text_muted']}; font-size: 11px; font-weight: 700; border: none; padding: 0 4px; }}
            QPushButton:hover {{ color: {t['accent_1']}; }}
        """)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['send_idle']}, stop:1 {t['send_idle']});
                color: white; border-radius: 9px; font-size: 15px; font-weight: 700; border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent_2']}, stop:1 {t['accent_1']});
            }}
        """)

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {t['bar_bg']}; color: {t['text_muted']}; font-size: 14px; border: 1px solid {t['border']}; border-radius: 8px; }}
            QPushButton:hover {{ background-color: {t['btn_active_bg']}; color: {t['text_main']}; border-color: {t['accent_2']}; }}
        """)
        self.update_frame.setStyleSheet(f"background-color: {t['bar_bg']}; border: 1px solid {t['border']}; border-radius: 8px;")

        self.chat_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent_2']}, stop:1 {t['accent_1']});
                color: white; border-radius: 8px; font-size: 12px; font-weight: 700; padding: 0 12px;
            }}
        """)
        self.work_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {t['text_muted']}; border-radius: 8px; font-size: 12px; padding: 0 12px; border: none; }}
            QPushButton:hover {{ background-color: {t['btn_hover_bg']}; color: {t['text_main']}; }}
        """)

        for i, btn in enumerate(self.nav_buttons):
            if i == 0:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['accent_soft_bg']}; color: {t['accent_text']};
                        font-size: 13px; text-align: left; padding: 7px 10px; border-radius: 8px;
                        border: none; font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: transparent; color: {t['text_muted']}; font-size: 13px; text-align: left; padding: 7px 10px; border-radius: 8px; border: none; }}
                    QPushButton:hover {{ background-color: {t['btn_active_bg']}; color: {t['text_main']}; }}
                """)

        for btn in self.history_buttons:
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: transparent; color: {t['text_muted']}; font-size: 12px; text-align: left; padding: 6px 8px; border-radius: 7px; border: none; }}
                QPushButton:hover {{ background-color: {t['btn_active_bg']}; color: {t['text_main']}; }}
            """)

        # ── scroll area + custom scrollbar (default OS scrollbars look cheap) ──
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 9px; margin: 6px 2px 6px 0px; }}
            QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 4px; min-height: 28px; }}
            QScrollBar::handle:vertical:hover {{ background: {t['text_faint']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; border: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

        self.settings_panel.apply_theme(mode)
        self.canvas_panel.apply_theme(mode)

        # re-apply shadows to any bubbles already on screen (theme swap mid-chat)
        for i in range(self.chat_layout.count()):
            row = self.chat_layout.itemAt(i).widget()
            if row is None:
                continue
            for bubble in row.findChildren(QFrame):
                if bubble.property("mist_bubble"):
                    bubble.setGraphicsEffect(self._make_shadow(blur=24, y=6, alpha=t['shadow_alpha']))

    def toggle_settings(self):
        if self.settings_panel.isHidden():
            self.show_settings()
        else:
            self.show_chat()

    def show_settings(self):
        if not self.settings_panel.isHidden():
            return
        self.scroll_area.hide()
        self.center_bar.hide()
        self.welcome_label.hide()
        self.mascot_label.hide()
        self.canvas_panel.hide()
        self.settings_panel.show()

    def show_chat(self):
        if self.settings_panel.isHidden():
            return
        self.settings_panel.hide()

        t = THEME[self.current_theme]
        self.chat_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent_2']}, stop:1 {t['accent_1']});
                color: white; border-radius: 8px; font-size: 12px; font-weight: 700; padding: 0 12px;
            }}
        """)

        if self.first_message_sent:
            self.scroll_area.show()
            self.center_bar.show()
        else:
            self.welcome_label.show()
            self.mascot_label.show()
            self.center_bar.show()

    def clear_chat_history(self):
        self._clear_layout(self.chat_layout)
        self.first_message_sent = False
        self.current_session_id = get_next_session_id()
        self.canvas_panel.hide()

        self.randomize_welcome_phrase()
        self.scroll_area.hide()
        self.center_bar.setGeometry((self.content.width() - self.center_bar.width()) // 2,
                                    (self.content.height() - self.center_bar.height()) // 2 + 20,
                                    self.center_bar.width(), self.center_bar.height())
        self.show_chat()

    def closeEvent(self, event):
        print("Shutting down Mixtral UI... Flushing AI from RAM.")
        stop_model(self.current_model_tag)
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not self.center_bar.isHidden() and not self.first_message_sent:
            self.center_bar.adjustSize()
            self.welcome_label.adjustSize()
            self.mascot_label.adjustSize()

            cw = self.content.width()
            ch = self.content.height()

            if cw > 0 and ch > 0:
                bw = self.center_bar.width()
                bh = self.center_bar.height()

                bar_y = (ch - bh) // 2 + 20
                self.center_bar.setGeometry((cw - bw) // 2, bar_y, bw, bh)
                self.center_bar.raise_()

                ww = self.welcome_label.width()
                wh = self.welcome_label.height()
                welcome_y = bar_y - wh - 16
                self.welcome_label.setGeometry((cw - ww) // 2, welcome_y, ww, wh)
                self.welcome_label.raise_()

                mw = self.mascot_label.width()
                mh = self.mascot_label.height()
                self.mascot_label.setGeometry((cw - mw) // 2, welcome_y - mh - 12, mw, mh)
                self.mascot_label.raise_()

    def animate_prompt_bar(self):
        self.welcome_label.hide()
        self.mascot_label.hide()

        start_rect = self.center_bar.geometry()
        margin = 30
        end_y = self.content.height() - self.center_bar.height() - margin
        end_x = (self.content.width() - self.center_bar.width()) // 2

        end_rect = QRect(end_x, end_y, self.center_bar.width(), self.center_bar.height())

        self.anim = QPropertyAnimation(self.center_bar, b"geometry")
        self.anim.setDuration(380)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(self._dock_prompt_bar)
        self.anim.start()

    def _dock_prompt_bar(self):
        self.scroll_area.show()

        try:
            for i in reversed(range(self.content_layout.count())):
                item = self.content_layout.itemAt(i)
                widget = item.widget()

                if widget in [self.settings_panel, self.scroll_area, self.center_bar]:
                    continue

                taken = self.content_layout.takeAt(i)
                if taken.widget():
                    taken.widget().deleteLater()
                elif taken.layout():
                    self._clear_layout(taken.layout())

            dock_layout = QHBoxLayout()
            dock_layout.addStretch()
            dock_layout.addWidget(self.center_bar)
            dock_layout.addStretch()
            self.content_layout.addLayout(dock_layout)
        except RuntimeError:
            pass

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                w = item.widget()
                if w not in [self.center_bar, self.settings_panel, self.scroll_area, self.canvas_panel]:
                    w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _make_bubble(self, text: str, sender: str) -> QFrame:
        t = THEME[self.current_theme]
        frame = QFrame()
        frame.setMaximumWidth(int(self.width() * 0.70))
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 12, 16, 12)
        frame_layout.setSpacing(8)

        if sender == "user":
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {t['user_bubble_bg']};
                    border-radius: 14px;
                    border: {'1px solid ' + t['border'] if self.current_theme == 'light' else 'none'};
                }}
            """)
            text_color = t['user_bubble_text']
            frame.setProperty("mist_bubble", True)
            frame.setGraphicsEffect(self._make_shadow(blur=20, y=5, alpha=t['shadow_alpha']))
        elif sender == "thinking":
            color = t['text_muted']
            frame.setStyleSheet(f"QFrame {{ background-color: transparent; color: {color}; font-style: italic; }}")
            text_color = color
        else:
            color = t['text_main']
            frame.setStyleSheet(f"QFrame {{ background-color: transparent; color: {color}; }}")
            text_color = color

        if sender in ["user", "thinking"] or "```" not in text:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setFont(QFont(self.font_family, 11))
            label.setStyleSheet(f"color: {text_color}; background: transparent; border: none;")
            frame_layout.addWidget(label)
        else:
            parts = text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    if part.strip():
                        lbl = QLabel(part.strip())
                        lbl.setWordWrap(True)
                        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                        lbl.setFont(QFont(self.font_family, 11))
                        lbl.setStyleSheet(f"color: {text_color}; background: transparent; border: none;")
                        frame_layout.addWidget(lbl)
                else:
                    lines = part.split('\n', 1)
                    lang = lines[0].strip() if len(lines) > 0 else ""
                    code = lines[1].strip() if len(lines) > 1 else ""

                    if code:
                        code_box = CodeBlockWidget(lang, code, self.mono_family, theme=self.current_theme)
                        frame_layout.addWidget(code_box)

        return frame

    def add_message(self, text: str, sender: str = "user") -> QFrame:
        bubble = self._make_bubble(text, sender)

        row_widget = QWidget()
        row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        center_column = QWidget()
        center_column.setMaximumWidth(780)
        center_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        center_layout = QHBoxLayout(center_column)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        if sender == "user":
            center_layout.addStretch()
            center_layout.addWidget(bubble, alignment=Qt.AlignTop)
        else:
            center_layout.addWidget(bubble, alignment=Qt.AlignTop)
            center_layout.addStretch()

        row_layout.addStretch()
        row_layout.addWidget(center_column)
        row_layout.addStretch()

        self.chat_layout.addWidget(row_widget)
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

        return bubble

    def switch_model(self, title: str, tag: str):
        if self.current_model_tag == tag:
            return

        old_tag = self.current_model_tag
        self.current_model_tag = tag

        short_name = title.split(" ")[0]
        self.fast_btn.setText(f"{short_name} ⌄")

        save_last_model(tag, title)
        stop_model(old_tag)

    def send_prompt(self):
        prompt = self.search_bar.text().strip()
        if not prompt or self.worker is not None:
            return

        self.search_bar.clear()
        self.search_bar.setEnabled(False)

        if not self.first_message_sent:
            self.first_message_sent = True
            self.animate_prompt_bar()

        self.add_message(prompt, sender="user")
        self.thinking_bubble = self.add_message("Thinking...", sender="thinking")

        self.worker = Worker7K(prompt, self.current_model_tag, self.current_session_id)
        self.worker.finished.connect(self._on_response)
        self.worker.start()

    def _on_response(self, response: str):
        if hasattr(self, 'thinking_bubble') and self.thinking_bubble:
            center_column = self.thinking_bubble.parentWidget()
            if center_column:
                row_widget = center_column.parentWidget()
                if row_widget:
                    row_widget.deleteLater()
            self.thinking_bubble = None

        # Walk the parsed protocol so we can special-case the "canvas" tool
        # (open the side panel) while still surfacing message/msg/reply text.
        final_parts = []
        for item in split_protocol(response):
            if item[0] == 'tool':
                _, tool, head, value = item
                if tool.lower() == "canvas":
                    self.canvas_panel.update_content(head, value)
                    self.canvas_panel.show()
                    sizes = self.splitter.sizes()
                    if sizes[1] == 0:
                        self.splitter.setSizes([max(1, sizes[0] - 450), 450])
                elif tool.lower() in ("message", "msg", "reply"):
                    final_parts.append(value)
            else:
                final_parts.append(item[1])

        display_text = "\n\n".join(p for p in final_parts if p).strip()
        if not display_text:
            display_text = "✓ Action executed successfully."

        self.add_message(display_text, sender="mixtral")
        self.refresh_history_sidebar()

        self.search_bar.setEnabled(True)
        self.search_bar.setFocus()
        self.worker = None
