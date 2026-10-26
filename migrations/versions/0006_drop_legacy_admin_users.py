"""Elimina la tabla heredada `admin_users` (y con ella su relación con `shelters`).

Venía del schema.sql original: no guardaba contraseñas y la API nunca la usó. Los
administradores viven en `admins`, que no está ligada a ningún refugio.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "admin_users"


def upgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {TABLE}")


def downgrade() -> None:
    """Recrea la estructura original; los datos eliminados no se recuperan."""
    op.create_table(
        TABLE,
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("shelter_id", sa.String(length=36), nullable=True),
        sa.CheckConstraint("role IN ('superadmin', 'shelter_manager')"),
        sa.ForeignKeyConstraint(["shelter_id"], ["shelters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("email"),
    )
