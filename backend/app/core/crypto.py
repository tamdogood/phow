"""Symmetric encryption for OAuth tokens stored at rest (Fernet)."""

from functools import lru_cache
from cryptography.fernet import Fernet
from .config import get_settings


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().review_token_encryption_key
    if not key:
        raise RuntimeError(
            "REVIEW_TOKEN_ENCRYPTION_KEY is not set. Generate one with "
            "`python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`"
        )
    return Fernet(key.encode())


def encrypt_token(plaintext: str | None) -> str | None:
    if not plaintext:
        return plaintext
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str | None) -> str | None:
    if not ciphertext:
        return ciphertext
    return _fernet().decrypt(ciphertext.encode()).decode()
