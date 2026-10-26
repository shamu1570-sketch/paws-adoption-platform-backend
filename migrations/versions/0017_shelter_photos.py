"""Galería de fotografías de los refugios (hasta 4, como las mascotas).

Cada refugio existente arranca con su imagen actual como única foto de la galería.

Revision ID: 0017
Revises: 0016
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | Sequence[str] | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("shelters", sa.Column("photos", sa.Text(), server_default="[]", nullable=False))
    for shelter_id, image in bind.execute(sa.text("select id, image from shelters")).all():
        bind.execute(
            sa.text("UPDATE shelters SET photos = :photos WHERE id = :id"),
            {"photos": json.dumps([image] if image else []), "id": shelter_id},
        )


def downgrade() -> None:
    op.drop_column("shelters", "photos")
