from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.security import (
    SecurityError,
    encrypt_phone_number,
    generate_otp,
    normalize_phone_number,
    otp_expiry,
    otp_hash,
    phone_hash,
    utc_now,
    verify_otp_hash,
)
from app.models import OTPChallenge, User
from app.repositories.users import UserRepository
from app.services.sms import SMSService


class AuthenticationError(ValueError):
    pass


class AuthService:
    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)
        self.sms = SMSService(settings)

    async def start_phone_verification(self, raw_phone_number: str) -> str:
        phone_number = normalize_phone_number(raw_phone_number)
        code = generate_otp()
        challenge = OTPChallenge(
            phone_number_hash=phone_hash(phone_number, self.settings),
            phone_number_ciphertext=encrypt_phone_number(phone_number, self.settings),
            otp_hash=otp_hash(phone_number, code, self.settings),
            expires_at=otp_expiry(self.settings),
        )
        self.db.add(challenge)
        await self.sms.send_otp(phone_number, code)
        await self.db.flush()
        return phone_number

    async def verify_otp(self, raw_phone_number: str, code: str) -> str:
        phone_number = normalize_phone_number(raw_phone_number)
        p_hash = phone_hash(phone_number, self.settings)
        result = await self.db.execute(
            select(OTPChallenge)
            .where(
                OTPChallenge.phone_number_hash == p_hash,
                OTPChallenge.consumed_at.is_(None),
                OTPChallenge.expires_at > utc_now(),
            )
            .order_by(OTPChallenge.created_at.desc())
        )
        challenge = result.scalars().first()
        if challenge is None:
            raise AuthenticationError("کد تایید منقضی شده یا یافت نشد.")

        if challenge.attempts >= 5:
            raise AuthenticationError("تعداد تلاش های ناموفق زیاد است. لطفا دوباره کد بگیرید.")

        challenge.attempts += 1
        if not verify_otp_hash(phone_number, code, challenge.otp_hash, self.settings):
            raise AuthenticationError("کد تایید صحیح نیست.")

        challenge.consumed_at = utc_now()
        await self.db.flush()
        return phone_number

    async def get_or_register_user(self, phone_number: str, full_name: str) -> User:
        p_hash = phone_hash(phone_number, self.settings)
        existing = await self.users.get_by_phone_hash(p_hash)
        if existing:
            if not existing.full_name and full_name:
                existing.full_name = full_name.strip()
            return existing

        try:
            encrypted_phone = encrypt_phone_number(phone_number, self.settings)
        except SecurityError:
            raise

        user = User(
            phone_number_ciphertext=encrypted_phone,
            phone_number_hash=p_hash,
            full_name=full_name.strip(),
        )
        return await self.users.add(user)
