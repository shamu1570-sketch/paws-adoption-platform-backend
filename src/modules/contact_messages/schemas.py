from datetime import datetime
from enum import StrEnum

from pydantic import Field

from src.core.schemas import (
    CamelModel,
    Email,
    OptionalStr,
    PersonName,
    Text150,
    bounded_text,
)

# Cuerpo de un mensaje o de una respuesta: suficiente para explicarse, acotado para la interfaz.
MessageBody = bounded_text(2000, min_length=10)

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 50


class ContactTopic(StrEnum):
    GENERAL = "general"
    # Exige la mascota de interés (o el refugio); el refugio se toma de la mascota.
    ADOPTION = "adopcion"
    # Entrega o ingreso de una mascota: exige el refugio destinatario.
    SURRENDER = "entrega"


class ContactMessageCreate(CamelModel):
    """Formulario público de contacto."""

    name: PersonName
    email: Email
    topic: ContactTopic = ContactTopic.GENERAL
    pet_id: OptionalStr = None
    shelter_id: OptionalStr = None
    subject: Text150
    message: MessageBody


class ContactMessageFilters(CamelModel):
    """Paginación y filtro de la bandeja de entrada."""

    # null = todos; true = solo leídos; false = solo no leídos.
    is_read: bool | None = None
    # Solo administradores generales: mensajes de un refugio en particular.
    shelter_id: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX)


class ContactReplyCreate(CamelModel):
    body: MessageBody


class ContactReplyOut(CamelModel):
    id: str
    admin_name: str
    body: str
    created_at: datetime | None


class ContactMessageOut(CamelModel):
    id: str
    name: str
    email: str
    topic: str
    shelter_id: str | None
    shelter_name: str | None
    pet_id: str | None
    pet_name: str | None
    subject: str
    message: str
    is_read: bool
    created_at: datetime | None
    replies: list[ContactReplyOut]


class ContactReceiptOut(CamelModel):
    """Acuse para el remitente: no devuelve el contenido ni datos de otros mensajes."""

    id: str
    created_at: datetime | None


class ContactInboxOut(CamelModel):
    """Una página de la bandeja de entrada."""

    items: list[ContactMessageOut]
    # Mensajes que cumplen el filtro (para paginar) y no leídos en total (para el indicador).
    total: int
    unread: int
    page: int
    page_size: int
