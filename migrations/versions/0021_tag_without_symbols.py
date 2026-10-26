"""Etiquetas del CMS sin caracteres especiales: "Únicos & Fuertes" -> "Únicos y Fuertes".

Desde ahora las etiquetas solo admiten letras, números y espacios. Solo se cambia el texto si
sigue siendo el original; si un administrador ya lo editó, se respeta.

Revision ID: 0021
Revises: 0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | Sequence[str] | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_KEY = {"section": "home", "key": "reason_4_badge"}
OLD_VALUE = "Únicos & Fuertes"
NEW_VALUE = "Únicos y Fuertes"

_UPDATE = sa.text(
    "UPDATE site_content SET value = :new WHERE section = :section AND key = :key AND value = :old"
)


def upgrade() -> None:
    op.get_bind().execute(_UPDATE, {**_KEY, "old": OLD_VALUE, "new": NEW_VALUE})


def downgrade() -> None:
    op.get_bind().execute(_UPDATE, {**_KEY, "old": NEW_VALUE, "new": OLD_VALUE})
