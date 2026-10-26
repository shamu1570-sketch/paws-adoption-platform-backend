import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from src.core.security import (
    InvalidTokenError,
    access_token_ttl_seconds,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.modules.auth.access import ensure_access_allowed
from src.modules.auth.interfaces import (
    AdminRepositoryPort,
    InvitationGrant,
    InvitationRepositoryPort,
    ShelterLookup,
)
from src.modules.auth.model import Admin, AdminInvitation
from src.modules.auth.schemas import (
    AdminOut,
    AdminRegister,
    AdminRole,
    InvitationCreate,
    InvitationOut,
    LoginRequest,
    TokenOut,
)

_INVALID_CREDENTIALS = "Correo o contraseña incorrectos"
_INVALID_SESSION = "La sesión no es válida o ha expirado. Inicia sesión nuevamente."
_GLOBAL_GRANT = InvitationGrant(role=AdminRole.SUPER_ADMIN, is_global=True, shelter_id=None)


def _hash_access_key(access_key: str) -> str:
    return hashlib.sha256(access_key.encode()).hexdigest()


class AuthService:
    def __init__(
        self,
        admins: AdminRepositoryPort,
        invitations: InvitationRepositoryPort,
        bootstrap_key: str | None = None,
        invitation_ttl_hours: int = 72,
        shelters: ShelterLookup | None = None,
    ) -> None:
        self._admins = admins
        self._invitations = invitations
        self._bootstrap_key = bootstrap_key
        self._invitation_ttl = timedelta(hours=invitation_ttl_hours)
        self._shelters = shelters

    async def register_admin(
        self,
        payload: AdminRegister,
        requester: Admin | None = None,
        access_key: str | None = None,
    ) -> Admin:
        """Registra un administrador si quien lo pide está autorizado.

        Autorizan el registro: la sesión de un super_admin, la llave inicial (solo mientras no
        exista ningún super_admin) o una llave de acceso de un solo uso vigente. El rol y el
        alcance (general o un refugio) los define quien autoriza.
        """
        email = payload.email.lower()
        await self._ensure_email_is_free(email)
        grant = await self._resolve_grant(payload, email, requester, access_key)
        admin = Admin(
            id=str(uuid4()),
            email=email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=grant.role,
            is_global=grant.is_global,
            shelter_id=grant.shelter_id,
            is_active=True,
        )
        # El mismo commit confirma el alta y el consumo de la llave: o ambos o ninguno.
        return await self._admins.save(admin)

    async def create_invitation(self, creator: Admin, payload: InvitationCreate) -> InvitationOut:
        """Genera una llave de un solo uso atada al correo y al alcance de la persona invitada."""
        email = payload.email.lower()
        await self._ensure_email_is_free(email)
        grant = await self._grant_for(payload.role, payload.shelter_id)
        shelter_name = await self._shelter_name(grant.shelter_id)
        access_key = secrets.token_urlsafe(24)
        invitation = AdminInvitation(
            id=str(uuid4()),
            token_hash=_hash_access_key(access_key),
            email=email,
            role=grant.role,
            is_global=grant.is_global,
            shelter_id=grant.shelter_id,
            created_by=creator.id,
            expires_at=datetime.now(UTC) + self._invitation_ttl,
        )
        await self._invitations.save(invitation)
        return InvitationOut(
            access_key=access_key,
            email=email,
            role=grant.role,
            is_global=grant.is_global,
            shelter_id=grant.shelter_id,
            shelter_name=shelter_name,
            expires_at=invitation.expires_at,
        )

    async def login(self, payload: LoginRequest) -> TokenOut:
        admin = await self._admins.find_by_email(payload.email)
        # Mismo mensaje para correo inexistente y contraseña errónea: no revela qué correos existen.
        if admin is None or not verify_password(payload.password, admin.password_hash):
            raise UnauthorizedError(_INVALID_CREDENTIALS, "Invalid email or password.")
        # Con la contraseña correcta sí se informa que el acceso está suspendido o expirado.
        ensure_access_allowed(admin.is_active, admin.access_starts_at, admin.access_expires_at)
        return TokenOut(
            access_token=create_access_token(admin.id, admin.role),
            expires_in=access_token_ttl_seconds(),
            admin=AdminOut.model_validate(admin),
        )

    async def authenticate(self, token: str) -> Admin:
        """Devuelve el administrador dueño del token: 401 si no es válido, 403 si está suspendido.

        Se valida en cada petición, así desactivar una cuenta o vencer su acceso surte efecto
        de inmediato aunque su token siga vigente.
        """
        try:
            admin_id = decode_access_token(token)
        except InvalidTokenError as error:
            raise UnauthorizedError(_INVALID_SESSION, str(error)) from error
        admin = await self._admins.get(admin_id)
        if admin is None:
            raise UnauthorizedError(_INVALID_SESSION, "Admin not found.")
        ensure_access_allowed(admin.is_active, admin.access_starts_at, admin.access_expires_at)
        return admin

    async def _ensure_email_is_free(self, email: str) -> None:
        if await self._admins.find_by_email(email) is not None:
            raise ConflictError(
                "Ya existe un administrador registrado con ese correo",
                f"Admin with email {email} already exists in table 'admins'.",
            )

    async def _resolve_grant(
        self,
        payload: AdminRegister,
        email: str,
        requester: Admin | None,
        access_key: str | None,
    ) -> InvitationGrant:
        """Decide el rol y el alcance del registro; lanza 403 si nada lo autoriza."""
        if requester is not None and requester.role == AdminRole.SUPER_ADMIN:
            return await self._grant_for(payload.role, payload.shelter_id)
        if access_key:
            if self._is_bootstrap_key(access_key) and not await self._has_super_admin():
                return _GLOBAL_GRANT
            grant = await self._invitations.consume(
                _hash_access_key(access_key), email, datetime.now(UTC)
            )
            if grant is not None:
                return grant
            raise ForbiddenError(
                "La llave de acceso no es válida para este correo, ya fue utilizada o expiró",
                "Access key not found, issued for another email, already used or expired.",
            )
        raise ForbiddenError(
            "Para registrarte necesitas una llave de acceso entregada por un super administrador",
            "Provide the X-Admin-Registration-Key header or a super_admin bearer token.",
        )

    async def _grant_for(self, role: str, shelter_id: str | None) -> InvitationGrant:
        """Un super_admin siempre es general; un administrador puede limitarse a un refugio."""
        if shelter_id is None:
            return InvitationGrant(role=role, is_global=True, shelter_id=None)
        if role == AdminRole.SUPER_ADMIN:
            raise BadRequestError(
                "Un super administrador no puede limitarse a un refugio",
                "super_admin accounts are always global.",
            )
        await self._shelter_name(shelter_id)
        return InvitationGrant(role=role, is_global=False, shelter_id=shelter_id)

    async def _shelter_name(self, shelter_id: str | None) -> str | None:
        if shelter_id is None:
            return None
        shelter = await self._shelters.get(shelter_id) if self._shelters else None
        if shelter is None:
            raise BadRequestError(
                "El refugio seleccionado no existe",
                f"Shelter with ID {shelter_id} was not found in table 'shelters'.",
            )
        return shelter.name

    def _is_bootstrap_key(self, access_key: str) -> bool:
        return bool(self._bootstrap_key) and hmac.compare_digest(access_key, self._bootstrap_key)

    async def _has_super_admin(self) -> bool:
        return await self._admins.exists_with_role(AdminRole.SUPER_ADMIN)
