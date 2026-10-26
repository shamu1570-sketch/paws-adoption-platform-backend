from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base

BREED_NAME_LENGTH = 60


class Breed(Base):
    """Raza del catálogo; las fichas de mascotas guardan su nombre en `pets.breed`."""

    __tablename__ = "breeds"
    __table_args__ = (UniqueConstraint("species", "name", name="uq_breeds_species_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(BREED_NAME_LENGTH))
    # Misma especie que `pets.type`: "perro" o "gato".
    species: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
