from sqlalchemy import update

from src.database.repository import RequestRepository
from src.modules.surrender_requests.model import SurrenderRequest


class SurrenderRequestRepository(RequestRepository[SurrenderRequest]):
    model = SurrenderRequest

    async def rename_shelter(self, shelter_id: str, shelter_name: str) -> None:
        """Sincroniza el nombre desnormalizado del refugio. No hace commit."""
        await self.db.execute(
            update(SurrenderRequest)
            .where(SurrenderRequest.shelter_id == shelter_id)
            .values(shelter_name=shelter_name)
        )
