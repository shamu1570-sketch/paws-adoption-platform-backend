from typing import Protocol

from src.modules.shelters.model import Shelter


class ShelterRepositoryPort(Protocol):
    async def find_all(self) -> list[Shelter]: ...

    async def get(self, entity_id: str) -> Shelter | None: ...

    async def save(self, entity: Shelter) -> Shelter: ...

    async def delete(self, entity: Shelter) -> None: ...


class ShelterNameSync(Protocol):
    """Tablas que guardan una copia del nombre del refugio y deben seguir sus cambios."""

    async def rename_shelter(self, shelter_id: str, shelter_name: str) -> None: ...
