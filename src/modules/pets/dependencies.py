from typing import Annotated

from fastapi import Depends

from src.api.deps import DbSession
from src.core.config import settings
from src.modules.adoption_requests.repository import AdoptionRequestRepository
from src.modules.breeds.repository import BreedRepository
from src.modules.personalities.repository import PersonalityRepository
from src.modules.pets.interfaces import PetReferences
from src.modules.pets.photo import PetPhotoStore
from src.modules.pets.repository import PetRepository
from src.modules.pets.service import PetService
from src.modules.shelters.repository import ShelterRepository
from src.modules.surrender_requests.repository import SurrenderRequestRepository
from src.storage.dependencies import FileStorageDep


def get_pet_service(db: DbSession, storage: FileStorageDep) -> PetService:
    return PetService(
        pets=PetRepository(db),
        references=PetReferences(
            shelters=ShelterRepository(db),
            surrenders=SurrenderRequestRepository(db),
            personalities=PersonalityRepository(db),
            breeds=BreedRepository(db),
            snapshots=AdoptionRequestRepository(db),
        ),
        photos=PetPhotoStore(storage, settings.MAX_PHOTO_SIZE_MB),
    )


PetServiceDep = Annotated[PetService, Depends(get_pet_service)]
