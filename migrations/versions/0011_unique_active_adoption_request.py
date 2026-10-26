"""Una sola solicitud de adopción activa por mascota y correo.

Normaliza los correos existentes a minúsculas y crea un índice único parcial sobre
(pet_id, user_email) para las solicitudes pendientes o en entrevista.

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "adoption_requests"
INDEX = "uq_adoption_requests_active_pet_email"
ACTIVE_FILTER = sa.text("status IN ('pendiente', 'en_entrevista')")


def upgrade() -> None:
    op.execute(f"UPDATE {TABLE} SET user_email = lower(user_email)")
    op.create_index(
        INDEX,
        TABLE,
        ["pet_id", "user_email"],
        unique=True,
        postgresql_where=ACTIVE_FILTER,
        sqlite_where=ACTIVE_FILTER,
    )


def downgrade() -> None:
    op.drop_index(INDEX, table_name=TABLE)
