from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.security import utc_now
from app.models import SubscriptionType, User
from app.repositories.usage import UsageRepository


@dataclass(frozen=True)
class UsageDecision:
    allowed: bool
    used: int
    limit: int
    remaining: int


class UsageLimitService:
    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.repository = UsageRepository(db)

    def daily_limit_for(self, user: User) -> int:
        if user.subscription_type == SubscriptionType.PREMIUM:
            return self.settings.premium_daily_limit
        return self.settings.free_daily_limit

    async def check(self, user: User) -> UsageDecision:
        today = utc_now().date()
        usage = await self.repository.get_or_create_today(user.id, today)
        limit = self.daily_limit_for(user)
        remaining = max(limit - usage.question_count, 0)
        return UsageDecision(
            allowed=usage.question_count < limit,
            used=usage.question_count,
            limit=limit,
            remaining=remaining,
        )

    async def increment(self, user: User) -> UsageDecision:
        today = utc_now().date()
        usage = await self.repository.get_or_create_today(user.id, today)
        limit = self.daily_limit_for(user)
        if usage.question_count >= limit:
            return UsageDecision(False, usage.question_count, limit, 0)

        usage.question_count += 1
        await self.db.flush()
        remaining = max(limit - usage.question_count, 0)
        return UsageDecision(True, usage.question_count, limit, remaining)
