from typing import Annotated

from fastapi import APIRouter, Query

from src.core.exceptions import ConflictError
from src.core.responses import ResponsePayload, success
from src.core.schemas import (
    STATUS_NOT_NOTIFIED,
    STATUS_NOTIFIED,
    RequestFilters,
    StatusUpdate,
    TrackingLookup,
)
from src.modules.adoption_requests.dependencies import AdoptionRequestServiceDep
from src.modules.adoption_requests.model import AdoptionRequest
from src.modules.adoption_requests.schemas import (
    AdoptionRequestCreate,
    AdoptionRequestOut,
    AdoptionTrackingOut,
)
from src.modules.adoption_requests.service import DuplicateAdoptionRequestError
from src.modules.auth.dependencies import AdminScopeDep
from src.notifications.dependencies import StatusNotifierDep, TrackingNotifierDep
from src.notifications.status import RequestKind, StatusEmail
from src.notifications.tracking import TrackingEmail

_HOUSE_TYPES = {"casa": "Casa", "departamento": "Departamento", "finca": "Finca"}
_STATUS_LABELS = {"pendiente": "Pendiente de revisión", "en_entrevista": "En entrevista"}

router = APIRouter(prefix="/adoptions", tags=["Solicitudes de adopción"])

_CODE_RESENT = "Te reenviamos el código de seguimiento a tu correo."
_CODE_NOT_RESENT = (
    "No fue posible reenviarte el código por correo: consúltalo en Mi Panel o contáctanos."
)


def _with_email_status(request: AdoptionRequest, email_sent: bool) -> AdoptionRequestOut:
    """DTO de la solicitud con el resultado del envío del correo."""
    data = AdoptionRequestOut.model_validate(request)
    return data.model_copy(update={"email_sent": email_sent})


def _tracking_email(request: AdoptionRequest) -> TrackingEmail:
    """Correo con el código de seguimiento y el resumen de la solicitud."""
    return TrackingEmail(
        to=request.user_email,
        recipient_name=request.user_name,
        tracking_code=request.tracking_code,
        details=(
            ("Mascota", request.pet_name),
            ("Solicitante", request.user_name),
            ("Teléfono de contacto", request.user_phone),
            ("Tipo de vivienda", _HOUSE_TYPES.get(request.house_type, request.house_type)),
            ("Otras mascotas en casa", "Sí" if request.has_other_pets else "No"),
            ("Estado", _STATUS_LABELS.get(request.status, request.status)),
        ),
    )


@router.get("", response_model=ResponsePayload[list[AdoptionRequestOut]])
async def list_adoption_requests(
    service: AdoptionRequestServiceDep,
    filters: Annotated[RequestFilters, Query()],
    scope: AdminScopeDep,
):
    # Cada administrador solo ve las solicitudes de los refugios que gestiona.
    filters = filters.model_copy(update={"shelter_id": scope.restrict(filters.shelter_id)})
    requests = await service.list_requests(filters)
    return success(requests, "Solicitudes de adopción recuperadas exitosamente")


@router.post("", response_model=ResponsePayload[AdoptionRequestOut], status_code=201)
async def create_adoption_request(
    payload: AdoptionRequestCreate,
    service: AdoptionRequestServiceDep,
    notifier: TrackingNotifierDep,
):
    try:
        request = await service.create_request(payload)
    except DuplicateAdoptionRequestError as error:
        # El código no se revela en la respuesta (cualquiera podría probar correos ajenos):
        # se reenvía al correo del dueño de la solicitud y se mantiene el 409.
        resent = await notifier.adoption_received(_tracking_email(error.existing))
        hint = _CODE_RESENT if resent else _CODE_NOT_RESENT
        raise ConflictError(f"{error.message} {hint}", error.detail_error) from error
    # Se espera al envío para informar en la respuesta si el correo salió o no.
    email_sent = await notifier.adoption_received(_tracking_email(request))
    message = (
        "Solicitud de adopción recibida. Te enviamos el código de seguimiento a tu correo."
        if email_sent
        else "Solicitud de adopción recibida, pero no fue posible enviarte el correo. "
        "Copia y guarda tu código de seguimiento."
    )
    return success(_with_email_status(request, email_sent), message, 201)


@router.post("/track", response_model=ResponsePayload[AdoptionTrackingOut])
async def track_adoption_request(lookup: TrackingLookup, service: AdoptionRequestServiceDep):
    """Seguimiento público con código y correo; el correo viaja en el cuerpo, no en la URL."""
    request = await service.track(lookup)
    return success(request, "Estado de la solicitud obtenido exitosamente")


@router.patch(
    "/{request_id}/status",
    response_model=ResponsePayload[AdoptionRequestOut],
)
async def update_adoption_status(
    request_id: str,
    payload: StatusUpdate,
    service: AdoptionRequestServiceDep,
    notifier: StatusNotifierDep,
    scope: AdminScopeDep,
):
    request = await service.update_status(request_id, payload, scope)
    # El solicitante recibe por correo el nuevo estado junto con la nota del administrador.
    email_sent = await notifier.status_changed(
        StatusEmail(
            kind=RequestKind.ADOPTION,
            status=request.status,
            to=request.user_email,
            recipient_name=request.user_name,
            tracking_code=request.tracking_code,
            admin_note=payload.admin_notes,
            details=(("Mascota", request.pet_name),),
        )
    )
    message = STATUS_NOTIFIED if email_sent else STATUS_NOT_NOTIFIED
    return success(_with_email_status(request, email_sent), message)
