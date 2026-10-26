"""Edad estructurada (cantidad + unidad) en las solicitudes de entrega, como en las mascotas.

Completa `pet_age_value` y `pet_age_unit` a partir del texto libre de `pet_age` y lo
normaliza ("1.5 años" -> "18 meses").

Revision ID: 0018
Revises: 0017
"""

import re
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "surrender_requests"
MONTHS_PER_YEAR = 12
MAX_MONTHS = 24
MAX_YEARS = 30
# Si el texto no se puede interpretar se deja 1 año; el refugio lo corrige al registrar la ficha.
FALLBACK_AGE = (1, "años")
_AGE_TEXT = re.compile(r"(\d+(?:[.,]\d+)?)\s*(a[ñn]o|mes)", re.IGNORECASE)


def _parse_age(text: str) -> tuple[int, str]:
    match = _AGE_TEXT.search(text or "")
    if match is None:
        return FALLBACK_AGE
    amount = float(match.group(1).replace(",", "."))
    months = amount if match.group(2).lower() == "mes" else amount * MONTHS_PER_YEAR
    months = max(1, round(months))
    if months % MONTHS_PER_YEAR == 0 or months > MAX_MONTHS:
        return min(max(1, months // MONTHS_PER_YEAR), MAX_YEARS), "años"
    return months, "meses"


def _age_label(value: int, unit: str) -> str:
    if value == 1:
        return "1 año" if unit == "años" else "1 mes"
    return f"{value} {unit}"


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(TABLE, sa.Column("pet_age_value", sa.Integer(), nullable=True))
    op.add_column(TABLE, sa.Column("pet_age_unit", sa.String(length=10), nullable=True))
    for request_id, age in bind.execute(sa.text(f"select id, pet_age from {TABLE}")).all():
        value, unit = _parse_age(age)
        bind.execute(
            sa.text(
                f"update {TABLE} set pet_age_value = :value, pet_age_unit = :unit, "
                "pet_age = :label where id = :id"
            ),
            {"value": value, "unit": unit, "label": _age_label(value, unit), "id": request_id},
        )
    op.alter_column(TABLE, "pet_age_value", nullable=False)
    op.alter_column(TABLE, "pet_age_unit", nullable=False)


def downgrade() -> None:
    # `pet_age` conserva el texto, así que la solicitud sigue mostrando la edad.
    op.drop_column(TABLE, "pet_age_unit")
    op.drop_column(TABLE, "pet_age_value")
