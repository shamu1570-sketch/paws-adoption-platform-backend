from typing import Annotated

from fastapi import APIRouter, Form

from src.core.responses import ResponsePayload, success
from src.core.schemas import DeletedOut
from src.modules.auth.dependencies import (
    AdminScopeDep,
    require_global_admin,
    require_super_admin,
)
from src.modules.shelters.dependencies import ShelterServiceDep
from src.modules.shelters.schemas import ShelterCreateForm, ShelterOut, ShelterUpdateForm
from src.storage.gallery import read_uploads

router = APIRouter(prefix="/shelters", tags=["Refugios"])

SHELTER_PATH = "/{shelter_id}"
# Los campos del refugio y sus fotografías (JPG, PNG o WEBP; se guardan como WebP)
# viajan en un mismo formulario.
MULTIPART_FORM = Form(media_type="multipart/form-data")


@router.get("", response_model=ResponsePayload[list[ShelterOut]])
async def list_shelters(service: ShelterServiceDep):
    shelters = await service.list_shelters()
    return success(shelters, "Refugios obtenidos exitosamente")


@router.get(SHELTER_PATH, response_model=ResponsePayload[ShelterOut])
async def get_shelter(shelter_id: str, service: ShelterServiceDep):
    shelter = await service.get_shelter(shelter_id)
    return success(shelter, "Refugio encontrado exitosamente")


@router.post(
    "",
    response_model=ResponsePayload[ShelterOut],
    status_code=201,
    # Dar de alta refugios es tarea de los administradores generales.
    dependencies=[require_global_admin],
)
async def create_shelter(
    service: ShelterServiceDep, form: Annotated[ShelterCreateForm, MULTIPART_FORM]
):
    shelter = await service.create_shelter(form.to_payload(), await read_uploads(form.photos))
    return success(shelter, "Refugio registrado exitosamente", 201)


@router.patch(SHELTER_PATH, response_model=ResponsePayload[ShelterOut])
async def update_shelter(
    shelter_id: str,
    service: ShelterServiceDep,
    form: Annotated[ShelterUpdateForm, MULTIPART_FORM],
    scope: AdminScopeDep,
):
    """Actualización parcial: solo cambian los campos y fotos enviados.

    Un administrador de refugio solo puede editar el suyo.
    """
    scope.ensure_access(shelter_id)
    shelter = await service.update_shelter(
        shelter_id,
        form.to_payload(),
        new_photos=await read_uploads(form.photos),
        remove_photos=form.remove_photos or [],
    )
    return success(shelter, "Refugio actualizado exitosamente")


@router.delete(
    SHELTER_PATH, response_model=ResponsePayload[DeletedOut], dependencies=[require_super_admin]
)
async def delete_shelter(shelter_id: str, service: ShelterServiceDep):
    await service.delete_shelter(shelter_id)
    return success(
        DeletedOut(id=shelter_id, deleted=True), "Refugio eliminado del sistema exitosamente"
    )
