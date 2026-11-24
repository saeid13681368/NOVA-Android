import json
import os
from pathlib import Path

from core.platform import data_path

FILE = data_path("memory/memory.json", Path(__file__).parent / "memory.json")

def load():
    if FILE.exists():
        return json.loads(FILE.read_text(encoding="utf-8"))
    return {}

def save(key, value):
    data = load()
    data[key] = value

    temp = FILE.with_name(FILE.name + ".tmp")
    try:
        with temp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        temp.replace(FILE)
    finally:
        if temp.exists():
            temp.unlink()

def remember(note):
    data = load()
    notes = data.get("user_notes", [])
    if note not in notes:
        notes.append(note)
    save("user_notes", notes)

def forget(note):
    data = load()
    notes = data.get("user_notes", [])
    if note not in notes:
        return False
    notes.remove(note)
    save("user_notes", notes)
    return True

def show():
    print(json.dumps(load(), ensure_ascii=False, indent=2))
