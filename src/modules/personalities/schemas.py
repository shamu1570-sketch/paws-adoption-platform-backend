from datetime import datetime
from typing import Annotated

from pydantic import StringConstraints

from src.core.schemas import PLAIN_NAME_PATTERN, CamelModel
from src.modules.personalities.model import PERSONALITY_NAME_LENGTH

# Rasgo: solo letras (con acentos) y espacios sencillos, ej. "Juguetón", "Bueno con niños".
PersonalityName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=PERSONALITY_NAME_LENGTH,
        pattern=PLAIN_NAME_PATTERN,
    ),
]


class PersonalityCreate(CamelModel):
    name: PersonalityName


class PersonalityOut(CamelModel):
    id: str
    name: str
    created_at: datetime | None
