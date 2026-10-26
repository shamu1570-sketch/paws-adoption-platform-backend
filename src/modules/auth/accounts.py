from src.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from src.modules.auth.access import access_state, as_utc
from src.modules.auth.interfaces import AdminRepositoryPort, ShelterLookup
from src.modules.auth.model import Admin
from src.modules.auth.schemas import AdminAccessUpdate, AdminFilters, AdminRole


class AdminAccountService:
    """Gestión de cuentas de administrador desde el panel del super administrador."""

    def __init__(self, admins: AdminRepositoryPort, shelters: ShelterLookup) -> None:
        self._admins = admins
        self._shelters = shelters

    async def list_admins(self, filters: AdminFilters) -> list[Admin]:
        admins = await self._admins.find_all(filters)
        if filters.status is None:
            return admins
        return [
            admin
            for admin in admins
            if access_state(admin.is_active, admin.access_starts_at, admin.access_expires_at)
            == filters.status
        ]

    async def update_access(
        self, requester: Admin, admin_id: str, payload: AdminAccessUpdate
    ) -> Admin:
        """Aplica solo los cambios enviados: estado, ventana de acceso y alcance."""
        if admin_id == requester.id:
            # Evita que el super administrador se bloquee a sí mismo por error.
            raise ForbiddenError(
                "No puedes modificar el acceso de tu propia cuenta",
                "Admins cannot change their own access settings.",
            )
        admin = await self._admins.get(admin_id)
        if admin is None:
            raise NotFoundError(
                "No se encontró el administrador indicado",
                f"Admin with ID {admin_id} was not found in table 'admins'.",
            )
        changes = payload.model_dump(exclude_unset=True)
        await self._apply_scope(admin, changes)
        for field in ("is_active", "access_starts_at", "access_expires_at"):
            if field in changes:
                setattr(admin, field, changes[field])
        self._ensure_valid_window(admin)
        return await self._admins.save(admin)

    async def _apply_scope(self, admin: Admin, changes: dict) -> None:
        wants_global = changes.get("is_global") is True
        shelter_id = changes.get("shelter_id")
        if not wants_global and shelter_id is None:
            if changes.get("is_global") is False:
                raise BadRequestError(
                    "Selecciona el refugio que gestionará este administrador",
                    "is_global=false requires a shelterId.",
                )
            return
        if admin.role == AdminRole.SUPER_ADMIN:
            raise BadRequestError(
                "El alcance de un super administrador no se puede cambiar: siempre es general",
                "super_admin accounts are always global.",
            )
        if wants_global:
            admin.is_global, admin.shelter_id = True, None
            return
        if await self._shelters.get(shelter_id) is None:
            raise BadRequestError(
                "El refugio seleccionado no existe",
                f"Shelter with ID {shelter_id} was not found in table 'shelters'.",
            )
        admin.is_global, admin.shelter_id = False, shelter_id

    @staticmethod
    def _ensure_valid_window(admin: Admin) -> None:
        starts, expires = admin.access_starts_at, admin.access_expires_at
        if starts is not None and expires is not None and as_utc(expires) <= as_utc(starts):
            raise BadRequestError(
                "La fecha de vencimiento debe ser posterior a la fecha de inicio del acceso",
                "access_expires_at must be after access_starts_at.",
            )
