from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.bale.keyboards import (
    ASK_AI_BUTTON,
    BEST_COUNTRY_BUTTON,
    CANCEL_BUTTON,
    PROFILE_BUTTON,
    START_BUTTON,
    immigration_method_keyboard,
    main_menu_keyboard,
    method_from_label,
    phone_keyboard,
)
from app.config.settings import Settings
from app.core.security import SecurityError, phone_hash, utc_now
from app.models import (
    Consultation,
    ConsultationStatus,
    ConversationSession,
    MessageDirection,
    SessionState,
    User,
)
from app.repositories.logs import ConversationLogRepository
from app.repositories.sessions import SessionRepository
from app.repositories.users import UserRepository
from app.schemas.bale import BaleMessage, BaleUpdate, ReplyKeyboardMarkup
from app.services.ai import AIConsultant
from app.services.auth import AuthenticationError, AuthService
from app.services.topic_guard import TopicGuard
from app.services.usage import UsageLimitService
from app.workflows.immigration import ImmigrationWorkflow


@dataclass(frozen=True)
class OutboundMessage:
    chat_id: str
    text: str
    reply_markup: ReplyKeyboardMarkup | None = None
    metadata: dict | None = None


class BotService:
    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.sessions = SessionRepository(db, settings)
        self.users = UserRepository(db)
        self.logs = ConversationLogRepository(db)
        self.auth = AuthService(db, settings)
        self.usage = UsageLimitService(db, settings)
        self.guard = TopicGuard()
        self.ai = AIConsultant(settings)
        self.workflow = ImmigrationWorkflow()

    async def handle_update(self, update: BaleUpdate) -> list[OutboundMessage]:
        message = self._extract_message(update)
        if message is None:
            return []

        chat_id = str(message.chat.id)
        text = self._message_text(message).strip()
        session = await self.sessions.get_or_create(chat_id)
        self._expire_session_if_needed(session)
        self.sessions.refresh(session)

        self.logs.add(
            bale_chat_id=chat_id,
            direction=MessageDirection.INBOUND,
            message_text=text or "[non-text message]",
            user_id=session.user_id,
            metadata={"update_id": update.update_id},
        )

        if text in {"/start", START_BUTTON} or session.state == SessionState.START:
            return [await self._start_or_resume(session)]

        if session.state == SessionState.AWAITING_PHONE:
            return [await self._handle_phone(session, message, text)]

        if session.state == SessionState.AWAITING_OTP:
            return [await self._handle_otp(session, text)]

        if session.state == SessionState.AWAITING_NAME:
            return [await self._handle_full_name(session, text)]

        if not session.user_id:
            session.state = SessionState.AWAITING_PHONE
            return [
                OutboundMessage(
                    chat_id=chat_id,
                    text="برای استفاده از مشاور مهاجرتی ابتدا شماره موبایل خود را تایید کنید.",
                    reply_markup=phone_keyboard(),
                )
            ]

        user = await self.users.get_by_id(session.user_id)
        if user is None or not user.is_active:
            session.user_id = None
            session.state = SessionState.AWAITING_PHONE
            return [
                OutboundMessage(
                    chat_id=chat_id,
                    text="حساب شما فعال نیست. لطفا دوباره با شماره موبایل وارد شوید.",
                    reply_markup=phone_keyboard(),
                )
            ]

        if text == CANCEL_BUTTON:
            return [await self._cancel_consultation(session)]

        if session.state == SessionState.CHOOSING_IMMIGRATION_METHOD:
            return [await self._handle_method_selection(session, user, text)]

        if session.state == SessionState.IN_CONSULTATION:
            return [await self._handle_consultation_answer(session, user, text)]

        return [await self._handle_authenticated_menu(session, user, text)]

    def _extract_message(self, update: BaleUpdate) -> BaleMessage | None:
        return update.message

    def _message_text(self, message: BaleMessage) -> str:
        if message.text:
            return message.text
        if message.contact:
            return message.contact.get("phone_number") or message.contact.get("phone") or ""
        return ""

    def _expire_session_if_needed(self, session: ConversationSession) -> None:
        if session.expires_at <= utc_now():
            session.user_id = None
            session.authenticated_at = None
            session.context = {}
            session.state = SessionState.START

    async def _start_or_resume(self, session: ConversationSession) -> OutboundMessage:
        if session.user_id:
            session.state = SessionState.AUTHENTICATED_MENU
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=(
                    "سلام، به مشاور هوشمند مهاجرت خوش آمدید. "
                    "یکی از گزینه های زیر را انتخاب کنید."
                ),
                reply_markup=main_menu_keyboard(),
            )

        session.state = SessionState.AWAITING_PHONE
        session.context = {}
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text=(
                "سلام! برای ارائه مشاوره دقیق و ذخیره سوابق گفتگو، ابتدا شماره موبایل "
                "خود را با کد پیامکی تایید کنید."
            ),
            reply_markup=phone_keyboard(),
        )

    async def _handle_phone(
        self,
        session: ConversationSession,
        message: BaleMessage,
        text: str,
    ) -> OutboundMessage:
        raw_phone = text
        if message.contact:
            raw_phone = message.contact.get("phone_number") or message.contact.get("phone") or text

        try:
            normalized_phone = await self.auth.start_phone_verification(raw_phone)
        except SecurityError as exc:
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=f"{exc}\nلطفا شماره موبایل را مثل 09123456789 یا +989123456789 وارد کنید.",
                reply_markup=phone_keyboard(),
            )

        session.context = {"pending_phone": normalized_phone}
        session.state = SessionState.AWAITING_OTP
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text="کد تایید پیامک شد. لطفا کد ۶ رقمی را وارد کنید.",
        )

    async def _handle_otp(self, session: ConversationSession, text: str) -> OutboundMessage:
        pending_phone = session.context.get("pending_phone")
        if not pending_phone:
            session.state = SessionState.AWAITING_PHONE
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text="برای دریافت کد تایید، ابتدا شماره موبایل خود را وارد کنید.",
                reply_markup=phone_keyboard(),
            )

        code = "".join(ch for ch in text if ch.isdigit())
        try:
            verified_phone = await self.auth.verify_otp(pending_phone, code)
        except (AuthenticationError, SecurityError) as exc:
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=str(exc),
            )

        existing = await self.users.get_by_phone_hash(phone_hash(verified_phone, self.settings))
        if existing:
            session.user_id = existing.id
            session.authenticated_at = utc_now()
            session.state = SessionState.AUTHENTICATED_MENU
            session.context = {}
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=f"{existing.full_name} عزیز، ورود شما با موفقیت انجام شد.",
                reply_markup=main_menu_keyboard(),
            )

        session.context = {"verified_phone": verified_phone}
        session.state = SessionState.AWAITING_NAME
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text="شماره شما تایید شد. لطفا نام و نام خانوادگی خود را وارد کنید.",
        )

    async def _handle_full_name(self, session: ConversationSession, text: str) -> OutboundMessage:
        full_name = " ".join(text.split())
        if len(full_name) < 3:
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text="لطفا نام و نام خانوادگی کامل خود را وارد کنید.",
            )

        verified_phone = session.context.get("verified_phone")
        if not verified_phone:
            session.state = SessionState.AWAITING_PHONE
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text="اعتبار تایید شماره پایان یافته است. لطفا دوباره شماره موبایل را ارسال کنید.",
                reply_markup=phone_keyboard(),
            )

        user = await self.auth.get_or_register_user(verified_phone, full_name)
        session.user_id = user.id
        session.authenticated_at = utc_now()
        session.state = SessionState.AUTHENTICATED_MENU
        session.context = {}
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text=(
                f"{user.full_name} عزیز، ثبت نام شما تکمیل شد. "
                "اکنون می توانید مشاوره مهاجرتی دریافت کنید."
            ),
            reply_markup=main_menu_keyboard(),
        )

    async def _handle_authenticated_menu(
        self,
        session: ConversationSession,
        user: User,
        text: str,
    ) -> OutboundMessage:
        if session.context.get("awaiting_ai_question"):
            return await self._handle_free_question(session, user, text)

        if text == BEST_COUNTRY_BUTTON:
            decision = await self.usage.check(user)
            if not decision.allowed:
                return self._limit_message(session, decision.limit)
            session.state = SessionState.CHOOSING_IMMIGRATION_METHOD
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text="چه نوع مهاجرتی مدنظر شماست؟",
                reply_markup=immigration_method_keyboard(),
            )

        if text == ASK_AI_BUTTON:
            session.context = {"awaiting_ai_question": True}
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=(
                    "سوال مهاجرتی خود را بنویسید. فقط به موضوعات مهاجرت، "
                    "ویزا و اقامت پاسخ می دهم."
                ),
            )

        if text == PROFILE_BUTTON:
            decision = await self.usage.check(user)
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=(
                    f"نام: {user.full_name}\n"
                    f"اشتراک: {user.subscription_type.value}\n"
                    f"مصرف امروز: {decision.used} از {decision.limit}\n"
                    f"باقی مانده امروز: {decision.remaining}"
                ),
                reply_markup=main_menu_keyboard(),
            )

        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text="لطفا یکی از گزینه های منو را انتخاب کنید.",
            reply_markup=main_menu_keyboard(),
        )

    async def _handle_method_selection(
        self,
        session: ConversationSession,
        user: User,
        text: str,
    ) -> OutboundMessage:
        category = method_from_label(text)
        if category is None:
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text="لطفا یکی از روش های مهاجرتی نمایش داده شده را انتخاب کنید.",
                reply_markup=immigration_method_keyboard(),
            )

        consultation = Consultation(user_id=user.id, category=category, collected_answers={})
        self.db.add(consultation)
        await self.db.flush()

        first_question = self.workflow.first_question(category)
        session.state = SessionState.IN_CONSULTATION
        session.context = {
            "consultation_id": str(consultation.id),
            "category": category,
            "answers": {},
            "current_question": first_question.key,
        }
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text=(
                f"عالی. برای {self.workflow.category_label(category)} چند سوال کوتاه می پرسم.\n"
                f"{first_question.prompt}"
            ),
            reply_markup=None,
        )

    async def _handle_consultation_answer(
        self,
        session: ConversationSession,
        user: User,
        text: str,
    ) -> OutboundMessage:
        category = session.context.get("category")
        current_key = session.context.get("current_question")
        answers = dict(session.context.get("answers", {}))
        if not category or not current_key:
            session.state = SessionState.AUTHENTICATED_MENU
            session.context = {}
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text="جریان مشاوره بازیابی نشد. لطفا دوباره از منو شروع کنید.",
                reply_markup=main_menu_keyboard(),
            )

        answers[current_key] = text
        next_question = self.workflow.next_question(category, set(answers))

        consultation = await self._get_active_consultation(session.context.get("consultation_id"))
        if consultation:
            consultation.collected_answers = answers

        if next_question:
            session.context = {
                **session.context,
                "answers": answers,
                "current_question": next_question.key,
            }
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=next_question.prompt,
            )

        decision = await self.usage.increment(user)
        if not decision.allowed:
            return self._limit_message(session, decision.limit)

        recommendation = await self.ai.recommend_countries(
            self.workflow.category_label(category),
            answers,
        )
        if consultation:
            consultation.recommendation = recommendation
            consultation.status = ConsultationStatus.COMPLETED

        session.state = SessionState.AUTHENTICATED_MENU
        session.context = {}
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text=f"نتیجه مشاوره هوشمند:\n\n{recommendation}",
            reply_markup=main_menu_keyboard(),
            metadata={"usage_remaining": decision.remaining},
        )

    async def _handle_free_question(
        self,
        session: ConversationSession,
        user: User,
        text: str,
    ) -> OutboundMessage:
        session.context = {}
        if not self.guard.is_immigration_related(text):
            return OutboundMessage(
                chat_id=session.bale_chat_id,
                text=self.guard.refusal_message,
                reply_markup=main_menu_keyboard(),
            )

        decision = await self.usage.increment(user)
        if not decision.allowed:
            return self._limit_message(session, decision.limit)

        answer = await self.ai.answer_question(text)
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text=answer,
            reply_markup=main_menu_keyboard(),
            metadata={"usage_remaining": decision.remaining},
        )

    async def _cancel_consultation(self, session: ConversationSession) -> OutboundMessage:
        consultation = await self._get_active_consultation(session.context.get("consultation_id"))
        if consultation:
            consultation.status = ConsultationStatus.CANCELLED
        session.state = SessionState.AUTHENTICATED_MENU
        session.context = {}
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text="مشاوره لغو شد. از منوی اصلی گزینه بعدی را انتخاب کنید.",
            reply_markup=main_menu_keyboard(),
        )

    async def _get_active_consultation(self, consultation_id: str | None) -> Consultation | None:
        if not consultation_id:
            return None
        try:
            return await self.db.get(Consultation, UUID(consultation_id))
        except ValueError:
            return None

    def _limit_message(self, session: ConversationSession, limit: int) -> OutboundMessage:
        session.state = SessionState.AUTHENTICATED_MENU
        session.context = {}
        return OutboundMessage(
            chat_id=session.bale_chat_id,
            text=(
                f"سهمیه امروز شما ({limit} سوال/مشاوره) تمام شده است. "
                "برای ادامه استفاده، اشتراک پریمیوم را فعال کنید."
            ),
            reply_markup=main_menu_keyboard(),
        )
