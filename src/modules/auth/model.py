from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:
    from src.modules.shelters.model import Shelter


class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (
        CheckConstraint("role IN ('super_admin', 'adoption_admin')", name="ck_admins_role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Alcance: administrador general (todos los refugios) o de un refugio específico.
    # Si se elimina su refugio, la cuenta queda sin alcance (no se vuelve general).
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    shelter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("shelters.id", ondelete="SET NULL"), index=True
    )
    # Ventana de acceso opcional; fuera de ella la cuenta recibe 403 aunque esté activa.
    access_starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    shelter: Mapped["Shelter | None"] = relationship(lazy="selectin")

    @property
    def shelter_name(self) -> str | None:
        return self.shelter.name if self.shelter is not None else None


class AdminInvitation(Base):
    """Llave de acceso de un solo uso con la que una persona se registra como administrador."""

    __tablename__ = "admin_invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # Solo se guarda el hash: la llave se muestra una única vez al generarla.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # Correo (en minúsculas) de la única persona que puede registrarse con esta llave.
    email: Mapped[str] = mapped_column(String(150), index=True)
    role: Mapped[str] = mapped_column(String(30))
    # Alcance que recibirá la cuenta al registrarse con esta llave.
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    shelter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("shelters.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("admins.id", ondelete="SET NULL"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
