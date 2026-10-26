from typing import Annotated

from fastapi import Depends

from src.api.deps import DbSession
from src.modules.testimonials.repository import TestimonialRepository
from src.modules.testimonials.service import TestimonialService


def get_testimonial_service(db: DbSession) -> TestimonialService:
    return TestimonialService(TestimonialRepository(db))


TestimonialServiceDep = Annotated[TestimonialService, Depends(get_testimonial_service)]
