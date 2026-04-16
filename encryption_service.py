import base64
import hashlib
import json
import os
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import MASTER_KEY_B64, SECRET_KEY, STRICT_KEY_MANAGEMENT


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data.encode("ascii"))


def _load_master_key() -> bytes:
    if MASTER_KEY_B64:
        key = _b64d(MASTER_KEY_B64)
        if len(key) != 32:
            raise ValueError("MASTER_KEY_B64 must decode to exactly 32 bytes")
        return key

    if STRICT_KEY_MANAGEMENT:
        raise ValueError(
            "MASTER_KEY_B64 must be configured when STRICT_KEY_MANAGEMENT=true"
        )

    # Development-only fallback for local sandbox execution.
    return hashlib.sha256(SECRET_KEY.encode("utf-8")).digest()


class SandboxKMS:
    def __init__(self, master_key: Optional[bytes] = None):
        self._master_key = master_key or _load_master_key()

    def wrap_key(self, dek: bytes, context: bytes = b"sandbox") -> Dict[str, str]:
        key_iv = os.urandom(12)
        wrapped = AESGCM(self._master_key).encrypt(key_iv, dek, context)
        return {
            "iv": _b64e(key_iv),
            "ciphertext": _b64e(wrapped),
        }

    def unwrap_key(self, payload: Dict[str, str], context: bytes = b"sandbox") -> bytes:
        key_iv = _b64d(payload["iv"])
        wrapped = _b64d(payload["ciphertext"])
        return AESGCM(self._master_key).decrypt(key_iv, wrapped, context)


kms = SandboxKMS()


def encrypt(data: str, *, aad: str = "sandbox", version: int = 1) -> str:
    if data is None:
        raise ValueError("encrypt(data) requires non-null input")

    dek = os.urandom(32)
    iv = os.urandom(12)
    ciphertext = AESGCM(dek).encrypt(iv, data.encode("utf-8"), aad.encode("utf-8"))
    wrapped_dek = kms.wrap_key(dek, context=aad.encode("utf-8"))

    envelope = {
        "v": version,
        "alg": "AES-256-GCM",
        "iv": _b64e(iv),
        "ciphertext": _b64e(ciphertext),
        "dek": wrapped_dek,
    }
    return json.dumps(envelope, separators=(",", ":"), sort_keys=True)


def decrypt(payload: str, *, aad: str = "sandbox") -> str:
    envelope = json.loads(payload)
    dek = kms.unwrap_key(envelope["dek"], context=aad.encode("utf-8"))
    iv = _b64d(envelope["iv"])
    ciphertext = _b64d(envelope["ciphertext"])
    plaintext = AESGCM(dek).decrypt(iv, ciphertext, aad.encode("utf-8"))
    return plaintext.decode("utf-8")


def looks_encrypted(value: Optional[str]) -> bool:
    if not value or not isinstance(value, str):
        return False
    try:
        obj = json.loads(value)
    except Exception:
        return False
    required = {"v", "alg", "iv", "ciphertext", "dek"}
    return isinstance(obj, dict) and required.issubset(set(obj.keys()))


def safe_decrypt(value: Optional[str], *, aad: str = "sandbox") -> Optional[str]:
    if value is None:
        return None
    if not looks_encrypted(value):
        return value
    return decrypt(value, aad=aad)


def stable_hash(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def mask_account_number(account_number: Optional[str]) -> Optional[str]:
    if account_number is None:
        return None
    digits = "".join(ch for ch in account_number if ch.isdigit())
    if not digits:
        return "****"
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def mask_sensitive_value(value: Optional[str], *, keep_last: int = 4) -> str:
    if not value:
        return "***"
    if len(value) <= keep_last:
        return "*" * len(value)
    return "*" * (len(value) - keep_last) + value[-keep_last:]
