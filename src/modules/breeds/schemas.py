import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, StringConstraints
from pydantic_core import PydanticCustomError

from src.core.schemas import USER_MESSAGE_ERROR, CamelModel, PetType
from src.modules.breeds.model import BREED_NAME_LENGTH

# Palabras de letras separadas por un espacio, un guion o " / " (ej. "Criollo / Mestizo").
_BREED_NAME = re.compile(r"[^\W\d_]+(?:(?: / |[ -])[^\W\d_]+)*")
BREED_NAME_ERROR = (
    "El nombre de la raza solo puede contener letras y espacios (se permiten '-' y ' / ' "
    "entre palabras)"
)


def _check_breed_name(value: str) -> str:
    if not _BREED_NAME.fullmatch(value):
        raise PydanticCustomError(USER_MESSAGE_ERROR, BREED_NAME_ERROR)
    return value


BreedName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=BREED_NAME_LENGTH),
    AfterValidator(_check_breed_name),
]


class BreedFilters(CamelModel):
    species: PetType | None = None


class BreedCreate(CamelModel):
    name: BreedName
    species: PetType


class BreedOut(CamelModel):
    id: str
    name: str
    species: str
    created_at: datetime | None
