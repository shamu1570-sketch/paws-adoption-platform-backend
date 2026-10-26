"""Visibilidad de mascotas, códigos de seguimiento y estado "en entrevista".

- pets.is_visible: publicación en el catálogo público (las fichas existentes quedan visibles).
- adoption_requests / surrender_requests.tracking_code: código público de seguimiento;
  a las solicitudes existentes se les genera uno.
- surrender_requests.pet_id: ficha creada al recibir la mascota de una entrega aprobada.
- adoption_requests.status admite además 'en_entrevista'.

Revision ID: 0009
Revises: 0008
"""

import secrets
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ADOPTIONS = "adoption_requests"
SURRENDERS = "surrender_requests"
TRACKING_CODE = "tracking_code"
PET_ID = "pet_id"
TRACKING_PREFIXES = {ADOPTIONS: "ADOP", SURRENDERS: "ENTR"}
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
PET_FK = "fk_surrender_requests_pet_id_pets"
PET_UNIQUE = "uq_surrender_requests_pet_id"
STATUS_CHECK = "adoption_requests_status_check"


def _new_code(prefix: str) -> str:
    suffix = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
    return f"{prefix}-{datetime.now(UTC).year}-{suffix}"


def _add_tracking_code(table: str) -> None:
    """Agrega la columna, genera un código para cada fila existente y la vuelve obligatoria."""
    op.add_column(table, sa.Column(TRACKING_CODE, sa.String(length=24), nullable=True))
    bind = op.get_bind()
    rows = bind.execute(sa.text(f"SELECT id FROM {table}")).fetchall()
    for (row_id,) in rows:
        bind.execute(
            sa.text(f"UPDATE {table} SET {TRACKING_CODE} = :code WHERE id = :id"),
            {"code": _new_code(TRACKING_PREFIXES[table]), "id": row_id},
        )
    with op.batch_alter_table(table) as batch:
        batch.alter_column(TRACKING_CODE, existing_type=sa.String(length=24), nullable=False)
        batch.create_index(op.f(f"ix_{table}_{TRACKING_CODE}"), [TRACKING_CODE], unique=True)


def _set_status_check(statuses: tuple[str, ...]) -> None:
    """Reemplaza el CHECK de estados heredado del schema.sql (solo PostgreSQL)."""
    if op.get_bind().dialect.name != "postgresql":
        return
    allowed = ", ".join(f"'{status}'" for status in statuses)
    op.execute(f"ALTER TABLE {ADOPTIONS} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}")
    op.execute(
        f"ALTER TABLE {ADOPTIONS} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN ({allowed}))"
    )


def upgrade() -> None:
    op.add_column(
        "pets",
        sa.Column("is_visible", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.create_index(op.f("ix_pets_is_visible"), "pets", ["is_visible"])

    _add_tracking_code(ADOPTIONS)
    _add_tracking_code(SURRENDERS)

    with op.batch_alter_table(SURRENDERS) as batch:
        batch.add_column(sa.Column(PET_ID, sa.String(length=36), nullable=True))
        batch.create_unique_constraint(PET_UNIQUE, [PET_ID])
        batch.create_foreign_key(PET_FK, "pets", [PET_ID], ["id"], ondelete="SET NULL")

    _set_status_check(("pendiente", "en_entrevista", "aprobado", "rechazado"))


def downgrade() -> None:
    op.execute(f"UPDATE {ADOPTIONS} SET status = 'pendiente' WHERE status = 'en_entrevista'")
    _set_status_check(("pendiente", "aprobado", "rechazado"))

    with op.batch_alter_table(SURRENDERS) as batch:
        batch.drop_constraint(PET_FK, type_="foreignkey")
        batch.drop_constraint(PET_UNIQUE, type_="unique")
        batch.drop_column(PET_ID)

    for table in (SURRENDERS, ADOPTIONS):
        with op.batch_alter_table(table) as batch:
            batch.drop_index(op.f(f"ix_{table}_{TRACKING_CODE}"))
            batch.drop_column(TRACKING_CODE)

    op.drop_index(op.f("ix_pets_is_visible"), table_name="pets")
    op.drop_column("pets", "is_visible")
