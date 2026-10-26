from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base
from src.database.types import JSONList


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(20), index=True)
    breed: Mapped[str] = mapped_column(String(100))
    # Edad indicada en el formulario: cantidad y unidad ("años" o "meses").
    age_value: Mapped[int] = mapped_column(Integer)
    age_unit: Mapped[str] = mapped_column(String(10))
    # Derivados de la edad (los calcula la API): texto para mostrar y etapa de vida.
    age: Mapped[str] = mapped_column(String(50))
    age_category: Mapped[str] = mapped_column(String(20), index=True)
    gender: Mapped[str] = mapped_column(String(20), index=True)
    size: Mapped[str] = mapped_column(String(20), index=True)
    personality: Mapped[list[str]] = mapped_column(JSONList)
    description: Mapped[str] = mapped_column(Text)
    story: Mapped[str] = mapped_column(Text)
    # Foto principal (la primera de la galería); la usan las tarjetas y las solicitudes.
    image: Mapped[str] = mapped_column(Text)
    # Galería completa: hasta 4 URLs públicas de fotos WebP, la primera es la principal.
    photos: Mapped[list[str]] = mapped_column(JSONList, server_default="[]")
    vaccinated: Mapped[bool] = mapped_column(Boolean, default=False)
    dewormed: Mapped[bool] = mapped_column(Boolean, default=False)
    sterilized: Mapped[bool] = mapped_column(Boolean, default=False)
    health_status: Mapped[str] = mapped_column(Text)
    adoption_status: Mapped[str] = mapped_column(String(20), default="disponible", index=True)
    # Publicación en el catálogo público; independiente del avance de la adopción.
    is_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), index=True
    )
    shelter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("shelters.id", ondelete="SET NULL"), index=True
    )
    shelter_name: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
