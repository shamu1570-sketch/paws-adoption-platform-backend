from typing import Protocol

from src.core.schemas import RequestFilters
from src.modules.adoption_requests.model import AdoptionRequest
from src.modules.pets.model import Pet


class AdoptionRequestRepositoryPort(Protocol):
    async def find_all(self, filters: RequestFilters) -> list[AdoptionRequest]: ...

    async def get(self, entity_id: str) -> AdoptionRequest | None: ...

    async def find_by_tracking_code(self, tracking_code: str) -> AdoptionRequest | None: ...

    async def find_active(self, pet_id: str, user_email: str) -> AdoptionRequest | None:
        """Solicitud pendiente o en entrevista de ese correo para esa mascota, si existe."""
        ...

    async def count_in_interview(self, pet_id: str, excluding_id: str) -> int:
        """Cuántas otras solicitudes de la mascota siguen en entrevista."""
        ...

    async def save(self, entity: AdoptionRequest) -> AdoptionRequest: ...

    async def discard_changes(self) -> None:
        """Deshace la transacción en curso tras un fallo al guardar."""
        ...


class PetLookup(Protocol):
    """Lo único que el dominio de adopciones necesita saber de las mascotas."""

    async def get(self, entity_id: str) -> Pet | None: ...
