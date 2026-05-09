from dataclasses import dataclass

from app.bale.keyboards import METHOD_LABELS


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str


COMMON_QUESTIONS = [
    Question("age", "سن شما چند سال است؟"),
    Question("family_status", "وضعیت خانوادگی شما چیست؟ مجرد، متاهل یا همراه با فرزند؟"),
    Question("education", "آخرین مدرک تحصیلی و رشته شما چیست؟"),
    Question("english_level", "سطح زبان انگلیسی یا زبان کشور مقصد شما چقدر است؟"),
    Question("budget", "بودجه تقریبی شما برای مهاجرت چقدر است؟"),
    Question("preferred_countries", "اگر کشور یا منطقه خاصی مدنظر دارید، نام ببرید."),
]

CATEGORY_SPECIFIC_QUESTIONS = {
    "work": [
        Question("work_experience", "چند سال سابقه کار مرتبط دارید و عنوان شغلی شما چیست؟"),
        Question("job_offer", "آیا پیشنهاد شغلی معتبر از خارج از کشور دارید؟"),
    ],
    "study": [
        Question("target_degree", "برای چه مقطع یا رشته ای قصد ادامه تحصیل دارید؟"),
        Question("gpa", "معدل تقریبی آخرین مقطع تحصیلی شما چقدر است؟"),
    ],
    "investment": [
        Question("investment_amount", "مبلغ قابل سرمایه گذاری شما تقریبا چقدر است؟"),
        Question("business_background", "آیا سابقه مالکیت کسب وکار یا مدیریت شرکت دارید؟"),
    ],
    "startup": [
        Question("startup_stage", "ایده یا استارتاپ شما در چه مرحله ای است؟ ایده، MVP، درآمد یا رشد؟"),
        Question("team_profile", "تیم شما چه تخصص هایی دارد و چند نفر هستید؟"),
    ],
    "permanent_residency": [
        Question("current_status", "در حال حاضر اقامت یا ویزای کشوری را دارید؟"),
        Question("ties", "آیا سابقه کار، تحصیل یا خانواده در کشور مقصد دارید؟"),
    ],
}


class ImmigrationWorkflow:
    def questions_for(self, category: str) -> list[Question]:
        return [
            *COMMON_QUESTIONS,
            *CATEGORY_SPECIFIC_QUESTIONS.get(category, []),
        ]

    def first_question(self, category: str) -> Question:
        return self.questions_for(category)[0]

    def next_question(self, category: str, answered_keys: set[str]) -> Question | None:
        for question in self.questions_for(category):
            if question.key not in answered_keys:
                return question
        return None

    def category_label(self, category: str) -> str:
        return METHOD_LABELS.get(category, category)
