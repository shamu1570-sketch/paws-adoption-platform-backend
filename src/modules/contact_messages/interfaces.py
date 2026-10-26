from typing import Protocol

from src.modules.contact_messages.model import ContactMessage, ContactReply
from src.modules.contact_messages.schemas import ContactMessageFilters
from src.modules.pets.model import Pet
from src.modules.shelters.model import Shelter


class ContactMessageRepositoryPort(Protocol):
    async def get(self, entity_id: str) -> ContactMessage | None: ...

    async def save(self, entity: ContactMessage) -> ContactMessage: ...

    async def find_page(self, filters: ContactMessageFilters) -> list[ContactMessage]:
        """Mensajes de la página pedida (del refugio de `filters.shelter_id` si se indica),
        del más reciente al más antiguo."""
        ...

    async def count(self, shelter_id: str | None, is_read: bool | None = None) -> int: ...

    async def add_reply(self, message: ContactMessage, reply: ContactReply) -> ContactMessage:
        """Guarda la respuesta y devuelve el mensaje con su hilo actualizado."""
        ...


class ReplyMailer(Protocol):
    """Envío de la respuesta al remitente; devuelve True solo si el correo salió."""

    async def send_reply(self, message: ContactMessage, body: str, admin_name: str) -> bool: ...


class PetLookup(Protocol):
    async def get(self, entity_id: str) -> Pet | None: ...


class ShelterLookup(Protocol):
    async def get(self, entity_id: str) -> Shelter | None: ...
