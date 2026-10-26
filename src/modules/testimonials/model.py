from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.connection import Base


class Testimonial(Base):
    __tablename__ = "testimonials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pet_name: Mapped[str] = mapped_column(String(100))
    pet_type: Mapped[str] = mapped_column(String(20))
    owner_name: Mapped[str] = mapped_column(String(150))
    story: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(30))
