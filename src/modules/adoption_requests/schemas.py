from datetime import datetime
from typing import Literal

from src.core.schemas import (
    CamelModel,
    Email,
    IdStr,
    MessageText,
    PersonName,
    Phone,
)

HouseType = Literal["casa", "departamento", "finca"]


class AdoptionRequestCreate(CamelModel):
    """`petName`, `petImage` y `shelterId` no se reciben: se toman de la mascota."""

    pet_id: IdStr
    user_name: PersonName
    user_email: Email
    user_phone: Phone
    house_type: HouseType
    has_other_pets: bool = False
    reason: MessageText


class AdoptionTrackingOut(CamelModel):
    """Estado de una solicitud para quien la envió (verificado con código y correo)."""

    tracking_code: str
    pet_id: str
    pet_name: str
    pet_image: str
    status: str
    # Última nota del refugio; es la misma que se le envió por correo al solicitante.
    admin_notes: str | None
    created_at: datetime | None


class AdoptionRequestOut(CamelModel):
    id: str
    # Indica si fue posible enviar el correo de esta operación; null en los listados.
    email_sent: bool | None = None
    tracking_code: str
    pet_id: str
    pet_name: str
    pet_image: str
    shelter_id: str | None
    user_name: str
    user_email: str
    user_phone: str
    house_type: str
    has_other_pets: bool
    reason: str
    status: str
    admin_notes: str | None
    created_at: datetime | None
