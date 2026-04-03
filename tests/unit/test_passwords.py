"""Unit tests for password hashing helpers."""

from velox.utils.passwords import (
    BCRYPT_PASSWORD_MAX_BYTES,
    ensure_password_within_bcrypt_limit,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password_roundtrip() -> None:
    password = "SuperSecure123!"

    password_hash = hash_password(password)

    assert password_hash.startswith("$2")
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_verify_password_returns_false_for_invalid_hash() -> None:
    assert not verify_password("SuperSecure123!", "not-a-valid-bcrypt-hash")


def test_ensure_password_within_bcrypt_limit_raises_for_long_utf8_password() -> None:
    too_long = "ğ" * (BCRYPT_PASSWORD_MAX_BYTES // 2 + 1)

    try:
        ensure_password_within_bcrypt_limit(too_long * 3)
    except ValueError as exc:
        assert "72 bytes" in str(exc)
    else:
        raise AssertionError("Expected ValueError for password exceeding bcrypt byte limit")
