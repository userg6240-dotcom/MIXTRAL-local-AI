# 🐺 Mixtral AI Core (Local AI Desktop Assistant)

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green?style=for-the-badge&logo=qt)
![Ollama](https://img.shields.io/badge/Local_LLM-Ollama-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**Mixtral AI Core** is a fully autonomous, locally hosted AI desktop assistant built in Python. Designed with a hyper-modern, cyberpunk-inspired UI, Mixtral AI doesn't just chat—it acts. Using advanced tool-calling and system-level interceptors, Mixtral AI can write code, execute Windows commands, bypass OS restrictions, and navigate the web completely independent of cloud APIs.

---

## ✨ Features

*   **Cyberpunk Terminal UI:** A highly polished, animated PyQt5 interface featuring glassmorphism, neon linear gradients, holographic chat bubbles, and a dedicated Dark/Light mode toggle.
*   **System God-Mode:** Safely executes system commands locally, bypassing Windows CMD quirks and permission locks. 
*   **Smart Web Interceptor:** Intelligently intercepts web links and forces them to launch directly in local browser binaries (like Google Chrome), completely evading Microsoft Edge redirects and OS-level security crashes.
*   **System Canvas:** A built-in, slide-out secondary code editor. When the AI generates scripts, they are routed directly to the Canvas for easy reading, explaining, and copying.
*   **100% Offline & Private:** Runs on local LLMs (Llama 3.1, Mistral, DeepSeek) with zero data leaving your machine.
*   **Portable Executable:** Fully compiled into a standalone Windows `.exe` using PyInstaller, bundling all assets, icons, and UI stylesheets into a single app.

---

## 🛠️ Prerequisites

Before you begin, ensure you have met the following requirements:
*   **Python 3.10+** installed on your machine.
*   **Ollama** (or a similar local LLM runner) installed and actively running on localhost.
*   A local model pulled (e.g., `ollama run llama3.1`).

---

## 🚀 Installation & Setup

[ 1. SYSTEM REQUIREMENTS ]
--------------------------------------------------------------------------------
- OS: Windows 10 / 11 (64-bit)
- Python: Version 3.10 to 3.12 installed (Ensure "Add Python to PATH" is checked)
- Terminal: PowerShell or Command Prompt
- Network: Active internet connection for initial model downloads and web routing


[ 2. WORKSPACE DIRECTORY SETUP ]
--------------------------------------------------------------------------------
1. Create a dedicated folder on your system:
   C:\Users\<YourUsername>\Mixtral AI\

2. Download the project repository ZIP file.
3. Extract all files directly into your workspace folder so the structure looks like this:

Mixtral AI/ ├── assets/ │ ├── GoogleSans-VariableFont_GRAD,opsz,wght.ttf │ ├── GoogleSansCode-VariableFont_MONO,wght.ttf │ └── ... (additional fonts) ├── wolf.png ├── connector.py ├── home.py ├── port.py ├── canvas.py ├── model_menu.py ├── settings.py 


[ 3. PYTHON ENVIRONMENT & DEPENDENCIES ]
--------------------------------------------------------------------------------
Open PowerShell / Command Prompt inside your project folder and install the required 
Python libraries:


pip install PyQt5 requests psutil 



[ 4. OLLAMA INSTALLATION & AUTHENTICATION ]
--------------------------------------------------------------------------------
1. Install Ollama:
   - Download the Windows installer from https://ollama.com/download/windows
   - Run the installer and ensure Ollama is running in your Windows System Tray.

2. Authenticate / Link your PC to Ollama:
   - Open a terminal and log into your Ollama account so your machine has access 
     to push/pull custom registry models:

 
    ollama login
 

   - Follow the prompt in your browser/terminal to authorize your machine.


[ 5. MODEL SETUP (7K, MASE, & CORES) ]
--------------------------------------------------------------------------------
The application relies on backend models for search evaluation and agentic workflows.

To add the additional models we have an Model_Installer.py which will automatically install all our models for you. just run the script.


[ 6. LAUNCHING THE APPLICATION ]
--------------------------------------------------------------------------------
1. Ensure the Ollama daemon is running in the background.
2. Ensure you have ran the Model_Installer.py by running the command

   python Model_Installer.py

4. Launch the application via terminal:

   python connector.py

5. The Mixtral desktop interface will launch and connect directly to your local Ollama port.
================================================================================

