from datetime import datetime
from typing import ClassVar

from fastapi import UploadFile
from pydantic import Field

from src.core.schemas import (
    CamelModel,
    Email,
    LongText,
    PartialUpdateModel,
    Phone,
    ShelterName,
    Text100,
    Text300,
    Website,
)


class ShelterCreate(CamelModel):
    """Datos del refugio; las fotografías viajan aparte como archivos."""

    name: ShelterName
    address: Text300
    city: Text100
    phone: Phone
    email: Email
    website: Website = None
    capacity: int = Field(default=0, ge=0)
    current_pet_count: int = Field(default=0, ge=0)
    description: LongText
    verified: bool = False


class ShelterUpdate(PartialUpdateModel):
    nullable_fields: ClassVar[frozenset[str]] = frozenset({"website"})

    name: ShelterName | None = None
    address: Text300 | None = None
    city: Text100 | None = None
    phone: Phone | None = None
    email: Email | None = None
    website: Website = None
    capacity: int | None = Field(default=None, ge=0)
    current_pet_count: int | None = Field(default=None, ge=0)
    description: LongText | None = None
    verified: bool | None = None


class ShelterCreateForm(ShelterCreate):
    """Formulario multipart de alta: los campos del refugio y de 1 a 4 fotografías."""

    photos: list[UploadFile]

    def to_payload(self) -> ShelterCreate:
        return ShelterCreate.model_validate(self.model_dump(exclude={"photos"}))


class ShelterUpdateForm(ShelterUpdate):
    """Formulario multipart de edición (PATCH): solo los campos que cambiaron.

    `photos` agrega fotografías nuevas y `remove_photos` indica las URLs actuales a quitar.
    """

    nullable_fields: ClassVar[frozenset[str]] = frozenset({"website"})

    photos: list[UploadFile] | None = None
    remove_photos: list[str] | None = None

    def to_payload(self) -> ShelterUpdate:
        data = self.model_dump(exclude={"photos", "remove_photos"}, exclude_unset=True)
        return ShelterUpdate.model_validate(data)


class ShelterOut(CamelModel):
    id: str
    name: str
    address: str
    city: str
    phone: str
    email: str
    website: str | None
    capacity: int
    current_pet_count: int
    description: str
    # Foto principal (la primera de la galería).
    image: str
    # Galería completa (1 a 4 fotos), la primera es la principal.
    photos: list[str]
    verified: bool
    created_at: datetime | None
