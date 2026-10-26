from typing import Protocol
from uuid import uuid4

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.breeds.model import Breed
from src.modules.breeds.schemas import BreedCreate

SPECIES_LABELS = {"perro": "perros", "gato": "gatos"}


class BreedRepositoryPort(Protocol):
    async def find_all(self, species: str | None) -> list[Breed]: ...

    async def get(self, entity_id: str) -> Breed | None: ...

    async def find_by_name(self, species: str, name: str) -> Breed | None: ...

    async def is_in_use(self, breed: Breed) -> bool: ...

    async def save(self, entity: Breed) -> Breed: ...

    async def delete(self, entity: Breed) -> None: ...


class BreedService:
    def __init__(self, breeds: BreedRepositoryPort) -> None:
        self._breeds = breeds

    async def list_breeds(self, species: str | None) -> list[Breed]:
        return await self._breeds.find_all(species)

    async def create(self, payload: BreedCreate) -> Breed:
        if await self._breeds.find_by_name(payload.species, payload.name) is not None:
            raise ConflictError(
                f"La raza '{payload.name}' ya existe en el catálogo de "
                f"{SPECIES_LABELS[payload.species]}",
                f"Breed '{payload.name}' already exists for species '{payload.species}'.",
            )
        breed = Breed(id=str(uuid4()), name=payload.name, species=payload.species)
        return await self._breeds.save(breed)

    async def delete(self, breed_id: str) -> None:
        breed = await self._breeds.get(breed_id)
        if breed is None:
            raise NotFoundError(
                "No se encontró la raza indicada", f"Breed with ID {breed_id} was not found."
            )
        # No se borra una raza en uso: las fichas quedarían con un valor fuera del catálogo.
        if await self._breeds.is_in_use(breed):
            raise ConflictError(
                f"'{breed.name}' está asignada a una o más mascotas. Cambia la raza de esas "
                "fichas antes de eliminarla.",
                f"Breed '{breed.name}' is in use.",
            )
        await self._breeds.delete(breed)
