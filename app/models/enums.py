from enum import StrEnum


class SubscriptionType(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


class SessionState(StrEnum):
    START = "start"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_OTP = "awaiting_otp"
    AWAITING_NAME = "awaiting_name"
    AUTHENTICATED_MENU = "authenticated_menu"
    CHOOSING_IMMIGRATION_METHOD = "choosing_immigration_method"
    IN_CONSULTATION = "in_consultation"


class ConsultationStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
