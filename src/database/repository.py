from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import RequestFilters
from src.database.connection import Base


class BaseRepository[ModelT: Base]:
    """Operaciones de persistencia comunes a todas las tablas."""

    model: type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, entity_id: str) -> ModelT | None:
        return await self.db.get(self.model, entity_id)

    async def save(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def discard_changes(self) -> None:
        await self.db.rollback()

    async def delete(self, entity: ModelT) -> None:
        await self.db.delete(entity)
        await self.db.commit()

    async def _fetch_all(self, query: Select[tuple[ModelT]]) -> list[ModelT]:
        return list((await self.db.scalars(query)).all())


class RequestRepository[ModelT: Base](BaseRepository[ModelT]):
    """Consultas comunes a las tablas de solicitudes (adopción y entrega)."""

    async def find_by_tracking_code(self, tracking_code: str) -> ModelT | None:
        query = select(self.model).where(self.model.tracking_code == tracking_code)
        return await self.db.scalar(query)

    async def find_all(self, filters: RequestFilters) -> list[ModelT]:
        query = select(self.model).order_by(self.model.created_at.desc(), self.model.id)
        if filters.shelter_id:
            query = query.where(self.model.shelter_id == filters.shelter_id)
        if filters.status:
            query = query.where(self.model.status == filters.status)
        return await self._fetch_all(query)
