import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def data_dir():
    configured = os.environ.get("NOVA_DATA_DIR", "").strip()
    if configured:
        path = Path(configured).expanduser()
    else:
        path = Path.home() / ".local" / "share" / "nova"
    path.mkdir(parents=True, exist_ok=True)
    return path

def data_path(relative, legacy=None):
    target = data_dir() / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() and legacy is not None:
        source = Path(legacy).expanduser()
        if source.is_file():
            shutil.copy2(source, target)
    return target
