from src.modules.testimonials.interfaces import TestimonialRepositoryPort
from src.modules.testimonials.model import Testimonial


class TestimonialService:
    def __init__(self, testimonials: TestimonialRepositoryPort) -> None:
        self._testimonials = testimonials

    async def list_testimonials(self) -> list[Testimonial]:
        return await self._testimonials.find_all()
