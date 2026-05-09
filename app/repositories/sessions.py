from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.security import utc_now
from app.models import ConversationSession, SessionState


class SessionRepository:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

    async def get_or_create(self, bale_chat_id: str) -> ConversationSession:
        result = await self.session.execute(
            select(ConversationSession).where(ConversationSession.bale_chat_id == bale_chat_id)
        )
        conversation_session = result.scalar_one_or_none()
        if conversation_session:
            return conversation_session

        conversation_session = ConversationSession(
            bale_chat_id=bale_chat_id,
            state=SessionState.START,
            context={},
            expires_at=self._new_expiry(),
        )
        self.session.add(conversation_session)
        await self.session.flush()
        return conversation_session

    def _new_expiry(self):
        return utc_now() + timedelta(hours=self.settings.session_ttl_hours)

    def refresh(self, conversation_session: ConversationSession) -> None:
        conversation_session.expires_at = self._new_expiry()
        conversation_session.updated_at = utc_now()
