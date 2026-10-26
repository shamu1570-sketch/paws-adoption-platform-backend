from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.modules.auth.model import Admin, AdminInvitation
from src.modules.auth.schemas import AdminFilters
from src.modules.shelters.model import Shelter


@dataclass(frozen=True)
class InvitationGrant:
    """Rol y alcance que concede una llave de acceso al consumirse."""

    role: str
    is_global: bool
    shelter_id: str | None


class AdminRepositoryPort(Protocol):
    async def get(self, entity_id: str) -> Admin | None: ...

    async def find_by_email(self, email: str) -> Admin | None: ...

    async def find_all(self, filters: AdminFilters) -> list[Admin]: ...

    async def exists_with_role(self, role: str) -> bool: ...

    async def save(self, entity: Admin) -> Admin: ...


class InvitationRepositoryPort(Protocol):
    async def save(self, entity: AdminInvitation) -> AdminInvitation: ...

    async def consume(self, token_hash: str, email: str, now: datetime) -> InvitationGrant | None:
        """Marca la llave como usada y devuelve lo que concede; None si no sirve.

        Solo sirve si existe, fue emitida para `email`, no se ha usado y no ha expirado.

        No confirma la transacción: se confirma junto con el alta del administrador.
        """
        ...


class ShelterLookup(Protocol):
    """Lo único que el dominio de autenticación necesita saber de los refugios."""

    async def get(self, entity_id: str) -> Shelter | None: ...
