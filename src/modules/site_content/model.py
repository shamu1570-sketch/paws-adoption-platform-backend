from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base
from src.modules.site_content.catalog import KEY_MAX_LENGTH


class SiteContent(Base):
    """Un texto editable del sitio público, identificado por su sección y su clave."""

    __tablename__ = "site_content"
    __table_args__ = (UniqueConstraint("section", "key", name="uq_site_content_section_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    section: Mapped[str] = mapped_column(String(50), index=True)
    key: Mapped[str] = mapped_column(String(KEY_MAX_LENGTH))
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Último administrador que lo modificó; el texto se conserva si se elimina su cuenta.
    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
