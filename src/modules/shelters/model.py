from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base
from src.database.types import JSONList


class Shelter(Base):
    __tablename__ = "shelters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    address: Mapped[str] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), index=True)
    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(150))
    website: Mapped[str | None] = mapped_column(String(255))
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    current_pet_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text)
    # Foto principal (la primera de la galería); la usan las tarjetas.
    image: Mapped[str] = mapped_column(Text)
    # Galería completa: hasta 4 URLs públicas de fotos WebP, la primera es la principal.
    photos: Mapped[list[str]] = mapped_column(JSONList, server_default="[]")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
