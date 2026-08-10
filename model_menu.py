from PyQt5.QtWidgets import QMenu, QWidgetAction, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QCursor

class ModelMenu(QMenu):
    # This signal broadcasts the chosen model's name and system tag back to home.py
    model_changed = pyqtSignal(str, str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_locked = True  # 🌟 Safety lock starts engaged
        self.setup_ui()

    def showEvent(self, event):
        """Fires automatically every time the menu opens to trap ghost clicks."""
        self.click_locked = True
        # Unlock the menu after 250ms so a natural release click doesn't auto-select
        QTimer.singleShot(250, self.unlock_menu)
        super().showEvent(event)

    def unlock_menu(self):
        """Releases the click lock."""
        self.click_locked = False

    def setup_ui(self):
        self.setStyleSheet("""
            QMenu { 
                background-color: #FFFFFF; 
                border: 1px solid #E5E7EB; 
                border-radius: 12px; 
                padding: 4px;
            }
            QMenu::separator {
                height: 1px;
                background: #E5E7EB;
                margin: 6px 10px;
            }
        """)

        # 🌟 Roster updated with your new custom Mxrl models!
        self.add_rich_item("Mxrl", "Everyday conversation and general logic.", "Mxrl_mist")
        self.add_rich_item("Gemma 2", "Deeply caring, high context accuracy.", "Mxrl_gemma2")
        self.add_rich_item("Qwen 2.5", "Lightning fast, great small coding tasks.", "Mxrl_qwen2.5")
        self.add_rich_item("CodeLlama", "Solid codebase analysis and writing.", "Mxrl_codellama")
        self.add_rich_item("CodeGemma", "Math and code with language personality.", "Mxrl_codegemma")
        self.add_rich_item("Llama3.1", "Very fast and capable.", "Mxrl_llama3.1")
        self.add_rich_item("Qwen 2.5 Mini", "Extremely low RAM, blazing fast.", "Mxrl_qwen_mini")
        self.add_rich_item("ULTRON", "An Agent for autonomous tasks.", "Ultron-Raska")
        
        self.addSeparator()
        
        self.add_rich_item("Dolphin Llama 3", "Uncensored, unrestricted logic.", "Mxrl_dolphin")
        self.add_rich_item("Nous Hermes 2", "Deeply caring, creative roleplay.", "Mxrl_hermes")

    def add_rich_item(self, title: str, subtitle: str, tag: str):
        action = QWidgetAction(self)
        container = QWidget()
        container.setCursor(QCursor(Qt.PointingHandCursor))
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #111827; background: transparent; border: none;")
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 11px; color: #6B7280; background: transparent; border: none;")
        
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        
        action.setDefaultWidget(container)
        
        # When clicked, trigger our safe evaluation handler
        container.mouseReleaseEvent = lambda event, t=title, tg=tag: self.trigger_change(t, tg)
        self.addAction(action)

    def trigger_change(self, title, tag):
        # 🌟 If the safety lock is active, completely ignore the accidental bounce click
        if self.click_locked:
            return
            
        # Emit the signal to home.py, then cleanly close the layout
        self.model_changed.emit(title, tag)
        self.close()