from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from src.core.config import settings

_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class InvalidTokenError(Exception):
    """El token no es válido, fue manipulado o ya expiró."""


def hash_password(password: str) -> str:
    return _password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_context.verify(password, password_hash)


def access_token_ttl_seconds() -> int:
    return settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=access_token_ttl_seconds()),
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """Valida firma y expiración y devuelve el identificador del administrador."""
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error
    return claims["sub"]
