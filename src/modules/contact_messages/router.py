from typing import Annotated

from fastapi import APIRouter, Query

from src.core.responses import ResponsePayload, success
from src.modules.auth.dependencies import AdminScopeDep, CurrentAdmin, require_admin
from src.modules.contact_messages.dependencies import ContactMessageServiceDep
from src.modules.contact_messages.schemas import (
    ContactInboxOut,
    ContactMessageCreate,
    ContactMessageFilters,
    ContactMessageOut,
    ContactReceiptOut,
    ContactReplyCreate,
)

# Formulario público de "Contáctanos".
public_router = APIRouter(prefix="/contact", tags=["Contacto"])
# Bandeja de entrada: cada administrador ve los mensajes de los refugios que gestiona;
# los generales y el super administrador ven todos.
admin_router = APIRouter(
    prefix="/admin/messages", tags=["Mensajes de contacto"], dependencies=[require_admin]
)

MESSAGE_PATH = "/{message_id}"


@public_router.post("", response_model=ResponsePayload[ContactReceiptOut], status_code=201)
async def send_contact_message(payload: ContactMessageCreate, service: ContactMessageServiceDep):
    message = await service.receive(payload)
    return success(
        message, "Recibimos tu mensaje. Te responderemos a tu correo a la brevedad.", 201
    )


@admin_router.get("", response_model=ResponsePayload[ContactInboxOut])
async def list_contact_messages(
    service: ContactMessageServiceDep,
    filters: Annotated[ContactMessageFilters, Query()],
    scope: AdminScopeDep,
):
    inbox = await service.list_inbox(filters, scope)
    return success(inbox, "Mensajes de contacto obtenidos exitosamente")


@admin_router.get(MESSAGE_PATH, response_model=ResponsePayload[ContactMessageOut])
async def open_contact_message(
    message_id: str, service: ContactMessageServiceDep, scope: AdminScopeDep
):
    """Devuelve el detalle del mensaje y lo marca como leído."""
    message = await service.open_message(message_id, scope)
    return success(message, "Mensaje de contacto obtenido exitosamente")


@admin_router.post(
    f"{MESSAGE_PATH}/reply", response_model=ResponsePayload[ContactMessageOut], status_code=201
)
async def reply_contact_message(
    message_id: str,
    payload: ContactReplyCreate,
    service: ContactMessageServiceDep,
    admin: CurrentAdmin,
    scope: AdminScopeDep,
):
    """Envía la respuesta por correo al remitente, firmada por el refugio destinatario;
    si el correo no sale, responde 503."""
    message = await service.reply(message_id, payload, admin, scope)
    return success(message, f"Respuesta enviada por correo a {message.email}.", 201)
