import sys
import os
import re
import random
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QScrollArea, QApplication,
    QSizePolicy, QSpacerItem, QTextEdit, QMainWindow, QSplitter,
    QMenu, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QTimer, QPoint
from PyQt5.QtGui import QColor, QFontDatabase, QFont, QPixmap, QCursor

from port import (
    query_mist, stop_model, get_all_sessions, get_session_history,
    get_next_session_id, save_last_model, load_last_model,
    rename_session, delete_session
)
from settings import SettingsPanel
from model_menu import ModelMenu
from canvas import CanvasPanel

# ══════════════════════════════════════════════════════
#  CUSTOM WIDGET: CODE BLOCK WITH COPY BUTTON
# ══════════════════════════════════════════════════════
class CodeBlockWidget(QFrame):
    """A custom mini-editor to display code with a copy button."""
    def __init__(self, language: str, code: str, mono_font: str = "Consolas"):
        super().__init__()
        self.code_text = code
        self.mono_font = mono_font
        
        self.setStyleSheet("""
            QFrame {
                background-color: #0A0A0A;
                border-radius: 8px;
                border: 1px solid #1A1A1A;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #111111; border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom: none;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 6, 12, 6)

        lang_label = QLabel(language.upper() if language else "CODE")
        lang_label.setStyleSheet("color: #41a8cc; font-size: 11px; font-weight: bold; background: transparent; border: none;")

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.copy_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #41ccbc; font-size: 11px; border: none; font-weight: bold; }
            QPushButton:hover { color: #c8ff50; }
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        top_layout.addWidget(lang_label)
        top_layout.addStretch()
        top_layout.addWidget(self.copy_btn)

        self.text_area = QTextEdit()
        self.text_area.setPlainText(code)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: #D4D4D4;
                font-family: "{self.mono_font}", Consolas, monospace;
                font-size: 13px;
                border: none;
                padding: 10px;
            }}
        """)
        
        line_count = len(code.split('\n'))
        calc_height = min(max(line_count * 20 + 20, 60), 400) 
        self.text_area.setMinimumHeight(calc_height)

        layout.addWidget(top_bar)
        layout.addWidget(self.text_area)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.code_text)
        self.copy_btn.setText("✅ Copied!")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("📋 Copy"))


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
        response = query_mist(self.prompt, self.model_name, self.session_id)
        self.finished.emit(response)


# ══════════════════════════════════════════════════════
#  MAIN APPLICATION UI
# ══════════════════════════════════════════════════════
class HomeScreen(QWidget):
    def __init__(self, username="guest user"):
        super().__init__()
        
        self.current_user = str(username) if not isinstance(username, list) else str(username[0])
            
        self.setWindowTitle("Dex Home")
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

        app_font = QFont(self.font_family, 11)
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
        self.sidebar.setFixedWidth(210)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(12, 14, 12, 14)
        side_layout.setSpacing(2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        self.logo_box = QLabel()
        self.logo_box.setFixedSize(26, 26)
        self.logo_box.setAlignment(Qt.AlignCenter)
        
        logo_pixmap = QPixmap("wolf.png") 
        if not logo_pixmap.isNull():
            self.logo_box.setPixmap(logo_pixmap.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.logo_box.setStyleSheet("background: transparent;")
        else:
            self.logo_box.setText("7K")
            self.logo_box.setStyleSheet("background-color: #E8510A; color: white; border-radius: 6px; font-weight: bold; font-size: 13px;")

        self.vibe_label = QLabel("Vibe")
        self.vibe_label.setFont(QFont(self.font_family, 13, QFont.Bold))

        chevron_label = QLabel("∨")
        chevron_label.setStyleSheet("color: #707070; background: transparent; font-size: 10px;")

        header_layout.addWidget(self.logo_box)
        header_layout.addWidget(self.vibe_label)
        header_layout.addWidget(chevron_label)
        header_layout.addStretch()

        self.icon_search = QPushButton("🔍")
        self.icon_search.setFixedSize(28, 28)
        self.icon_search.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #A0A0A0;")

        self.icon_panel = QPushButton("⊞")
        self.icon_panel.setFixedSize(28, 28)
        self.icon_panel.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #A0A0A0;")

        header_layout.addWidget(self.icon_search)
        header_layout.addWidget(self.icon_panel)
        side_layout.addLayout(header_layout)
        side_layout.addSpacing(10)

        toggle_frame = QFrame()
        toggle_frame.setFixedHeight(36)
        toggle_frame.setStyleSheet("background-color: transparent;")
        toggle_layout = QHBoxLayout(toggle_frame)
        toggle_layout.setContentsMargins(3, 3, 3, 3)
        toggle_layout.setSpacing(0)

        self.chat_btn = QPushButton("Chat")
        self.chat_btn.setFixedHeight(28)
        self.chat_btn.clicked.connect(self.show_chat)

        self.work_btn = QPushButton("Work")
        self.work_btn.setFixedHeight(28)

        toggle_layout.addWidget(self.chat_btn)
        toggle_layout.addWidget(self.work_btn)
        side_layout.addWidget(toggle_frame)
        side_layout.addSpacing(6)

        nav_items = [("⊕", "New Chat", True), ("🤖", "Agents", False), ("⊞", "Context", False)]

        for icon, name, active in nav_items:
            btn = QPushButton(f"  {icon}     {name}")
            if active:
                btn.clicked.connect(self.clear_chat_history)
            self.nav_buttons.append(btn) 
            side_layout.addWidget(btn)

        side_layout.addSpacing(14)

        proj_row = QHBoxLayout()
        self.proj_lbl = QLabel("Projects")
        self.proj_plus = QPushButton("+")
        self.proj_plus.setFixedSize(20, 20)
        self.proj_plus.setStyleSheet("QPushButton { background: transparent; color: #606060; border: none; font-size: 16px; padding: 0; } QPushButton:hover { color: #AAAAAA; }")
        proj_row.addWidget(self.proj_lbl)
        proj_row.addStretch()
        proj_row.addWidget(self.proj_plus)
        side_layout.addLayout(proj_row)
        side_layout.addSpacing(8)

        self.chats_lbl = QLabel("Chats")
        side_layout.addWidget(self.chats_lbl)
        side_layout.addSpacing(4)

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
        profile_layout.setSpacing(8)

        avatar_text = (self.current_user[:2].upper() if len(self.current_user) >= 2 else "GU")
        avatar = QLabel(avatar_text)
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #3f48cc; color: white; border-radius: 6px; font-weight: bold; font-size: 11px;")

        user_col = QVBoxLayout()
        user_col.setSpacing(0)
        
        self.name_lbl = QLabel(self.current_user.lower())
        self.tier_lbl = QLabel("Free")
        user_col.addWidget(self.name_lbl)
        user_col.addWidget(self.tier_lbl)

        self.swap_btn = QPushButton("⇅")
        self.swap_btn.setFixedSize(24, 24)
        self.swap_btn.setStyleSheet("background: transparent; border: none; color: #606060; font-size: 14px;")

        profile_layout.addWidget(avatar)
        profile_layout.addLayout(user_col)
        profile_layout.addStretch()
        profile_layout.addWidget(self.swap_btn)
        side_layout.addWidget(profile_frame)

        action_row = QFrame()
        action_row.setStyleSheet("background: transparent;")
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(4, 8, 4, 4)
        action_layout.setSpacing(8)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.toggle_settings) 

        self.update_frame = QFrame()
        update_layout = QHBoxLayout(self.update_frame)
        update_layout.setContentsMargins(10, 0, 10, 0)
        
        self.up_text = QLabel(f"Update: {self.current_user.capitalize()}")
        update_layout.addWidget(self.up_text)

        self.toggle_pill = QLabel(" ◉ ")
        self.toggle_pill.setFixedSize(30, 20)
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
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_area.hide()

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(0, 8, 0, 8)
        self.chat_layout.setSpacing(6)

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
        self.center_bar.setMaximumWidth(680)
        self.center_bar.setMinimumWidth(480)
        self.center_bar.setFixedHeight(52)

        self.input_layout = QHBoxLayout(self.center_bar)
        self.input_layout.setContentsMargins(8, 6, 8, 6)
        self.input_layout.setSpacing(8)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(34, 34)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type / for quick access")

        self.fast_btn = QPushButton("Dex ∨")
        self.model_dropdown = ModelMenu(self)
        self.model_dropdown.model_changed.connect(self.switch_model)
        self.fast_btn.setMenu(self.model_dropdown)

        last_model = load_last_model()
        if last_model:
            self.current_model_tag = last_model.get("tag", self.current_model_tag)
            last_title = last_model.get("title") or "Dex"
            short_name = last_title.split(" ")[0] if last_title else "Dex"
            self.fast_btn.setText(f"{short_name} ∨")

        self.send_btn = QPushButton("🎤")
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

    # ══════════════════════════════════════════════════════
    #  SPLASH SCREEN RANDOMIZER
    # ══════════════════════════════════════════════════════
    def randomize_welcome_phrase(self):
        """Picks a random phrase and font for the welcome splash screen."""
        phrase = random.choice(self.splash_phrases)
        chosen_font = random.choice(self.splash_fonts)
        self.welcome_label.setText(phrase)
        self.welcome_label.setFont(QFont(chosen_font, 24, QFont.Bold))
        self.welcome_label.adjustSize()

    # ══════════════════════════════════════════════════════
    #  DYNAMIC HISTORY & 3-DOT MANAGEMENT MENU
    # ══════════════════════════════════════════════════════
    def refresh_history_sidebar(self):
        """Clears and re-populates the sidebar buttons with 3-dot management menus."""
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
            dots_btn.setStyleSheet("""
                QPushButton { background: transparent; color: #707070; font-weight: bold; border: none; border-radius: 4px; }
                QPushButton:hover { background-color: rgba(120, 120, 120, 0.2); color: white; }
            """)
            
            def show_options_menu(pos, s_id=sess_id, current_title=title, sender_btn=dots_btn):
                menu = QMenu(self)
                menu.setStyleSheet("""
                    QMenu { background-color: #1A1A1A; color: white; border: 1px solid #333333; border-radius: 8px; padding: 4px; }
                    QMenu::item { padding: 6px 14px; border-radius: 4px; font-size: 12px; }
                    QMenu::item:selected { background-color: #3f48cc; color: white; }
                """)
                edit_action = menu.addAction("✏️ Edit Name")
                delete_action = menu.addAction("🗑️ Delete")
                
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
        """Prompts user for a new chat name and updates Chat.txt."""
        new_title, ok = QInputDialog.getText(self, "Edit Chat Name", "Enter new chat title:", text=old_title)
        if ok and new_title.strip():
            rename_session(session_id, new_title.strip())
            self.refresh_history_sidebar()

    def prompt_delete_session(self, session_id: int):
        """Deletes session data and refreshes UI."""
        delete_session(session_id)
        self.refresh_history_sidebar()
        if self.current_session_id == session_id:
            self.clear_chat_history()

    def load_session(self, session_id: int):
        """Loads all conversation messages for the selected session into the chat view."""
        self.current_session_id = session_id
        self._clear_layout(self.chat_layout)

        history = get_session_history(session_id)
        if not history:
            return

        if not self.first_message_sent:
            self.first_message_sent = True
            self.animate_prompt_bar()

        for sender, raw_text in history:
            if sender == "mist":
                pattern = r'[/\\]{2,4}tool=["\']([^"\']+)["\'](?:\s+head=["\']([^"\']*)["\'])?\s+value=["\']((?:[^"\'\\]|\\.)*)["\']'
                commands = re.findall(pattern, raw_text, re.DOTALL | re.IGNORECASE)
                
                messages = []
                for t_name, t_head, t_val in commands:
                    if t_name.lower() in ["message", "msg", "reply"]:
                        clean_val = t_val.replace('\\"', '"').replace('\\\\', '\\').strip()
                        messages.append(clean_val)
                
                if messages:
                    display_text = "\n\n".join(messages)
                else:
                    clean_text = re.sub(pattern, '', raw_text).strip()
                    display_text = clean_text if clean_text else "✅ Task completed."
            else:
                display_text = raw_text

            self.add_message(display_text, sender=sender)

        self.show_chat()

    # ══════════════════════════════════════════════════════
    #  THEME ENGINE
    # ══════════════════════════════════════════════════════
    def apply_theme(self, mode):
        self.current_theme = mode
        
        if mode == "light":
            bg = "#F9FAFB"
            side_bg = "#FFFFFF"
            text_main = "#111827"
            text_muted = "#6B7280"
            border = "#E5E7EB"
            bar_bg = "#FFFFFF"
            btn_active_bg = "#F3F4F6"
            btn_hover_bg = "#E5E7EB"
            settings_btn_bg = "#FFFFFF"
            
            self.settings_panel.btn_light.setStyleSheet("QPushButton { background-color: #3f48cc; color: white; border-radius: 8px; font-weight: bold; }")
            self.settings_panel.btn_dark.setStyleSheet(f"QPushButton {{ background-color: {settings_btn_bg}; color: {text_muted}; border: 1px solid {border}; border-radius: 8px; font-weight: bold; }}")

            self.content.setStyleSheet(f"background-color: {bg};")
            self.sidebar.setStyleSheet(f"background-color: {side_bg}; border-right: 1px solid {border};")
            self.welcome_label.setStyleSheet(f"color: {text_main}; background: transparent;")
            self.vibe_label.setStyleSheet(f"color: {text_main}; background: transparent;")
            self.name_lbl.setStyleSheet(f"color: {text_main}; font-size: 13px; font-weight: bold; background: transparent;")
            self.tier_lbl.setStyleSheet(f"color: {text_muted}; font-size: 11px; background: transparent;")
            self.proj_lbl.setStyleSheet(f"color: {text_muted}; font-size: 11px; background: transparent;")
            self.chats_lbl.setStyleSheet(f"color: {text_muted}; font-size: 11px; background: transparent;")
            
            self.up_text.setText(f"Update: <span style='color:#3f48cc; font-weight:bold;'>{self.current_user.capitalize()}</span>")
            self.toggle_pill.setStyleSheet(f"background-color: #3f48cc; border-radius: 10px; color: white; font-size: 10px; font-weight: bold;")
            if not self.logo_box.pixmap():
                self.logo_box.setStyleSheet(f"background-color: #3f48cc; color: white; border-radius: 6px; font-weight: bold; font-size: 13px;")

            self.center_bar.setStyleSheet(f"QFrame {{ background-color: {bar_bg}; border: 1px solid {border}; border-radius: 14px; }}")
            self.search_bar.setStyleSheet(f"QLineEdit {{ background-color: transparent; color: {text_main}; font-size: 13px; border: none; padding: 0px 4px; }}")
            self.plus_btn.setStyleSheet(f"QPushButton {{ background-color: {btn_active_bg}; color: {text_muted}; border-radius: 9px; font-size: 20px; border: none; }} QPushButton:hover {{ background-color: {btn_hover_bg}; }}")
            self.fast_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; font-size: 11px; font-weight: bold; border: none; padding: 0 4px; }} QPushButton:hover {{ color: {text_main}; }}")
            self.send_btn.setStyleSheet(f"QPushButton {{ background-color: #DCDCDC; color: black; border-radius: 10px; font-size: 14px; border: none; }} QPushButton:hover {{ background-color: white; }}")

            self.settings_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {settings_btn_bg}; color: {text_muted}; font-size: 14px; border: 1px solid {border}; border-radius: 8px; }}
                QPushButton:hover {{ background-color: {btn_active_bg}; color: {text_main}; border: 1px solid #C0C0C0; }}
            """)
            self.update_frame.setStyleSheet(f"background-color: {settings_btn_bg}; border: 1px solid {border}; border-radius: 8px;")

            self.chat_btn.setStyleSheet(f"QPushButton {{ background-color: {btn_active_bg}; color: {text_main}; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 0 12px; }}")
            self.work_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; border-radius: 6px; font-size: 12px; padding: 0 12px; }} QPushButton:hover {{ background-color: {btn_hover_bg}; color: {text_main}; }}")

            for i, btn in enumerate(self.nav_buttons):
                if i == 0:
                    btn.setStyleSheet(f"QPushButton {{ background-color: {btn_active_bg}; color: {text_main}; font-size: 13px; text-align: left; padding: 7px 10px; border-radius: 7px; border: none; }}")
                else:
                    btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; font-size: 13px; text-align: left; padding: 7px 10px; border-radius: 7px; border: none; }} QPushButton:hover {{ background-color: {btn_active_bg}; color: {text_main}; }}")

            for btn in self.history_buttons:
                btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; font-size: 12px; text-align: left; padding: 6px 8px; border-radius: 6px; border: none; }} QPushButton:hover {{ background-color: {btn_active_bg}; color: {text_main}; }}")

        else: # Dark Theme
            bg = "#000000"
            side_bg = "#050505"
            text_main = "white"
            text_muted = "#808080"
            border = "#1a1a1a"
            bar_bg = "#080808"
            
            c_deep_blue = "#3f48cc"
            c_light_blue = "#41a8cc"
            c_teal = "#41ccbc"
            c_green = "#42cc5b"
            c_lime = "#c8ff50"
            settings_btn_bg = "#0a0a0a"
            
            self.settings_panel.btn_dark.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c_teal}, stop:1 {c_green}); color: black; border-radius: 8px; font-weight: bold; }}")
            self.settings_panel.btn_light.setStyleSheet(f"QPushButton {{ background-color: {settings_btn_bg}; color: {text_muted}; border-radius: 8px; font-weight: bold; border: 1px solid {border}; }}")

            self.content.setStyleSheet(f"background-color: {bg};")
            self.sidebar.setStyleSheet(f"background-color: {side_bg}; border-right: 1px solid {border};")
            
            self.welcome_label.setStyleSheet(f"color: {text_main}; background: transparent;")
            self.vibe_label.setStyleSheet(f"color: {text_main}; background: transparent;")
            self.name_lbl.setStyleSheet(f"color: {text_main}; font-size: 13px; font-weight: bold; background: transparent;")
            self.tier_lbl.setStyleSheet(f"color: {c_teal}; font-size: 11px; background: transparent;")
            self.proj_lbl.setStyleSheet(f"color: {text_muted}; font-size: 11px; background: transparent;")
            self.chats_lbl.setStyleSheet(f"color: {text_muted}; font-size: 11px; background: transparent;")

            self.up_text.setText(f"Update: <span style='color:{c_lime}; font-weight:bold;'>{self.current_user.capitalize()}</span>")
            self.toggle_pill.setStyleSheet(f"background-color: {c_green}; border-radius: 10px; color: black; font-size: 10px; font-weight: bold;")
            if not self.logo_box.pixmap():
                self.logo_box.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c_deep_blue}, stop:1 {c_light_blue}); color: white; border-radius: 6px; font-weight: bold; font-size: 13px;")

            self.center_bar.setStyleSheet(f"QFrame {{ background-color: {bar_bg}; border: 1px solid {c_deep_blue}; border-radius: 14px; }}")
            self.search_bar.setStyleSheet(f"QLineEdit {{ background-color: transparent; color: {text_main}; font-size: 13px; border: none; padding: 0px 4px; }}")
            
            self.send_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c_lime}, stop:1 {c_green}); color: black; border-radius: 10px; font-size: 14px; border: none; }} QPushButton:hover {{ background: {c_lime}; }}")
            self.plus_btn.setStyleSheet(f"QPushButton {{ background-color: #111; color: {c_light_blue}; border-radius: 9px; font-size: 20px; border: none; }} QPushButton:hover {{ background-color: #222; }}")
            self.fast_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {c_teal}; font-size: 11px; font-weight: bold; border: none; padding: 0 4px; }} QPushButton:hover {{ color: {c_lime}; }}")

            self.settings_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {settings_btn_bg}; color: {text_muted}; font-size: 14px; border: 1px solid {border}; border-radius: 8px; }}
                QPushButton:hover {{ background-color: #111; color: {text_main}; border: 1px solid {c_deep_blue}; }}
            """)
            self.update_frame.setStyleSheet(f"background-color: {settings_btn_bg}; border: 1px solid {border}; border-radius: 8px;")

            self.chat_btn.setStyleSheet(f"QPushButton {{ background-color: {c_deep_blue}; color: {text_main}; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 0 12px; }}")
            self.work_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; border-radius: 6px; font-size: 12px; padding: 0 12px; }} QPushButton:hover {{ background-color: #111; color: {text_main}; }}")

            for i, btn in enumerate(self.nav_buttons):
                if i == 0:
                    btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c_deep_blue}, stop:1 {c_light_blue}); color: {text_main}; font-size: 13px; text-align: left; padding: 7px 10px; border-radius: 7px; border: none; }}")
                else:
                    btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; font-size: 13px; text-align: left; padding: 7px 10px; border-radius: 7px; border: none; }} QPushButton:hover {{ background-color: #111; color: {text_main}; }}")

            for btn in self.history_buttons:
                btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; font-size: 12px; text-align: left; padding: 6px 8px; border-radius: 6px; border: none; }} QPushButton:hover {{ background-color: #111; color: {text_main}; }}")

        self.settings_panel.apply_theme(mode)
        self.canvas_panel.apply_theme(mode)

    # ══════════════════════════════════════════════════════
    #  VIEW SWITCHING LOGIC
    # ══════════════════════════════════════════════════════
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
        
        active_bg = "#F3F4F6" if self.current_theme == "light" else "#3f48cc"
        text_col = "#111827" if self.current_theme == "light" else "white"
        self.chat_btn.setStyleSheet(f"QPushButton {{ background-color: {active_bg}; color: {text_col}; border-radius: 6px; font-size: 12px; font-weight: bold; padding: 0 12px; }}")

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

    # ══════════════════════════════════════════════════════
    #  ANIMATION & CHAT LOGIC 
    # ══════════════════════════════════════════════════════
    def closeEvent(self, event):
        print("Shutting down Dex... Flushing AI from RAM.")
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
                welcome_y = bar_y - wh - 14
                self.welcome_label.setGeometry((cw - ww) // 2, welcome_y, ww, wh)
                self.welcome_label.raise_()

                mw = self.mascot_label.width()
                mh = self.mascot_label.height()
                self.mascot_label.setGeometry((cw - mw) // 2, welcome_y - mh - 10, mw, mh)
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
        self.anim.setDuration(500)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
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
        frame = QFrame()
        frame.setMaximumWidth(int(self.width() * 0.65))
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 10, 16, 10)
        frame_layout.setSpacing(10)

        if sender == "user":
            if self.current_theme == "light":
                frame.setStyleSheet("QFrame { background-color: #E5E7EB; border-radius: 16px; color: #111827; }")
                text_color = "#111827"
            else:
                frame.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3f48cc, stop:1 #41a8cc); border-radius: 16px; color: white; }")
                text_color = "white"
        elif sender == "thinking":
            color = "#6B7280" if self.current_theme == "light" else "#41ccbc"
            frame.setStyleSheet(f"QFrame {{ background-color: transparent; color: {color}; font-style: italic; }}")
            text_color = color
        else:
            color = "#111827" if self.current_theme == "light" else "#E0E0E0"
            frame.setStyleSheet(f"QFrame {{ background-color: transparent; color: {color}; }}")
            text_color = color

        if sender in ["user", "thinking"] or "```" not in text:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setFont(QFont(self.font_family, 13))
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
                        lbl.setFont(QFont(self.font_family, 13))
                        lbl.setStyleSheet(f"color: {text_color}; background: transparent; border: none;")
                        frame_layout.addWidget(lbl)
                else:
                    lines = part.split('\n', 1)
                    lang = lines[0].strip() if len(lines) > 0 else ""
                    code = lines[1].strip() if len(lines) > 1 else ""
                    
                    if code:
                        code_box = CodeBlockWidget(lang, code, self.mono_family)
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
        center_column.setMaximumWidth(760) 
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
        self.fast_btn.setText(f"{short_name} ∨")

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
        self.thinking_bubble = self.add_message("thinking…", sender="thinking")

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

        pattern = r'[/\\]{2,4}tool=["\']([^"\']+)["\'](?:\s+head=["\']([^"\']*)["\'])?\s+value=["\']((?:[^"\'\\]|\\.)*)["\']'
        commands = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)

        messages = []
        for t_name, t_head, t_val in commands:
            clean_val = t_val.replace('\\"', '"').replace('\\\\', '\\').strip()

            if t_name.lower() == "canvas":
                self.canvas_panel.update_content(t_head, clean_val)
                self.canvas_panel.show()
                sizes = self.splitter.sizes()
                if sizes[1] == 0:
                    self.splitter.setSizes([max(1, sizes[0] - 450), 450])

            elif t_name.lower() in ["message", "msg", "reply"]:
                messages.append(clean_val)

        if messages:
            display_text = "\n\n".join(messages)
        else:
            clean_text = re.sub(pattern, '', response).strip()
            display_text = clean_text if clean_text else "✅ Action executed successfully."

        self.add_message(display_text, sender="mist")
        self.refresh_history_sidebar()
        
        self.search_bar.setEnabled(True)
        self.search_bar.setFocus()
        self.worker = None
