from datetime import datetime
from enum import StrEnum
from typing import Annotated, ClassVar

from pydantic import EmailStr, StringConstraints, computed_field

from src.core.schemas import (
    CamelModel,
    Email,
    OptionalStr,
    PartialUpdateModel,
    PersonName,
    RequiredStr,
)
from src.modules.auth.access import AccessState, access_state

# bcrypt solo considera los primeros 72 bytes de la contraseña.
Password = Annotated[str, StringConstraints(min_length=8, max_length=72)]


class AdminRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADOPTION_ADMIN = "adoption_admin"


class AdminRegister(CamelModel):
    """`role` y `shelter_id` solo se respetan cuando registra un super_admin con sesión; con una
    llave de acceso el rol y el alcance los define la llave."""

    email: Email
    full_name: PersonName
    password: Password
    role: AdminRole = AdminRole.ADOPTION_ADMIN
    # Refugio que gestionará; sin refugio es administrador general.
    shelter_id: OptionalStr = None


class InvitationCreate(CamelModel):
    """`email` es el correo de la persona invitada: la llave solo servirá para ese correo.

    `shelter_id` limita la cuenta a un refugio; sin él, el invitado será administrador general.
    """

    email: EmailStr
    role: AdminRole = AdminRole.ADOPTION_ADMIN
    shelter_id: OptionalStr = None


class InvitationOut(CamelModel):
    """La llave en claro solo se devuelve aquí, al generarla."""

    access_key: str
    email: str
    role: str
    is_global: bool
    shelter_id: str | None = None
    shelter_name: str | None = None
    expires_at: datetime
    # Si la llave se envió por correo al invitado. Si no, el super_admin debe entregarla.
    email_sent: bool = False


class LoginRequest(CamelModel):
    email: EmailStr
    password: RequiredStr


class AdminOut(CamelModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_global: bool
    shelter_id: str | None
    shelter_name: str | None
    access_starts_at: datetime | None
    access_expires_at: datetime | None
    created_at: datetime | None

    @computed_field
    @property
    def access_status(self) -> AccessState:
        """Estado efectivo: activo, inactivo, programado (aún no inicia) o expirado."""
        return access_state(self.is_active, self.access_starts_at, self.access_expires_at)


class TokenOut(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: AdminOut


class AdminFilters(CamelModel):
    """Búsqueda y filtros del listado de administradores."""

    search: str | None = None
    role: AdminRole | None = None
    status: AccessState | None = None
    shelter_id: str | None = None


class AdminAccessUpdate(PartialUpdateModel):
    """Cambios de acceso de una cuenta: estado, ventana de tiempo y alcance.

    Las fechas y el refugio aceptan `null` para quitarlos. `is_global=true` convierte la cuenta
    en administrador general; un `shelter_id` la limita a ese refugio.
    """

    nullable_fields: ClassVar[frozenset[str]] = frozenset(
        {"access_starts_at", "access_expires_at", "shelter_id"}
    )

    is_active: bool | None = None
    access_starts_at: datetime | None = None
    access_expires_at: datetime | None = None
    is_global: bool | None = None
    shelter_id: OptionalStr = None
