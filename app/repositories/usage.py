from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsageCounter


class UsageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_today(self, user_id, today: date) -> UsageCounter:
        result = await self.session.execute(
            select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.usage_date == today,
            )
        )
        usage = result.scalar_one_or_none()
        if usage:
            return usage

        usage = UsageCounter(user_id=user_id, usage_date=today, question_count=0)
        self.session.add(usage)
        await self.session.flush()
        return usage
