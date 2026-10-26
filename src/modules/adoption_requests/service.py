from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from src.core.exceptions import ConflictError, NotFoundError
from src.core.ids import generate_id, generate_tracking_code
from src.core.schemas import RequestFilters, RequestStatus, StatusUpdate, TrackingLookup
from src.core.workflow import ensure_transition_allowed
from src.modules.adoption_requests.interfaces import AdoptionRequestRepositoryPort, PetLookup
from src.modules.adoption_requests.model import AdoptionRequest
from src.modules.adoption_requests.schemas import AdoptionRequestCreate
from src.modules.auth.access import GLOBAL_SCOPE, AdminScope
from src.modules.pets.model import Pet
from src.modules.pets.schemas import AdoptionStatus

TRACKING_PREFIX = "ADOP"


class DuplicateAdoptionRequestError(ConflictError):
    """El solicitante ya tiene una solicitud activa para esa mascota (HTTP 409)."""

    def __init__(self, existing: AdoptionRequest) -> None:
        super().__init__(
            f"Ya tienes una solicitud de adopción activa para {existing.pet_name}.",
            "An active adoption request already exists for this pet and email.",
        )
        self.existing = existing


class AdoptionRequestService:
    def __init__(self, requests: AdoptionRequestRepositoryPort, pets: PetLookup) -> None:
        self._requests = requests
        self._pets = pets

    async def list_requests(self, filters: RequestFilters) -> list[AdoptionRequest]:
        return await self._requests.find_all(filters)

    async def track(self, lookup: TrackingLookup) -> AdoptionRequest:
        """Solicitud del código dado, solo si también coincide el correo del solicitante."""
        request = await self._requests.find_by_tracking_code(lookup.tracking_code)
        # Mismo mensaje si el código no existe o el correo no coincide: no revela cuál falló.
        if request is None or request.user_email.lower() != lookup.email.lower():
            raise NotFoundError(
                "No encontramos una solicitud con ese código y correo. Revisa ambos datos.",
                "No request matches the given tracking code and email.",
            )
        return request

    async def create_request(self, payload: AdoptionRequestCreate) -> AdoptionRequest:
        # La mascota es la fuente de verdad de su nombre, imagen y refugio.
        pet = await self._pets.get(payload.pet_id)
        if pet is None or not pet.is_visible:
            raise NotFoundError(
                "No se encontró la mascota con el ID especificado",
                f"Pet with ID {payload.pet_id} was not found in table 'pets'.",
            )
        if pet.adoption_status == AdoptionStatus.ADOPTED:
            raise ConflictError(
                f"{pet.name} ya fue adoptada y no admite nuevas solicitudes",
                f"Pet {pet.id} has adoption status '{pet.adoption_status}'.",
            )
        # El correo se guarda en minúsculas para que la comparación no dependa de mayúsculas.
        user_email = payload.user_email.lower()
        existing = await self._requests.find_active(pet.id, user_email)
        if existing is not None:
            raise DuplicateAdoptionRequestError(existing)
        request = AdoptionRequest(
            id=generate_id("req"),
            tracking_code=generate_tracking_code(TRACKING_PREFIX),
            status=RequestStatus.PENDING,
            pet_name=pet.name,
            pet_image=pet.image,
            shelter_id=pet.shelter_id,
            user_email=user_email,
            **payload.model_dump(exclude={"user_email"}),
        )
        try:
            return await self._requests.save(request)
        except IntegrityError as error:
            # Dos envíos simultáneos: el índice único de la base rechazó el segundo.
            await self._requests.discard_changes()
            existing = await self._requests.find_active(payload.pet_id, user_email)
            if existing is None:
                raise
            raise DuplicateAdoptionRequestError(existing) from error

    async def update_status(
        self, request_id: str, payload: StatusUpdate, scope: AdminScope = GLOBAL_SCOPE
    ) -> AdoptionRequest:
        """Cambia el estado de la solicitud y, en el mismo commit, el de la mascota."""
        request = await self._requests.get(request_id)
        if request is None:
            raise NotFoundError(
                "Solicitud de adopción no encontrada",
                f"Adoption request with ID {request_id} was not found "
                "in table 'adoption_requests'.",
            )
        scope.ensure_access(request.shelter_id)
        ensure_transition_allowed(request.status, payload.status)
        pet = await self._pets.get(request.pet_id)
        if pet is not None:
            await self._apply_to_pet(pet, request, payload.status)
        request.status = payload.status
        request.admin_notes = payload.admin_notes
        # Fecha de la decisión: alimenta la gráfica de adopciones concretadas.
        request.status_changed_at = datetime.now(UTC)
        return await self._requests.save(request)

    async def _apply_to_pet(self, pet: Pet, request: AdoptionRequest, new_status: str) -> None:
        """Refleja el avance de la solicitud en el estado de adopción de la mascota."""
        if new_status == RequestStatus.REJECTED:
            others_in_interview = await self._requests.count_in_interview(pet.id, request.id)
            if pet.adoption_status == AdoptionStatus.IN_PROCESS and not others_in_interview:
                pet.adoption_status = AdoptionStatus.AVAILABLE
            return
        if pet.adoption_status == AdoptionStatus.ADOPTED:
            raise ConflictError(
                f"{pet.name} ya fue adoptada: no se puede avanzar otra solicitud",
                f"Pet {pet.id} already has an approved adoption request.",
            )
        if new_status == RequestStatus.APPROVED:
            pet.adoption_status = AdoptionStatus.ADOPTED
        else:
            pet.adoption_status = AdoptionStatus.IN_PROCESS
