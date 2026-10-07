import sys
import json
import requests

# ANSI Color formatting for a sleek CLI aesthetic
BLUE = '\033[94m'
GREEN = '\033[92m'
GRAY = '\033[90m'
RESET = '\033[0m'
BOLD = '\033[1m'

OLLAMA_API = "http://localhost:11434/api/chat"

def start_maxdev_env(model_name: str):
    # Clear terminal screen for a fresh environment
    print('\033[2J\033[H', end='')
    print(f"{BLUE}{BOLD}MaxDev Terminal Environment{RESET} (Connected: {GREEN}{model_name}{RESET})")
    print(f"{GRAY}Type 'exit' or press Ctrl+C to close.{RESET}\n")
    
    messages = []
    
    while True:
        try:
            # Claude-style minimalist prompt
            user_input = input(f"\n{BOLD}❯ {RESET}")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})
            
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": True,
                "options": {"temperature": 0.2}
            }
            
            print(f"{BLUE}MaxDev ❯ {RESET}", end="", flush=True)
            
            # Stream the response directly to the console
            response = requests.post(OLLAMA_API, json=payload, stream=True)
            response.raise_for_status()
            
            full_reply = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    print(content, end="", flush=True)
                    full_reply += content
            
            print() 
            messages.append({"role": "assistant", "content": full_reply})
            
        except KeyboardInterrupt:
            print(f"\n{GRAY}Session terminated.{RESET}")
            break
        except requests.exceptions.RequestException as e:
            print(f"\n{GRAY}[!] Connection to Ollama failed: {e}{RESET}")
            break

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1].lower() != "run":
        print(f"Usage: {BOLD}maxdev run <model_name>{RESET}")
        sys.exit(1)
        
    target_model = sys.argv[2]
    start_maxdev_env(target_model)