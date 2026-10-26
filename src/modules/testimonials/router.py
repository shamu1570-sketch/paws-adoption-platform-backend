from fastapi import APIRouter

from src.core.responses import ResponsePayload, success
from src.modules.testimonials.dependencies import TestimonialServiceDep
from src.modules.testimonials.schemas import TestimonialOut

router = APIRouter(prefix="/testimonials", tags=["Testimonios"])


@router.get("", response_model=ResponsePayload[list[TestimonialOut]])
async def list_testimonials(service: TestimonialServiceDep):
    testimonials = await service.list_testimonials()
    return success(testimonials, "Testimonios obtenidos exitosamente")
