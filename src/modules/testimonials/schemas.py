from src.core.schemas import CamelModel


class TestimonialOut(CamelModel):
    id: str
    pet_name: str
    pet_type: str
    owner_name: str
    story: str
    image: str
    date: str
