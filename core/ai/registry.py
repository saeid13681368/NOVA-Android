import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from core.platform import data_path
REGISTRY = data_path("memory/model_registry.json", ROOT / "memory" / "model_registry.json")

def load_models():
    if not REGISTRY.exists():
        return []

    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        print("Registry file could not be read safely.")
        return []

def save_models(models):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(
        json.dumps(models, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def save_model(name, provider, model_type, status="NOT_CONNECTED"):
    models = load_models()

    for model in models:
        if (
            model["name"].lower() == name.lower()
            and model["provider"].lower() == provider.lower()
        ):
            model.update({
                "type": model_type,
                "status": status
            })
            save_models(models)
            print("Existing model updated.")
            return

    models.append({
        "name": name,
        "provider": provider,
        "type": model_type,
        "status": status
    })

    save_models(models)
    print("New model registered.")

def search_models(name):
    for model in load_models():
        if name.lower() in model["name"].lower():
            print(model)

def remove_model(name, provider):
    models = load_models()
    updated = [
        model for model in models
        if not (
            model["name"].lower() == name.lower()
            and model["provider"].lower() == provider.lower()
        )
    ]

    if len(updated) == len(models):
        print("Model not found.")
    else:
        save_models(updated)
        print("Model removed.")

def show_models():
    print("\n===== NOVA MODEL REGISTRY =====")
    models = load_models()

    if not models:
        print("No models registered.")
        return

    for model in models:
        print(
            f"{model['name']} | "
            f"{model['provider']} | "
            f"{model['type']} | "
            f"{model['status']}"
        )

if __name__ == "__main__":
    show_models()
