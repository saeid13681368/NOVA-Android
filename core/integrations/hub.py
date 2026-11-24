import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
from core.platform import data_path
REGISTRY = data_path("integrations/registry.json", ROOT / "registry.json")

DEFAULTS = {
    "openrouter": {"name": "OpenRouter", "category": "AI", "status": "existing_gateway", "permissions": []},
    "gemini": {"name": "Google Gemini", "category": "AI", "status": "planned", "permissions": []},
    "deepseek": {"name": "DeepSeek", "category": "AI", "status": "planned", "permissions": []},
    "android": {"name": "Android Bridge", "category": "Device", "status": "planned", "permissions": []},
    "files": {"name": "File Manager", "category": "Storage", "status": "planned", "permissions": []},
    "web": {"name": "Web Research", "category": "Research", "status": "planned", "permissions": []},
    "gmail": {"name": "Gmail", "category": "Productivity", "status": "planned", "permissions": []},
    "calendar": {"name": "Google Calendar", "category": "Productivity", "status": "planned", "permissions": []}
}

class IntegrationHub:
    def __init__(self):
        self.adapters = {}
        self.data = self._load()

    def _load(self):
        if REGISTRY.exists():
            try:
                data = json.loads(REGISTRY.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("connectors"), dict):
                    return data
            except (ValueError, OSError):
                pass
        return {"version": 1, "connectors": dict(DEFAULTS)}

    def _save(self):
        temp = REGISTRY.with_suffix(".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(REGISTRY)

    def list_connectors(self):
        return self.data["connectors"]

    def register(self, connector_id, name, category, adapter=None):
        if not connector_id.replace("_", "").isalnum():
            raise ValueError("Invalid connector ID")
        item = self.data["connectors"].setdefault(connector_id, {})
        item.update({"name": name, "category": category, "status": "registered"})
        self.adapters[connector_id] = adapter if adapter is not None else self.adapters.get(connector_id)
        self._save()
        return True

    def authorize(self, connector_id, permissions):
        item = self.data["connectors"].get(connector_id)
        if item is None:
            raise KeyError("Connector not found")
        if not isinstance(permissions, list) or not all(isinstance(x, str) for x in permissions):
            raise ValueError("Permissions must be a list of strings")
        item["permissions"] = sorted(set(permissions))
        item["authorized_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return True

    def revoke(self, connector_id):
        item = self.data["connectors"].get(connector_id)
        if item is None:
            raise KeyError("Connector not found")
        item["permissions"] = []
        item.pop("authorized_at", None)
        self._save()
        return True

    def call(self, connector_id, action, payload=None, required_permission=None):
        item = self.data["connectors"].get(connector_id)
        if item is None:
            return {"success": False, "error": "Connector not registered"}
        if required_permission and required_permission not in item.get("permissions", []):
            return {"success": False, "error": "Permission denied"}
        adapter = self.adapters.get(connector_id)
        if adapter is None:
            return {"success": False, "error": "Connector adapter not implemented"}
        try:
            return {"success": True, "result": adapter(action, payload or {})}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

def get_hub():
    return IntegrationHub()
