from app.schemas.bale import ReplyKeyboardMarkup

START_BUTTON = "شروع / ورود"
REQUEST_PHONE_BUTTON = "ارسال شماره موبایل"
BEST_COUNTRY_BUTTON = "انتخاب بهترین کشور بر اساس روش مهاجرت"
ASK_AI_BUTTON = "سوال آزاد مهاجرتی از مشاور هوشمند"
PROFILE_BUTTON = "وضعیت حساب و اشتراک"
CANCEL_BUTTON = "لغو مشاوره"

METHOD_LABELS = {
    "work": "مهاجرت کاری",
    "study": "مهاجرت تحصیلی",
    "investment": "مهاجرت سرمایه گذاری",
    "startup": "ویزای استارتاپ",
    "permanent_residency": "اقامت دائم",
}


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[START_BUTTON]])


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [{"text": REQUEST_PHONE_BUTTON, "request_contact": True}],
            ["شماره را دستی وارد می کنم"],
        ],
        one_time_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [BEST_COUNTRY_BUTTON],
            [ASK_AI_BUTTON],
            [PROFILE_BUTTON],
        ]
    )


def immigration_method_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [METHOD_LABELS["work"], METHOD_LABELS["study"]],
            [METHOD_LABELS["investment"], METHOD_LABELS["startup"]],
            [METHOD_LABELS["permanent_residency"]],
            [CANCEL_BUTTON],
        ]
    )


def method_from_label(label: str) -> str | None:
    for key, value in METHOD_LABELS.items():
        if label == value:
            return key
    return None
