"""Pone al día el nombre y la foto de la mascota guardados en las solicitudes de adopción.

Hasta ahora se copiaban al recibir la solicitud y no cambiaban si luego se editaba la ficha.
Desde esta versión la API los sincroniza en cada edición; esta migración corrige los
registros anteriores. Solo cambia datos, no el esquema.

Revision ID: 0014
Revises: 0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | Sequence[str] | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    pets = bind.execute(sa.text("SELECT id, name, image FROM pets")).fetchall()
    for pet_id, name, image in pets:
        bind.execute(
            sa.text(
                "UPDATE adoption_requests SET pet_name = :name, pet_image = :image "
                "WHERE pet_id = :pet_id AND (pet_name <> :name OR pet_image <> :image)"
            ),
            {"name": name, "image": image, "pet_id": pet_id},
        )


def downgrade() -> None:
    """No hay vuelta atrás: los valores anteriores estaban desactualizados."""
