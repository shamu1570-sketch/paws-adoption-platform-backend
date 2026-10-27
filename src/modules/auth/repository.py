from datetime import datetime

from sqlalchemy import or_, select, update

from src.database.repository import BaseRepository
from src.modules.auth.interfaces import InvitationGrant
from src.modules.auth.model import Admin, AdminInvitation
from src.modules.auth.schemas import AdminFilters

 
class AdminRepository(BaseRepository[Admin]):
    model = Admin

    async def find_by_email(self, email: str) -> Admin | None:
        # Los correos se guardan en minúsculas, así la búsqueda usa el índice único.
        query = select(Admin).where(Admin.email == email.lower())
        return await self.db.scalar(query)

    async def find_all(self, filters: AdminFilters) -> list[Admin]:
        """Filtra por texto, rol y refugio; el estado de acceso se calcula en el servicio."""
        query = select(Admin).order_by(Admin.created_at.desc(), Admin.id)
        if filters.search and filters.search.strip():
            pattern = f"%{filters.search.strip()}%"
            query = query.where(or_(Admin.full_name.ilike(pattern), Admin.email.ilike(pattern)))
        if filters.role:
            query = query.where(Admin.role == filters.role)
        if filters.shelter_id:
            query = query.where(Admin.shelter_id == filters.shelter_id)
        return await self._fetch_all(query)

    async def exists_with_role(self, role: str) -> bool:
        query = select(Admin.id).where(Admin.role == role).limit(1)
        return await self.db.scalar(query) is not None


class InvitationRepository(BaseRepository[AdminInvitation]):
    model = AdminInvitation

    async def consume(self, token_hash: str, email: str, now: datetime) -> InvitationGrant | None:
        # Un único UPDATE condicionado: dos registros simultáneos no pueden usar la misma llave.
        statement = (
            update(AdminInvitation)
            .where(
                AdminInvitation.token_hash == token_hash,
                AdminInvitation.email == email,
                AdminInvitation.used_at.is_(None),
                AdminInvitation.expires_at > now,
            )
            .values(used_at=now)
            .returning(AdminInvitation.role, AdminInvitation.is_global, AdminInvitation.shelter_id)
        )
        row = (await self.db.execute(statement)).first()
        if row is None:
            return None
        return InvitationGrant(role=row.role, is_global=row.is_global, shelter_id=row.shelter_id)
