from typing import Annotated

from fastapi import Depends

from src.api.deps import DbSession
from src.modules.adoption_requests.repository import AdoptionRequestRepository
from src.modules.adoption_requests.service import AdoptionRequestService
from src.modules.pets.repository import PetRepository


def get_adoption_request_service(db: DbSession) -> AdoptionRequestService:
    return AdoptionRequestService(requests=AdoptionRequestRepository(db), pets=PetRepository(db))


AdoptionRequestServiceDep = Annotated[AdoptionRequestService, Depends(get_adoption_request_service)]
