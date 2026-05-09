from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationLog, MessageDirection


class ConversationLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(
        self,
        *,
        bale_chat_id: str,
        direction: MessageDirection,
        message_text: str,
        user_id=None,
        metadata: dict | None = None,
    ) -> None:
        self.session.add(
            ConversationLog(
                bale_chat_id=bale_chat_id,
                direction=direction,
                message_text=message_text,
                user_id=user_id,
                event_metadata=metadata or {},
            )
        )
