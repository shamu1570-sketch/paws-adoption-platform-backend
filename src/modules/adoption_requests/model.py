from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base

ACTIVE_STATUSES = ("pendiente", "en_entrevista")
_ACTIVE_FILTER = text("status IN ('pendiente', 'en_entrevista')")


class AdoptionRequest(Base):
    __tablename__ = "adoption_requests"
    __table_args__ = (
        # Última barrera contra duplicados: una sola solicitud activa por mascota y correo,
        # incluso si dos envíos llegan al mismo tiempo.
        Index(
            "uq_adoption_requests_active_pet_email",
            "pet_id",
            "user_email",
            unique=True,
            postgresql_where=_ACTIVE_FILTER,
            sqlite_where=_ACTIVE_FILTER,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # Código público con el que el solicitante consulta el estado sin iniciar sesión.
    tracking_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    pet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pets.id", ondelete="CASCADE"), index=True
    )
    pet_name: Mapped[str] = mapped_column(String(50))
    pet_image: Mapped[str] = mapped_column(Text)
    shelter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("shelters.id", ondelete="SET NULL"), index=True
    )
    user_name: Mapped[str] = mapped_column(String(50))
    user_email: Mapped[str] = mapped_column(String(150))
    user_phone: Mapped[str] = mapped_column(String(30))
    house_type: Mapped[str] = mapped_column(String(20))
    has_other_pets: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pendiente", index=True)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    # Último cambio de estado hecho por un administrador (null mientras esté pendiente).
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
