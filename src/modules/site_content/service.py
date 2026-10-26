import re
from typing import Protocol

from src.core.exceptions import BadRequestError, NotFoundError
from src.modules.site_content.catalog import SECTION_FIELDS, ContentSection, is_optional, is_tag
from src.modules.site_content.model import SiteContent
from src.modules.site_content.schemas import ContentOut, ContentUpdate

# Etiquetas: palabras de letras (con tildes y ñ) o números separadas por un único espacio.
_TAG_PATTERN = re.compile(r"[^\W_]+(?: [^\W_]+)*")
TAG_ERROR = "Las etiquetas solo pueden contener letras, números y espacios"


class SiteContentRepositoryPort(Protocol):
    async def find_section(self, section: str) -> list[SiteContent]: ...

    async def save_section(self, section: str, values: dict[str, str], admin_id: str) -> None: ...


class SiteContentService:
    def __init__(self, contents: SiteContentRepositoryPort) -> None:
        self._contents = contents

    async def get_section(self, section: str) -> ContentOut:
        fields = self._fields(section)
        rows = [row for row in await self._contents.find_section(section) if row.key in fields]
        return ContentOut(
            section=section,
            values={row.key: row.value for row in rows},
            updated_at=max((row.updated_at for row in rows if row.updated_at), default=None),
        )

    async def update_section(
        self, section: str, payload: ContentUpdate, admin_id: str
    ) -> ContentOut:
        fields = self._fields(section)
        values = {key: self._clean(key, value, fields) for key, value in payload.values.items()}
        await self._contents.save_section(section, values, admin_id)
        return await self.get_section(section)

    @staticmethod
    def _fields(section: str) -> dict[str, int]:
        if section not in set(ContentSection):
            raise NotFoundError(
                "La sección de contenido solicitada no existe",
                f"Unknown content section '{section}'.",
            )
        return SECTION_FIELDS[ContentSection(section)]

    @staticmethod
    def _clean(key: str, value: str, fields: dict[str, int]) -> str:
        if key not in fields:
            raise BadRequestError(
                "Uno de los textos enviados no pertenece a esta sección",
                f"Unknown content key '{key}'.",
            )
        text = value.strip()
        if not text and not is_optional(key):
            raise BadRequestError(
                "Ningún texto del sitio puede quedar vacío", f"Content key '{key}' is empty."
            )
        if len(text) > fields[key]:
            raise BadRequestError(
                f"Uno de los textos supera los {fields[key]} caracteres permitidos",
                f"Content key '{key}' exceeds {fields[key]} characters.",
            )
        if is_tag(key) and not _TAG_PATTERN.fullmatch(text):
            raise BadRequestError(TAG_ERROR, f"Content key '{key}' has special characters.")
        return text
