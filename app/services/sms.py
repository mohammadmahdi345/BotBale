import httpx
import structlog

from app.config.settings import Settings

logger = structlog.get_logger(__name__)


class SMSService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_otp(self, phone_number: str, otp_code: str) -> None:
        message = f"کد ورود شما به مشاور مهاجرتی بات بله: {otp_code}"
        if not self.settings.sms_provider_url:
            logger.info("otp_generated_local_development", phone_number=phone_number, otp=otp_code)
            return

        headers = {}
        if self.settings.sms_provider_api_key:
            headers["Authorization"] = (
                f"Bearer {self.settings.sms_provider_api_key.get_secret_value()}"
            )

        payload = {
            "to": phone_number,
            "sender": self.settings.sms_sender,
            "message": message,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                self.settings.sms_provider_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        logger.info("otp_sms_sent", phone_number=phone_number)
