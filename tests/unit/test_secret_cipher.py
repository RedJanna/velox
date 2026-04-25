"""Tests for integration secret encryption helper."""

import pytest

from velox.utils.token_cipher import SecretCipher, SecretCipherNotConfiguredError, mask_secret, secret_last4


def test_secret_cipher_round_trips_with_raw_key_material() -> None:
    """Raw env key material should be derived into a stable Fernet key."""
    cipher = SecretCipher("local-test-secret-material")

    encrypted = cipher.encrypt("EAA-test-token")

    assert encrypted != "EAA-test-token"
    assert cipher.decrypt(encrypted) == "EAA-test-token"


def test_secret_cipher_requires_key_material() -> None:
    """Encrypt/decrypt fail closed when no key is configured."""
    cipher = SecretCipher("")

    with pytest.raises(SecretCipherNotConfiguredError):
        cipher.encrypt("secret")


def test_secret_mask_helpers_do_not_expose_full_value() -> None:
    assert secret_last4("abcdef") == "cdef"
    assert mask_secret("cdef") == "***cdef"
    assert mask_secret(None) == "not_stored"
