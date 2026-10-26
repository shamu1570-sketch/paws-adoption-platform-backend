"""Catálogo de personalidades, galería de fotos por mascota y nombres de hasta 50 caracteres.

- personalities: catálogo administrable. Se llena con los rasgos que ya usan las mascotas,
  para que las fichas existentes sigan siendo válidas.
- pets.photos: galería (hasta 4 URLs). Cada mascota existente arranca con su foto actual.
- Columnas de nombres de personas y mascotas pasan a VARCHAR(50), igual que la validación.

Revision ID: 0013
Revises: 0012
"""

import json
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | Sequence[str] | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERSONALITIES = "personalities"
CLIENT_ROLES = ["anon", "authenticated"]
NAME_LENGTH = 50
# (tabla, columna, longitud anterior)
NAME_COLUMNS = (
    ("pets", "name", 100),
    ("adoption_requests", "pet_name", 100),
    ("adoption_requests", "user_name", 150),
    ("surrender_requests", "pet_name", 100),
    ("surrender_requests", "user_name", 150),
    ("admins", "full_name", 150),
    ("contact_messages", "name", 100),
    ("contact_message_replies", "admin_name", 150),
)


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        PERSONALITIES,
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_personalities_name"), PERSONALITIES, ["name"], unique=True)
    _deny_client_access(PERSONALITIES)

    pets = bind.execute(sa.text("SELECT id, image, personality FROM pets")).fetchall()
    used = sorted({trait for _, _, raw in pets for trait in json.loads(raw or "[]")})
    for trait in used:
        bind.execute(
            sa.text(f"INSERT INTO {PERSONALITIES} (id, name) VALUES (:id, :name)"),
            {"id": str(uuid.uuid4()), "name": trait},
        )

    op.add_column("pets", sa.Column("photos", sa.Text(), server_default="[]", nullable=False))
    for pet_id, image, _ in pets:
        bind.execute(
            sa.text("UPDATE pets SET photos = :photos WHERE id = :id"),
            {"photos": json.dumps([image]), "id": pet_id},
        )

    for table, column, old_length in NAME_COLUMNS:
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                column,
                existing_type=sa.String(length=old_length),
                type_=sa.String(length=NAME_LENGTH),
                existing_nullable=False,
            )


def _deny_client_access(table: str) -> None:
    """Cierra la tabla a la API de datos de Supabase (roles anon y authenticated)."""
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
    for table, column, old_length in NAME_COLUMNS:
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                column,
                existing_type=sa.String(length=NAME_LENGTH),
                type_=sa.String(length=old_length),
                existing_nullable=False,
            )
    op.drop_column("pets", "photos")
    op.drop_index(op.f("ix_personalities_name"), table_name=PERSONALITIES)
    op.drop_table(PERSONALITIES)
