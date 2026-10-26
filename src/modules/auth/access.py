"""Reglas de acceso de las cuentas de administrador: estado y alcance por refugio."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from src.core.exceptions import ForbiddenError

ACCESS_SUSPENDED = "Acceso suspendido o expirado"
NO_SHELTER_ACCESS = "No tienes permisos para gestionar los datos de este refugio"
GLOBAL_ONLY = "Esta acción está reservada a los administradores generales"


class AccessState(StrEnum):
    ACTIVE = "activo"
    DISABLED = "inactivo"
    SCHEDULED = "programado"
    EXPIRED = "expirado"


def as_utc(moment: datetime) -> datetime:
    """Algunas bases (SQLite) devuelven fechas sin zona: se interpretan como UTC."""
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def access_state(
    is_active: bool | None,
    starts_at: datetime | None,
    expires_at: datetime | None,
    now: datetime | None = None,
) -> AccessState:
    now = now or datetime.now(UTC)
    if is_active is False:
        return AccessState.DISABLED
    if starts_at is not None and now < as_utc(starts_at):
        return AccessState.SCHEDULED
    if expires_at is not None and now >= as_utc(expires_at):
        return AccessState.EXPIRED
    return AccessState.ACTIVE


def ensure_access_allowed(
    is_active: bool | None, starts_at: datetime | None, expires_at: datetime | None
) -> None:
    """403 si la cuenta está desactivada o fuera de su ventana de acceso."""
    state = access_state(is_active, starts_at, expires_at)
    if state is not AccessState.ACTIVE:
        raise ForbiddenError(ACCESS_SUSPENDED, f"Admin account access state is '{state}'.")


@dataclass(frozen=True)
class AdminScope:
    """Refugios que puede gestionar un administrador; `shelter_id` None significa todos."""

    shelter_id: str | None = None

    @property
    def is_global(self) -> bool:
        return self.shelter_id is None

    def can_access(self, shelter_id: str | None) -> bool:
        """Lo que no tiene refugio asignado solo lo gestionan los administradores generales."""
        return self.is_global or shelter_id == self.shelter_id

    def ensure_access(self, shelter_id: str | None) -> None:
        if not self.can_access(shelter_id):
            raise ForbiddenError(
                NO_SHELTER_ACCESS, f"Admin scope is limited to shelter '{self.shelter_id}'."
            )

    def restrict(self, requested: str | None) -> str | None:
        """Filtro de refugio efectivo en listados: el propio si el alcance es limitado."""
        return requested if self.is_global else self.shelter_id

    def ensure_global(self) -> None:
        if not self.is_global:
            raise ForbiddenError(GLOBAL_ONLY, "Global admin scope required.")


GLOBAL_SCOPE = AdminScope()
