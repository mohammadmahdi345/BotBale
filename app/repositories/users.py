from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_phone_hash(self, phone_number_hash: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.phone_number_hash == phone_number_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id) -> User | None:
        return await self.session.get(User, user_id)

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
