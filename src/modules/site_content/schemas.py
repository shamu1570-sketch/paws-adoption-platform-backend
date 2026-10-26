from datetime import datetime

from pydantic import Field

from src.core.schemas import CamelModel


class ContentUpdate(CamelModel):
    """Actualización por lotes de una sección: `{clave: texto}` solo con los campos que cambian."""

    values: dict[str, str] = Field(min_length=1)


class ContentOut(CamelModel):
    section: str
    values: dict[str, str]
    # Fecha de la última modificación de cualquier texto de la sección.
    updated_at: datetime | None
