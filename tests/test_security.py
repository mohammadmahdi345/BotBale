from types import SimpleNamespace

from pydantic import SecretStr

from app.core.security import normalize_phone_number, otp_hash, phone_hash, verify_otp_hash


def test_normalize_iran_phone_number_to_e164() -> None:
    assert normalize_phone_number("09123456789") == "+989123456789"


def test_hashes_are_deterministic_and_otp_verifies() -> None:
    settings = SimpleNamespace(otp_secret=SecretStr("test-secret"))

    assert phone_hash("+989123456789", settings) == phone_hash("+989123456789", settings)
    expected = otp_hash("+989123456789", "123456", settings)

    assert verify_otp_hash("+989123456789", "123456", expected, settings)
    assert not verify_otp_hash("+989123456789", "000000", expected, settings)
