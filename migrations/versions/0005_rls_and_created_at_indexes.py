"""Seguridad a nivel de fila (RLS) en todas las tablas e índices por fecha de creación.

RLS: en Supabase el esquema `public` queda expuesto por su API REST a los roles `anon` y
`authenticated`. Esta API (FastAPI) es el único cliente de la base y se conecta como dueña de
las tablas, que no está sujeta a RLS; por eso a esos dos roles se les niega todo acceso.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROTECTED_TABLES = (
    "alembic_version",
    "admins",
    "shelters",
    "pets",
    "adoption_requests",
    "surrender_requests",
    "testimonials",
)
# Tablas que la API lista ordenadas por fecha de creación.
TABLES_SORTED_BY_CREATED_AT = ("pets", "adoption_requests", "surrender_requests")
CREATED_AT = "created_at"
CLIENT_ROLES = ("anon", "authenticated")
POLICY = "deny_client_access"


def _existing_client_roles() -> list[str]:
    """Roles de la API de datos de Supabase; en un PostgreSQL normal no existen."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return []
    rows = bind.execute(
        sa.text("select rolname from pg_roles where rolname = any(:roles)"),
        {"roles": list(CLIENT_ROLES)},
    )
    return [row[0] for row in rows]


def upgrade() -> None:
    for table in TABLES_SORTED_BY_CREATED_AT:
        op.create_index(op.f(f"ix_{table}_{CREATED_AT}"), table, [CREATED_AT])

    if op.get_bind().dialect.name != "postgresql":
        return
    roles = ", ".join(_existing_client_roles())
    for table in PROTECTED_TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        if roles:
            # Defensa en profundidad: sin privilegios y con una política que lo niega todo.
            op.execute(f"REVOKE ALL ON TABLE public.{table} FROM {roles}")
            op.execute(f"DROP POLICY IF EXISTS {POLICY} ON public.{table}")
            op.execute(
                f"CREATE POLICY {POLICY} ON public.{table} AS RESTRICTIVE "
                f"FOR ALL TO {roles} USING (false) WITH CHECK (false)"
            )


def downgrade() -> None:
    """Quita las políticas y los índices. No reactiva el acceso público a las tablas."""
    if op.get_bind().dialect.name == "postgresql":
        for table in PROTECTED_TABLES:
            op.execute(f"DROP POLICY IF EXISTS {POLICY} ON public.{table}")
    for table in TABLES_SORTED_BY_CREATED_AT:
        op.drop_index(op.f(f"ix_{table}_{CREATED_AT}"), table_name=table)
