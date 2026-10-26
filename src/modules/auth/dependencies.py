from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.deps import DbSession
from src.core.config import settings
from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.modules.auth.access import GLOBAL_SCOPE, AdminScope
from src.modules.auth.accounts import AdminAccountService
from src.modules.auth.model import Admin
from src.modules.auth.repository import AdminRepository, InvitationRepository
from src.modules.auth.schemas import AdminRole
from src.modules.auth.service import AuthService
from src.modules.shelters.repository import ShelterRepository

_bearer = HTTPBearer(auto_error=False, description="Token JWT obtenido en POST /auth/login")

BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(
        admins=AdminRepository(db),
        invitations=InvitationRepository(db),
        bootstrap_key=settings.ADMIN_REGISTRATION_KEY,
        invitation_ttl_hours=settings.ADMIN_INVITATION_EXPIRE_HOURS,
        shelters=ShelterRepository(db),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_admin_account_service(db: DbSession) -> AdminAccountService:
    return AdminAccountService(admins=AdminRepository(db), shelters=ShelterRepository(db))


AdminAccountServiceDep = Annotated[AdminAccountService, Depends(get_admin_account_service)]


async def get_current_admin(credentials: BearerCredentials, service: AuthServiceDep) -> Admin:
    if credentials is None:
        raise UnauthorizedError(
            "Debes iniciar sesión para realizar esta acción", "Missing bearer token."
        )
    return await service.authenticate(credentials.credentials)


CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]


async def get_optional_admin(
    credentials: BearerCredentials, service: AuthServiceDep
) -> Admin | None:
    """Administrador de la sesión si se envió un token; None para peticiones anónimas."""
    if credentials is None:
        return None
    return await service.authenticate(credentials.credentials)


OptionalAdmin = Annotated[Admin | None, Depends(get_optional_admin)]


def scope_of(admin: Admin) -> AdminScope:
    """Refugios que gestiona el administrador: todos, o solo el que tiene asignado."""
    if admin.role == AdminRole.SUPER_ADMIN or admin.is_global:
        return GLOBAL_SCOPE
    if admin.shelter_id is None:
        # Su refugio fue eliminado: la cuenta no se vuelve general, se queda sin alcance.
        raise ForbiddenError(
            "Tu cuenta no tiene un refugio asignado. Contacta a un super administrador.",
            f"Admin {admin.id} is shelter-scoped but has no shelter.",
        )
    return AdminScope(shelter_id=admin.shelter_id)


async def get_admin_scope(admin: CurrentAdmin) -> AdminScope:
    return scope_of(admin)


AdminScopeDep = Annotated[AdminScope, Depends(get_admin_scope)]


async def get_optional_scope(admin: OptionalAdmin) -> AdminScope | None:
    return scope_of(admin) if admin is not None else None


OptionalScope = Annotated[AdminScope | None, Depends(get_optional_scope)]


def require_roles(*roles: AdminRole) -> Callable[[Admin], Coroutine[Any, Any, Admin]]:
    """Dependencia que exige que el administrador autenticado tenga uno de los roles dados."""

    async def checker(admin: CurrentAdmin) -> Admin:
        if admin.role not in roles:
            raise ForbiddenError(
                "No tienes permisos para realizar esta acción",
                f"Role '{admin.role}' is not allowed. Required: {', '.join(roles)}.",
            )
        return admin

    return checker


async def _global_scope(scope: AdminScopeDep) -> AdminScope:
    scope.ensure_global()
    return scope


# Cualquier administrador autenticado.
require_admin = Depends(get_current_admin)
# Administradores generales y super administradores (catálogos, contenidos, alta de refugios).
require_global_admin = Depends(_global_scope)
# Solo super administradores.
require_super_admin = Depends(require_roles(AdminRole.SUPER_ADMIN))
