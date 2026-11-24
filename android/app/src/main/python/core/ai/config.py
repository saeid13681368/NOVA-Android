import os
from pathlib import Path

from core.platform import data_path
_legacy_key = Path.home() / ".config" / "nova" / "api_key" if not os.getenv("NOVA_DATA_DIR") else None
KEY_FILE = data_path("config/api_key", _legacy_key)

def load_api_key():
    key = os.getenv("NOVA_API_KEY", "").strip()
    if key:
        return key
    try:
        return KEY_FILE.read_text().strip()
    except FileNotFoundError:
        return ""

AI_CONFIG = {
    "provider": os.getenv("NOVA_AI_PROVIDER", "openrouter"),
    "model": os.getenv("NOVA_AI_MODEL", "openrouter/free"),
    "local_url": os.getenv("NOVA_LOCAL_URL", ""),
    "cloud_url": os.getenv("NOVA_CLOUD_URL", ""),
    "api_key": load_api_key(),
    "openrouter_url": "https://openrouter.ai/api/v1/chat/completions"
}

def save_api_key(value):
    key = value.strip() if isinstance(value, str) else ""
    if len(key) < 8 or len(key) > 500:
        raise ValueError("کلید API معتبر نیست")
    if any(ord(c) < 32 or ord(c) == 127 for c in key):
        raise ValueError("ساختار کلید API معتبر نیست")

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = KEY_FILE.with_name(KEY_FILE.name + ".tmp")

    try:
        with temporary.open("w", encoding="utf-8") as file:
            file.write(key)
            file.flush()
            os.fsync(file.fileno())

        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass

        os.replace(temporary, KEY_FILE)

        try:
            os.chmod(KEY_FILE, 0o600)
        except OSError:
            pass

        AI_CONFIG["api_key"] = key
        AI_CONFIG["provider"] = "openrouter"
    finally:
        temporary.unlink(missing_ok=True)


def show_config():

    print("\n===== NOVA AI CONFIG =====")
    print("Provider:", AI_CONFIG["provider"])
    print("Model:", AI_CONFIG["model"] or "Not selected")
    print("Local URL:", AI_CONFIG["local_url"] or "Not configured")
    print("Cloud URL:", AI_CONFIG["cloud_url"] or "Not configured")
    print("OpenRouter API Key:", "Configured" if AI_CONFIG["api_key"] else "Not configured")

if __name__ == "__main__":
    show_config()
