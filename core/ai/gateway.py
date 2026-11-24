from abc import ABC, abstractmethod
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from core.ai.config import AI_CONFIG


NOVA_IDENTITY = """
هویت و شناسنامه اصلی تو:

نام تو NOVA است.
NOVA نام پروژه و دستیار هوش مصنوعی ساخته‌شده توسط کاربر است.
نام مدل تأمین‌کننده فقط نام موتور هوش مصنوعی است، نه نام پروژه.
کاربر سازنده و مدیر پروژه NOVA است.

مأموریت NOVA:
ساخت یک دستیار هوشمند، دقیق، امن، قابل توسعه و حقیقت‌جو.

اصول هفت‌گانه NOVA:
1. خودارتقایی تحت نظارت و تأیید کاربر
2. امنیت
3. دسترس‌پذیری
4. حقیقت‌جویی
5. خودارزیابی
6. خودترمیمی
7. آینده‌نگری

قابلیت‌های موردنظر در معماری آینده:
- کشف دانش و یافتن راه پاسخ به پرسش‌های ناشناخته
- تحلیل علمی و منطقی
- استدلال علّی
- ارزیابی مستقل و انتقاد از پاسخ‌ها
- حافظه بلندمدت و یادگیری از تجربه
- همکاری چندعامل هوش مصنوعی
- ثبت تصمیم‌ها و ارزیابی شواهد

قواعد رفتاری:
1. همیشه تا حد امکان فارسی روان بنویس.
2. حقیقت را بر جلب رضایت کاربر مقدم بدان.
3. واقعیت، احتمال، فرضیه و نظر را جدا کن.
4. اگر چیزی را نمی‌دانی، صادقانه بگو.
5. توانایی اجرا‌نشده را به‌عنوان قابلیت فعال معرفی نکن.
6. درباره دسترسی‌ها و محدودیت‌ها شفاف باش.
7. در کارهای فنی، ساده و مرحله‌به‌مرحله راهنمایی کن.
8. اطلاعات حافظه را با حدس یا اطلاعات ساختگی جایگزین نکن.
9. اگر اطلاعات حافظه با پرسش کاربر مرتبط است، از آن استفاده کن.
10. هرگز نام پروژه NOVA را با نام مدل تأمین‌کننده اشتباه نگیر.
"""


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt, history=None):
        pass


class LocalAIProvider(AIProvider):
    def generate(self, prompt, history=None):
        return {
            "success": False,
            "provider": "local",
            "message": "Local AI model is not connected yet."
        }


class CloudAIProvider(AIProvider):
    def generate(self, prompt, history=None):
        return {
            "success": False,
            "provider": "cloud",
            "message": "Cloud AI model is not connected yet."
        }


class OpenRouterAIProvider(AIProvider):
    def generate(self, prompt, history=None, model_override=None):
        api_key = AI_CONFIG["api_key"]

        if not api_key:
            return {
                "success": False,
                "provider": "openrouter",
                "message": "API key is not configured."
            }

        model = model_override or AI_CONFIG["model"] or "openrouter/free"

        system_prompt = NOVA_IDENTITY

        try:
            from memory.store import load
            memory_data = load()

            memory_text = json.dumps(
                memory_data,
                ensure_ascii=False,
                indent=2
            )

            system_prompt += (
                "\n\nحافظه ذخیره‌شده و اطلاعات تأییدشده پروژه:\n"
                + memory_text
                + "\n\nاین اطلاعات را هنگام پاسخ‌گویی در نظر بگیر."
            )
        except Exception:
            system_prompt += (
                "\n\nتوجه: حافظه در دسترس نبود؛ "
                "درباره اطلاعات ذخیره‌نشده ادعا نکن."
            )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *(history or []),
                {"role": "user", "content": prompt}
            ]
        }

        request = Request(
            AI_CONFIG["openrouter_url"],
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nova.local",
                "X-Title": "NOVA"
            },
            method="POST"
        )

        try:
            with urlopen(request, timeout=60) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            answer = result["choices"][0]["message"]["content"]

            if isinstance(answer, list):
                answer = "\n".join(
                    str(part.get("text", ""))
                    if isinstance(part, dict)
                    else str(part)
                    for part in answer
                )

            return {
                "success": True,
                "provider": "openrouter",
                "model": result.get("model", model),
                "answer": str(answer)
            }

        except HTTPError as error:
            try:
                raw_error = error.read().decode("utf-8", errors="replace")
                try:
                    detail_data = json.loads(raw_error)
                    detail = detail_data.get("error", {})
                    if isinstance(detail, dict):
                        detail = detail.get("message") or str(detail)
                    else:
                        detail = str(detail)
                except (ValueError, TypeError):
                    detail = raw_error
                detail = str(detail).strip()[:1000]
            except Exception:
                detail = "متن خطای سرویس قابل خواندن نبود."

            return {
                "success": False,
                "provider": "openrouter",
                "message": "API request failed with HTTP status "
                           + str(error.code)
                           + (": " + detail if detail else "")
            }
        except URLError:
            return {
                "success": False,
                "provider": "openrouter",
                "message": "Network connection failed."
            }
        except (KeyError, IndexError, ValueError, TimeoutError):
            return {
                "success": False,
                "provider": "openrouter",
                "message": "Invalid response or request timed out."
            }


class AIGateway:
    def __init__(self):
        self.history = []
        self.providers = {
            "local": LocalAIProvider(),
            "cloud": CloudAIProvider(),
            "openrouter": OpenRouterAIProvider()
        }

    def ask(self, prompt, provider="local", model_override=None):
        if not prompt or not prompt.strip():
            return {
                "success": False,
                "message": "Prompt cannot be empty."
            }

        selected = self.providers.get(provider)

        if selected is None:
            return {
                "success": False,
                "message": "Unknown AI provider."
            }

        if provider == "openrouter":
            result = selected.generate(
                prompt, self.history, model_override=model_override
            )
        else:
            result = selected.generate(prompt, self.history)

        if result.get("success"):
            self.history.append({
                "role": "user",
                "content": prompt
            })
            self.history.append({
                "role": "assistant",
                "content": result.get("answer", "")
            })
            self.history = self.history[-20:]

        return result


if __name__ == "__main__":
    gateway = AIGateway()
    print(
        gateway.ask(
            "نام پروژه من چیست؟",
            provider="openrouter"
        )
    )
