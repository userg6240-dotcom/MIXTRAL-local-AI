from PyQt5.QtWidgets import QMenu, QWidgetAction, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

try:
    from click_delayer import install_click_delay
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from click_delayer import install_click_delay


class ClickableModelItem(QWidget):
    """Custom widget inside QWidgetAction that captures clicks and forwards them."""
    clicked = pyqtSignal(str, str)

    def __init__(self, title: str, subtitle: str, tag: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.tag = tag
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_Hover, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #111827; background: transparent; border: none;")

        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #6B7280; background: transparent; border: none;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.sub_lbl)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.title, self.tag)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class ModelMenu(QMenu):
    model_changed = pyqtSignal(str, str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QMenu { 
                background-color: #FFFFFF; 
                border: 1px solid #E5E7EB; 
                border-radius: 10px; 
                padding: 4px;
            }
            QMenu::separator {
                height: 1px;
                background: #E5E7EB;
                margin: 4px 8px;
            }
        """)

        self.add_rich_item("Mixtral 8x7B", "Everyday conversation and general logic.", "Mxrl_mixtral")
        self.add_rich_item("Gemma 2", "Deeply caring, high context accuracy.", "Mxrl_gemma2")
        self.add_rich_item("Qwen 2.5 Coder", "Lightning fast, great coding performance.", "Mxrl_qwen2.5")
        self.add_rich_item("CodeLlama", "Solid codebase analysis and writing.", "Mxrl_codellama")
        self.add_rich_item("CodeGemma", "Math and code with language personality.", "Mxrl_codegemma")
        self.add_rich_item("Llama 3.1", "Very fast and general reasoning.", "Mxrl_llama3.1")
        self.add_rich_item("Qwen 2.5 Mini", "Extremely low RAM, blazing fast.", "Mxrl_qwen_mini")
        self.add_rich_item("7K Orchestrator", "Agent for autonomous desktop workflows.", "7K-V2")
        self.add_rich_item("AutoAgent Offline", "Agent for offline local operations.", "AutoAgent-Test-V4")
        
        self.addSeparator()
        
        self.add_rich_item("Dolphin Llama 3", "Uncensored, unrestricted logic.", "Mxrl_dolphin")
        self.add_rich_item("Nous Hermes 2", "Deeply caring, creative roleplay.", "Mxrl_hermes")

    def add_rich_item(self, title: str, subtitle: str, tag: str):
        action = QWidgetAction(self)
        container = ClickableModelItem(title, subtitle, tag, self)
        
        # Connect click event directly to trigger_change
        container.clicked.connect(self.trigger_change)
        
        action.setDefaultWidget(container)
        self.addAction(action)

    def trigger_change(self, title: str, tag: str):
        self.model_changed.emit(title, tag)
        self.close()