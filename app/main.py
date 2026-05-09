from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.config.settings import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="BotBale Immigration Consultant",
    version="0.1.0",
    description="Persian AI immigration consultation bot for Bale Messenger.",
)

app.include_router(health_router)
app.include_router(webhook_router)
