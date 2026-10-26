from sqlalchemy import func, select, update

from src.core.schemas import RequestStatus
from src.database.repository import RequestRepository
from src.modules.adoption_requests.model import ACTIVE_STATUSES, AdoptionRequest


class AdoptionRequestRepository(RequestRepository[AdoptionRequest]):
    model = AdoptionRequest

    async def find_active(self, pet_id: str, user_email: str) -> AdoptionRequest | None:
        query = select(AdoptionRequest).where(
            AdoptionRequest.pet_id == pet_id,
            AdoptionRequest.user_email == user_email,
            AdoptionRequest.status.in_(ACTIVE_STATUSES),
        )
        return await self.db.scalar(query)

    async def sync_pet_snapshot(self, pet_id: str, pet_name: str, pet_image: str) -> None:
        """Copia el nombre y la foto vigentes de la mascota en sus solicitudes. No hace commit."""
        await self.db.execute(
            update(AdoptionRequest)
            .where(AdoptionRequest.pet_id == pet_id)
            .values(pet_name=pet_name, pet_image=pet_image)
        )

    async def count_in_interview(self, pet_id: str, excluding_id: str) -> int:
        query = (
            select(func.count())
            .select_from(AdoptionRequest)
            .where(
                AdoptionRequest.pet_id == pet_id,
                AdoptionRequest.id != excluding_id,
                AdoptionRequest.status == RequestStatus.IN_INTERVIEW,
            )
        )
        return (await self.db.scalar(query)) or 0
