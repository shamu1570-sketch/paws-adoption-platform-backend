from datetime import datetime

from sqlalchemy import ColumnElement, Select, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from src.core.schemas import RequestStatus
from src.database.connection import Base
from src.modules.adoption_requests.model import AdoptionRequest
from src.modules.contact_messages.model import ContactMessage, ContactReply
from src.modules.pets.model import Pet
from src.modules.pets.schemas import AdoptionStatus
from src.modules.shelters.model import Shelter
from src.modules.surrender_requests.model import SurrenderRequest


class MetricsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count_pets(self, shelter_id: str | None, status: AdoptionStatus | None = None) -> int:
        conditions = [Pet.adoption_status == status] if status else []
        return await self._count(Pet, Pet.shelter_id, shelter_id, *conditions)

    async def count_adoption_requests(
        self, shelter_id: str | None, *statuses: RequestStatus
    ) -> int:
        return await self._count(
            AdoptionRequest,
            AdoptionRequest.shelter_id,
            shelter_id,
            AdoptionRequest.status.in_(statuses),
        )

    async def count_surrender_requests(self, shelter_id: str | None, status: RequestStatus) -> int:
        return await self._count(
            SurrenderRequest,
            SurrenderRequest.shelter_id,
            shelter_id,
            SurrenderRequest.status == status,
        )

    async def count_unread_messages(self, shelter_id: str | None) -> int:
        return await self._count(
            ContactMessage, ContactMessage.shelter_id, shelter_id, ContactMessage.is_read.is_(False)
        )

    async def count_shelters(self, shelter_id: str | None) -> int:
        return await self._count(Shelter, Shelter.id, shelter_id)

    async def adoption_dates(
        self, shelter_id: str | None, since: datetime
    ) -> tuple[list[datetime], list[datetime]]:
        received = _scoped(
            select(AdoptionRequest.created_at).where(AdoptionRequest.created_at >= since),
            AdoptionRequest.shelter_id,
            shelter_id,
        )
        approved = _scoped(
            select(AdoptionRequest.status_changed_at).where(
                AdoptionRequest.status == RequestStatus.APPROVED,
                AdoptionRequest.status_changed_at >= since,
            ),
            AdoptionRequest.shelter_id,
            shelter_id,
        )
        return (
            list((await self.db.scalars(received)).all()),
            list((await self.db.scalars(approved)).all()),
        )

    async def stale_adoptions(
        self, shelter_id: str | None, created_before: datetime, limit: int
    ) -> tuple[int, list[AdoptionRequest]]:
        conditions = (
            AdoptionRequest.status == RequestStatus.PENDING,
            AdoptionRequest.created_at < created_before,
        )
        return await self._oldest(
            AdoptionRequest, AdoptionRequest.shelter_id, shelter_id, conditions, limit
        )

    async def unanswered_messages(
        self, shelter_id: str | None, limit: int
    ) -> tuple[int, list[ContactMessage]]:
        has_reply = exists().where(ContactReply.message_id == ContactMessage.id)
        return await self._oldest(
            ContactMessage, ContactMessage.shelter_id, shelter_id, (~has_reply,), limit
        )

    async def pending_surrenders(
        self, shelter_id: str | None, limit: int
    ) -> tuple[int, list[SurrenderRequest]]:
        conditions = (SurrenderRequest.status == RequestStatus.PENDING,)
        return await self._oldest(
            SurrenderRequest, SurrenderRequest.shelter_id, shelter_id, conditions, limit
        )

    async def _oldest[ModelT: Base](
        self,
        model: type[ModelT],
        shelter_column: InstrumentedAttribute,
        shelter_id: str | None,
        conditions: tuple[ColumnElement[bool], ...],
        limit: int,
    ) -> tuple[int, list[ModelT]]:
        """Total que cumple las condiciones y los `limit` más antiguos."""
        total = await self._count(model, shelter_column, shelter_id, *conditions)
        query = _scoped(
            select(model).where(*conditions).order_by(model.created_at).limit(limit),
            shelter_column,
            shelter_id,
        )
        return total, list((await self.db.scalars(query)).all())

    async def _count(
        self,
        model: type[Base],
        shelter_column: InstrumentedAttribute,
        shelter_id: str | None,
        *conditions: ColumnElement[bool],
    ) -> int:
        query = _scoped(
            select(func.count()).select_from(model).where(*conditions), shelter_column, shelter_id
        )
        return (await self.db.scalar(query)) or 0


def _scoped(query: Select, shelter_column: InstrumentedAttribute, shelter_id: str | None) -> Select:
    return query.where(shelter_column == shelter_id) if shelter_id else query
