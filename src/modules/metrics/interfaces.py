from datetime import datetime
from typing import Protocol

from src.core.schemas import RequestStatus
from src.modules.adoption_requests.model import AdoptionRequest
from src.modules.contact_messages.model import ContactMessage
from src.modules.pets.schemas import AdoptionStatus
from src.modules.surrender_requests.model import SurrenderRequest


class MetricsRepositoryPort(Protocol):
    """Consultas del panel; con `shelter_id` se limitan a ese refugio."""

    async def count_pets(
        self, shelter_id: str | None, status: AdoptionStatus | None = None
    ) -> int: ...

    async def count_adoption_requests(
        self, shelter_id: str | None, *statuses: RequestStatus
    ) -> int: ...

    async def count_surrender_requests(
        self, shelter_id: str | None, status: RequestStatus
    ) -> int: ...

    async def count_unread_messages(self, shelter_id: str | None) -> int: ...

    async def count_shelters(self, shelter_id: str | None) -> int: ...

    async def adoption_dates(
        self, shelter_id: str | None, since: datetime
    ) -> tuple[list[datetime], list[datetime]]:
        """(fechas de las solicitudes recibidas, fechas de las aprobadas) desde `since`."""
        ...

    async def stale_adoptions(
        self, shelter_id: str | None, created_before: datetime, limit: int
    ) -> tuple[int, list[AdoptionRequest]]: ...

    async def unanswered_messages(
        self, shelter_id: str | None, limit: int
    ) -> tuple[int, list[ContactMessage]]: ...

    async def pending_surrenders(
        self, shelter_id: str | None, limit: int
    ) -> tuple[int, list[SurrenderRequest]]: ...
