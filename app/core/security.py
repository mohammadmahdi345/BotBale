import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import phonenumbers
from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import Settings


class SecurityError(ValueError):
    """Raised when sensitive data cannot be validated or decrypted."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_phone_number(raw_phone_number: str, default_region: str = "IR") -> str:
    try:
        parsed = phonenumbers.parse(raw_phone_number, default_region)
    except phonenumbers.NumberParseException as exc:
        raise SecurityError("شماره تلفن وارد شده معتبر نیست.") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise SecurityError("شماره تلفن وارد شده معتبر نیست.")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def phone_hash(phone_number: str, settings: Settings) -> str:
    return hmac.new(
        settings.otp_secret.get_secret_value().encode(),
        phone_number.encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def otp_hash(phone_number: str, otp_code: str, settings: Settings) -> str:
    message = f"{phone_number}:{otp_code}".encode()
    return hmac.new(
        settings.otp_secret.get_secret_value().encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def verify_otp_hash(phone_number: str, otp_code: str, expected_hash: str, settings: Settings) -> bool:
    return hmac.compare_digest(otp_hash(phone_number, otp_code, settings), expected_hash)


def otp_expiry(settings: Settings) -> datetime:
    return utc_now() + timedelta(seconds=settings.otp_ttl_seconds)


def get_fernet(settings: Settings) -> Fernet:
    key = settings.phone_encryption_key.get_secret_value()
    if key == "replace-with-fernet-key":
        raise SecurityError("PHONE_ENCRYPTION_KEY must be configured with a Fernet key.")

    try:
        base64.urlsafe_b64decode(key)
    except Exception as exc:
        raise SecurityError("PHONE_ENCRYPTION_KEY is not a valid Fernet key.") from exc
    return Fernet(key.encode())


def encrypt_phone_number(phone_number: str, settings: Settings) -> str:
    return get_fernet(settings).encrypt(phone_number.encode()).decode()


def decrypt_phone_number(ciphertext: str, settings: Settings) -> str:
    try:
        return get_fernet(settings).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise SecurityError("Stored phone number cannot be decrypted.") from exc
