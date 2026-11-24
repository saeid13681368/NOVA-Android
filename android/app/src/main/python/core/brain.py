class NOVABrain:
    teams = [
        {
            "id": "problem_architect",
            "name": "Problem Architect",
            "name_fa": "معمار مسئله",
            "mission": "تعریف دقیق مسئله، شکستن آن به بخش‌های کوچک و تعیین مسیر حل."
        },
        {
            "id": "researcher",
            "name": "Researcher",
            "name_fa": "پژوهشگر",
            "mission": "شناسایی اطلاعات موردنیاز، جست‌وجوی منابع و گردآوری شواهد."
        },
        {
            "id": "specialist",
            "name": "Specialist",
            "name_fa": "متخصص",
            "mission": "تحلیل تخصصی موضوع با توجه به دانش و حوزه مربوط."
        },
        {
            "id": "reasoner",
            "name": "Reasoner",
            "name_fa": "استدلال‌گر",
            "mission": "بررسی منطقی، تحلیل فرضیه‌ها و ساختن استدلال معتبر."
        },
        {
            "id": "independent_critic",
            "name": "Independent Critic",
            "name_fa": "منتقد مستقل",
            "mission": "جست‌وجوی خطاها، تناقض‌ها، سوگیری‌ها و فرض‌های اثبات‌نشده."
        },
        {
            "id": "evidence_judge",
            "name": "Evidence Judge",
            "name_fa": "داور شواهد",
            "mission": "ارزیابی کیفیت منابع، قدرت شواهد و میزان اطمینان به نتایج."
        },
        {
            "id": "decision_maker",
            "name": "Decision Maker",
            "name_fa": "تصمیم‌گیرنده",
            "mission": "جمع‌بندی دیدگاه‌ها و ارائه پاسخ نهایی همراه با محدودیت‌ها."
        }
    ]

    def status(self):
        print("\n" + "=" * 48)
        print("          NOVA CENTRAL BRAIN")
        print("          SEVEN INTELLIGENCE ROLES")
        print("=" * 48)

        for index, team in enumerate(self.teams, 1):
            print(f"\n{index}. {team['name_fa']} ({team['name']})")
            print("   وظیفه:", team["mission"])

        print("\n" + "=" * 48)
        print("STATUS: ROLE STRUCTURE READY")
        print("NOTE: Roles are defined; independent AI agents are not yet implemented.")
        print("=" * 48)


if __name__ == "__main__":
    NOVABrain().status()
