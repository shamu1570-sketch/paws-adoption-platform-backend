from datetime import datetime
from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from fastapi import UploadFile
from pydantic import Field, model_validator

from src.core.schemas import (
    CamelModel,
    LongText,
    OptionalStr,
    PartialUpdateModel,
    PersonName,
    PetType,
    Text100,
    bounded_text,
)
from src.modules.pets.life_stage import AgeUnit, check_age

# Hasta 10 rasgos de personalidad, cortos para que quepan en las etiquetas de la interfaz.
Personality = Annotated[list[bounded_text(40)], Field(max_length=10)]

AgeCategory = Literal["cachorro", "joven", "adulto", "senior"]
Gender = Literal["macho", "hembra"]
Size = Literal["pequeño", "mediano", "grande"]


class AdoptionStatus(StrEnum):
    AVAILABLE = "disponible"
    IN_PROCESS = "en_proceso"
    ADOPTED = "adoptado"


class PetFilters(CamelModel):
    """Filtros opcionales por query string del catálogo de mascotas."""

    type: PetType | None = None
    gender: Gender | None = None
    size: Size | None = None
    age_category: AgeCategory | None = None
    adoption_status: AdoptionStatus | None = None
    shelter_id: str | None = None
    search: str | None = None
    vaccinated: bool | None = None
    dewormed: bool | None = None
    sterilized: bool | None = None
    # Incluye las fichas no publicadas; exige sesión de administrador.
    include_hidden: bool = False


class PetCreate(CamelModel):
    """Datos del formulario; la fotografía viaja aparte como archivo y el nombre del refugio
    se toma de la base de datos."""

    name: PersonName
    type: PetType
    breed: Text100
    # La etapa de vida y el texto de la edad los calcula la API a partir de estos dos.
    age_value: int
    age_unit: AgeUnit
    gender: Gender
    size: Size
    personality: Personality = Field(default_factory=list)
    description: LongText
    story: LongText
    vaccinated: bool = False
    dewormed: bool = False
    sterilized: bool = False
    health_status: LongText
    adoption_status: AdoptionStatus = AdoptionStatus.AVAILABLE
    # Publicar de inmediato en el catálogo público o dejarla oculta en revisión.
    is_visible: bool = True
    shelter_id: OptionalStr = None
    # Solicitud de entrega aprobada de la que proviene la mascota, si aplica.
    surrender_request_id: OptionalStr = None

    @model_validator(mode="after")
    def check_age(self) -> "PetCreate":
        check_age(self.age_value, self.age_unit)
        return self


class PetUpdate(PartialUpdateModel):
    nullable_fields: ClassVar[frozenset[str]] = frozenset({"shelter_id"})

    name: PersonName | None = None
    type: PetType | None = None
    breed: Text100 | None = None
    age_value: int | None = None
    age_unit: AgeUnit | None = None
    gender: Gender | None = None
    size: Size | None = None
    personality: Personality | None = None
    description: LongText | None = None
    story: LongText | None = None
    vaccinated: bool | None = None
    dewormed: bool | None = None
    sterilized: bool | None = None
    health_status: LongText | None = None
    adoption_status: AdoptionStatus | None = None
    is_visible: bool | None = None
    shelter_id: OptionalStr = None


class PetCreateForm(PetCreate):
    """Formulario multipart de alta: los campos de la mascota y de 1 a 4 fotografías."""

    photos: list[UploadFile]

    def to_payload(self) -> PetCreate:
        return PetCreate.model_validate(self.model_dump(exclude={"photos"}))


class PetUpdateForm(PetUpdate):
    """Formulario multipart de edición (PATCH): solo los campos que cambiaron.

    `photos` agrega fotografías nuevas y `remove_photos` indica las URLs actuales a quitar.
    """

    nullable_fields: ClassVar[frozenset[str]] = frozenset({"shelter_id"})

    photos: list[UploadFile] | None = None
    remove_photos: list[str] | None = None

    def to_payload(self) -> PetUpdate:
        data = self.model_dump(exclude={"photos", "remove_photos"}, exclude_unset=True)
        return PetUpdate.model_validate(data)


class PetOut(CamelModel):
    id: str
    name: str
    type: str
    breed: str
    age_value: int
    age_unit: str
    age: str
    age_category: str
    gender: str
    size: str
    personality: list[str]
    description: str
    story: str
    image: str
    # Galería completa (1 a 4 fotos), la primera es la principal.
    photos: list[str]
    vaccinated: bool
    dewormed: bool
    sterilized: bool
    health_status: str
    adoption_status: str
    is_visible: bool
    shelter_id: str | None
    shelter_name: str | None
    created_at: datetime | None
