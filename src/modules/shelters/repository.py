from sqlalchemy import select

from src.database.repository import BaseRepository
from src.modules.shelters.model import Shelter


class ShelterRepository(BaseRepository[Shelter]):
    model = Shelter

    async def find_all(self) -> list[Shelter]:
        return await self._fetch_all(select(Shelter).order_by(Shelter.created_at, Shelter.id))
