from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.ai.gateway import AIGateway

def show_ai_status():
    gateway = AIGateway()

    print("\n===== NOVA AI STATUS =====")

    for name in gateway.providers:
        print(f"{name.upper()}: Registered")

    print("\nRegistered does not mean connected.")
    print("No real AI model is connected yet.")

if __name__ == "__main__":
    show_ai_status()
