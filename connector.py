import sys
from PyQt5.QtWidgets import QApplication
from home import HomeScreen
from PyQt5.QtCore import Qt

# --- FIX UI SQUISHING & FONT SCALING IN .EXE ---
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
# ---------------------------------------------

def main():
    print("🚀 Booting Mist UI directly...")
    app = QApplication(sys.argv)
    
    # We bypass login and pass a hardcoded name straight to the interface
    window = HomeScreen(username="Daksh") 
    window.showMaximized()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 

