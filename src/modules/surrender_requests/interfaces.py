from typing import Protocol

from src.core.schemas import RequestFilters
from src.modules.shelters.model import Shelter
from src.modules.surrender_requests.model import SurrenderRequest


class SurrenderRequestRepositoryPort(Protocol):
    async def find_all(self, filters: RequestFilters) -> list[SurrenderRequest]: ...

    async def get(self, entity_id: str) -> SurrenderRequest | None: ...

    async def find_by_tracking_code(self, tracking_code: str) -> SurrenderRequest | None: ...

    async def save(self, entity: SurrenderRequest) -> SurrenderRequest: ...


class ShelterLookup(Protocol):
    """Lo único que el dominio de entregas necesita saber de los refugios."""

    async def get(self, entity_id: str) -> Shelter | None: ...
