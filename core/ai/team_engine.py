from core.brain import NOVABrain


class NOVATeamEngine:
    def __init__(self):
        self.brain = NOVABrain()

    def get_teams(self):
        return self.brain.teams

    def build_team_prompt(self, prompt):
        text = prompt.strip()

        # Fast path for simple questions
        complex_markers = (
            "تحلیل", "مقایسه", "طراحی", "بررسی", "اثبات",
            "برنامه", "پروژه", "علت", "چرا", "چگونه",
            "امنیت", "علمی", "فلسفی", "پزشکی", "حقوقی"
        )

        if len(text) < 180 and not any(
            marker in text for marker in complex_markers
        ):
            return (
                "تو NOVA هستی. دقیق، روشن و مستقیم پاسخ بده. "
                "برای سؤال ساده پاسخ کوتاه بده. "
                "اگر مطمئن نیستی صادقانه بگو.\n\n"
                "سؤال کاربر:\n" + text
            )

        instructions = [
            "تو هماهنگ‌کننده تحلیل هفت‌نقشی NOVA هستی.",
            "هر هفت نقش را در یک پاسخ منظم بررسی کن.",
            "از تکرار و توضیحات غیرضروری خودداری کن.",
            "اختلاف‌نظر و عدم قطعیت مهم را حفظ کن.",
            "در پایان نتیجه، محدودیت‌ها و میزان اطمینان را بگو.",
            "ادعا نکن عامل‌های مستقل واقعاً اجرا شده‌اند."
        ]

        for index, team in enumerate(self.get_teams(), 1):
            instructions.append(
                f"{index}. {team['name_fa']}: {team['mission']}"
            )

        instructions.append("\nمسئله کاربر:\n" + text)
        return "\n".join(instructions)


if __name__ == "__main__":
    engine = NOVATeamEngine()
    print(engine.build_team_prompt("یک مسئله آزمایشی"))
