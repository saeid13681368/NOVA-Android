
import json
from datetime import datetime, timezone
from pathlib import Path

from core.ai.gateway import AIGateway
from core.platform import data_path

class MultiModelEngine:
    def __init__(self):
        self.gateway = AIGateway()
        self.history_file = data_path("memory/model_comparisons.json", Path("memory/model_comparisons.json"))
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load()

    def _load(self):
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def _save(self):
        temp = self.history_file.with_suffix(".tmp")
        temp.write_text(
            json.dumps(self.history[-100:], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        temp.replace(self.history_file)

    def compare(self, prompt, providers=None):
        if not isinstance(prompt, str) or not prompt.strip():
            return {"success": False, "error": "Prompt is required"}

        providers = providers or ["openrouter"]
        results = {}

        for provider in providers:
            response = self.gateway.ask(prompt, provider=provider)
            results[provider] = {
                "success": bool(response.get("success")),
                "answer": response.get("answer", ""),
                "error": response.get("message", "")
            }

        successful = {
            name: item["answer"]
            for name, item in results.items()
            if item["success"]
        }

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "results": results,
            "successful_models": list(successful.keys())
        }

        self.history.append(record)
        self._save()

        return {
            "success": bool(successful),
            "results": results,
            "successful_models": list(successful.keys()),
            "comparison_note": (
                "Only one model answered; independent agreement cannot be assessed."
                if len(successful) < 2
                else "Multiple responses collected; differences require evidence-based review."
            )
        }

    def recent(self, limit=10):
        return self.history[-max(1, min(int(limit), 100)):]

def get_multi_model_engine():
    return MultiModelEngine()
