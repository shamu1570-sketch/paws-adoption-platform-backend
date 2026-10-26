import secrets
from datetime import UTC, datetime
from uuid import uuid4

# Sin caracteres ambiguos (0/O, 1/I/L) para que el código se pueda dictar o copiar a mano.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8


def generate_id(prefix: str) -> str:
    """Genera un identificador corto y único con prefijo, ej: `req_3f9a1c0b7d21`."""
    return f"{prefix}_{uuid4().hex[:12]}"


def generate_tracking_code(prefix: str) -> str:
    """Código de seguimiento público difícil de adivinar, ej: `ADOP-2026-K7M2QX9D`."""
    suffix = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
    return f"{prefix}-{datetime.now(UTC).year}-{suffix}"


def normalize_tracking_code(code: str) -> str:
    return code.strip().upper()
