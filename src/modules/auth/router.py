from typing import Annotated

from fastapi import APIRouter, Header, Query

from src.core.responses import ResponsePayload, success
from src.modules.auth.dependencies import (
    AdminAccountServiceDep,
    AuthServiceDep,
    CurrentAdmin,
    OptionalAdmin,
    require_super_admin,
)
from src.modules.auth.schemas import (
    AdminAccessUpdate,
    AdminFilters,
    AdminOut,
    AdminRegister,
    InvitationCreate,
    InvitationOut,
    LoginRequest,
    TokenOut,
)
from src.notifications.dependencies import InvitationNotifierDep

router = APIRouter(prefix="/auth", tags=["Autenticación"])
# Gestión de cuentas de administrador: solo super administradores.
admin_users_router = APIRouter(
    prefix="/admin/users", tags=["Administradores"], dependencies=[require_super_admin]
)


@router.post("/register-admin", response_model=ResponsePayload[AdminOut], status_code=201)
async def register_admin(
    payload: AdminRegister,
    service: AuthServiceDep,
    requester: OptionalAdmin,
    access_key: Annotated[str | None, Header(alias="X-Admin-Registration-Key")] = None,
):
    admin = await service.register_admin(payload, requester, access_key)
    return success(admin, "Administrador registrado exitosamente", 201)


@router.post(
    "/invitations",
    response_model=ResponsePayload[InvitationOut],
    status_code=201,
    dependencies=[require_super_admin],
)
async def create_invitation(
    payload: InvitationCreate,
    admin: CurrentAdmin,
    service: AuthServiceDep,
    notifier: InvitationNotifierDep,
):
    invitation = await service.create_invitation(admin, payload)
    # Se espera al envío para poder confirmar en pantalla si el invitado recibió la llave.
    email_sent = await notifier.send_invitation(invitation, invited_by=admin.full_name)
    message = (
        f"La llave de acceso ha sido generada y enviada exitosamente al correo {invitation.email}."
        if email_sent
        else "La llave de acceso fue generada, pero no fue posible enviarla por correo. "
        "Cópiala ahora y entrégala al invitado: solo se muestra una vez."
    )
    return success(invitation.model_copy(update={"email_sent": email_sent}), message, 201)


@router.post("/login", response_model=ResponsePayload[TokenOut])
async def login(payload: LoginRequest, service: AuthServiceDep):
    token = await service.login(payload)
    return success(token, "Inicio de sesión exitoso")


@router.get("/me", response_model=ResponsePayload[AdminOut])
async def get_current_session(admin: CurrentAdmin):
    return success(admin, "Sesión activa")


@admin_users_router.get("", response_model=ResponsePayload[list[AdminOut]])
async def list_admins(service: AdminAccountServiceDep, filters: Annotated[AdminFilters, Query()]):
    admins = await service.list_admins(filters)
    return success(admins, "Administradores obtenidos exitosamente")


@admin_users_router.patch("/{admin_id}", response_model=ResponsePayload[AdminOut])
async def update_admin_access(
    admin_id: str,
    payload: AdminAccessUpdate,
    requester: CurrentAdmin,
    service: AdminAccountServiceDep,
):
    """Activa o desactiva la cuenta, fija su ventana de acceso o cambia su alcance."""
    admin = await service.update_access(requester, admin_id, payload)
    return success(admin, "Acceso del administrador actualizado")
