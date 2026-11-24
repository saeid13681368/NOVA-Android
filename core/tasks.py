from pathlib import Path
from datetime import datetime
import json

ROOT = Path(__file__).resolve().parent.parent
from core.platform import data_path
LEDGER = data_path("logs/task_ledger.json", ROOT / "logs" / "task_ledger.json")

ROLES = [
    ("Problem Architect", "تعریف و تقسیم مسئله"),
    ("Researcher", "جمع‌آوری اطلاعات"),
    ("Specialist", "بررسی تخصصی"),
    ("Reasoner", "تحلیل و استدلال"),
    ("Independent Critic", "بررسی انتقادی"),
    ("Evidence Judge", "ارزیابی شواهد"),
    ("Decision Maker", "جمع‌بندی نهایی")
]

def create_task():
    question = input("\nDescribe the task: ").strip()

    if not question:
        print("Task cannot be empty.")
        return

    task = {
        "id": datetime.now().isoformat(),
        "question": question,
        "status": "PLANNED",
        "workflow": [
            {"role": role, "duty": duty}
            for role, duty in ROLES
        ]
    }

    LEDGER.parent.mkdir(parents=True, exist_ok=True)

    data = []
    if LEDGER.exists():
        data = json.loads(LEDGER.read_text(encoding="utf-8"))

    data.append(task)
    LEDGER.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\nTASK PLAN CREATED")
    for item in task["workflow"]:
        print("-", item["role"], ":", item["duty"])

    print("\nTask saved successfully.")

def show_tasks():
    if not LEDGER.exists():
        print("No tasks recorded.")
        return

    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    for task in data:
        print("\nTask:", task["question"])
        print("Status:", task["status"])

if __name__ == "__main__":
    create_task()
