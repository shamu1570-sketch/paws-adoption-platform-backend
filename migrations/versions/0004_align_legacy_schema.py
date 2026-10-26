"""Alinea con los modelos las bases creadas con el schema.sql original.

Renombra los índices `idx_*` a los nombres que usan los modelos (`ix_*`) y marca `created_at`
como obligatorio. En una base creada desde la migración 0001 no cambia nada.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# nombre heredado del schema.sql -> nombre que generan los modelos
INDEX_RENAMES = {
    "idx_shelters_city": "ix_shelters_city",
    "idx_pets_type": "ix_pets_type",
    "idx_pets_status": "ix_pets_adoption_status",
    "idx_pets_age_category": "ix_pets_age_category",
    "idx_pets_size": "ix_pets_size",
    "idx_pets_gender": "ix_pets_gender",
    "idx_pets_shelter_id": "ix_pets_shelter_id",
    "idx_adoption_requests_pet_id": "ix_adoption_requests_pet_id",
    "idx_adoption_requests_shelter_id": "ix_adoption_requests_shelter_id",
    "idx_adoption_requests_status": "ix_adoption_requests_status",
    "idx_surrender_requests_shelter_id": "ix_surrender_requests_shelter_id",
    "idx_surrender_requests_status": "ix_surrender_requests_status",
}
TABLES_WITH_CREATED_AT = ("shelters", "pets", "adoption_requests", "surrender_requests")


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgresql():
        return
    for legacy_name, model_name in INDEX_RENAMES.items():
        op.execute(f"ALTER INDEX IF EXISTS {legacy_name} RENAME TO {model_name}")
    for table in TABLES_WITH_CREATED_AT:
        op.execute(f"UPDATE {table} SET created_at = now() WHERE created_at IS NULL")
        op.alter_column(table, "created_at", nullable=False)


def downgrade() -> None:
    if not _is_postgresql():
        return
    for table in TABLES_WITH_CREATED_AT:
        op.alter_column(table, "created_at", nullable=True)
    for legacy_name, model_name in INDEX_RENAMES.items():
        op.execute(f"ALTER INDEX IF EXISTS {model_name} RENAME TO {legacy_name}")
