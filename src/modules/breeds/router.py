from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.deps import DbSession
from src.core.responses import ResponsePayload, success
from src.core.schemas import DeletedOut
from src.modules.auth.dependencies import require_global_admin
from src.modules.breeds.repository import BreedRepository
from src.modules.breeds.schemas import BreedCreate, BreedFilters, BreedOut
from src.modules.breeds.service import BreedService

# Catálogo público: lo usan el formulario de mascotas y los filtros.
public_router = APIRouter(prefix="/breeds", tags=["Razas"])
# Alta y baja: administradores generales (el catálogo es común a todos los refugios).
admin_router = APIRouter(
    prefix="/admin/breeds", tags=["Razas"], dependencies=[require_global_admin]
)


def get_breed_service(db: DbSession) -> BreedService:
    return BreedService(BreedRepository(db))


BreedServiceDep = Annotated[BreedService, Depends(get_breed_service)]


@public_router.get("", response_model=ResponsePayload[list[BreedOut]])
async def list_breeds(service: BreedServiceDep, filters: Annotated[BreedFilters, Query()]):
    breeds = await service.list_breeds(filters.species)
    return success(breeds, "Razas obtenidas exitosamente")


@admin_router.post("", response_model=ResponsePayload[BreedOut], status_code=201)
async def create_breed(payload: BreedCreate, service: BreedServiceDep):
    breed = await service.create(payload)
    return success(breed, "Raza agregada al catálogo", 201)


@admin_router.delete("/{breed_id}", response_model=ResponsePayload[DeletedOut])
async def delete_breed(breed_id: str, service: BreedServiceDep):
    await service.delete(breed_id)
    return success(DeletedOut(id=breed_id, deleted=True), "Raza eliminada del catálogo")
