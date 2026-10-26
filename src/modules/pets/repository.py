from sqlalchemy import or_, select, update

from src.database.repository import BaseRepository
from src.modules.pets.model import Pet
from src.modules.pets.schemas import PetFilters


class PetRepository(BaseRepository[Pet]):
    model = Pet

    async def find_all(self, filters: PetFilters) -> list[Pet]:
        query = select(Pet).order_by(Pet.created_at.desc(), Pet.id)
        exact_matches = {
            Pet.type: filters.type,
            Pet.gender: filters.gender,
            Pet.size: filters.size,
            Pet.age_category: filters.age_category,
            Pet.adoption_status: filters.adoption_status,
            Pet.shelter_id: filters.shelter_id,
        }
        for column, value in exact_matches.items():
            if value:
                query = query.where(column == value)
        health_flags = {
            Pet.vaccinated: filters.vaccinated,
            Pet.dewormed: filters.dewormed,
            Pet.sterilized: filters.sterilized,
        }
        for column, flag in health_flags.items():
            if flag is not None:
                query = query.where(column.is_(flag))
        if not filters.include_hidden:
            query = query.where(Pet.is_visible.is_(True))
        if filters.search and filters.search.strip():
            pattern = f"%{filters.search.strip()}%"
            query = query.where(or_(Pet.name.ilike(pattern), Pet.breed.ilike(pattern)))
        return await self._fetch_all(query)

    async def rename_shelter(self, shelter_id: str, shelter_name: str) -> None:
        """Sincroniza el nombre desnormalizado del refugio. No hace commit."""
        await self.db.execute(
            update(Pet).where(Pet.shelter_id == shelter_id).values(shelter_name=shelter_name)
        )
