from uuid import uuid4

from src.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from src.modules.auth.access import GLOBAL_SCOPE, AdminScope
from src.modules.auth.model import Admin
from src.modules.contact_messages.interfaces import (
    ContactMessageRepositoryPort,
    PetLookup,
    ReplyMailer,
    ShelterLookup,
)
from src.modules.contact_messages.model import ContactMessage, ContactReply
from src.modules.contact_messages.schemas import (
    ContactInboxOut,
    ContactMessageCreate,
    ContactMessageFilters,
    ContactMessageOut,
    ContactReplyCreate,
    ContactTopic,
)


class ContactMessageService:
    def __init__(
        self,
        messages: ContactMessageRepositoryPort,
        mailer: ReplyMailer,
        pets: PetLookup,
        shelters: ShelterLookup,
    ) -> None:
        self._messages = messages
        self._mailer = mailer
        self._pets = pets
        self._shelters = shelters

    async def receive(self, payload: ContactMessageCreate) -> ContactMessage:
        """Registra un mensaje del formulario público.

        Los de adopción o entrega se dirigen a un refugio: solo lo ven sus administradores y
        los generales. Los generales (sin refugio) solo los ven los administradores generales.
        """
        data = payload.model_dump(exclude={"pet_id", "shelter_id"})
        data["email"] = payload.email.lower()
        target = await self._resolve_target(payload)
        return await self._messages.save(
            ContactMessage(id=str(uuid4()), is_read=False, **data, **target)
        )

    async def list_inbox(
        self, filters: ContactMessageFilters, scope: AdminScope = GLOBAL_SCOPE
    ) -> ContactInboxOut:
        filters = filters.model_copy(update={"shelter_id": scope.restrict(filters.shelter_id)})
        items = await self._messages.find_page(filters)
        return ContactInboxOut(
            items=[ContactMessageOut.model_validate(item) for item in items],
            total=await self._messages.count(filters.shelter_id, filters.is_read),
            unread=await self._messages.count(filters.shelter_id, is_read=False),
            page=filters.page,
            page_size=filters.page_size,
        )

    async def open_message(
        self, message_id: str, scope: AdminScope = GLOBAL_SCOPE
    ) -> ContactMessage:
        """Devuelve el detalle y lo marca como leído."""
        message = await self._get(message_id, scope)
        if not message.is_read:
            message.is_read = True
            message = await self._messages.save(message)
        return message

    async def reply(
        self,
        message_id: str,
        payload: ContactReplyCreate,
        admin: Admin,
        scope: AdminScope = GLOBAL_SCOPE,
    ) -> ContactMessage:
        """Envía la respuesta por correo y, solo si salió, la guarda en el hilo del mensaje."""
        message = await self._get(message_id, scope)
        if not await self._mailer.send_reply(message, payload.body, admin.full_name):
            raise ServiceUnavailableError(
                "No fue posible enviar la respuesta por correo. Intenta de nuevo más tarde.",
                "The email provider did not accept the reply; nothing was stored.",
            )
        reply = ContactReply(
            id=str(uuid4()),
            message_id=message.id,
            admin_id=admin.id,
            admin_name=admin.full_name,
            body=payload.body,
        )
        message.is_read = True
        return await self._messages.add_reply(message, reply)

    async def _resolve_target(self, payload: ContactMessageCreate) -> dict:
        """Refugio (y mascota) al que va dirigido el mensaje según su motivo."""
        if payload.topic == ContactTopic.GENERAL:
            return {"shelter_id": None, "pet_id": None, "pet_name": None}
        if payload.topic == ContactTopic.ADOPTION and payload.pet_id:
            pet = await self._pets.get(payload.pet_id)
            if pet is None or not pet.is_visible:
                raise BadRequestError(
                    "La mascota seleccionada no está disponible",
                    f"Pet with ID {payload.pet_id} was not found or is hidden.",
                )
            return {"shelter_id": pet.shelter_id, "pet_id": pet.id, "pet_name": pet.name}
        if payload.shelter_id is None:
            message = (
                "Selecciona la mascota de tu interés o el refugio al que va dirigido tu mensaje"
                if payload.topic == ContactTopic.ADOPTION
                else "Selecciona el refugio al que va dirigido tu mensaje"
            )
            raise BadRequestError(message, f"Topic '{payload.topic}' requires a target.")
        if await self._shelters.get(payload.shelter_id) is None:
            raise BadRequestError(
                "El refugio seleccionado no existe",
                f"Shelter with ID {payload.shelter_id} was not found in table 'shelters'.",
            )
        return {"shelter_id": payload.shelter_id, "pet_id": None, "pet_name": None}

    async def _get(self, message_id: str, scope: AdminScope) -> ContactMessage:
        message = await self._messages.get(message_id)
        # Un mensaje de otro refugio se trata como inexistente: no revela que existe.
        if message is None or not scope.can_access(message.shelter_id):
            raise NotFoundError(
                "No se encontró el mensaje de contacto",
                f"Contact message with ID {message_id} was not found in table 'contact_messages'.",
            )
        return message
