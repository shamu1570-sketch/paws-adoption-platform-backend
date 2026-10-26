"""Edad de la mascota (cantidad + unidad) y su etapa de vida, que se calcula, nunca se elige.

Espejo de src/utils/lifeStage.ts en el frontend: cambiar una regla implica cambiar ambas.
"""

from typing import Literal

from pydantic_core import PydanticCustomError

from src.core.schemas import USER_MESSAGE_ERROR

AgeUnit = Literal["años", "meses"]

MONTHS_PER_YEAR = 12
# Límites de la cantidad según la unidad (más de 24 meses se expresa en años).
AGE_LIMITS: dict[str, int] = {"años": 30, "meses": 24}

# Límite superior (en meses, inclusive) de cada etapa; lo que pasa de 84 meses es senior.
_STAGES = (
    (MONTHS_PER_YEAR - 1, "cachorro"),  # menos de 1 año
    (3 * MONTHS_PER_YEAR, "joven"),  # de 1 a 3 años (12 - 36 meses)
    (7 * MONTHS_PER_YEAR, "adulto"),  # de 4 a 7 años (37 - 84 meses)
)


def age_in_months(value: int, unit: str) -> int:
    return value * MONTHS_PER_YEAR if unit == "años" else value


def life_stage(value: int, unit: str) -> str:
    months = age_in_months(value, unit)
    for limit, stage in _STAGES:
        if months <= limit:
            return stage
    return "senior"


def age_label(value: int, unit: str) -> str:
    """Texto que muestran las fichas, ej. "1 año", "3 meses"."""
    if value == 1:
        return "1 año" if unit == "años" else "1 mes"
    return f"{value} {unit}"


def age_error(value: int, unit: str) -> str | None:
    """Mensaje para el usuario si la cantidad no es válida para la unidad, o None."""
    limit = AGE_LIMITS[unit]
    if 1 <= value <= limit:
        return None
    return f"La edad debe estar entre 1 y {limit} {unit}"


def check_age(value: int, unit: str) -> None:
    """Validación de los DTOs: el mensaje de error se muestra tal cual al usuario."""
    error = age_error(value, unit)
    if error:
        raise PydanticCustomError(USER_MESSAGE_ERROR, error)
