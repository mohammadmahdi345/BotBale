import hmac

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.bale.client import BaleClient
from app.config.settings import Settings, get_settings
from app.db.session import get_db_session
from app.models import MessageDirection
from app.repositories.logs import ConversationLogRepository
from app.schemas.bale import BaleUpdate
from app.services.bot import BotService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = structlog.get_logger(__name__)


@router.post("/bale/{webhook_secret}")
async def handle_bale_webhook(
    update: BaleUpdate,
    webhook_secret: str = Path(...),
    x_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, bool]:
    expected = settings.webhook_secret.get_secret_value()
    provided = x_webhook_secret or webhook_secret
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    bot = BotService(db, settings)
    bale = BaleClient(settings)
    outbox = await bot.handle_update(update)
    log_repo = ConversationLogRepository(db)

    for outbound in outbox:
        await bale.send_message(outbound.chat_id, outbound.text, outbound.reply_markup)
        log_repo.add(
            bale_chat_id=outbound.chat_id,
            direction=MessageDirection.OUTBOUND,
            message_text=outbound.text,
            metadata=outbound.metadata or {},
        )

    await db.commit()
    logger.info("bale_update_processed", update_id=update.update_id, outbound_count=len(outbox))
    return {"ok": True}
