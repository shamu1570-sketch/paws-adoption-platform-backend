from sqlalchemy import func, select

from src.database.repository import BaseRepository
from src.modules.breeds.model import Breed
from src.modules.pets.model import Pet


class BreedRepository(BaseRepository[Breed]):
    model = Breed

    async def find_all(self, species: str | None) -> list[Breed]:
        query = select(Breed).order_by(Breed.species, Breed.name)
        if species:
            query = query.where(Breed.species == species)
        return await self._fetch_all(query)

    async def find_by_name(self, species: str, name: str) -> Breed | None:
        """Búsqueda sin distinguir mayúsculas, para no duplicar "Siamés" y "siamés"."""
        query = select(Breed).where(
            Breed.species == species, func.lower(Breed.name) == name.lower()
        )
        return await self.db.scalar(query)

    async def exists(self, species: str, name: str) -> bool:
        query = select(Breed.id).where(Breed.species == species, Breed.name == name).limit(1)
        return await self.db.scalar(query) is not None

    async def is_in_use(self, breed: Breed) -> bool:
        query = select(Pet.id).where(Pet.type == breed.species, Pet.breed == breed.name).limit(1)
        return await self.db.scalar(query) is not None
