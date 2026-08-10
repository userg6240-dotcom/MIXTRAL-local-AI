# 🐺 Dex Core (Local AI Desktop Assistant)

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green?style=for-the-badge&logo=qt)
![Ollama](https://img.shields.io/badge/Local_LLM-Ollama-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**Dex Core** is a fully autonomous, locally hosted AI desktop assistant built in Python. Designed with a hyper-modern, cyberpunk-inspired UI, Dex doesn't just chat—it acts. Using advanced tool-calling and system-level interceptors, Dex can write code, execute Windows commands, bypass OS restrictions, and navigate the web completely independent of cloud APIs.

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

1. **Clone the repository:**
   ```bash
git clone https://github.com/user6240-dotcom/dex-core.git
