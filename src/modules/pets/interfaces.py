from dataclasses import dataclass
from typing import Protocol

from src.modules.pets.model import Pet
from src.modules.pets.schemas import PetFilters
from src.modules.shelters.model import Shelter
from src.modules.surrender_requests.model import SurrenderRequest


class PetRepositoryPort(Protocol):
    async def find_all(self, filters: PetFilters) -> list[Pet]: ...

    async def get(self, entity_id: str) -> Pet | None: ...

    async def save(self, entity: Pet) -> Pet: ...

    async def delete(self, entity: Pet) -> None: ...


class ShelterLookup(Protocol):
    """Lo único que el dominio de mascotas necesita saber de los refugios."""

    async def get(self, entity_id: str) -> Shelter | None: ...


class PersonalityCatalog(Protocol):
    """Catálogo de personalidades administrable."""

    async def missing(self, names: list[str]) -> list[str]:
        """Nombres que no existen en el catálogo."""
        ...


class BreedCatalog(Protocol):
    """Catálogo de razas administrable, por especie."""

    async def exists(self, species: str, name: str) -> bool: ...


class SurrenderLookup(Protocol):
    """Lo único que el dominio de mascotas necesita saber de las solicitudes de entrega."""

    async def get(self, entity_id: str) -> SurrenderRequest | None: ...


class PetSnapshotSync(Protocol):
    """Tablas que guardan una copia del nombre y la foto principal de la mascota."""

    async def sync_pet_snapshot(self, pet_id: str, pet_name: str, pet_image: str) -> None:
        """Actualiza la copia sin confirmar: se confirma en el mismo commit que la ficha."""
        ...


@dataclass(frozen=True)
class PetReferences:
    """Datos de otros dominios que la ficha de la mascota consulta o mantiene al día."""

    shelters: ShelterLookup
    surrenders: SurrenderLookup
    personalities: PersonalityCatalog
    breeds: BreedCatalog
    snapshots: PetSnapshotSync
