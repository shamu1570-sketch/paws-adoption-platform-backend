"""Registro de modelos y creación directa de tablas para bases efímeras (pruebas).

En bases reales el esquema se versiona con Alembic: `uv run alembic upgrade head`.
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from src.database.connection import Base, engine

# Importar cada modelo lo registra en Base.metadata.
from src.modules.adoption_requests.model import AdoptionRequest
from src.modules.auth.model import Admin, AdminInvitation
from src.modules.breeds.model import Breed
from src.modules.contact_messages.model import ContactMessage, ContactReply
from src.modules.personalities.model import Personality
from src.modules.pets.model import Pet
from src.modules.shelters.model import Shelter
from src.modules.site_content.model import SiteContent
from src.modules.surrender_requests.model import SurrenderRequest
from src.modules.testimonials.model import Testimonial

MODELS = (
    Shelter,
    Admin,
    AdminInvitation,
    Pet,
    AdoptionRequest,
    SurrenderRequest,
    Testimonial,
    ContactMessage,
    ContactReply,
    Personality,
    SiteContent,
    Breed,
)


async def create_tables(target: AsyncEngine = engine) -> None:
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
