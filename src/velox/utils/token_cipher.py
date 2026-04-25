"""Small encryption helper for admin-managed integration tokens."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class SecretCipherNotConfiguredError(RuntimeError):
    """Raised when encryption was requested without a configured key."""


class SecretCipher:
    """Encrypt and decrypt short integration secrets with a configured key."""

    def __init__(self, key_material: str) -> None:
        self._key_material = key_material.strip()

    @property
    def is_configured(self) -> bool:
        """Return whether a non-empty key was configured."""
        return bool(self._key_material)

    def encrypt(self, value: str) -> str:
        """Encrypt a non-empty string value."""
        if not self.is_configured:
            raise SecretCipherNotConfiguredError("Secret encryption key is not configured.")
        return self._fernet().encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        """Decrypt a string encrypted by this helper."""
        if not self.is_configured:
            raise SecretCipherNotConfiguredError("Secret encryption key is not configured.")
        try:
            return self._fernet().decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Encrypted secret cannot be decrypted with the configured key.") from exc

    def _fernet(self) -> Fernet:
        """Build a Fernet instance from either a Fernet key or raw key material."""
        raw = self._key_material.encode("utf-8")
        try:
            return Fernet(raw)
        except ValueError:
            derived = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
            return Fernet(derived)


def secret_last4(value: str | None) -> str | None:
    """Return the last four characters of a secret for diagnostics."""
    if not value:
        return None
    stripped = value.strip()
    return stripped[-4:] if len(stripped) >= 4 else "***"


def mask_secret(last4: str | None) -> str:
    """Return a UI-safe masked secret label."""
    if not last4:
        return "not_stored"
    return f"***{last4}"
