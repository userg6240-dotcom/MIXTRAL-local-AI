import sys
import os
import re
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QScrollArea, QApplication,
    QSizePolicy, QSpacerItem, QTextEdit, QMainWindow, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PyQt5.QtGui import QColor, QFontDatabase, QFont, QPixmap, QCursor
from port import query_mist, stop_model
from settings import SettingsPanel
from model_menu import ModelMenu
from canvas import CanvasPanel 

# ══════════════════════════════════════════════════════
#  CUSTOM WIDGET: CYBER CODE BLOCK
# ══════════════════════════════════════════════════════
class CodeBlockWidget(QFrame):
    def __init__(self, language: str, code: str):
        super().__init__()
        self.code_text = code
        
        self.setStyleSheet("""
            QFrame {
                background-color: #09090B;
                border-radius: 8px;
                border: 1px solid #27272A;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #18181B; border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom: 1px solid #27272A;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 6, 12, 6)

        lang_label = QLabel(language.upper() if language else "CODE_BLOCK")
        lang_label.setStyleSheet("color: #00F0FF; font-size: 10px; letter-spacing: 1px; font-weight: bold; background: transparent; border: none;")

        self.copy_btn = QPushButton("COPY")
        self.copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.copy_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #A1A1AA; font-size: 10px; letter-spacing: 1px; border: none; font-weight: bold; }
            QPushButton:hover { color: #00F0FF; }
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        top_layout.addWidget(lang_label)
        top_layout.addStretch()
        top_layout.addWidget(self.copy_btn)

        self.text_area = QTextEdit()
        self.text_area.setPlainText(code)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #E4E4E7;
                font-family: Consolas, Monaco, monospace;
                font-size: 13px;
                border: none;
                padding: 12px;
                selection-background-color: rgba(0, 240, 255, 0.2);
            }
        """)
        
        line_count = len(code.split('\n'))
        calc_height = min(max(line_count * 20 + 20, 60), 400) 
        self.text_area.setMinimumHeight(calc_height)

        layout.addWidget(top_bar)
        layout.addWidget(self.text_area)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.code_text)
        self.copy_btn.setText("COPIED")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("COPY"))

# ══════════════════════════════════════════════════════
#  BACKGROUND WORKER THREAD
# ══════════════════════════════════════════════════════
class MistWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, prompt: str, model_name: str):
        super().__init__()
        self.prompt = prompt
        self.model_name = model_name

    def run(self):
        response = query_mist(self.prompt, self.model_name)
        self.finished.emit(response)

# ══════════════════════════════════════════════════════
#  MAIN APPLICATION UI (HOLOGRAPHIC REDESIGN)
# ══════════════════════════════════════════════════════
class HomeScreen(QWidget):
    def __init__(self, username="Dev Aggarwal"):
        super().__init__()
        
        self.current_user = str(username)
        self.setWindowTitle("DEX CORE")
        self.worker = None
        self.first_message_sent = False
        self.current_theme = "dark"
        self.current_model_tag = "llama3.1" 

        font_path = "assets/GoogleSans-VariableFont_GRAD,opsz,wght.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.font_family = "Segoe UI" if font_id == -1 else QFontDatabase.applicationFontFamilies(font_id)[0]

        app_font = QFont(self.font_family, 11)
        QApplication.setFont(app_font)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── MINIMALIST SIDEBAR ───
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(16, 20, 16, 20)
        side_layout.setSpacing(0)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.logo_box = QLabel()
        self.logo_box.setFixedSize(32, 32)
        self.logo_box.setAlignment(Qt.AlignCenter)
        
        logo_pixmap = QPixmap("wolf.png") 
        if not logo_pixmap.isNull():
            self.logo_box.setPixmap(logo_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.logo_box.setStyleSheet("background: transparent;")
        else:
            self.logo_box.setText("DX")

        self.vibe_label = QLabel("DEX CORE")
        self.vibe_label.setFont(QFont(self.font_family, 14, QFont.Bold))
        
        header_layout.addWidget(self.logo_box)
        header_layout.addWidget(self.vibe_label)
        header_layout.addStretch()
        
        side_layout.addLayout(header_layout)
        side_layout.addSpacing(30)

        # Functional New Chat Button
        self.new_chat_btn = QPushButton("+ NEW SESSION")
        self.new_chat_btn.setFixedHeight(40)
        self.new_chat_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.new_chat_btn.clicked.connect(self.clear_chat_history)
        side_layout.addWidget(self.new_chat_btn)

        side_layout.addStretch()

        # Profile & Settings block combined
        profile_frame = QFrame()
        profile_frame.setStyleSheet("background: transparent;")
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(12)

        avatar = QLabel(self.current_user[:2].upper())
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        self.avatar_lbl = avatar # Saved for styling

        user_col = QVBoxLayout()
        user_col.setSpacing(2)
        self.name_lbl = QLabel(self.current_user.upper())
        self.tier_lbl = QLabel("SYS.ADMIN")
        user_col.addWidget(self.name_lbl)
        user_col.addWidget(self.tier_lbl)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.settings_btn.clicked.connect(self.toggle_settings) 

        profile_layout.addWidget(avatar)
        profile_layout.addLayout(user_col)
        profile_layout.addStretch()
        profile_layout.addWidget(self.settings_btn)
        
        side_layout.addWidget(profile_frame)

        # ─── MAIN CONTENT ───
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")

        self.content = QFrame()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(40, 20, 40, 40)
        self.content_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Custom futuristic scrollbar applied in apply_theme
        self.scroll_area.hide()

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(0, 8, 0, 8)
        self.chat_layout.setSpacing(15)

        self.scroll_area.setWidget(self.chat_container)
        self.content_layout.addWidget(self.scroll_area)

        self.mascot_label = QLabel(self.content)
        self.mascot_label.setAlignment(Qt.AlignCenter)
        self.mascot_label.setStyleSheet("background: transparent;")
        pixmap = QPixmap("wolf.png") 
        if not pixmap.isNull():
            self.mascot_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.mascot_label.setText("🐺")
            self.mascot_label.setStyleSheet("font-size: 56px; background: transparent;")
        self.mascot_label.adjustSize()

        self.welcome_label = QLabel(f"TERMINAL READY, {self.current_user.upper()}", self.content)
        self.welcome_label.setFont(QFont(self.font_family, 24, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)

        # Cleaned up input bar
        self.center_bar = QFrame(self.content)
        self.center_bar.setMaximumWidth(750)
        self.center_bar.setMinimumWidth(500)
        self.center_bar.setFixedHeight(56)

        self.input_layout = QHBoxLayout(self.center_bar)
        self.input_layout.setContentsMargins(20, 6, 8, 6)
        self.input_layout.setSpacing(12)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter command...")

        self.fast_btn = QPushButton("LLAMA 3.1 ∨")
        self.fast_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.model_dropdown = ModelMenu(self)
        self.model_dropdown.model_changed.connect(self.switch_model)
        self.fast_btn.setMenu(self.model_dropdown)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.send_btn.clicked.connect(self.send_prompt)
        self.search_bar.returnPressed.connect(self.send_prompt)

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

        self.apply_theme("dark")

    # ══════════════════════════════════════════════════════
    #  THEME ENGINE (CYBERPUNK NEON AESTHETICS)
    # ══════════════════════════════════════════════════════
    def apply_theme(self, mode):
        self.current_theme = mode
        
        if mode == "light":
            bg = "#F8FAFC"
            side_bg = "#FFFFFF"
            text_main = "#0F172A"
            text_muted = "#64748B"
            border = "#E2E8F0"
            
            self.content.setStyleSheet(f"background-color: {bg};")
            self.sidebar.setStyleSheet(f"background-color: {side_bg}; border-right: 1px solid {border};")
            self.welcome_label.setStyleSheet(f"color: {text_main}; background: transparent; letter-spacing: -1px;")
            self.vibe_label.setStyleSheet(f"color: {text_main}; background: transparent; letter-spacing: 1px;")
            self.name_lbl.setStyleSheet(f"color: {text_main}; font-size: 13px; font-weight: bold; background: transparent; letter-spacing: 1px;")
            self.tier_lbl.setStyleSheet(f"color: #3B82F6; font-size: 10px; font-weight: bold; background: transparent; letter-spacing: 1px;")
            
            if not self.logo_box.pixmap():
                self.logo_box.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 8px; font-weight: bold; font-size: 14px;")
            self.avatar_lbl.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 18px; font-weight: bold; font-size: 12px;")

            self.new_chat_btn.setStyleSheet(f"QPushButton {{ background-color: #F1F5F9; color: {text_main}; border-radius: 8px; font-size: 12px; font-weight: bold; letter-spacing: 1px; border: 1px solid {border}; }} QPushButton:hover {{ background-color: #E2E8F0; }}")

            self.center_bar.setStyleSheet(f"QFrame {{ background-color: #FFFFFF; border: 1px solid {border}; border-radius: 28px; }}")
            self.search_bar.setStyleSheet(f"QLineEdit {{ background-color: transparent; color: {text_main}; font-size: 14px; border: none; padding: 0px; }}")
            self.fast_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {text_muted}; font-size: 11px; font-weight: bold; border: none; padding: 0 8px; letter-spacing: 1px; }} QPushButton:hover {{ color: {text_main}; }}")
            self.send_btn.setStyleSheet("QPushButton { background-color: #3B82F6; color: white; border-radius: 20px; font-size: 16px; border: none; } QPushButton:hover { background-color: #2563EB; }")
            
            self.settings_btn.setStyleSheet(f"QPushButton {{ background-color: #F1F5F9; color: {text_muted}; border-radius: 18px; border: 1px solid {border}; }} QPushButton:hover {{ background-color: #E2E8F0; color: {text_main}; }}")
            
            self.scroll_area.setStyleSheet("""
                QScrollArea { background-color: transparent; border: none; }
                QScrollBar:vertical { background: transparent; width: 6px; margin: 0px; }
                QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 3px; }
                QScrollBar::handle:vertical:hover { background: #94A3B8; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """)

        else: # 🌟 DARK THEME (NEON CYBERPUNK)
            bg = "#0D0D12"
            side_bg = "#111116"
            text_main = "#FFFFFF"
            text_muted = "#8B8B9E"
            border = "#1F1F2E"
            
            # SciFi Accents
            c_cyan = "#00F0FF"
            c_magenta = "#FF003C"
            c_glass = "rgba(255, 255, 255, 0.03)"
            
            self.content.setStyleSheet(f"background-color: {bg};")
            self.sidebar.setStyleSheet(f"background-color: {side_bg}; border-right: 1px solid {border};")
            
            self.welcome_label.setStyleSheet(f"color: {text_main}; background: transparent; letter-spacing: 2px;")
            self.vibe_label.setStyleSheet(f"color: {text_main}; background: transparent; letter-spacing: 2px;")
            self.name_lbl.setStyleSheet(f"color: {text_main}; font-size: 13px; font-weight: bold; background: transparent; letter-spacing: 1px;")
            self.tier_lbl.setStyleSheet(f"color: {c_cyan}; font-size: 10px; font-weight: bold; background: transparent; letter-spacing: 1px;")

            if not self.logo_box.pixmap():
                self.logo_box.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c_cyan}, stop:1 {c_magenta}); color: white; border-radius: 8px; font-weight: bold; font-size: 14px;")
            self.avatar_lbl.setStyleSheet(f"background-color: {border}; color: {c_cyan}; border: 1px solid {c_cyan}; border-radius: 18px; font-weight: bold; font-size: 12px;")

            # Glowing New Session Button
            self.new_chat_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c_cyan}, stop:1 {c_magenta}); color: black; border-radius: 8px; font-size: 12px; font-weight: bold; letter-spacing: 1px; border: none; }} QPushButton:hover {{ opacity: 0.8; }}")

            # Floating glassmorphic command palette
            self.center_bar.setStyleSheet(f"QFrame {{ background-color: {c_glass}; border: 1px solid {c_cyan}; border-radius: 28px; }}")
            self.search_bar.setStyleSheet(f"QLineEdit {{ background-color: transparent; color: {text_main}; font-size: 14px; border: none; padding: 0px; }}")
            self.fast_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {c_cyan}; font-size: 11px; font-weight: bold; border: none; padding: 0 8px; letter-spacing: 1px; }} QPushButton:hover {{ color: white; }}")
            self.send_btn.setStyleSheet(f"QPushButton {{ background-color: {c_cyan}; color: black; border-radius: 20px; font-size: 16px; border: none; }} QPushButton:hover {{ background-color: white; }}")

            self.settings_btn.setStyleSheet(f"QPushButton {{ background-color: {c_glass}; color: {text_muted}; border-radius: 18px; border: 1px solid {border}; }} QPushButton:hover {{ background-color: #1F1F2E; color: {text_main}; border: 1px solid {c_cyan}; }}")
            
            # Futuristic glowing scrollbar
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{ background-color: transparent; border: none; }}
                QScrollBar:vertical {{ background: transparent; width: 4px; margin: 0px; }}
                QScrollBar::handle:vertical {{ background: {c_cyan}; border-radius: 2px; }}
                QScrollBar::handle:vertical:hover {{ background: {c_magenta}; }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            """)

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
        if not self.settings_panel.isHidden(): return
        self.scroll_area.hide()
        self.center_bar.hide()
        self.welcome_label.hide()
        self.mascot_label.hide()
        self.canvas_panel.hide()
        self.settings_panel.show() 

    def show_chat(self):
        if self.settings_panel.isHidden(): return
        self.settings_panel.hide() 
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
        self.canvas_panel.hide()
        
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
                welcome_y = bar_y - wh - 20
                self.welcome_label.setGeometry((cw - ww) // 2, welcome_y, ww, wh)
                self.welcome_label.raise_()

                mw = self.mascot_label.width()
                mh = self.mascot_label.height()
                self.mascot_label.setGeometry((cw - mw) // 2, welcome_y - mh - 20, mw, mh)
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
        self.anim.setDuration(600)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.OutExpo) # Snappier futuristic easing
        self.anim.finished.connect(self._dock_prompt_bar)
        self.anim.start()

    def _dock_prompt_bar(self):
        self.scroll_area.show()
        try:
            for i in reversed(range(self.content_layout.count())):
                item = self.content_layout.itemAt(i)
                widget = item.widget()
                if widget is self.settings_panel or widget is self.scroll_area: continue
                taken = self.content_layout.takeAt(i)
                if taken.widget(): taken.widget().deleteLater()
                elif taken.layout(): self._clear_layout(taken.layout())

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
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())

    def _make_bubble(self, text: str, sender: str) -> QFrame:
        frame = QFrame()
        frame.setMaximumWidth(int(self.width() * 0.65))
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(18, 14, 18, 14)
        frame_layout.setSpacing(10)

        if sender == "user":
            if self.current_theme == "light":
                frame.setStyleSheet("QFrame { background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 16px; border-bottom-right-radius: 4px; }")
                text_color = "#0F172A"
            else:
                frame.setStyleSheet("QFrame { background-color: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.2); border-radius: 16px; border-bottom-right-radius: 4px; }")
                text_color = "#00F0FF"
        elif sender == "thinking":
            color = "#94A3B8" if self.current_theme == "light" else "#FF003C"
            frame.setStyleSheet(f"QFrame {{ background-color: transparent; border: none; }}")
            text_color = color
        else:
            if self.current_theme == "light":
                frame.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; border-bottom-left-radius: 4px; }")
                text_color = "#0F172A"
            else:
                frame.setStyleSheet("QFrame { background-color: rgba(255, 255, 255, 0.02); border: 1px solid #27272A; border-radius: 16px; border-bottom-left-radius: 4px; }")
                text_color = "#E4E4E7"

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
                        code_box = CodeBlockWidget(lang, code)
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
        center_column.setMaximumWidth(800) 
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
        if self.current_model_tag == tag: return
        old_tag = self.current_model_tag
        self.current_model_tag = tag
        self.fast_btn.setText(f"{title.split(' ')[0].upper()} ∨")
        stop_model(old_tag)

    def send_prompt(self):
        prompt = self.search_bar.text().strip()
        if not prompt or self.worker is not None: return

        self.search_bar.clear()
        self.search_bar.setEnabled(False)

        if not self.first_message_sent:
            self.first_message_sent = True
            self.animate_prompt_bar()

        self.add_message(prompt, sender="user")
        self.thinking_bubble = self.add_message("PROCESSING REQUEST...", sender="thinking")

        self.worker = MistWorker(prompt, self.current_model_tag)
        self.worker.finished.connect(self._on_response)
        self.worker.start()

    def _on_response(self, response: str):
        if hasattr(self, 'thinking_bubble') and self.thinking_bubble:
            center_column = self.thinking_bubble.parentWidget()
            if center_column:
                row_widget = center_column.parentWidget()
                if row_widget: row_widget.deleteLater()
            self.thinking_bubble = None

        canvas_pattern = r'/\\/\\tool="canvas"\s+head="(.*?)"\s+value="(.*?)"'
        canvas_matches = re.findall(canvas_pattern, response, re.DOTALL)
        
        if canvas_matches:
            head, code = canvas_matches[-1]
            self.canvas_panel.update_content(head, code)
            self.canvas_panel.show()

        msg_pattern = r'/\\/\\tool="message"\s+value="(.*?)"'
        messages = re.findall(msg_pattern, response, re.DOTALL)
        
        if messages: display_text = "\n\n".join(messages)
        elif response.strip(): display_text = f"⚠️ [SYSTEM OUTPUT]: {response.strip()}"
        else: display_text = "✅ PROCESS EXECUTED."

        self.add_message(display_text, sender="mist")
        
        self.search_bar.setEnabled(True)
        self.search_bar.setFocus()
        self.worker = None