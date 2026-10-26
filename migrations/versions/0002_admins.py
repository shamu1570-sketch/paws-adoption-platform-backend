"""Tabla de administradores del sistema de adopción (login con JWT).

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("role IN ('super_admin', 'adoption_admin')", name="ck_admins_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_email"), "admins", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_admins_email"), table_name="admins")
    op.drop_table("admins")
