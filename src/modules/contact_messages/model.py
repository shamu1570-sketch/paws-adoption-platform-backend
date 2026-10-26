from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:
    from src.modules.shelters.model import Shelter


class ContactMessage(Base):
    """Mensaje enviado desde el formulario público de contacto."""

    __tablename__ = "contact_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), index=True)
    # Motivo: "general", "adopcion" o "entrega"; los dos últimos van dirigidos a un refugio.
    topic: Mapped[str] = mapped_column(String(20), default="general", server_default="general")
    # Refugio destinatario: solo sus administradores (y los generales) ven el mensaje.
    shelter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("shelters.id", ondelete="SET NULL"), index=True
    )
    # Mascota de interés (consultas de adopción); el nombre se conserva si se elimina la ficha.
    pet_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pets.id", ondelete="SET NULL")
    )
    pet_name: Mapped[str | None] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(150))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Respuestas enviadas por correo, de la más antigua a la más reciente.
    replies: Mapped[list["ContactReply"]] = relationship(
        order_by="ContactReply.created_at",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    shelter: Mapped["Shelter | None"] = relationship(lazy="selectin")

    @property
    def shelter_name(self) -> str | None:
        return self.shelter.name if self.shelter is not None else None


class ContactReply(Base):
    """Respuesta de un administrador que ya fue enviada por correo al remitente."""

    __tablename__ = "contact_message_replies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contact_messages.id", ondelete="CASCADE"), index=True
    )
    admin_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("admins.id", ondelete="SET NULL")
    )
    # Nombre del administrador al momento de responder; se conserva aunque se elimine su cuenta.
    admin_name: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
