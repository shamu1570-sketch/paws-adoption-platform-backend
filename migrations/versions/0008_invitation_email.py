"""Ata cada llave de acceso al correo de la persona invitada.

Las llaves emitidas antes de este cambio no tienen correo y dejan de ser válidas: se eliminan.

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "admin_invitations"
EMAIL_INDEX = "ix_admin_invitations_email"


def upgrade() -> None:
    op.execute(f"DELETE FROM {TABLE}")
    with op.batch_alter_table(TABLE) as batch:
        batch.add_column(sa.Column("email", sa.String(length=150), nullable=False))
        batch.create_index(EMAIL_INDEX, ["email"])


def downgrade() -> None:
    with op.batch_alter_table(TABLE) as batch:
        batch.drop_index(EMAIL_INDEX)
        batch.drop_column("email")
