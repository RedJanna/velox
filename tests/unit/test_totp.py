"""Unit tests for TOTP helpers."""

from velox.utils.totp import build_otpauth_uri, generate_totp_code, generate_totp_secret, verify_totp_code


def test_generate_totp_secret_returns_base32_without_padding() -> None:
    secret = generate_totp_secret()

    assert len(secret) >= 32
    assert "=" not in secret
    assert secret.isalnum()


def test_build_otpauth_uri_contains_expected_google_authenticator_fields() -> None:
    uri = build_otpauth_uri("JBSWY3DPEHPK3PXP", "admin", "NexlumeAI")

    assert uri.startswith("otpauth://totp/")
    assert "issuer=NexlumeAI" in uri
    assert "secret=JBSWY3DPEHPK3PXP" in uri


def test_verify_totp_code_matches_rfc6238_reference_vector() -> None:
    assert verify_totp_code("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "287082", at_time=59, valid_window=0)


def test_verify_totp_code_rejects_invalid_code() -> None:
    assert not verify_totp_code("JBSWY3DPEHPK3PXP", "12345A")


def test_generate_totp_code_can_roundtrip_with_verify() -> None:
    secret = "JBSWY3DPEHPK3PXP"  # noqa: S105
    code = generate_totp_code(secret, at_time=120)

    assert verify_totp_code(secret, code, at_time=120, valid_window=0)
