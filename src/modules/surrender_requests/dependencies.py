from typing import Annotated

from fastapi import Depends

from src.api.deps import DbSession
from src.modules.shelters.repository import ShelterRepository
from src.modules.surrender_requests.repository import SurrenderRequestRepository
from src.modules.surrender_requests.service import SurrenderRequestService


def get_surrender_request_service(db: DbSession) -> SurrenderRequestService:
    return SurrenderRequestService(
        requests=SurrenderRequestRepository(db), shelters=ShelterRepository(db)
    )


SurrenderRequestServiceDep = Annotated[
    SurrenderRequestService, Depends(get_surrender_request_service)
]
