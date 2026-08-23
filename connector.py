import sys
from PyQt5.QtWidgets import QApplication
from home import HomeScreen
from PyQt5.QtCore import Qt
from port import execute_protocol, execute_tool

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
    window = HomeScreen(username="Dhruv") 
    window.showMaximized()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 

def handle_ai_response(self, raw_ai_text):
    # 1. Execute any tool calls contained in the response
    tool_results = execute_protocol(raw_ai_text)
    
    # 2. Extract clean user messages (filter out raw tool syntax from chat bubble)
    clean_messages = []
    for tool, res in tool_results:
        if tool.lower() in ["message", "msg", "reply"]:
            clean_messages.append(res)
        elif tool.lower() == "web_open":
            clean_messages.append(f"🌐 Opening {res}...")
        elif tool.lower() == "app_launch":
            clean_messages.append(f"🚀 Launching {res}...")

    # 3. If tools executed, display clean status instead of [Raw Output] warning
    if tool_results:
        display_text = "\n".join(clean_messages) if clean_messages else "Action executed successfully."
        self.add_message_bubble(display_text, sender="assistant")
    else:
        # Fallback if the AI just spoke regular text without tools
        self.add_message_bubble(raw_ai_text, sender="assistant")
