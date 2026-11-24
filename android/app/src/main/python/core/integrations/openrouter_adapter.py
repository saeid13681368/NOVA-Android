from core.ai.gateway import AIGateway

class OpenRouterAdapter:
    def __init__(self):
        self.gateway = AIGateway()

    def __call__(self, action, payload):
        if action != "chat":
            return {"success": False, "error": "Unsupported action"}
        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            return {"success": False, "error": "Prompt is required"}
        return self.gateway.ask(prompt, provider="openrouter")
