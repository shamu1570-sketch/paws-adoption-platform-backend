from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.deps import DbSession
from src.core.responses import ResponsePayload, success
from src.core.schemas import DeletedOut
from src.modules.auth.dependencies import require_global_admin
from src.modules.personalities.repository import PersonalityRepository
from src.modules.personalities.schemas import PersonalityCreate, PersonalityOut
from src.modules.personalities.service import PersonalityService

router = APIRouter(prefix="/personalities", tags=["Personalidades"])


def get_personality_service(db: DbSession) -> PersonalityService:
    return PersonalityService(PersonalityRepository(db))


PersonalityServiceDep = Annotated[PersonalityService, Depends(get_personality_service)]


@router.get("", response_model=ResponsePayload[list[PersonalityOut]])
async def list_personalities(service: PersonalityServiceDep):
    """Catálogo público: lo usan los filtros del catálogo y el formulario de mascotas."""
    personalities = await service.list_personalities()
    return success(personalities, "Personalidades obtenidas exitosamente")


@router.post(
    "",
    response_model=ResponsePayload[PersonalityOut],
    status_code=201,
    dependencies=[require_global_admin],
)
async def create_personality(payload: PersonalityCreate, service: PersonalityServiceDep):
    personality = await service.create(payload)
    return success(personality, "Personalidad agregada al catálogo", 201)


@router.delete(
    "/{personality_id}",
    response_model=ResponsePayload[DeletedOut],
    dependencies=[require_global_admin],
)
async def delete_personality(personality_id: str, service: PersonalityServiceDep):
    await service.delete(personality_id)
    return success(
        DeletedOut(id=personality_id, deleted=True), "Personalidad eliminada del catálogo"
    )
