from typing import Protocol

from src.modules.testimonials.model import Testimonial


class TestimonialRepositoryPort(Protocol):
    async def find_all(self) -> list[Testimonial]: ...
