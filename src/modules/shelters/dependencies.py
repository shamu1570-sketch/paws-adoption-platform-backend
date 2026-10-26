from typing import Annotated

from fastapi import Depends

from src.api.deps import DbSession
from src.core.config import settings
from src.modules.pets.repository import PetRepository
from src.modules.shelters.repository import ShelterRepository
from src.modules.shelters.service import ShelterService
from src.modules.surrender_requests.repository import SurrenderRequestRepository
from src.storage.dependencies import FileStorageDep
from src.storage.gallery import PhotoGalleryStore


def get_shelter_service(db: DbSession, storage: FileStorageDep) -> ShelterService:
    return ShelterService(
        shelters=ShelterRepository(db),
        photos=PhotoGalleryStore(storage, settings.MAX_PHOTO_SIZE_MB, folder="shelters"),
        name_syncs=[PetRepository(db), SurrenderRequestRepository(db)],
    )


ShelterServiceDep = Annotated[ShelterService, Depends(get_shelter_service)]
