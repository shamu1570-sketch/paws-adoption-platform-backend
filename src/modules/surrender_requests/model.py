from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base


class SurrenderRequest(Base):
    __tablename__ = "surrender_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # Código público con el que el solicitante consulta el estado sin iniciar sesión.
    tracking_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    # Ficha creada en el catálogo cuando el refugio recibe a la mascota.
    pet_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pets.id", ondelete="SET NULL"), unique=True
    )
    pet_name: Mapped[str] = mapped_column(String(50))
    pet_type: Mapped[str] = mapped_column(String(20))
    # Edad indicada en el formulario (cantidad y unidad) y su texto para mostrar.
    pet_age_value: Mapped[int] = mapped_column(Integer)
    pet_age_unit: Mapped[str] = mapped_column(String(10))
    pet_age: Mapped[str] = mapped_column(String(50))
    shelter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("shelters.id", ondelete="CASCADE"), index=True
    )
    shelter_name: Mapped[str] = mapped_column(String(150))
    user_name: Mapped[str] = mapped_column(String(50))
    user_email: Mapped[str] = mapped_column(String(150))
    user_phone: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    health_condition: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pendiente", index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
