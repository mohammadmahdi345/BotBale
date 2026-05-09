IMMIGRATION_KEYWORDS = {
    "مهاجرت",
    "ویزا",
    "اقامت",
    "پناهندگی",
    "تحصیل",
    "کاری",
    "کار",
    "سرمایه",
    "استارتاپ",
    "کانادا",
    "آلمان",
    "استرالیا",
    "انگلیس",
    "آمریکا",
    "اروپا",
    "ترکیه",
    "دبی",
    "امارات",
    "ielts",
    "toefl",
    "study permit",
    "work permit",
    "visa",
    "immigration",
    "migration",
    "residency",
    "citizenship",
    "asylum",
}


class TopicGuard:
    refusal_message = (
        "من فقط برای مشاوره مهاجرت و امور مرتبط با ویزا، اقامت، تحصیل، کار، سرمایه گذاری "
        "و انتخاب کشور مناسب طراحی شده ام. لطفا سوال خود را در همین حوزه مطرح کنید."
    )

    def is_immigration_related(self, text: str) -> bool:
        normalized = text.casefold()
        return any(keyword.casefold() in normalized for keyword in IMMIGRATION_KEYWORDS)
