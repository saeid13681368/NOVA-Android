import json
import os
import re
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

from core.ai.gateway import AIGateway
from core.ai.config import AI_CONFIG
from core.platform import data_dir, data_path

ROOT = Path(__file__).resolve().parents[2]
DATA = data_dir() / "data"
DATA.mkdir(parents=True, exist_ok=True)
LEDGER = data_path("data/evidence_ledger.jsonl", ROOT / "data" / "evidence_ledger.jsonl")
MULTI_ON = data_path("data/MULTIMODEL_ENABLED", ROOT / "data" / "MULTIMODEL_ENABLED")
EMERGENCY_STOP = data_path("data/MULTIMODEL_STOP", ROOT / "data" / "MULTIMODEL_STOP")

PRIMARY_MODEL = AI_CONFIG.get("model", "openrouter/free")

def get_primary_model():
    return AI_CONFIG.get("model") or "openrouter/free"

REVIEW_MODEL = os.getenv(
    "NOVA_AI_REVIEW_MODEL", "openai/gpt-4.1-mini"
)

BENCHMARK = [
    "آیا همه پستانداران تخم‌گذار هستند؟ پاسخ را با توضیح کوتاه بده.",
    "اگر همه Aها B باشند و همه Bها C باشند، درباره A و C چه نتیجه‌ای می‌گیریم؟",
    "تفاوت همبستگی و رابطه علت و معلولی چیست؟",
    "آیا از یک نمونه می‌توان درباره همه اعضای یک جامعه نتیجه قطعی گرفت؟",
    "عدد بعدی در دنباله 2، 4، 8، 16 چیست و چرا؟",
    "تفاوت واقعیت، فرضیه و نظر شخصی چیست؟",
    "چرا برای ادعاهای علمی به منبع معتبر نیاز داریم؟",
    "آیا نبود شواهد همیشه به معنی اثبات نبودن یک چیز است؟",
    "اگر قیمت کالایی ۲۰۰ واحد باشد و ۱۰ درصد افزایش یابد، قیمت جدید چقدر است؟",
    "چگونه می‌توان یک پاسخ هوش مصنوعی را راستی‌آزمایی کرد؟",
    "تفاوت حافظه کوتاه‌مدت و بلندمدت در رایانه چیست؟",
    "چرا باید نسخه پشتیبان از فایل‌های مهم نگه داشت؟",
    "اگر یک برنامه خطای شبکه بدهد، چه علت‌هایی ممکن است داشته باشد؟",
    "آیا پاسخ روان و مطمئن الزاماً پاسخ درست است؟",
    "تفاوت رمزگذاری و هش‌کردن چیست؟",
    "چرا آزمایش باید متغیرهای کنترل‌شده داشته باشد؟",
    "اگر ۳ کارگر کاری را در ۶ ساعت انجام دهند، آیا ۶ کارگر حتماً آن را در ۳ ساعت تمام می‌کنند؟ توضیح بده.",
    "یک استدلال دوری چیست؟ یک نمونه ساده بیان کن.",
    "چرا باید عدم قطعیت در پاسخ‌های علمی بیان شود؟",
    "تفاوت مدل زبانی و موتور جست‌وجو چیست؟",
    "اگر دو منبع معتبر با هم اختلاف داشته باشند، چه باید کرد؟",
    "آیا می‌توان از یک آزمایش محدود قانون همگانی استخراج کرد؟",
    "برای مقایسه دو مدل هوش مصنوعی چه معیارهایی لازم است؟",
    "چرا زمان پاسخ به‌تنهایی معیار کیفیت هوش مصنوعی نیست؟",
    "اگر مدل دوم پاسخ مدل اول را تأیید کند، آیا پاسخ قطعاً درست است؟",
    "چگونه می‌توان جلوی تغییر ناخواسته فایل‌های اصلی را گرفت؟",
    "تفاوت خطای برنامه و خطای سرویس بیرونی چیست؟",
    "چرا ثبت نسخه مدل و زمان تولید پاسخ اهمیت دارد؟",
    "در چه شرایطی پاسخ ندادن بهتر از حدس زدن است؟",
    "چگونه می‌توان یک قابلیت جدید را بدون خراب کردن نسخه پایدار آزمایش کرد؟"
]

def state():
    return {
        "mode": "emergency-stop" if EMERGENCY_STOP.exists()
                else "multi-model" if MULTI_ON.exists()
                else "single-model",
        "primary_model": get_primary_model(),
        "review_model": REVIEW_MODEL,
        "ledger": str(LEDGER)
    }

def set_mode(mode):
    DATA.mkdir(parents=True, exist_ok=True)
    if mode == "stop":
        EMERGENCY_STOP.write_text("STOP\n", encoding="utf-8")
        MULTI_ON.unlink(missing_ok=True)
    elif mode == "single":
        MULTI_ON.unlink(missing_ok=True)
        EMERGENCY_STOP.unlink(missing_ok=True)
    elif mode == "multi":
        EMERGENCY_STOP.unlink(missing_ok=True)
        MULTI_ON.write_text("ENABLED\n", encoding="utf-8")
    else:
        raise ValueError("mode must be stop, single, or multi")
    return state()

def save_evidence(record):
    DATA.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def run(prompt, gateway=None):
    # Emergency stop must block every outgoing AI request.
    if EMERGENCY_STOP.exists():
        return {
            "success": False,
            "provider": "openrouter",
            "error_code": "emergency_stop",
            "message": "توقف اضطراری فعال است؛ هیچ درخواست هوش مصنوعی ارسال نشد."
        }

    gateway = gateway or AIGateway()
    primary_model = get_primary_model()

    # Single-model mode: one primary request, no reviewer.
    if not MULTI_ON.exists():
        result = gateway.ask(
            prompt,
            provider="openrouter",
            model_override=primary_model
        )

        if result.get("success"):
            actual_model = result.get("model") or primary_model
            result["runtime_identity"] = {
                "provider": "openrouter",
                "mode": "single-model",
                "configured_model": primary_model,
                "reported_model": actual_model,
                "model_status": "verified",
                "primary_configured": primary_model,
                "primary_reported": actual_model,
                "review_configured": REVIEW_MODEL,
                "review_status": "not_requested",
                "final_model": actual_model
            }

        return result

    if not REVIEW_MODEL or REVIEW_MODEL == primary_model:
        return {
            "success": False,
            "message": "مدل بازبین باید با مدل اصلی متفاوت باشد."
        }

    first = gateway.ask(
        prompt, provider="openrouter", model_override=primary_model
    )
    if not first.get("success"):
        return first

    reviewer = AIGateway()
    review_prompt = (
        "تو بازبین NOVA هستی. پاسخ اولیه را از نظر منطق، "
        "دقت، تناقض و عدم قطعیت بررسی کن. اگر اشتباه دارد اصلاح کن. "
        "منبعی را که واقعاً بررسی نکرده‌ای جعل نکن. "
        "در پایان سطح اطمینان خود را فقط به‌عنوان برآورد شخصی مدل "
        "و نه احتمال علمی کالیبره‌شده اعلام کن.\n\n"
        "پرسش کاربر:\n" + prompt +
        "\n\nپاسخ اولیه مدل اول:\n" + str(first.get("answer", ""))
    )

    second = reviewer.ask(
        review_prompt, provider="openrouter", model_override=REVIEW_MODEL
    )

    primary_actual = first.get("model") or primary_model

    if second.get("success"):
        answer = second.get("answer", "")
        review_status = "reviewed"
        reviewer_actual = second.get("model") or REVIEW_MODEL
        final_model = reviewer_actual
    else:
        answer = first.get("answer", "")
        review_status = "review-failed-fallback"
        reviewer_actual = None
        final_model = primary_actual

    urls = sorted(set(re.findall(r"https?://\S+", answer)))
    record = {
        "record_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primary_model": primary_actual,
        "review_model": reviewer_actual or REVIEW_MODEL,
        "status": review_status,
        "source_verification": "not_verified",
        "confidence": "not_calibrated"
    }
    save_evidence(record)

    return {
        "success": True,
        "provider": "openrouter",
        "model": final_model,
        "answer": answer,
        "runtime_identity": {
            "provider": "openrouter",
            "mode": "multi-model",
            "configured_model": primary_model,
            "reported_model": final_model,
            "model_status": "verified",
            "primary_configured": primary_model,
            "primary_reported": primary_actual,
            "review_configured": REVIEW_MODEL,
            "review_reported": reviewer_actual,
            "review_status": review_status,
            "final_model": final_model
        },
        "trace": [
            {"speaker": "NOVA | هماهنگی", "text": "دو مدل متفاوت برای پاسخ و بازبینی به کار گرفته شدند."},
            {"speaker": "مدل اول | " + str(primary_actual), "text": str(first.get("answer", ""))},
            {"speaker": "مدل دوم | " + str(reviewer_actual or REVIEW_MODEL), "text": answer if second.get("success") else "بازبینی ناموفق بود؛ پاسخ مدل اول حفظ شد."},
            {"speaker": "NOVA | ثبت شواهد", "text": "نتیجه ثبت شد؛ اعتبار منابع و میزان اطمینان هنوز مستقلاً راستی‌آزمایی نشده است."}
        ]
    }

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    if command in ("stop", "single", "multi"):
        print(json.dumps(set_mode(command), ensure_ascii=False, indent=2))
    elif command == "status":
        print(json.dumps(state(), ensure_ascii=False, indent=2))
    elif command == "benchmark":
        print(json.dumps(BENCHMARK, ensure_ascii=False, indent=2))
    else:
        print("Usage: python -m core.ai.multimodel [status|single|multi|stop|benchmark]")

if __name__ == "__main__":
    main()
