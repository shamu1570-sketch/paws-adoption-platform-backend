from datetime import datetime

from pydantic import model_validator

from src.core.schemas import (
    CamelModel,
    Email,
    IdStr,
    MessageText,
    PersonName,
    PetType,
    Phone,
)
from src.modules.pets.life_stage import AgeUnit, check_age


class SurrenderRequestCreate(CamelModel):
    """`shelterName` no se recibe: se toma del refugio indicado en `shelterId`."""

    pet_name: PersonName
    pet_type: PetType
    # Misma edad estructurada que la ficha de mascota; el texto lo arma la API.
    pet_age_value: int
    pet_age_unit: AgeUnit
    shelter_id: IdStr
    user_name: PersonName
    user_email: Email
    user_phone: Phone
    reason: MessageText
    health_condition: MessageText

    @model_validator(mode="after")
    def check_pet_age(self) -> "SurrenderRequestCreate":
        check_age(self.pet_age_value, self.pet_age_unit)
        return self


class SurrenderTrackingOut(CamelModel):
    """Estado de una solicitud de entrega para quien la envió (verificado con código y correo)."""

    tracking_code: str
    pet_name: str
    shelter_name: str
    status: str
    # Última nota del refugio; es la misma que se le envió por correo al solicitante.
    admin_notes: str | None
    created_at: datetime | None


class SurrenderRequestOut(CamelModel):
    id: str
    # Indica si fue posible enviar el correo de esta operación; null en los listados.
    email_sent: bool | None = None
    tracking_code: str
    # Ficha del catálogo creada al recibir a la mascota; null mientras no se registre.
    pet_id: str | None
    pet_name: str
    pet_type: str
    pet_age_value: int
    pet_age_unit: str
    pet_age: str
    shelter_id: str
    shelter_name: str
    user_name: str
    user_email: str
    user_phone: str
    reason: str
    health_condition: str
    status: str
    admin_notes: str | None
    created_at: datetime | None
