import json

from sqlalchemy import Text, cast, func, select

from src.database.repository import BaseRepository
from src.modules.personalities.model import Personality
from src.modules.pets.model import Pet


class PersonalityRepository(BaseRepository[Personality]):
    model = Personality

    async def find_all(self) -> list[Personality]:
        return await self._fetch_all(select(Personality).order_by(Personality.name))

    async def find_by_name(self, name: str) -> Personality | None:
        query = select(Personality).where(func.lower(Personality.name) == name.lower())
        return await self.db.scalar(query)

    async def missing(self, names: list[str]) -> list[str]:
        """Nombres que no existen en el catálogo (la comparación respeta mayúsculas)."""
        if not names:
            return []
        query = select(Personality.name).where(Personality.name.in_(names))
        existing = set((await self.db.scalars(query)).all())
        return [name for name in names if name not in existing]

    async def is_in_use(self, name: str) -> bool:
        """Si alguna mascota tiene asignado el rasgo (la lista se guarda como texto JSON)."""
        token = json.dumps(name, ensure_ascii=False)
        query = select(Pet.id).where(cast(Pet.personality, Text).contains(token)).limit(1)
        return await self.db.scalar(query) is not None
