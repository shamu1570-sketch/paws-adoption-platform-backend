from typing import Annotated

from fastapi import APIRouter, Query

from src.core.responses import ResponsePayload, success
from src.core.schemas import (
    STATUS_NOT_NOTIFIED,
    STATUS_NOTIFIED,
    RequestFilters,
    StatusUpdate,
    TrackingLookup,
)
from src.modules.auth.dependencies import AdminScopeDep
from src.modules.surrender_requests.dependencies import SurrenderRequestServiceDep
from src.modules.surrender_requests.model import SurrenderRequest
from src.modules.surrender_requests.schemas import (
    SurrenderRequestCreate,
    SurrenderRequestOut,
    SurrenderTrackingOut,
)
from src.notifications.dependencies import StatusNotifierDep, TrackingNotifierDep
from src.notifications.status import RequestKind, StatusEmail
from src.notifications.tracking import TrackingEmail

router = APIRouter(prefix="/surrender-requests", tags=["Solicitudes de entrega responsable"])


def _with_email_status(request: SurrenderRequest, email_sent: bool) -> SurrenderRequestOut:
    """DTO de la solicitud con el resultado del envío del correo."""
    data = SurrenderRequestOut.model_validate(request)
    return data.model_copy(update={"email_sent": email_sent})


@router.get("", response_model=ResponsePayload[list[SurrenderRequestOut]])
async def list_surrender_requests(
    service: SurrenderRequestServiceDep,
    filters: Annotated[RequestFilters, Query()],
    scope: AdminScopeDep,
):
    # Cada administrador solo ve las entregas dirigidas a los refugios que gestiona.
    filters = filters.model_copy(update={"shelter_id": scope.restrict(filters.shelter_id)})
    requests = await service.list_requests(filters)
    return success(requests, "Solicitudes de entrega recuperadas con éxito")


@router.post("", response_model=ResponsePayload[SurrenderRequestOut], status_code=201)
async def create_surrender_request(
    payload: SurrenderRequestCreate,
    service: SurrenderRequestServiceDep,
    notifier: TrackingNotifierDep,
):
    request = await service.create_request(payload)
    # Se espera al envío para informar en la respuesta si el correo salió o no.
    email_sent = await notifier.surrender_received(
        TrackingEmail(
            to=request.user_email,
            recipient_name=request.user_name,
            tracking_code=request.tracking_code,
            details=(
                ("Mascota", f"{request.pet_name} ({request.pet_type}, {request.pet_age})"),
                ("Refugio", request.shelter_name),
                ("Solicitante", request.user_name),
                ("Teléfono de contacto", request.user_phone),
                ("Estado", "Pendiente de revisión"),
            ),
        )
    )
    message = (
        "Solicitud de entrega registrada. Te enviamos el código de seguimiento a tu correo."
        if email_sent
        else "Solicitud de entrega registrada, pero no fue posible enviarte el correo. "
        "Copia y guarda tu código de seguimiento."
    )
    return success(_with_email_status(request, email_sent), message, 201)


@router.post("/track", response_model=ResponsePayload[SurrenderTrackingOut])
async def track_surrender_request(lookup: TrackingLookup, service: SurrenderRequestServiceDep):
    """Seguimiento público con código y correo; el correo viaja en el cuerpo, no en la URL."""
    request = await service.track(lookup)
    return success(request, "Estado de la solicitud obtenido exitosamente")


@router.patch(
    "/{request_id}/status",
    response_model=ResponsePayload[SurrenderRequestOut],
)
async def update_surrender_status(
    request_id: str,
    payload: StatusUpdate,
    service: SurrenderRequestServiceDep,
    notifier: StatusNotifierDep,
    scope: AdminScopeDep,
):
    request = await service.update_status(request_id, payload, scope)
    email_sent = await notifier.status_changed(
        StatusEmail(
            kind=RequestKind.SURRENDER,
            status=request.status,
            to=request.user_email,
            recipient_name=request.user_name,
            tracking_code=request.tracking_code,
            admin_note=payload.admin_notes,
            details=(
                ("Mascota", f"{request.pet_name} ({request.pet_type}, {request.pet_age})"),
                ("Refugio", request.shelter_name),
            ),
        )
    )
    message = STATUS_NOTIFIED if email_sent else STATUS_NOT_NOTIFIED
    return success(_with_email_status(request, email_sent), message)
