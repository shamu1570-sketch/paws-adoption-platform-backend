"""Mensajes del formulario de contacto y sus respuestas.

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MESSAGES = "contact_messages"
REPLIES = "contact_message_replies"
CLIENT_ROLES = ["anon", "authenticated"]
ID_LENGTH = 36


def upgrade() -> None:
    op.create_table(
        MESSAGES,
        sa.Column("id", sa.String(length=ID_LENGTH), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("subject", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contact_messages_email"), MESSAGES, ["email"])
    op.create_index(op.f("ix_contact_messages_is_read"), MESSAGES, ["is_read"])
    op.create_index(op.f("ix_contact_messages_created_at"), MESSAGES, ["created_at"])

    op.create_table(
        REPLIES,
        sa.Column("id", sa.String(length=ID_LENGTH), nullable=False),
        sa.Column("message_id", sa.String(length=ID_LENGTH), nullable=False),
        sa.Column("admin_id", sa.String(length=ID_LENGTH), nullable=True),
        sa.Column("admin_name", sa.String(length=150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["message_id"], [f"{MESSAGES}.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contact_message_replies_message_id"), REPLIES, ["message_id"])

    for table in (MESSAGES, REPLIES):
        _deny_client_access(table)


def _deny_client_access(table: str) -> None:
    """Cierra la tabla a la API de datos de Supabase (roles anon y authenticated).

    Solo la API (FastAPI), que se conecta como dueña de las tablas, lee y escribe; el acceso
    por rol de administrador se controla en sus endpoints.
    """
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
    rows = bind.execute(
        sa.text("select rolname from pg_roles where rolname = any(:roles)"),
        {"roles": CLIENT_ROLES},
    )
    roles = ", ".join(row[0] for row in rows)
    if roles:
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM {roles}")
        op.execute(
            f"CREATE POLICY deny_client_access ON public.{table} AS RESTRICTIVE "
            f"FOR ALL TO {roles} USING (false) WITH CHECK (false)"
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_contact_message_replies_message_id"), table_name=REPLIES)
    op.drop_table(REPLIES)
    op.drop_index(op.f("ix_contact_messages_created_at"), table_name=MESSAGES)
    op.drop_index(op.f("ix_contact_messages_is_read"), table_name=MESSAGES)
    op.drop_index(op.f("ix_contact_messages_email"), table_name=MESSAGES)
    op.drop_table(MESSAGES)
