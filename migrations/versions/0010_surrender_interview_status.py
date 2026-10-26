"""Las solicitudes de entrega admiten el estado 'en_entrevista' (cita de evaluación).

Solo cambia el CHECK heredado del schema.sql; en bases creadas desde las migraciones
no existía y se agrega. No aplica a SQLite.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "surrender_requests"
STATUS_CHECK = "surrender_requests_status_check"


def _set_status_check(statuses: tuple[str, ...]) -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    allowed = ", ".join(f"'{status}'" for status in statuses)
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}")
    op.execute(f"ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN ({allowed}))")


def upgrade() -> None:
    _set_status_check(("pendiente", "en_entrevista", "aprobado", "rechazado"))


def downgrade() -> None:
    op.execute(f"UPDATE {TABLE} SET status = 'pendiente' WHERE status = 'en_entrevista'")
    _set_status_check(("pendiente", "aprobado", "rechazado"))
