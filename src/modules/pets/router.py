from typing import Annotated

from fastapi import APIRouter, Form, Query

from src.core.exceptions import UnauthorizedError
from src.core.responses import ResponsePayload, success
from src.core.schemas import DeletedOut
from src.modules.auth.dependencies import AdminScopeDep, OptionalScope
from src.modules.pets.dependencies import PetServiceDep
from src.modules.pets.schemas import PetCreateForm, PetFilters, PetOut, PetUpdateForm
from src.storage.gallery import read_uploads

router = APIRouter(prefix="/pets", tags=["Mascotas"])

PET_PATH = "/{pet_id}"
# Los campos de la mascota y sus fotografías (JPG, PNG o WEBP; se guardan como WebP)
# viajan en un mismo formulario.
MULTIPART_FORM = Form(media_type="multipart/form-data")


@router.get("", response_model=ResponsePayload[list[PetOut]])
async def list_pets(
    service: PetServiceDep, filters: Annotated[PetFilters, Query()], scope: OptionalScope
):
    if filters.include_hidden and scope is None:
        raise UnauthorizedError(
            "Debes iniciar sesión para ver las mascotas no publicadas",
            "includeHidden requires an authenticated admin.",
        )
    if filters.include_hidden:
        # El listado del panel solo incluye las mascotas de los refugios que gestiona.
        filters = filters.model_copy(update={"shelter_id": scope.restrict(filters.shelter_id)})
    pets = await service.list_pets(filters)
    return success(pets, "Catálogo de mascotas obtenido exitosamente")


@router.get(PET_PATH, response_model=ResponsePayload[PetOut])
async def get_pet(pet_id: str, service: PetServiceDep, scope: OptionalScope):
    pet = await service.get_pet(pet_id, scope)
    return success(pet, "Detalle de mascota obtenido exitosamente")


@router.post("", response_model=ResponsePayload[PetOut], status_code=201)
async def create_pet(
    service: PetServiceDep,
    form: Annotated[PetCreateForm, MULTIPART_FORM],
    scope: AdminScopeDep,
):
    pet = await service.create_pet(form.to_payload(), await read_uploads(form.photos), scope)
    return success(pet, "Mascota registrada exitosamente", 201)


@router.patch(PET_PATH, response_model=ResponsePayload[PetOut])
async def update_pet(
    pet_id: str,
    service: PetServiceDep,
    form: Annotated[PetUpdateForm, MULTIPART_FORM],
    scope: AdminScopeDep,
):
    """Actualización parcial: solo cambian los campos y fotos enviados."""
    pet = await service.update_pet(
        pet_id,
        form.to_payload(),
        new_photos=await read_uploads(form.photos),
        remove_photos=form.remove_photos or [],
        scope=scope,
    )
    return success(pet, "Ficha de la mascota actualizada exitosamente")


@router.delete(PET_PATH, response_model=ResponsePayload[DeletedOut])
async def delete_pet(pet_id: str, service: PetServiceDep, scope: AdminScopeDep):
    await service.delete_pet(pet_id, scope)
    return success(
        DeletedOut(id=pet_id, deleted=True), "Mascota eliminada del sistema exitosamente"
    )
