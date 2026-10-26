"""Esquema inicial: refugios, mascotas, solicitudes y testimonios.

En una base que ya tenga estas tablas (creadas con el schema.sql original) no se ejecuta:
se marca como aplicada con `alembic stamp 0001`.

Revision ID: 0001
Revises:
Create Date: 2026-10-12 14:24:41.778182

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shelters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("current_pet_count", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image", sa.Text(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shelters_city"), "shelters", ["city"], unique=False)
    op.create_table(
        "testimonials",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pet_name", sa.String(length=100), nullable=False),
        sa.Column("pet_type", sa.String(length=20), nullable=False),
        sa.Column("owner_name", sa.String(length=150), nullable=False),
        sa.Column("story", sa.Text(), nullable=False),
        sa.Column("image", sa.Text(), nullable=False),
        sa.Column("date", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "pets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("breed", sa.String(length=100), nullable=False),
        sa.Column("age", sa.String(length=50), nullable=False),
        sa.Column("age_category", sa.String(length=20), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("size", sa.String(length=20), nullable=False),
        sa.Column("personality", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("story", sa.Text(), nullable=False),
        sa.Column("image", sa.Text(), nullable=False),
        sa.Column("vaccinated", sa.Boolean(), nullable=False),
        sa.Column("dewormed", sa.Boolean(), nullable=False),
        sa.Column("sterilized", sa.Boolean(), nullable=False),
        sa.Column("health_status", sa.Text(), nullable=False),
        sa.Column("adoption_status", sa.String(length=20), nullable=False),
        sa.Column("shelter_id", sa.String(length=36), nullable=True),
        sa.Column("shelter_name", sa.String(length=150), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["shelter_id"], ["shelters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pets_adoption_status"), "pets", ["adoption_status"], unique=False)
    op.create_index(op.f("ix_pets_age_category"), "pets", ["age_category"], unique=False)
    op.create_index(op.f("ix_pets_gender"), "pets", ["gender"], unique=False)
    op.create_index(op.f("ix_pets_shelter_id"), "pets", ["shelter_id"], unique=False)
    op.create_index(op.f("ix_pets_size"), "pets", ["size"], unique=False)
    op.create_index(op.f("ix_pets_type"), "pets", ["type"], unique=False)
    op.create_table(
        "surrender_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pet_name", sa.String(length=100), nullable=False),
        sa.Column("pet_type", sa.String(length=20), nullable=False),
        sa.Column("pet_age", sa.String(length=50), nullable=False),
        sa.Column("shelter_id", sa.String(length=36), nullable=False),
        sa.Column("shelter_name", sa.String(length=150), nullable=False),
        sa.Column("user_name", sa.String(length=150), nullable=False),
        sa.Column("user_email", sa.String(length=150), nullable=False),
        sa.Column("user_phone", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("health_condition", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["shelter_id"], ["shelters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_surrender_requests_shelter_id"), "surrender_requests", ["shelter_id"], unique=False
    )
    op.create_index(
        op.f("ix_surrender_requests_status"), "surrender_requests", ["status"], unique=False
    )
    op.create_table(
        "adoption_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pet_id", sa.String(length=36), nullable=False),
        sa.Column("pet_name", sa.String(length=100), nullable=False),
        sa.Column("pet_image", sa.Text(), nullable=False),
        sa.Column("shelter_id", sa.String(length=36), nullable=True),
        sa.Column("user_name", sa.String(length=150), nullable=False),
        sa.Column("user_email", sa.String(length=150), nullable=False),
        sa.Column("user_phone", sa.String(length=30), nullable=False),
        sa.Column("house_type", sa.String(length=20), nullable=False),
        sa.Column("has_other_pets", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["pet_id"], ["pets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shelter_id"], ["shelters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_adoption_requests_pet_id"), "adoption_requests", ["pet_id"], unique=False
    )
    op.create_index(
        op.f("ix_adoption_requests_shelter_id"), "adoption_requests", ["shelter_id"], unique=False
    )
    op.create_index(
        op.f("ix_adoption_requests_status"), "adoption_requests", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_adoption_requests_status"), table_name="adoption_requests")
    op.drop_index(op.f("ix_adoption_requests_shelter_id"), table_name="adoption_requests")
    op.drop_index(op.f("ix_adoption_requests_pet_id"), table_name="adoption_requests")
    op.drop_table("adoption_requests")
    op.drop_index(op.f("ix_surrender_requests_status"), table_name="surrender_requests")
    op.drop_index(op.f("ix_surrender_requests_shelter_id"), table_name="surrender_requests")
    op.drop_table("surrender_requests")
    op.drop_index(op.f("ix_pets_type"), table_name="pets")
    op.drop_index(op.f("ix_pets_size"), table_name="pets")
    op.drop_index(op.f("ix_pets_shelter_id"), table_name="pets")
    op.drop_index(op.f("ix_pets_gender"), table_name="pets")
    op.drop_index(op.f("ix_pets_age_category"), table_name="pets")
    op.drop_index(op.f("ix_pets_adoption_status"), table_name="pets")
    op.drop_table("pets")
    op.drop_table("testimonials")
    op.drop_index(op.f("ix_shelters_city"), table_name="shelters")
    op.drop_table("shelters")
