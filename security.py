"""
Security helpers: password hashing, symmetric encryption at rest, and
signed tokens for password-reset links.

Design notes
------------
- Passwords are hashed with Werkzeug's PBKDF2-SHA256 implementation
  (generate_password_hash / check_password_hash). Plaintext passwords are
  never stored or logged.
- Sensitive stored payloads (simulation results, uploaded dataset contents)
  are encrypted at rest with Fernet (AES-128-CBC + HMAC), a symmetric
  authenticated encryption scheme from the `cryptography` library.
- Password reset tokens are signed + time-limited using itsdangerous, so a
  token cannot be forged or replayed after it expires, and never contains
  the password itself.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """Return a salted PBKDF2-SHA256 hash of the given password."""
    return generate_password_hash(plain_password, method="pbkdf2:sha256", salt_length=16)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time verification of a password against its stored hash."""
    try:
        return check_password_hash(password_hash, plain_password)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Encryption at rest
# ---------------------------------------------------------------------------
def _derive_fernet_key_from_secret(secret: str) -> bytes:
    """
    Deterministically derive a valid 32-byte urlsafe-base64 Fernet key from
    an arbitrary secret string, so a developer can run the app with just
    SECRET_KEY set and not have to separately manage a Fernet key in dev.
    In production, set MC_ENCRYPTION_KEY explicitly (a real Fernet.generate_key()).
    """
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    key = Config.ENCRYPTION_KEY or _derive_fernet_key_from_secret(Config.SECRET_KEY)
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


def encrypt_bytes(data: bytes) -> bytes:
    """Encrypt raw bytes for storage."""
    return _get_fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    """Decrypt bytes previously produced by encrypt_bytes. Raises ValueError on tamper/corruption."""
    try:
        return _get_fernet().decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Stored data could not be decrypted (corrupted or tampered).") from exc


def encrypt_text(text: str) -> bytes:
    return encrypt_bytes(text.encode("utf-8"))


def decrypt_text(token: bytes) -> str:
    return decrypt_bytes(token).decode("utf-8")


# ---------------------------------------------------------------------------
# Signed, time-limited tokens (password reset)
# ---------------------------------------------------------------------------
def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=Config.SECRET_KEY, salt="password-reset")


def generate_reset_token(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id})


def verify_reset_token(token: str, max_age_seconds: int | None = None):
    """Return the user_id encoded in the token, or None if invalid/expired."""
    max_age = max_age_seconds or Config.PASSWORD_RESET_TOKEN_MAX_AGE_SECONDS
    try:
        data = _serializer().loads(token, max_age=max_age)
        return data.get("uid")
    except (BadSignature, SignatureExpired):
        return None


def new_random_token(num_bytes: int = 24) -> str:
    """General-purpose random token (e.g. for CSRF or one-off links)."""
    return base64.urlsafe_b64encode(os.urandom(num_bytes)).decode("utf-8")
