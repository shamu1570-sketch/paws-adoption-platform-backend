from sqlalchemy import select

from src.database.repository import BaseRepository
from src.modules.testimonials.model import Testimonial


class TestimonialRepository(BaseRepository[Testimonial]):
    model = Testimonial

    async def find_all(self) -> list[Testimonial]:
        query = select(Testimonial).order_by(Testimonial.date.desc(), Testimonial.id)
        return await self._fetch_all(query)
