"""Small encryption utility for secure token storage."""

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings


class TokenCipher:
    """Encrypt/decrypt connector credentials with a stable key."""

    def __init__(self, raw_key: str):
        key = self._normalize_key(raw_key)
        self._fernet = Fernet(key)

    @staticmethod
    def _normalize_key(raw_key: str) -> bytes:
        if raw_key:
            candidate = raw_key.encode("utf-8")
            if len(candidate) == 44:
                return candidate
            digest = hashlib.sha256(candidate).digest()
            return base64.urlsafe_b64encode(digest)

        fallback_seed = get_settings().supabase_service_key or "phow-default-local-key"
        digest = hashlib.sha256(fallback_seed.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return None


@lru_cache
def get_token_cipher() -> TokenCipher:
    settings = get_settings()
    return TokenCipher(settings.reputation_token_encryption_key)
