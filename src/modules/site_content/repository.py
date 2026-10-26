from uuid import uuid4

from sqlalchemy import select

from src.database.repository import BaseRepository
from src.modules.site_content.model import SiteContent


class SiteContentRepository(BaseRepository[SiteContent]):
    model = SiteContent

    async def find_section(self, section: str) -> list[SiteContent]:
        query = select(SiteContent).where(SiteContent.section == section).order_by(SiteContent.key)
        return await self._fetch_all(query)

    async def save_section(self, section: str, values: dict[str, str], admin_id: str) -> None:
        """Inserta o actualiza los textos indicados en una sola transacción."""
        current = {row.key: row for row in await self.find_section(section)}
        for key, value in values.items():
            row = current.get(key)
            if row is None:
                self.db.add(
                    SiteContent(
                        id=str(uuid4()), section=section, key=key, value=value, updated_by=admin_id
                    )
                )
            elif row.value != value:
                row.value = value
                row.updated_by = admin_id
        await self.db.commit()
