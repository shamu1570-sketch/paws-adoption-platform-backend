from typing import Annotated

from fastapi import Depends

from src.api.deps import DbSession
from src.core.config import settings
from src.modules.contact_messages.repository import ContactMessageRepository
from src.modules.contact_messages.service import ContactMessageService
from src.modules.pets.repository import PetRepository
from src.modules.shelters.repository import ShelterRepository
from src.notifications.contact import ContactReplyNotifier
from src.notifications.dependencies import get_email_sender
from src.notifications.interfaces import EmailSender


def get_contact_message_service(
    db: DbSession, sender: Annotated[EmailSender, Depends(get_email_sender)]
) -> ContactMessageService:
    return ContactMessageService(
        messages=ContactMessageRepository(db),
        mailer=ContactReplyNotifier(sender, settings.APP_NAME),
        pets=PetRepository(db),
        shelters=ShelterRepository(db),
    )


ContactMessageServiceDep = Annotated[ContactMessageService, Depends(get_contact_message_service)]
