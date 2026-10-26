from typing import Protocol
from uuid import uuid4

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.personalities.model import Personality
from src.modules.personalities.schemas import PersonalityCreate


class PersonalityRepositoryPort(Protocol):
    async def find_all(self) -> list[Personality]: ...

    async def get(self, entity_id: str) -> Personality | None: ...

    async def find_by_name(self, name: str) -> Personality | None: ...

    async def is_in_use(self, name: str) -> bool: ...

    async def save(self, entity: Personality) -> Personality: ...

    async def delete(self, entity: Personality) -> None: ...


class PersonalityService:
    def __init__(self, personalities: PersonalityRepositoryPort) -> None:
        self._personalities = personalities

    async def list_personalities(self) -> list[Personality]:
        return await self._personalities.find_all()

    async def create(self, payload: PersonalityCreate) -> Personality:
        if await self._personalities.find_by_name(payload.name) is not None:
            raise ConflictError(
                f"La personalidad '{payload.name}' ya existe en el catálogo",
                f"Personality '{payload.name}' already exists.",
            )
        return await self._personalities.save(Personality(id=str(uuid4()), name=payload.name))

    async def delete(self, personality_id: str) -> None:
        personality = await self._personalities.get(personality_id)
        if personality is None:
            raise NotFoundError(
                "No se encontró la personalidad indicada",
                f"Personality with ID {personality_id} was not found.",
            )
        # No se borra un rasgo en uso: las fichas quedarían con un valor fuera del catálogo.
        if await self._personalities.is_in_use(personality.name):
            raise ConflictError(
                f"'{personality.name}' está asignada a una o más mascotas. Quítala de sus fichas "
                "antes de eliminarla.",
                f"Personality '{personality.name}' is in use.",
            )
        await self._personalities.delete(personality)
