"""Llaves de acceso de un solo uso para registrar administradores.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "admin_invitations"
CLIENT_ROLES = ["anon", "authenticated"]


def upgrade() -> None:
    op.create_table(
        "admin_invitations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["admins.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_invitations_created_by"), "admin_invitations", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_admin_invitations_token_hash"), "admin_invitations", ["token_hash"], unique=True
    )
    _deny_client_access()


def _deny_client_access() -> None:
    """Cierra la tabla a la API de datos de Supabase (roles anon y authenticated)."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(f"ALTER TABLE public.{TABLE} ENABLE ROW LEVEL SECURITY")
    rows = bind.execute(
        sa.text("select rolname from pg_roles where rolname = any(:roles)"), {"roles": CLIENT_ROLES}
    )
    roles = ", ".join(row[0] for row in rows)
    if roles:
        op.execute(f"REVOKE ALL ON TABLE public.{TABLE} FROM {roles}")
        op.execute(
            f"CREATE POLICY deny_client_access ON public.{TABLE} AS RESTRICTIVE "
            f"FOR ALL TO {roles} USING (false) WITH CHECK (false)"
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_invitations_token_hash"), table_name="admin_invitations")
    op.drop_index(op.f("ix_admin_invitations_created_by"), table_name="admin_invitations")
    op.drop_table("admin_invitations")
