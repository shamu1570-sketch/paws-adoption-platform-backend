from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base

PERSONALITY_NAME_LENGTH = 40


class Personality(Base):
    """Rasgo de personalidad del catálogo que los administradores asignan a las mascotas."""

    __tablename__ = "personalities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(PERSONALITY_NAME_LENGTH), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
