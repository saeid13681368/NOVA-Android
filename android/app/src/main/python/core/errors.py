from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
from core.platform import data_path
LOG = data_path("logs/errors.log", ROOT / "logs" / "errors.log")

def record_error(message):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {message}\n")
    print("Error saved.")

def show_errors():
    if LOG.exists():
        print(LOG.read_text(encoding="utf-8"))
    else:
        print("No errors recorded.")
