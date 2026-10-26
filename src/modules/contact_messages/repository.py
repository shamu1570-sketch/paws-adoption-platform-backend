from sqlalchemy import func, select

from src.database.repository import BaseRepository
from src.modules.contact_messages.model import ContactMessage, ContactReply
from src.modules.contact_messages.schemas import ContactMessageFilters


class ContactMessageRepository(BaseRepository[ContactMessage]):
    model = ContactMessage

    async def find_page(self, filters: ContactMessageFilters) -> list[ContactMessage]:
        query = select(ContactMessage).order_by(ContactMessage.created_at.desc(), ContactMessage.id)
        if filters.is_read is not None:
            query = query.where(ContactMessage.is_read.is_(filters.is_read))
        if filters.shelter_id:
            query = query.where(ContactMessage.shelter_id == filters.shelter_id)
        query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        return await self._fetch_all(query)

    async def count(self, shelter_id: str | None, is_read: bool | None = None) -> int:
        query = select(func.count()).select_from(ContactMessage)
        if is_read is not None:
            query = query.where(ContactMessage.is_read.is_(is_read))
        if shelter_id:
            query = query.where(ContactMessage.shelter_id == shelter_id)
        return (await self.db.scalar(query)) or 0

    async def add_reply(self, message: ContactMessage, reply: ContactReply) -> ContactMessage:
        self.db.add(reply)
        await self.db.commit()
        # Recarga el mensaje para que el hilo incluya la respuesta recién guardada.
        await self.db.refresh(message, attribute_names=["replies"])
        return message
