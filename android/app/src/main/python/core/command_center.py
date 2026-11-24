from pathlib import Path
from datetime import datetime
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

class NOVACommandCenter:

    def __init__(self):
        from core.ai.gateway import AIGateway
        self.ai_gateway = AIGateway()
        self.modules = {
            "Main Core": ROOT / "core/main.py",
            "Central Brain": ROOT / "core/brain.py",
            "Memory": ROOT / "memory/store.py",
            "Error Manager": ROOT / "core/errors.py",
            "Installer": ROOT / "installer/build.py"
        }

    def show_status(self):
        print("\n" + "=" * 40)
        print("       NOVA COMMAND CENTER")
        print("=" * 40)
        print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        for name, path in self.modules.items():
            status = "READY" if path.exists() else "MISSING"
            print(f"{name}: {status}")

        print("=" * 40)

    def show_menu(self):
        while True:
            self.show_status()

            print("\n1. Show Brain Teams")
            print("2. Show Memory")
            print("3. Show Errors")
            print("4. Exit")
            print("5. Create Task")
            print("6. Show Tasks")
            print("7. Talk to NOVA AI")

            choice = input("\nSelect: ").strip()

            if choice == "1":
                from core.brain import NOVABrain
                NOVABrain().status()

            elif choice == "2":
                from memory.store import show
                show()

            elif choice == "3":
                from core.errors import show_errors
                show_errors()

            elif choice == "5":
                from core.tasks import create_task
                create_task()

            elif choice == "6":
                from core.tasks import show_tasks
                show_tasks()

            elif choice == "7":
                prompt = input("\nYour question: ").strip()
                if prompt.startswith("/remember "):
                    from memory.store import remember
                    note = prompt[len("/remember "):].strip()
                    if note:
                        remember(note)
                        print("NOVA: یادداشت ذخیره شد.")
                    else:
                        print("متن یادداشت خالی است.")

                elif prompt == "/memory":
                    from memory.store import show
                    show()

                elif prompt.startswith("/forget "):
                    from memory.store import forget
                    note = prompt[len("/forget "):].strip()
                    if forget(note):
                        print("NOVA: یادداشت حذف شد.")
                    else:
                        print("این یادداشت پیدا نشد.")

                elif prompt:
                    result = self.ai_gateway.ask(prompt, provider="openrouter")
                    if result.get("success"):
                        print("\nNOVA:", result.get("answer", "No answer returned."))
                    else:
                        print("\nAI Error:", result.get("message", "Unknown error."))
                else:
                    print("Empty question.")

            elif choice == "4":
                print("NOVA Command Center closed.")
                break

            else:
                print("Invalid choice.")

            input("\nPress Enter to continue...")

if __name__ == "__main__":
    NOVACommandCenter().show_menu()
