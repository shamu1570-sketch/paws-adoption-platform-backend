from src.core.exceptions import NotFoundError
from src.core.ids import generate_id, generate_tracking_code
from src.core.schemas import RequestFilters, RequestStatus, StatusUpdate, TrackingLookup
from src.core.workflow import ensure_transition_allowed
from src.modules.auth.access import GLOBAL_SCOPE, AdminScope
from src.modules.pets.life_stage import age_label
from src.modules.surrender_requests.interfaces import (
    ShelterLookup,
    SurrenderRequestRepositoryPort,
)
from src.modules.surrender_requests.model import SurrenderRequest
from src.modules.surrender_requests.schemas import SurrenderRequestCreate

TRACKING_PREFIX = "ENTR"


class SurrenderRequestService:
    def __init__(self, requests: SurrenderRequestRepositoryPort, shelters: ShelterLookup) -> None:
        self._requests = requests
        self._shelters = shelters

    async def list_requests(self, filters: RequestFilters) -> list[SurrenderRequest]:
        return await self._requests.find_all(filters)

    async def track(self, lookup: TrackingLookup) -> SurrenderRequest:
        """Solicitud del código dado, solo si también coincide el correo del solicitante."""
        request = await self._requests.find_by_tracking_code(lookup.tracking_code)
        if request is None or request.user_email.lower() != lookup.email.lower():
            raise NotFoundError(
                "No encontramos una solicitud con ese código y correo. Revisa ambos datos.",
                "No request matches the given tracking code and email.",
            )
        return request

    async def create_request(self, payload: SurrenderRequestCreate) -> SurrenderRequest:
        shelter = await self._shelters.get(payload.shelter_id)
        if shelter is None:
            raise NotFoundError(
                "No se encontró el refugio con el ID especificado",
                f"Shelter with ID {payload.shelter_id} was not found in table 'shelters'.",
            )
        request = SurrenderRequest(
            id=generate_id("surr"),
            tracking_code=generate_tracking_code(TRACKING_PREFIX),
            status=RequestStatus.PENDING,
            shelter_name=shelter.name,
            pet_age=age_label(payload.pet_age_value, payload.pet_age_unit),
            **payload.model_dump(),
        )
        return await self._requests.save(request)

    async def update_status(
        self, request_id: str, payload: StatusUpdate, scope: AdminScope = GLOBAL_SCOPE
    ) -> SurrenderRequest:
        request = await self._requests.get(request_id)
        if request is None:
            raise NotFoundError(
                "Solicitud de entrega no encontrada",
                f"Surrender request with ID {request_id} was not found "
                "in table 'surrender_requests'.",
            )
        scope.ensure_access(request.shelter_id)
        ensure_transition_allowed(request.status, payload.status)
        request.status = payload.status
        request.admin_notes = payload.admin_notes
        return await self._requests.save(request)
