import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt

# Inject paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT_DIR, "maxdev_studio"))
sys.path.append(os.path.join(ROOT_DIR, "agent_forge"))

from home import HomeScreen
from maxdev_studio.main import MaxDevStudio
from agent_forge.display import AgentForgeWindow
from feature_intro import show_intro_if_needed  # <--- Added import

class MasterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mixtral AI & MaxDev Studio // Unified Workspace")
        self.resize(1500, 920)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pages
        self.home_screen = HomeScreen(username="Dhruv")
        self.maxdev = MaxDevStudio()
        self.forge_page = AgentForgeWindow()

        # Stack indexing
        self.stack.addWidget(self.home_screen)  # 0
        self.stack.addWidget(self.maxdev)       # 1
        self.stack.addWidget(self.forge_page)   # 2

        # ─── WIRE ALL NAVIGATION SIGNALS ───
        self.home_screen.switch_to_ide.connect(self.show_ide)
        self.home_screen.switch_to_forge.connect(self.show_forge)
        self.maxdev.switch_to_chat.connect(self.show_chat)
        self.forge_page.back_requested.connect(self.show_home)

    def show_ide(self):
        # Trigger the intro dialog if not yet seen
        show_intro_if_needed(self, "ide")
        self.stack.setCurrentIndex(1)
        self.maxdev.setFocus()

    def show_chat(self):
        self.stack.setCurrentIndex(0)
        self.home_screen.setFocus()

    def show_home(self):
        print("Returning to Home Screen...")
        self.stack.setCurrentWidget(self.home_screen)
        self.home_screen.setFocus()

    def show_forge(self):
        print("Switching to Agent Forge...")
        # Trigger the intro dialog if not yet seen
        show_intro_if_needed(self, "forge")
        self.forge_page.refresh_models()
        self.stack.setCurrentWidget(self.forge_page)

    def closeEvent(self, event):
        if hasattr(self.home_screen, "closeEvent"):
            self.home_screen.closeEvent(event)
        if hasattr(self.maxdev, "closeEvent"):
            self.maxdev.closeEvent(event)
        if hasattr(self.forge_page, "closeEvent"):
            self.forge_page.closeEvent(event)
        event.accept()

def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = MasterApp()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()