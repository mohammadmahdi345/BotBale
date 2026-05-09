from typing import Any

import httpx
import structlog

from app.config.settings import Settings
from app.schemas.bale import ReplyKeyboardMarkup

logger = structlog.get_logger(__name__)


class BaleClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = str(settings.bale_api_base_url).rstrip("/")

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: ReplyKeyboardMarkup | dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = (
                reply_markup.model_dump(exclude_none=True)
                if hasattr(reply_markup, "model_dump")
                else reply_markup
            )

        token = self.settings.bale_bot_token.get_secret_value()
        url = f"{self.base_url}/bot{token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("bale_message_sent", chat_id=chat_id)
